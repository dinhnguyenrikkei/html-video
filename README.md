# html-video

> **Open-source HTML→Video meta-layer.** Connect any local coding agent (Claude Code, Cursor, Codex, Gemini, OpenCode) and let it pick the right engine and template to render your idea into video.

## Why html-video

HTML→Video is a real category — but each existing engine is opinionated and limited:

- **[Hyperframes](https://github.com/heygen-com/hyperframes)** — HTML+GSAP first, agent-skill-driven, but locked to a single rendering paradigm
- **[Remotion](https://www.remotion.dev/)** — React-first, source-available (paid above 4 devs)
- **[Motion Canvas](https://github.com/motion-canvas/motion-canvas)** / **[Revideo](https://github.com/redotvideo/revideo)** — TypeScript generators on canvas, best for explainers
- **[Manim](https://github.com/3b1b/manim)** / **[DefinedMotion](https://github.com/HugoOlsson/DefinedMotion)** / others — math/3D-first, niche

Picking the right engine per use case, learning each authoring model, stitching them into one workflow — all takes engineering time. Most teams pick one and live with its tradeoffs.

**html-video** is the meta-layer:

- **Agent-native by default** — connect any local coding agent; the agent picks the right engine for the task
- **Multi-engine** — Hyperframes, Remotion, Motion Canvas, Revideo as pluggable backends; new engines drop in as adapters
- **Template marketplace** — curated, reusable patterns from across the ecosystem (data viz, product demos, social shorts, explainers, transitions)
- **Apache-2.0** — no per-render fees, no seat caps, no contributor agreements

## Status

**v0.1 alpha skeleton — 2026-05-27.** Architecture is in place; engine adapter wiring is stubbed. Smoke test runs end-to-end:

```
▸ workdir / bootstrap / doctor / engines + 5 templates loaded
▸ assets bundle (3 assets)
▸ planner emitted 4 scene suggestions
▸ storyboard with 4 scenes, 21s total
▸ scene previews rendered (HTML)
▸ edit / approve / render → final.mp4
✅ smoke test passed
```

Real Hyperframes upstream wiring + ffmpeg concat land in v0.2 once the contract is validated.

## Quick start (dev)

```bash
pnpm install
pnpm -r build
pnpm --filter @html-video/cli smoke

# or the CLI directly
node packages/cli/dist/bin.js doctor
node packages/cli/dist/bin.js search-templates --intent "github stars race" --top 3
```

## Architecture

```
packages/
├── core/                  Asset/Bundle/Storyboard/Scene types + registries + orchestrator
├── adapter-hyperframes/   First reference engine adapter (HTML+CSS+GSAP)
├── cli/                   `html-video` command (doctor / search-templates / assets / storyboard)
└── storyboard-ui/         Browser preview UI (timeline + scene grid + inline edit)
templates/                 5 reference scene templates (intro / chart / pan / quote / outro)
research/                  RFCs (engine adapter / template metadata / agent skill / storyboard)
```

## Roadmap

1. ✅ Engine adapter spec (RFC-01) — one interface, N backends
2. ✅ Template metadata format (RFC-02) — license-first, agent-readable
3. ✅ Storyboard-first workflow (RFC-04) — assets → scenes → review → MP4
4. ✅ v0.1 skeleton (5 templates, HF stub adapter, CLI smoke pass)
5. ⏳ Real Hyperframes upstream wiring (replace stubs in adapter-hyperframes)
6. ⏳ ffmpeg concat for final MP4 mux
7. ⏳ Adapters for Remotion / Motion Canvas / Revideo
8. ⏳ Agent skill packages (Claude Code / Cursor / Codex)
9. ⏳ Template marketplace / registry website

## License

[Apache-2.0](LICENSE)

## Maintained by

[nexu-io](https://github.com/nexu-io) — same team behind [Open Design](https://github.com/nexu-io/open-design).
