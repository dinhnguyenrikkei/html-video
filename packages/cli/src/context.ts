/**
 * Bootstrap shared CLI context: project root, registries, stores, orchestrator.
 */

import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  AssetStore,
  BundleStore,
  EngineRegistry,
  StoryboardOrchestrator,
  StoryboardStore,
  TemplateRegistry,
} from '@html-video/core';
import hfAdapter from '@html-video/adapter-hyperframes';

export interface CliContext {
  projectRoot: string;
  engines: EngineRegistry;
  templates: TemplateRegistry;
  bundles: BundleStore;
  storyboards: StoryboardStore;
  assets: AssetStore;
  orchestrator: StoryboardOrchestrator;
}

/** Find project root by walking up looking for package.json or .html-video/. */
export function findProjectRoot(start: string = process.cwd()): string {
  let dir = start;
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(dir, '.html-video'))) return dir;
    if (existsSync(join(dir, 'pnpm-workspace.yaml'))) return dir;
    if (existsSync(join(dir, 'package.json')) && existsSync(join(dir, 'templates'))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return start;
}

/** Find the templates/ directory: prefer projectRoot/templates, fallback to monorepo root. */
function findTemplatesDir(projectRoot: string): string {
  const candidates = [
    join(projectRoot, 'templates'),
    // When CLI is installed in a user's project, templates ship inside our package
    // packages/cli/dist/context.js → up 3 levels → monorepo root → templates/
    join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', 'templates'),
  ];
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  return candidates[0]!;
}

export async function bootstrap(opts: { cwd?: string } = {}): Promise<CliContext> {
  const projectRoot = findProjectRoot(opts.cwd);

  const engines = new EngineRegistry();
  engines.register(hfAdapter);

  const templates = new TemplateRegistry();
  await templates.scan(findTemplatesDir(projectRoot));

  const bundles = new BundleStore(projectRoot);
  const storyboards = new StoryboardStore(projectRoot);
  const assets = new AssetStore({ projectRoot });

  const orchestrator = new StoryboardOrchestrator({
    projectRoot,
    engines,
    templates,
    storyboards,
  });

  return { projectRoot, engines, templates, bundles, storyboards, assets, orchestrator };
}
