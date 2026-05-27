import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { BundleBuilder } from '@html-video/core';
import type { CliContext } from '../context.js';
import { fail, ok } from '../output.js';

interface UploadOpts {
  intent: string;
  aspect?: string;
  durationTargetSec?: number;
  format?: 'mp4' | 'webm';
  fps?: number;
  mood?: string;
  language?: string;
  commercial?: boolean;
  files?: string[];
  inlineText?: string[];
  inlineDataFile?: string[];
}

export async function uploadAssets(ctx: CliContext, opts: UploadOpts): Promise<void> {
  if (!opts.intent) {
    fail('invalid-input', '--intent is required');
  }
  const builder = new BundleBuilder(ctx.assets, ctx.bundles);
  const files = (opts.files ?? []).map((f) => resolve(f));
  for (const f of files) {
    if (!existsSync(f)) fail('asset-not-found', `File not found: ${f}`);
  }

  const inlineText = (opts.inlineText ?? []).map((content) => ({ content }));
  const inlineData: { content: string }[] = [];
  for (const f of opts.inlineDataFile ?? []) {
    if (!existsSync(f)) fail('asset-not-found', `Data file not found: ${f}`);
    inlineData.push({ content: await readFile(f, 'utf8') });
  }

  const bundle = await builder.build({
    intent: opts.intent,
    preferences: {
      ...(opts.aspect !== undefined && { aspect: opts.aspect }),
      ...(opts.durationTargetSec !== undefined && { durationTargetSec: opts.durationTargetSec }),
      ...(opts.format !== undefined && { format: opts.format }),
      ...(opts.fps !== undefined && { fps: opts.fps }),
      ...(opts.mood !== undefined && { mood: opts.mood }),
      ...(opts.language !== undefined && { language: opts.language }),
      ...(opts.commercial !== undefined && { commercial: opts.commercial }),
    },
    files,
    inlineText,
    inlineData,
  });

  ok({
    bundle_id: bundle.id,
    asset_count: bundle.assets.length,
    intent: bundle.intent,
    assets: bundle.assets.map((a) => ({
      id: a.id,
      type: a.type,
      filename: a.metadata.filename,
      size_bytes: a.metadata.sizeBytes,
    })),
  });
}
