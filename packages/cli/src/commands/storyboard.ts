import { resolve } from 'node:path';
import type { CliContext } from '../context.js';
import { fail, ok, progress } from '../output.js';
import { planScenes } from '../planner.js';
import { startPreviewServer } from '../preview-server.js';

export async function generateStoryboard(
  ctx: CliContext,
  bundleId: string,
): Promise<void> {
  const bundle = await ctx.bundles.load(bundleId);
  const suggestions = planScenes(bundle, ctx.templates);
  if (suggestions.length === 0) {
    fail('invalid-input', 'Could not plan any scenes from the bundle (no matching templates or assets)');
  }
  const sb = await ctx.orchestrator.generate({ bundle, sceneSuggestions: suggestions });
  ok({
    storyboard_id: sb.id,
    bundle_id: sb.bundleId,
    scene_count: sb.scenes.length,
    estimated_duration_sec: sb.estimatedDurationSec,
    status: sb.status,
    scenes: sb.scenes.map((s) => ({
      id: s.id,
      template_id: s.template.id,
      engine: s.template.engine,
      start_sec: s.startSec,
      duration_sec: s.durationSec,
      agent_note: s.agentNote,
      preview_html: s.previewHtmlPath,
    })),
  });
}

interface EditOpts {
  op: 'remove-scene' | 'set-duration' | 'reorder' | 'approve';
  sceneId?: string;
  durationSec?: number;
  scenes?: string;
}

export async function editStoryboard(
  ctx: CliContext,
  storyboardId: string,
  opts: EditOpts,
): Promise<void> {
  let sb;
  switch (opts.op) {
    case 'remove-scene':
      if (!opts.sceneId) fail('invalid-input', '--scene-id required');
      sb = await ctx.orchestrator.removeScene(storyboardId, opts.sceneId!);
      break;
    case 'set-duration':
      if (!opts.sceneId || opts.durationSec == null)
        fail('invalid-input', '--scene-id and --duration-sec required');
      sb = await ctx.orchestrator.setDuration(storyboardId, opts.sceneId!, opts.durationSec!);
      break;
    case 'reorder':
      if (!opts.scenes) fail('invalid-input', '--scenes <id1,id2,...> required');
      sb = await ctx.orchestrator.reorderScenes(
        storyboardId,
        opts.scenes!.split(',').map((s) => s.trim()),
      );
      break;
    case 'approve':
      sb = await ctx.orchestrator.approve(storyboardId);
      break;
    default:
      fail('invalid-input', `Unknown op: ${opts.op}`);
  }
  ok({
    storyboard_id: sb.id,
    status: sb.status,
    scene_count: sb.scenes.length,
    estimated_duration_sec: sb.estimatedDurationSec,
  });
}

export async function previewStoryboard(
  ctx: CliContext,
  storyboardId: string,
  port: number,
): Promise<void> {
  const handle = await startPreviewServer(ctx, storyboardId, port);
  ok({
    storyboard_id: storyboardId,
    url: handle.url,
    port: handle.port,
    pid: process.pid,
    note: 'Preview server running. Press Ctrl+C to stop.',
  });
  // Keep process alive
  process.on('SIGINT', () => {
    handle.close();
    process.exit(0);
  });
}

export async function renderStoryboard(
  ctx: CliContext,
  storyboardId: string,
  outputPath: string,
  streamProgress: boolean,
): Promise<void> {
  const result = await ctx.orchestrator.renderToVideo({
    storyboardId,
    outputPath: resolve(outputPath),
    onProgress: streamProgress
      ? (pct, stage) => progress(stage, pct)
      : undefined,
  });
  ok({
    output_path: result.outputPath,
    duration_sec: result.durationSec,
    scene_outputs: result.sceneOutputs,
    note: 'v0.1: scene MP4s are stub placeholders; final concat is also a placeholder. Real rendering lands when adapter-hyperframes wires upstream.',
  });
}
