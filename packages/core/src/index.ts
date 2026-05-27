/**
 * @html-video/core — Public API surface.
 */

export * from './types/index.js';
export { HtmlVideoError } from './errors.js';
export type { ErrorCode } from './errors.js';
export { AssetStore } from './asset-store.js';
export type { AssetStoreOptions } from './asset-store.js';
export {
  EngineRegistry,
  TemplateRegistry,
  BundleStore,
  StoryboardStore,
} from './registry.js';
export { StoryboardOrchestrator } from './storyboard.js';
export type {
  GenerateOpts,
  OrchestratorDeps,
  SceneSuggestion,
} from './storyboard.js';
export { BundleBuilder } from './bundle.js';
export type { BundleInput } from './bundle.js';
