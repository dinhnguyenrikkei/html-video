#!/usr/bin/env node
import cacModule from 'cac';
import { bootstrap } from './context.js';
import { setJsonMode, fail } from './output.js';
import { runDoctor } from './commands/doctor.js';
import { listEngines } from './commands/list-engines.js';
import { searchTemplates, inspectTemplate } from './commands/templates.js';
import { uploadAssets } from './commands/assets.js';
import {
  generateStoryboard,
  editStoryboard,
  previewStoryboard,
  renderStoryboard,
} from './commands/storyboard.js';

// cac is a CJS default export; ESM interop sometimes wraps it in `.default`
// biome-ignore lint/suspicious/noExplicitAny: cac's types don't expose this shape
const cacFn: (name: string) => any =
  typeof cacModule === 'function' ? (cacModule as any) : (cacModule as any).default;
const cli = cacFn('html-video');

cli.option('--json', 'JSON output (default: on)', { default: true });
cli.option('--no-color', 'disable ANSI colors');
cli.option('--cwd <path>', 'project root');

cli.command('doctor', 'Diagnose environment').action(async (opts: any) => {
  setJsonMode(!!opts.json);
  const ctx = await bootstrap({ cwd: opts.cwd });
  await runDoctor(ctx);
});

cli.command('list-engines', 'List installed engine adapters').action(async (opts: any) => {
  setJsonMode(!!opts.json);
  const ctx = await bootstrap({ cwd: opts.cwd });
  await listEngines(ctx);
});

cli
  .command('search-templates', 'Search templates by intent')
  .option('--intent <text>', 'Free-text user intent')
  .option('--aspect <ratio>', '16:9 / 9:16 / 1:1')
  .option('--license-allow <list>', 'Comma-separated SPDX ids')
  .option('--top <n>', 'Top N matches', { default: 5 })
  .action(async (opts: any) => {
    setJsonMode(!!opts.json);
    const ctx = await bootstrap({ cwd: opts.cwd });
    await searchTemplates(ctx, {
      intent: opts.intent,
      aspect: opts.aspect,
      licenseAllow: opts.licenseAllow,
      top: Number(opts.top),
    });
  });

cli.command('inspect-template <id>', 'Show full metadata for a template').action(
  async (id: string, opts: any) => {
    setJsonMode(!!opts.json);
    const ctx = await bootstrap({ cwd: opts.cwd });
    await inspectTemplate(ctx, id);
  },
);

cli
  .command('assets upload', 'Create asset bundle from intent + files/text/data')
  .option('--intent <text>', 'One-sentence user intent (required)')
  .option('--aspect <ratio>', 'Aspect ratio')
  .option('--duration-target-sec <n>', 'Target total duration in seconds')
  .option('--format <fmt>', 'mp4 or webm')
  .option('--fps <n>', 'fps')
  .option('--mood <text>', 'Free-text mood')
  .option('--language <code>', 'zh-CN or en-US etc')
  .option('--commercial', 'Filter to commercial-use templates')
  .option('--files <paths>', 'Comma-separated file paths', { type: [String] })
  .option('--inline-text <text>', 'Inline text asset (repeatable)', { type: [String] })
  .option('--inline-data-file <path>', 'JSON/CSV file to embed (repeatable)', { type: [String] })
  .action(async (opts: any) => {
    setJsonMode(!!opts.json);
    const ctx = await bootstrap({ cwd: opts.cwd });
    await uploadAssets(ctx, {
      intent: opts.intent,
      aspect: opts.aspect,
      durationTargetSec: opts.durationTargetSec ? Number(opts.durationTargetSec) : undefined,
      format: opts.format,
      fps: opts.fps ? Number(opts.fps) : undefined,
      mood: opts.mood,
      language: opts.language,
      commercial: !!opts.commercial,
      files: flattenList(opts.files),
      inlineText: flattenList(opts.inlineText),
      inlineDataFile: flattenList(opts.inlineDataFile),
    });
  });

cli
  .command('storyboard generate <bundleId>', 'Generate storyboard from a bundle')
  .action(async (bundleId: string, opts: any) => {
    setJsonMode(!!opts.json);
    const ctx = await bootstrap({ cwd: opts.cwd });
    await generateStoryboard(ctx, bundleId);
  });

cli
  .command('storyboard edit <storyboardId>', 'Edit storyboard')
  .option('--op <op>', 'remove-scene | set-duration | reorder | approve')
  .option('--scene-id <id>', 'Scene id (for remove-scene / set-duration)')
  .option('--duration-sec <n>', 'New duration in seconds')
  .option('--scenes <ids>', 'Comma-separated ids for reorder')
  .action(async (storyboardId: string, opts: any) => {
    setJsonMode(!!opts.json);
    const ctx = await bootstrap({ cwd: opts.cwd });
    if (!opts.op) fail('invalid-input', '--op required');
    await editStoryboard(ctx, storyboardId, {
      op: opts.op,
      sceneId: opts.sceneId,
      durationSec: opts.durationSec ? Number(opts.durationSec) : undefined,
      scenes: opts.scenes,
    });
  });

cli
  .command('storyboard preview <storyboardId>', 'Start preview server')
  .option('--port <n>', 'Port (0=auto)', { default: 3071 })
  .action(async (storyboardId: string, opts: any) => {
    setJsonMode(!!opts.json);
    const ctx = await bootstrap({ cwd: opts.cwd });
    await previewStoryboard(ctx, storyboardId, Number(opts.port));
  });

cli
  .command('storyboard render <storyboardId>', 'Render storyboard to MP4')
  .option('--output <path>', 'Output MP4 path', { default: 'output.mp4' })
  .option('--stream-progress', 'Emit progress events as NDJSON')
  .action(async (storyboardId: string, opts: any) => {
    setJsonMode(!!opts.json);
    const ctx = await bootstrap({ cwd: opts.cwd });
    await renderStoryboard(ctx, storyboardId, opts.output, !!opts.streamProgress);
  });

cli.help();
cli.version('0.1.0');
cli.parse();

function flattenList(input: unknown): string[] | undefined {
  if (input == null) return undefined;
  if (Array.isArray(input)) {
    const out: string[] = [];
    for (const item of input) {
      if (typeof item === 'string') {
        out.push(...item.split(',').map((s) => s.trim()).filter(Boolean));
      }
    }
    return out;
  }
  if (typeof input === 'string') {
    return input.split(',').map((s) => s.trim()).filter(Boolean);
  }
  return undefined;
}
