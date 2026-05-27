/**
 * AssetBundle helpers — build/load bundles from user inputs.
 * RFC-04 §Stage 1.
 */

import { randomUUID } from 'node:crypto';
import type { Asset, AssetBundle, UserPreferences } from './types/index.js';
import type { AssetStore } from './asset-store.js';
import type { BundleStore } from './registry.js';

export interface BundleInput {
  intent: string;
  preferences: UserPreferences;
  files?: string[];
  inlineText?: { content: string; tags?: string[]; caption?: string }[];
  inlineData?: { content: string; tags?: string[]; caption?: string }[];
}

export class BundleBuilder {
  constructor(
    private readonly assetStore: AssetStore,
    private readonly bundleStore: BundleStore,
  ) {}

  async build(input: BundleInput): Promise<AssetBundle> {
    const id = `b_${randomUUID().slice(0, 12)}`;
    const assets: Asset[] = [];

    for (const f of input.files ?? []) {
      assets.push(await this.assetStore.addFileAsset(id, f));
    }
    for (const t of input.inlineText ?? []) {
      assets.push(
        await this.assetStore.addInlineAsset(id, t.content, 'text', t.tags ?? [], t.caption),
      );
    }
    for (const d of input.inlineData ?? []) {
      assets.push(
        await this.assetStore.addInlineAsset(id, d.content, 'data', d.tags ?? [], d.caption),
      );
    }

    const bundle: AssetBundle = {
      id,
      intent: input.intent,
      preferences: input.preferences,
      assets,
      createdAt: new Date().toISOString(),
    };
    await this.bundleStore.save(bundle);
    return bundle;
  }
}
