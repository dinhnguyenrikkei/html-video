/**
 * Storyboard orchestrator: takes an AssetBundle + agent-suggested scene plan,
 * delegates per-scene HTML rendering to engine adapters, persists the result.
 *
 * RFC-04 §Stage 2 (generate) + §Stage 3 (edit) + §Stage 4 (render).
 */

import { randomUUID } from 'node:crypto';
import { join } from 'node:path';
import { mkdir, writeFile } from 'node:fs/promises';
import type {
  Asset,
  AssetBundle,
  EngineAdapter,
  EngineId,
  Scene,
  Storyboard,
  TemplateMetadata,
  TransitionId,
} from './types/index.js';
import { HtmlVideoError } from './errors.js';
import type { EngineRegistry, StoryboardStore, TemplateRegistry } from './registry.js';

export interface SceneSuggestion {
  templateId: string;
  variables: Record<string, unknown>;
  assetRefs: string[];
  durationSec: number;
  agentNote: string;
  transitionToNext?: TransitionId;
}

export interface GenerateOpts {
  bundle: AssetBundle;
  /** Pre-computed scene suggestions from the agent. v0.1 doesn't auto-plan; agent computes externally. */
  sceneSuggestions: SceneSuggestion[];
  defaultTransition?: TransitionId;
}

export interface OrchestratorDeps {
  projectRoot: string;
  engines: EngineRegistry;
  templates: TemplateRegistry;
  storyboards: StoryboardStore;
}

export class StoryboardOrchestrator {
  constructor(private readonly deps: OrchestratorDeps) {}

