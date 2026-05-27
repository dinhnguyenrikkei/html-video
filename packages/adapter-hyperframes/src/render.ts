/**
 * Hyperframes render() and renderToHtml().
 *
 * v0.1 STATUS: stubbed — does not actually invoke Hyperframes upstream yet.
 * Generates a placeholder MP4 marker file + a syntactically valid preview HTML
 * so the storyboard pipeline runs end-to-end. Real upstream wiring lands in v0.2
 * once the contract is validated by the smoke test.
 */

import { copyFile, mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import type {
  HtmlSceneOutput,
  RenderContext,
  RenderInput,
  RenderOutput,
} from '@html-video/core';
import { HtmlVideoError } from '@html-video/core';

const ADAPTER_VERSION = '0.1.0-stub';

/** Stubbed full render. Writes a placeholder file at outputPath. */
export async function render(input: RenderInput, ctx: RenderContext): Promise<RenderOutput> {
  ctx.onProgress?.(5, 'preparing');
  const outDir = dirname(input.config.outputPath);
  await mkdir(outDir, { recursive: true });
  if (ctx.signal?.aborted) throw new HtmlVideoError('cancelled', 'Aborted');

  ctx.onProgress?.(50, 'rendering');
  const stub = [
    `# Hyperframes adapter stub render`,
    `template_id=${input.template.id}`,
    `source=${input.template.sourcePath}`,
    `format=${input.config.format}`,
    `resolution=${input.config.resolution.width}x${input.config.resolution.height}`,
    `fps=${input.config.fps}`,
    `duration=${input.config.duration}`,
    `vars=${JSON.stringify(input.variables)}`,
    `ts=${new Date().toISOString()}`,
  ].join('\n');
  await writeFile(input.config.outputPath, stub, 'utf8');

  ctx.onProgress?.(95, 'muxing');
  const totalDuration =
    input.config.duration === 'auto' ? 5 : input.config.duration;
  const fps = input.config.fps;
  const frames = Math.round(totalDuration * fps);

  ctx.onProgress?.(100, 'done');
  return {
    outputPath: input.config.outputPath,
    meta: {
      durationSec: totalDuration,
      fileSizeBytes: Buffer.byteLength(stub),
      actualResolution: input.config.resolution,
      fps,
      renderedFrames: frames,
      renderWallClockSec: 0.05,
      engineVersion: `hyperframes-stub@${ADAPTER_VERSION}`,
    },
    diagnostics: ['hyperframes adapter is in stub mode (v0.1)'],
  };
}

/**
 * Render template to a single HTML preview.
 *
 * v0.1: read the source HTML file (a Hyperframes template is HTML+CSS+JS),
 * inject a banner showing the variables, copy referenced assets, write to ctx.workDir.
 * Real upstream Hyperframes integration will replace the inject + add a frame-bound clock.
 */
export async function renderToHtml(
  input: RenderInput,
  ctx: RenderContext,
): Promise<HtmlSceneOutput> {
  if (!existsSync(input.template.sourcePath)) {
    throw new HtmlVideoError(
      'template-invalid',
      `Source not found: ${input.template.sourcePath}`,
    );
  }

  await mkdir(ctx.workDir, { recursive: true });
  const htmlPath = join(ctx.workDir, 'preview.html');
  const posterPath = join(ctx.workDir, 'poster.svg');

  const sourceHtml = await readFile(input.template.sourcePath, 'utf8');
  const augmented = sourceHtml.replace(
    '</body>',
    `<script>
window.__HV_VARS__ = ${JSON.stringify(input.variables)};
window.__HV_DURATION__ = ${typeof input.config.duration === 'number' ? input.config.duration : 5};
console.log('html-video preview vars', window.__HV_VARS__);
</script></body>`,
  );
  await writeFile(htmlPath, augmented, 'utf8');

  // Cheap poster: an SVG placeholder we draw ourselves (no headless chromium yet).
  const { width, height } = input.config.resolution;
  const title = String(input.variables.title ?? input.template.id);
  const poster = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
  <rect width="100%" height="100%" fill="#1a1a1a"/>
  <text x="50%" y="50%" fill="#eee" font-family="Inter, system-ui, sans-serif"
        font-size="72" text-anchor="middle" dominant-baseline="middle">${escapeXml(title)}</text>
  <text x="50%" y="${height - 80}" fill="#888" font-family="monospace" font-size="32"
        text-anchor="middle">hyperframes · ${input.template.id}</text>
</svg>`;
  await writeFile(posterPath, poster, 'utf8');

  // Copy any referenced asset files mentioned in variables (best-effort)
  const referencedAssets: { assetId: string; usagePath: string }[] = [];
  for (const v of Object.values(input.variables)) {
    if (typeof v !== 'string') continue;
    if (!v.includes('/.html-video/bundles/')) continue;
    if (!existsSync(v)) continue;
    const dest = join(ctx.workDir, 'assets', v.split('/').pop() ?? 'asset');
    await mkdir(dirname(dest), { recursive: true });
    if (!existsSync(dest)) await copyFile(v, dest);
    const m = /assets\/([0-9a-f]{40})\./.exec(v);
    if (m && m[1]) {
      referencedAssets.push({ assetId: m[1], usagePath: dest });
    }
  }

  const totalDuration =
    input.config.duration === 'auto' ? 5 : input.config.duration;
  return {
    htmlPath,
    referencedAssets,
    posterPath,
    durationSec: totalDuration,
  };
}

function escapeXml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&apos;',
    };
    return map[c] ?? c;
  });
}

// silence unused imports warning until real impl uses them
void stat;
