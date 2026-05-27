/**
 * End-to-end smoke test (no agent, no real Hyperframes).
 * Asserts the v0.1 pipeline runs cleanly:
 *   doctor → assets upload → storyboard generate → edit → render
 */

import { mkdtemp, mkdir, writeFile, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { existsSync } from 'node:fs';
import { BundleBuilder } from '@html-video/core';
import { bootstrap } from './context.js';

const log = (msg: string) => process.stdout.write(`▸ ${msg}\n`);
const ok = (msg: string) => process.stdout.write(`  ✓ ${msg}\n`);

async function main() {
  // Create a throwaway project root with .html-video/ inside
  const projectRoot = await mkdtemp(join(tmpdir(), 'html-video-smoke-'));
  await mkdir(join(projectRoot, '.html-video'), { recursive: true });
  log(`workdir: ${projectRoot}`);

  // packages/cli/dist/smoke.js → up 3 levels → monorepo root
  const monorepoRoot = resolve(__dirname_polyfill(), '..', '..', '..');

  // Make a fake logo file in projectRoot so planner emits the intro scene
  const fakeLogoPath = join(projectRoot, 'fake-logo.png');
  // 1×1 transparent PNG bytes (smallest valid)
  const PNG_1x1 = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=',
    'base64',
  );
  await writeFile(fakeLogoPath, PNG_1x1);

  const fakeDataJson = JSON.stringify([
    { label: 'Templates', value: 231, color: '#ffb84d' },
    { label: 'Skills', value: 15, color: '#9b87f5' },
    { label: 'Systems', value: 150, color: '#6dd99c' },
  ]);

  log('bootstrap context');
  const ctx = await bootstrap({ cwd: projectRoot });
  // Ensure templates loaded by re-scanning monorepo if needed
  if (ctx.templates.list().length === 0) {
    await ctx.templates.scan(join(monorepoRoot, 'templates'));
  }
  ok(`engines: ${ctx.engines.list().map((e) => e.id).join(', ')}`);
  ok(`templates: ${ctx.templates.list().map((t) => t.id).join(', ')}`);

  // 1. Doctor (returns programmatically OK if engines+templates loaded)
  log('doctor');
  ok(`engines=${ctx.engines.list().length} templates=${ctx.templates.list().length}`);

  // 2. Build a bundle via BundleBuilder directly (CLI assets upload uses this)
  log('build bundle');
  const builder = new BundleBuilder(ctx.assets, ctx.bundles);
  const bundle = await builder.build({
    intent: 'Showcase OD plugin library distribution',
    preferences: { aspect: '16:9', commercial: true, language: 'en-US' },
    files: [fakeLogoPath],
    inlineText: [{ content: 'Design that evolves itself' }],
    inlineData: [{ content: fakeDataJson }],
  });
  ok(`bundle ${bundle.id} with ${bundle.assets.length} assets`);

  // 3. Generate storyboard
  log('generate storyboard');
  const { planScenes } = await import('./planner.js');
  const suggestions = planScenes(bundle, ctx.templates);
  if (suggestions.length === 0) throw new Error('Planner produced 0 scenes');
  ok(`planner emitted ${suggestions.length} scene suggestions`);
  const sb = await ctx.orchestrator.generate({ bundle, sceneSuggestions: suggestions });
  ok(`storyboard ${sb.id} with ${sb.scenes.length} scenes, ${sb.estimatedDurationSec}s total`);

  // 4. Verify each scene has a preview HTML
  log('verify scene previews exist');
  for (const scene of sb.scenes) {
    if (!existsSync(scene.previewHtmlPath)) {
      throw new Error(`Scene ${scene.id} preview missing: ${scene.previewHtmlPath}`);
    }
    const content = await readFile(scene.previewHtmlPath, 'utf8');
    if (!content.includes('html-video')) {
      // Most reference templates contain the string "html-video" in title/comment
      // Just sanity check that the file is non-trivially HTML
      if (!content.includes('<html')) {
        throw new Error(`Scene ${scene.id} preview HTML looks malformed`);
      }
    }
    ok(`${scene.id}: ${scene.template.id} (${scene.durationSec}s) → ${scene.previewHtmlPath}`);
  }

  // 5. Edit: trim a scene
  log('edit: shorten first scene to 2s');
  const shortenedSb = await ctx.orchestrator.setDuration(sb.id, sb.scenes[0]!.id, 2);
  if (shortenedSb.scenes[0]!.durationSec !== 2)
    throw new Error('setDuration did not persist');
  ok(`new total: ${shortenedSb.estimatedDurationSec}s`);

  // 6. Approve
  log('approve');
  const approved = await ctx.orchestrator.approve(sb.id);
  if (approved.status !== 'approved') throw new Error('approve did not flip status');
  ok(`status: ${approved.status}`);

  // 7. Render to MP4 (stub)
  log('render to MP4 (stub)');
  const outputPath = join(projectRoot, 'final.mp4');
  const result = await ctx.orchestrator.renderToVideo({
    storyboardId: sb.id,
    outputPath,
    onProgress: (pct, stage) => {
      if (pct === 0 || pct === 100 || pct % 25 === 0) ok(`render ${stage} ${pct}%`);
    },
  });
  if (!existsSync(result.outputPath)) throw new Error('Render output missing');
  ok(`final: ${result.outputPath}`);
  ok(`scene MP4s: ${result.sceneOutputs.length}`);

  process.stdout.write('\n✅ smoke test passed\n');
}

// __dirname polyfill for ESM
function __dirname_polyfill(): string {
  const url = import.meta.url;
  const path = url.replace(/^file:\/\//, '');
  return path.replace(/\/[^/]*$/, '');
}

main().catch((err) => {
  process.stderr.write(`\n❌ smoke test failed: ${err.message ?? err}\n`);
  if (err.stack) process.stderr.write(err.stack + '\n');
  process.exit(1);
});