  /** Generate a storyboard from a bundle + scene suggestions, rendering HTML per scene. */
  async generate(opts: GenerateOpts): Promise<Storyboard> {
    const { bundle, sceneSuggestions, defaultTransition } = opts;
    const sbId = `sb_${randomUUID().slice(0, 12)}`;
    const sbDir = join(this.deps.projectRoot, '.html-video', 'storyboards', sbId);
    await mkdir(join(sbDir, 'scenes'), { recursive: true });

    const scenes: Scene[] = [];
    let cursor = 0;
    let i = 0;
    for (const sug of sceneSuggestions) {
      const scene = await this.renderSceneToHtml({
        suggestion: sug,
        bundle,
        sbDir,
        index: i,
        startSec: cursor,
      });
      scenes.push(scene);
      cursor += sug.durationSec;
      i += 1;
    }

    const sb: Storyboard = {
      id: sbId,
      bundleId: bundle.id,
      intent: bundle.intent,
      scenes,
      ...(defaultTransition !== undefined && { defaultTransition }),
      estimatedDurationSec: cursor,
      status: 'ready-for-review',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    await this.deps.storyboards.save(sb);
    return sb;
  }

  private async renderSceneToHtml(args: {
    suggestion: SceneSuggestion;
    bundle: AssetBundle;
    sbDir: string;
    index: number;
    startSec: number;
  }): Promise<Scene> {
    const { suggestion, bundle, sbDir, index, startSec } = args;
    const tmpl = this.deps.templates.get(suggestion.templateId);
    const adapter = this.deps.engines.get(tmpl.engine);

    const sceneId = `s${String(index).padStart(3, '0')}_${randomUUID().slice(0, 6)}`;
    const sceneDir = join(sbDir, 'scenes', sceneId);
    await mkdir(sceneDir, { recursive: true });

    const templateRef = templateRefFromMeta(tmpl);
    const renderInput = {
      template: templateRef,
      variables: suggestion.variables,
      config: {
        format: 'mp4' as const,
        resolution: bundle.preferences.resolution ?? { width: 1920, height: 1080 },
        fps: bundle.preferences.fps ?? 60,
        duration: suggestion.durationSec,
        outputPath: join(sceneDir, 'scene.mp4'),
      },
    };
    const renderCtx = { workDir: sceneDir };

    let htmlPath: string;
    let posterPath: string | undefined;
    let referencedAssets: { assetId: string; usagePath: string }[] = [];

    if (adapter.renderToHtml) {
      const out = await adapter.renderToHtml(renderInput, renderCtx);
      htmlPath = out.htmlPath;
      posterPath = out.posterPath;
      referencedAssets = out.referencedAssets;
    } else {
      // Fallback: render an empty placeholder HTML so storyboard preview still works
      htmlPath = join(sceneDir, 'preview.html');
      await writeFile(
        htmlPath,
        `<!doctype html><html><head><meta charset="utf-8"><title>${tmpl.name}</title>
<style>body{margin:0;display:grid;place-items:center;height:100vh;font-family:system-ui;background:#222;color:#eee}</style>
</head><body><div><h1>${tmpl.name}</h1><p>Engine ${tmpl.engine} has no renderToHtml; placeholder shown.</p>
<pre>${escapeHtml(JSON.stringify(suggestion.variables, null, 2))}</pre></div></body></html>`,
        'utf8',
      );
    }

    return {
      id: sceneId,
      template: { id: tmpl.id, engine: tmpl.engine },
      variables: suggestion.variables,
      assetRefs: suggestion.assetRefs.length > 0 ? suggestion.assetRefs : referencedAssets.map((r) => r.assetId),
      startSec,
      durationSec: suggestion.durationSec,
      ...(suggestion.transitionToNext !== undefined && { transitionToNext: suggestion.transitionToNext }),
      agentNote: suggestion.agentNote,
      previewHtmlPath: htmlPath,
      ...(posterPath !== undefined && { previewPosterPath: posterPath }),
    };
  }

  // ------------- Edit operations (RFC-04 §Stage 3) -------------

  async addScene(
    storyboardId: string,
    suggestion: SceneSuggestion,
    bundle: AssetBundle,
    insertAtSec: number,
  ): Promise<Storyboard> {
    const sb = await this.deps.storyboards.load(storyboardId);
    const sbDir = join(this.deps.projectRoot, '.html-video', 'storyboards', sb.id);
    const scene = await this.renderSceneToHtml({
      suggestion,
      bundle,
      sbDir,
      index: sb.scenes.length,
      startSec: insertAtSec,
    });
    // Insert and re-flow startSec for everything after
    const before = sb.scenes.filter((s) => s.startSec < insertAtSec);
    const after = sb.scenes.filter((s) => s.startSec >= insertAtSec);
    const newScenes = [...before, scene, ...after];
    let cursor = 0;
    for (const s of newScenes) {
      s.startSec = cursor;
      cursor += s.durationSec;
    }
    sb.scenes = newScenes;
    sb.estimatedDurationSec = cursor;
    sb.updatedAt = new Date().toISOString();
    await this.deps.storyboards.save(sb);
    return sb;
  }

  async removeScene(storyboardId: string, sceneId: string): Promise<Storyboard> {
    const sb = await this.deps.storyboards.load(storyboardId);
    const newScenes = sb.scenes.filter((s) => s.id !== sceneId);
    let cursor = 0;
    for (const s of newScenes) {
      s.startSec = cursor;
      cursor += s.durationSec;
    }
    sb.scenes = newScenes;
    sb.estimatedDurationSec = cursor;
    sb.updatedAt = new Date().toISOString();
    await this.deps.storyboards.save(sb);
    return sb;
  }

  async setDuration(
    storyboardId: string,
    sceneId: string,
    durationSec: number,
  ): Promise<Storyboard> {
    const sb = await this.deps.storyboards.load(storyboardId);
    const scene = sb.scenes.find((s) => s.id === sceneId);
    if (!scene) throw new HtmlVideoError('invalid-input', `Scene ${sceneId} not found`);
    scene.durationSec = durationSec;
    let cursor = 0;
    for (const s of sb.scenes) {
      s.startSec = cursor;
      cursor += s.durationSec;
    }
    sb.estimatedDurationSec = cursor;
    sb.updatedAt = new Date().toISOString();
    await this.deps.storyboards.save(sb);
    return sb;
  }

  async reorderScenes(storyboardId: string, sceneIds: string[]): Promise<Storyboard> {
    const sb = await this.deps.storyboards.load(storyboardId);
    if (sceneIds.length !== sb.scenes.length) {
      throw new HtmlVideoError(
        'invalid-input',
        `Reorder must list all ${sb.scenes.length} scenes; got ${sceneIds.length}`,
      );
    }
    const map = new Map(sb.scenes.map((s) => [s.id, s]));
    const reordered: Scene[] = [];
    for (const id of sceneIds) {
      const s = map.get(id);
      if (!s) throw new HtmlVideoError('invalid-input', `Unknown scene id ${id}`);
      reordered.push(s);
    }
    let cursor = 0;
    for (const s of reordered) {
      s.startSec = cursor;
      cursor += s.durationSec;
    }
    sb.scenes = reordered;
    sb.estimatedDurationSec = cursor;
    sb.updatedAt = new Date().toISOString();
    await this.deps.storyboards.save(sb);
    return sb;
  }

  async approve(storyboardId: string): Promise<Storyboard> {
    const sb = await this.deps.storyboards.load(storyboardId);
    sb.status = 'approved';
    sb.updatedAt = new Date().toISOString();
    await this.deps.storyboards.save(sb);
    return sb;
  }

  // ------------- Final MP4 render (RFC-04 §Stage 4) -------------

  /**
   * Render each scene to MP4 then concat. v0.1: each adapter renders independently;
   * concat uses ffmpeg via core/ffmpeg helper (placeholder in v0.1).
   */
  async renderToVideo(args: {
    storyboardId: string;
    outputPath: string;
    onProgress?: (pct: number, stage: string) => void;
    signal?: AbortSignal;
  }): Promise<{ outputPath: string; sceneOutputs: string[]; durationSec: number }> {
    const sb = await this.deps.storyboards.load(args.storyboardId);
    if (sb.status !== 'approved' && sb.status !== 'ready-for-review') {
      throw new HtmlVideoError(
        'storyboard-not-approved',
        `Storyboard status is "${sb.status}"; must be approved before render`,
      );
    }
    args.onProgress?.(0, 'preparing');

    const sceneOutputs: string[] = [];
    for (let i = 0; i < sb.scenes.length; i++) {
      const scene = sb.scenes[i];
      if (!scene) continue;
      const adapter: EngineAdapter = this.deps.engines.get(scene.template.engine);
      const tmpl = this.deps.templates.get(scene.template.id);
      const sceneOut = scene.previewHtmlPath.replace(/\.html$/, '.mp4');
      args.onProgress?.(Math.floor((i / sb.scenes.length) * 90), 'rendering');
      await adapter.render(
        {
          template: templateRefFromMeta(tmpl),
          variables: scene.variables,
          config: {
            format: 'mp4',
            resolution: { width: 1920, height: 1080 },
            fps: 60,
            duration: scene.durationSec,
            outputPath: sceneOut,
          },
        },
        { workDir: sceneOut.replace(/\/[^/]+$/, ''), signal: args.signal },
      );
      sceneOutputs.push(sceneOut);
    }

    args.onProgress?.(95, 'muxing');
    // v0.1 placeholder: just record what would be concatenated.
    // v0.2 will shell out to ffmpeg concat demuxer.
    await writeFile(
      `${args.outputPath}.concat-plan.txt`,
      sceneOutputs.map((p) => `file '${p}'`).join('\n'),
      'utf8',
    );
    await writeFile(args.outputPath, '<placeholder mp4>\n', 'utf8');

    sb.status = 'rendered';
    sb.updatedAt = new Date().toISOString();
    await this.deps.storyboards.save(sb);

    args.onProgress?.(100, 'done');
    return {
      outputPath: args.outputPath,
      sceneOutputs,
      durationSec: sb.estimatedDurationSec,
    };
  }
}

function templateRefFromMeta(meta: TemplateMetadata) {
  if (!meta.__dir) {
    throw new HtmlVideoError(
      'template-invalid',
      `Template ${meta.id} has no __dir set; was it loaded via TemplateRegistry?`,
    );
  }
  return {
    id: meta.id,
    engine: meta.engine,
    sourcePath: join(meta.__dir, meta.source_entry),
  };
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };
    return map[c] ?? c;
  });
}

// Helper exported for adapter use cases / tests
export function _internal_templateRefFromMeta(m: TemplateMetadata) {
  return templateRefFromMeta(m);
}
