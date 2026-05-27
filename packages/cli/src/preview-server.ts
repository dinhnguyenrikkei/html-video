/**
 * Minimal HTTP server for storyboard preview.
 * Serves the static UI from @html-video/storyboard-ui + a couple of API endpoints.
 */

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { existsSync, statSync } from 'node:fs';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { CliContext } from './context.js';

interface PreviewHandle {
  url: string;
  port: number;
  close: () => void;
}

const MIME: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.json': 'application/json; charset=utf-8',
  '.webp': 'image/webp',
};

function resolveUiRoot(): string {
  // packages/cli/dist/preview-server.js → ../../storyboard-ui/public
  const here = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(here, '..', '..', 'storyboard-ui', 'public'),
    resolve(here, '..', 'public'),
  ];
  for (const c of candidates) if (existsSync(c)) return c;
  return candidates[0]!;
}

export async function startPreviewServer(
  ctx: CliContext,
  storyboardId: string,
  port: number,
): Promise<PreviewHandle> {
  const uiRoot = resolveUiRoot();

  const server = createServer(async (req, res) => {
    try {
      if (!req.url) {
        res.writeHead(400);
        res.end();
        return;
      }
      const url = new URL(req.url, 'http://x');

      // === API ===
      if (url.pathname === '/api/storyboard') {
        const sb = await ctx.storyboards.load(storyboardId);
        res.writeHead(200, { 'content-type': MIME['.json']! });
        res.end(JSON.stringify(sb));
        return;
      }
      if (url.pathname === '/api/edit' && req.method === 'POST') {
        const body = await readBody(req);
        const op = body.op as string;
        let sb;
        if (op === 'remove-scene')
          sb = await ctx.orchestrator.removeScene(storyboardId, body.sceneId as string);
        else if (op === 'set-duration')
          sb = await ctx.orchestrator.setDuration(
            storyboardId,
            body.sceneId as string,
            body.durationSec as number,
          );
        else if (op === 'reorder')
          sb = await ctx.orchestrator.reorderScenes(storyboardId, body.sceneIds as string[]);
        else if (op === 'approve') sb = await ctx.orchestrator.approve(storyboardId);
        else {
          res.writeHead(400, { 'content-type': MIME['.json']! });
          res.end(JSON.stringify({ error: `Unknown op: ${op}` }));
          return;
        }
        res.writeHead(200, { 'content-type': MIME['.json']! });
        res.end(JSON.stringify({ storyboard: sb }));
        return;
      }
      if (url.pathname === '/api/approve-and-render' && req.method === 'POST') {
        await ctx.orchestrator.approve(storyboardId);
        // For v0.1 don't actually kick render here — give the user the CLI command
        res.writeHead(200, { 'content-type': MIME['.json']! });
        res.end(
          JSON.stringify({
            ok: true,
            note: 'Storyboard approved. Run: html-video storyboard render ' + storyboardId,
          }),
        );
        return;
      }

      // === Scene preview HTML / assets (serve from storyboard work dir) ===
      if (url.pathname.startsWith('/preview/')) {
        const sb = await ctx.storyboards.load(storyboardId);
        const reqPath = url.pathname.replace('/preview/', '');
        // Match by scene id at path start (e.g. /preview/s000/preview.html or /preview/s000.html)
        for (const scene of sb.scenes) {
          if (reqPath.startsWith(scene.id) || url.pathname.endsWith(`/${scene.id}.html`)) {
            await serveFile(scene.previewHtmlPath, res);
            return;
          }
        }
        res.writeHead(404);
        res.end();
        return;
      }

      // === Asset reverse-lookup (preview HTML may reference asset paths) ===
      // In v0.1 the preview HTML is loaded with absolute paths in vars; assets
      // are served via direct fs (browser will request file:// or fail). We only
      // serve under /assets/ if preview HTML rewrites them — TODO v0.2.

      // === Static UI ===
      let path = url.pathname === '/' ? '/index.html' : url.pathname;
      const filePath = join(uiRoot, path);
      if (filePath.startsWith(uiRoot) && existsSync(filePath) && statSync(filePath).isFile()) {
        await serveFile(filePath, res);
        return;
      }

      res.writeHead(404);
      res.end('Not found');
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      res.writeHead(500, { 'content-type': MIME['.json']! });
      res.end(JSON.stringify({ error: msg }));
    }
  });

  return new Promise((resolveFn) => {
    server.listen(port, '127.0.0.1', () => {
      const addr = server.address();
      const actualPort = typeof addr === 'object' && addr ? addr.port : port;
      resolveFn({
        url: `http://127.0.0.1:${actualPort}`,
        port: actualPort,
        close: () => server.close(),
      });
    });
  });
}

async function serveFile(filePath: string, res: import('node:http').ServerResponse) {
  const ext = extname(filePath).toLowerCase();
  const buf = await readFile(filePath);
  res.writeHead(200, { 'content-type': MIME[ext] ?? 'application/octet-stream' });
  res.end(buf);
}

async function readBody(req: import('node:http').IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolveFn, reject) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
    });
    req.on('end', () => {
      try {
        resolveFn(data ? JSON.parse(data) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}
