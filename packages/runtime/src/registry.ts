import { claude } from './defs/claude.js';
import { cursorAgent } from './defs/cursor-agent.js';
import type { AgentDef } from './types.js';

/** Built-in agent definitions. Order matters: `claude` first = default. */
export const AGENT_DEFS: AgentDef[] = [claude, cursorAgent];

export function findAgent(id: string): AgentDef | undefined {
  return AGENT_DEFS.find((a) => a.id === id);
}
