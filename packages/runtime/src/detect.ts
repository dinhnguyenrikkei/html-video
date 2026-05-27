import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { AGENT_DEFS } from './registry.js';
import type { AgentDef, DetectedAgent } from './types.js';

const exec = promisify(execFile);

async function which(bin: string): Promise<string | null> {
  try {
    const { stdout } = await exec('which', [bin], { timeout: 2000 });
    return stdout.trim() || null;
  } catch {
    return null;
  }
}

async function probeVersion(bin: string, args: string[]): Promise<string | null> {
  try {
    const { stdout } = await exec(bin, args, { timeout: 5000 });
    return stdout.trim().split('\n')[0] ?? null;
  } catch {
    return null;
  }
}

export async function detectOne(def: AgentDef): Promise<DetectedAgent> {
  const path = await which(def.bin);
  if (!path) {
    return {
      id: def.id,
      name: def.name,
      bin: def.bin,
      available: false,
      ...(def.installUrl !== undefined && { installUrl: def.installUrl }),
    };
  }
  const version = await probeVersion(path, def.versionArgs);
  return {
    id: def.id,
    name: def.name,
    bin: def.bin,
    available: true,
    path,
    version,
    ...(def.installUrl !== undefined && { installUrl: def.installUrl }),
  };
}

export async function detectAll(): Promise<DetectedAgent[]> {
  return Promise.all(AGENT_DEFS.map(detectOne));
}
