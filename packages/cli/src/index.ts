// Re-export programmatic API so other packages can compose with the CLI logic.
export { bootstrap, findProjectRoot } from './context.js';
export type { CliContext } from './context.js';
export { planScenes } from './planner.js';
export { startPreviewServer } from './preview-server.js';
