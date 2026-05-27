import type { AgentDef } from '../types.js';

/**
 * Claude Code CLI def (`claude`, by Anthropic).
 * Slim version: prompt via stdin, plain text streamFormat.
 * v0.2 will switch to stream-json when we wire interactive tool_result.
 */
export const claude: AgentDef = {
  id: 'claude',
  name: 'Claude Code',
  bin: 'claude',
  versionArgs: ['--version'],
  buildArgs(_prompt, ctx) {
    const args: string[] = ['--print', '--permission-mode', 'plan'];
    if (ctx.cwd) args.push('--add-dir', ctx.cwd);
    for (const dir of ctx.extraAllowedDirs ?? []) args.push('--add-dir', dir);
    return args;
  },
  streamFormat: 'plain',
  promptViaStdin: true,
  installUrl: 'https://docs.claude.com/en/docs/claude-code/setup',
};
