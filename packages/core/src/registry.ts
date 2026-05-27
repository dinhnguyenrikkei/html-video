/**
 * Registries for engine adapters, templates, asset bundles, and storyboards.
 * v0.1: in-memory + JSON-on-disk persistence (sqlite slot reserved for v0.2).
 */

import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { parse as parseYaml } from 'yaml';
import type {
  AssetBundle,
  EngineAdapter,
  EngineId,
  Storyboard,
  TemplateMetadata,
} from './types/index.js';
import { HtmlVideoError } from './errors.js';

// ---------------------------------------------------------------------------
// EngineRegistry — adapter discovery & retrieval
// ---------------------------------------------------------------------------

export class EngineRegistry {
  private adapters = new Map<EngineId, EngineAdapter>();

  register(adapter: EngineAdapter): void {
    this.adapters.set(adapter.id, adapter);
  }

  get(id: EngineId): EngineAdapter {
    const a = this.adapters.get(id);
    if (!a) {
      throw new HtmlVideoError(
        'engine-not-registered',
        `Engine "${id}" is not registered. Did you forget to install @html-video/adapter-${id}?`,
      );
    }
    return a;
  }

  list(): EngineAdapter[] {
    return [...this.adapters.values()];
  }

  has(id: EngineId): boolean {
    return this.adapters.has(id);
  }
}

// ---------------------------------------------------------------------------
// TemplateRegistry — fs-based scan of templates/ directory
// ---------------------------------------------------------------------------

export class TemplateRegistry {
  private templates = new Map<string, TemplateMetadata>();

  /** Scan a directory containing one subdirectory per template. */
  async scan(rootDir: string): Promise<TemplateMetadata[]> {
    if (!existsSync(rootDir)) return [];
    const entries = await readdir(rootDir, { withFileTypes: true });
    const found: TemplateMetadata[] = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const dir = join(rootDir, entry.name);
      const yamlPath = join(dir, 'template.html-video.yaml');
      if (!existsSync(yamlPath)) continue;
      const raw = await readFile(yamlPath, 'utf8');
      const meta = parseYaml(raw) as TemplateMetadata;
      meta.__dir = dir;
      this.templates.set(meta.id, meta);
      found.push(meta);
    }
    return found;
  }

  get(id: string): TemplateMetadata {
    const t = this.templates.get(id);
    if (!t) {
      throw new HtmlVideoError('template-not-found', `Template "${id}" not found`);
    }
    return t;
  }

  has(id: string): boolean {
    return this.templates.has(id);
  }

  list(): TemplateMetadata[] {
    return [...this.templates.values()];
  }

  /**
   * Simple intent-based search.
   * v0.1: lowercase keyword match against tags + best_for + name + description.
   * v0.2: replace with embedding-based retrieval.
   */
  search(opts: {
    intent?: string;
    aspect?: string;
    licenseAllow?: string[];
    enginesAvailable?: EngineId[];
    top?: number;
  }): { template: TemplateMetadata; score: number; reason: string }[] {
    const top = opts.top ?? 5;
    const intentLower = (opts.intent ?? '').toLowerCase();
    const intentTokens = intentLower.split(/\W+/).filter((s) => s.length > 2);

    const ranked: { template: TemplateMetadata; score: number; reason: string }[] = [];

    for (const t of this.templates.values()) {
      const reasonParts: string[] = [];
      let score = 0;

      // Tag/best_for/name/description tokens
      const haystack = [
        ...t.tags,
        ...t.best_for,
        t.name,
        t.description,
        t.category,
        t.subcategory ?? '',
      ]
        .join(' ')
        .toLowerCase();
      const matched = intentTokens.filter((tok) => haystack.includes(tok));
      if (matched.length > 0) {
        score += matched.length * 0.2;
        reasonParts.push(`matched ${matched.length} intent tokens`);
      }

      // Aspect support
      if (opts.aspect) {
        if (t.output.resolution.supported_aspects.includes(opts.aspect)) {
          score += 0.15;
          reasonParts.push(`aspect ${opts.aspect} supported`);
        } else {
          // soft penalty, don't filter out — let agent decide
          score -= 0.1;
        }
      }

      // License filter (hard)
      if (opts.licenseAllow && !opts.licenseAllow.includes(t.license.spdx)) {
        continue;
      }
      reasonParts.push(`license ${t.license.spdx} ok`);

      // Engine availability
      if (opts.enginesAvailable && !opts.enginesAvailable.includes(t.engine)) {
        continue;
      }

      // Cap score
      score = Math.max(0, Math.min(1, score));

      ranked.push({
        template: t,
        score,
        reason: reasonParts.join('; '),
      });
    }

    ranked.sort((a, b) => b.score - a.score);
    return ranked.slice(0, top);
  }
}

// ---------------------------------------------------------------------------
// BundleStore / StoryboardStore — JSON-on-disk persistence
// ---------------------------------------------------------------------------

abstract class JsonStore<T extends { id: string }> {
  constructor(
    protected projectRoot: string,
    protected subdir: string,
  ) {}

  protected dir(): string {
    return join(this.projectRoot, '.html-video', this.subdir);
  }

  protected path(id: string): string {
    return join(this.dir(), id, `${this.subdir.replace(/s$/, '')}.json`);
  }

  async save(item: T): Promise<void> {
    const dir = join(this.dir(), item.id);
    await mkdir(dir, { recursive: true });
    await writeFile(this.path(item.id), JSON.stringify(item, null, 2), 'utf8');
  }

  async load(id: string): Promise<T> {
    const p = this.path(id);
    if (!existsSync(p)) {
      throw new HtmlVideoError(
        this.subdir === 'bundles' ? 'asset-not-found' : 'storyboard-not-found',
        `${this.subdir.replace(/s$/, '')} ${id} not found`,
      );
    }
    const raw = await readFile(p, 'utf8');
    return JSON.parse(raw) as T;
  }

  async list(): Promise<T[]> {
    const d = this.dir();
    if (!existsSync(d)) return [];
    const ids = await readdir(d);
    const items: T[] = [];
    for (const id of ids) {
      try {
        items.push(await this.load(id));
      } catch {
        // skip corrupt entries
      }
    }
    return items;
  }
}

export class BundleStore extends JsonStore<AssetBundle> {
  constructor(projectRoot: string) {
    super(projectRoot, 'bundles');
  }
}

export class StoryboardStore extends JsonStore<Storyboard> {
  constructor(projectRoot: string) {
    super(projectRoot, 'storyboards');
  }
}
