/**
 * Content-addressed asset store.
 * Files are stored by sha1 of content; deduplication is automatic.
 * RFC-04 §Storyboard 文件存储约定.
 */

import { createHash } from 'node:crypto';
import { copyFile, mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { extname, join } from 'node:path';
import type { Asset, AssetType } from './types/index.js';
import { HtmlVideoError } from './errors.js';

export interface AssetStoreOptions {
  /** Project root that contains .html-video/ */
  projectRoot: string;
}

export class AssetStore {
  private readonly bundlesDir: string;

  constructor(opts: AssetStoreOptions) {
    this.bundlesDir = join(opts.projectRoot, '.html-video', 'bundles');
  }

  private bundleDir(bundleId: string): string {
    return join(this.bundlesDir, bundleId);
  }

  private assetsDir(bundleId: string): string {
    return join(this.bundleDir(bundleId), 'assets');
  }

  /** Compute content-addressed id (sha1 of bytes). */
  static async computeId(filePath: string): Promise<string> {
    const buf = await readFile(filePath);
    return createHash('sha1').update(buf).digest('hex');
  }

  /** Compute id for inline content (text/data). */
  static computeInlineId(content: string): string {
    return createHash('sha1').update(content).digest('hex');
  }

  /** Best-effort mime type detection by extension. v0.1 doesn't sniff bytes. */
  static guessMime(filePath: string): { mime: string; type: AssetType } {
    const ext = extname(filePath).toLowerCase();
    const map: Record<string, { mime: string; type: AssetType }> = {
      '.png': { mime: 'image/png', type: 'image' },
      '.jpg': { mime: 'image/jpeg', type: 'image' },
      '.jpeg': { mime: 'image/jpeg', type: 'image' },
      '.webp': { mime: 'image/webp', type: 'image' },
      '.gif': { mime: 'image/gif', type: 'image' },
      '.svg': { mime: 'image/svg+xml', type: 'image' },
      '.mp3': { mime: 'audio/mpeg', type: 'audio' },
      '.wav': { mime: 'audio/wav', type: 'audio' },
      '.aac': { mime: 'audio/aac', type: 'audio' },
      '.m4a': { mime: 'audio/mp4', type: 'audio' },
      '.mp4': { mime: 'video/mp4', type: 'video' },
      '.webm': { mime: 'video/webm', type: 'video' },
      '.mov': { mime: 'video/quicktime', type: 'video' },
      '.csv': { mime: 'text/csv', type: 'data' },
      '.json': { mime: 'application/json', type: 'data' },
      '.tsv': { mime: 'text/tab-separated-values', type: 'data' },
      '.txt': { mime: 'text/plain', type: 'text' },
      '.md': { mime: 'text/markdown', type: 'text' },
    };
    return map[ext] ?? { mime: 'application/octet-stream', type: 'reference-link' };
  }

  /** Add a file asset by copying it into the bundle. */
  async addFileAsset(
    bundleId: string,
    sourcePath: string,
    userTags: string[] = [],
    userCaption?: string,
  ): Promise<Asset> {
    if (!existsSync(sourcePath)) {
      throw new HtmlVideoError('asset-not-found', `Source file not found: ${sourcePath}`);
    }
    const id = await AssetStore.computeId(sourcePath);
    const { mime, type } = AssetStore.guessMime(sourcePath);
    const ext = extname(sourcePath);
    const dir = this.assetsDir(bundleId);
    await mkdir(dir, { recursive: true });
    const destPath = join(dir, `${id}${ext}`);
    if (!existsSync(destPath)) {
      await copyFile(sourcePath, destPath);
    }
    const st = await stat(destPath);
    const filename = sourcePath.split('/').pop() ?? sourcePath;
    return {
      id,
      type,
      path: destPath,
      metadata: {
        filename,
        mimeType: mime,
        sizeBytes: st.size,
        ...(userCaption !== undefined && { userCaption }),
      },
      userTags,
    };
  }

  /** Add an inline text/data asset. */
  async addInlineAsset(
    bundleId: string,
    content: string,
    type: 'text' | 'data',
    userTags: string[] = [],
    userCaption?: string,
  ): Promise<Asset> {
    const id = AssetStore.computeInlineId(content);
    const dir = this.assetsDir(bundleId);
    await mkdir(dir, { recursive: true });
    const ext = type === 'data' ? '.json' : '.txt';
    const destPath = join(dir, `${id}${ext}`);
    if (!existsSync(destPath)) {
      await writeFile(destPath, content, 'utf8');
    }
    return {
      id,
      type,
      path: destPath,
      content,
      metadata: {
        filename: `inline${ext}`,
        mimeType: type === 'data' ? 'application/json' : 'text/plain',
        sizeBytes: Buffer.byteLength(content, 'utf8'),
        ...(userCaption !== undefined && { userCaption }),
      },
      userTags,
    };
  }

  /** Resolve absolute path of an asset within a bundle. */
  resolvePath(bundleId: string, asset: Asset): string {
    if (asset.path) return asset.path;
    throw new HtmlVideoError('asset-not-found', `Asset ${asset.id} has no path`);
  }
}
