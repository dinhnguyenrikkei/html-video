/**
 * Runtime types — slim variant of OD's RuntimeAgentDef.
 * v0.1: only the fields html-video needs to spawn + read stdout.
 * Future expansion (prompt-budget, stream-json, MCP) lands per-need.
 */

export interface AgentDef {
  /** Stable id — `claude` / `cursor-agent` / `codex` / `opencode` etc */
  id: string;
  /** Human label */
  name: string;
  /** CLI binary name (looked up via PATH) */
  bin: string;
  /** Args to print version (used in `doctor`) */
  versionArgs: string[];
  /** Build the argv list given the user prompt */
  buildArgs(prompt: string, ctx: AgentInvokeContext): string[];
  /**
   * How agent emits to stdout:
   * - `plain`: free-form text (everything printed is output)
   * - `claude-stream`: claude --output-format stream-json (NDJSON wrapped events)
   * - `json-event-stream`: NDJSON {type, ...} event stream
   */
  streamFormat: 'plain' | 'claude-stream' | 'json-event-stream';
  /** Pass prompt via stdin instead of argv (recommended for long prompts) */
  promptViaStdin?: boolean;
  /** Extra fixed env vars on spawn */
  env?: Record<string, string>;
  /** Where to find install instructions */
  installUrl?: string;
}

export interface AgentInvokeContext {
  cwd: string;
  /** Allowed working dirs (e.g. project's .html-video/projects/<id>/) */
  extraAllowedDirs?: string[];
}

export interface DetectedAgent {
  id: string;
  name: string;
  bin: string;
  available: boolean;
  path?: string;
  version?: string | null;
  installUrl?: string;
}

export type AgentEvent =
  | { type: 'text'; chunk: string }
  | { type: 'tool_use'; tool: string; input: unknown; id?: string }
  | { type: 'tool_result'; id?: string; output: unknown; isError?: boolean }
  | { type: 'message_end'; reason?: string }
  | { type: 'error'; message: string };

export interface SpawnHandle {
  pid: number;
  stop(): void;
  done: Promise<{ exitCode: number; signal: NodeJS.Signals | null }>;
}
