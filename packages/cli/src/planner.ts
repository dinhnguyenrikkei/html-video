/**
 * v0.1 minimal scene planner.
 *
 * Real scene planning is the job of the upstream coding agent (Claude Code,
 * Cursor, etc) — they have the LLM smarts to map intent + assets to scenes.
 * The CLI provides a heuristic fallback so `storyboard generate` can run
 * end-to-end without an agent for smoke testing.
 *
 * Heuristic v0.1:
 *   - Always emit an intro-logo-reveal if any image asset looks like a logo
 *   - Emit one image-pan-ken-burns scene per image asset (max 3)
 *   - Emit a data-bar-chart scene if any data asset contains parseable JSON array
 *   - Emit a text-card-quote scene with the first inline text asset (or intent)
 *   - Always close with an outro-cta scene using preferences (not real URLs)
 */

import type { Asset, AssetBundle, TemplateRegistry } from '@html-video/core';
import type { SceneSuggestion } from '@html-video/core';

export function planScenes(
  bundle: AssetBundle,
  templates: TemplateRegistry,
): SceneSuggestion[] {
  const out: SceneSuggestion[] = [];

  const images = bundle.assets.filter((a) => a.type === 'image');
  const texts = bundle.assets.filter((a) => a.type === 'text');
  const datas = bundle.assets.filter((a) => a.type === 'data');

  // 1. Intro
  const logo = images.find((a) =>
    (a.metadata.filename ?? '').toLowerCase().includes('logo'),
  );
  if (templates.has('intro-logo-reveal') && logo) {
    out.push({
      templateId: 'intro-logo-reveal',
      variables: {
        logo_path: logo.path,
        brand_name: 'Open Design',
        tagline: bundle.intent,
        duration_sec: 4,
      },
      assetRefs: [logo.id],
      durationSec: 4,
      agentNote: `Brand intro using ${logo.metadata.filename ?? 'logo image'}`,
      transitionToNext: 'fade',
    });
  }

  // 2. Image pans (skip the logo if used in intro)
  const panImages = images.filter((a) => a !== logo).slice(0, 3);
  for (const img of panImages) {
    if (!templates.has('image-pan-ken-burns')) break;
    out.push({
      templateId: 'image-pan-ken-burns',
      variables: {
        image_path: img.path,
        caption: img.metadata.userCaption ?? img.metadata.filename ?? '',
        pan_direction: 'zoom-in',
        duration_sec: 5,
      },
      assetRefs: [img.id],
      durationSec: 5,
      agentNote: `Ken Burns pan over ${img.metadata.filename ?? img.id}`,
      transitionToNext: 'fade',
    });
  }

  // 3. Data chart
  const dataJson = parseFirstJsonArray(datas);
  if (dataJson && templates.has('data-bar-chart')) {
    out.push({
      templateId: 'data-bar-chart',
      variables: {
        title: 'Data Highlight',
        data: dataJson.slice(0, 8),
        value_format: 'number',
        duration_sec: 8,
      },
      assetRefs: datas.map((d) => d.id),
      durationSec: 8,
      agentNote: 'Bar chart from uploaded data',
      transitionToNext: 'fade',
    });
  }

  // 4. Text card / quote
  const firstText = texts[0];
  const quoteText = firstText?.content?.trim() ?? bundle.intent;
  if (quoteText && templates.has('text-card-quote')) {
    out.push({
      templateId: 'text-card-quote',
      variables: {
        quote: quoteText.slice(0, 200),
        emphasis_words: [],
        duration_sec: 5,
      },
      assetRefs: firstText ? [firstText.id] : [],
      durationSec: 5,
      agentNote: firstText ? `Pull-quote from text asset` : 'Manifesto line from intent',
      transitionToNext: 'fade',
    });
  }

  // 5. Outro
  if (templates.has('outro-cta')) {
    out.push({
      templateId: 'outro-cta',
      variables: {
        headline: 'Made with html-video',
        primary_url: 'github.com/nexu-io/html-video',
        handles: [
          { label: 'Twitter', value: '@tuturetom' },
          { label: 'Email', value: 'open-design@nexu.io' },
        ],
        duration_sec: 4,
      },
      assetRefs: [],
      durationSec: 4,
      agentNote: 'Closing CTA',
    });
  }

  return out;
}

function parseFirstJsonArray(datas: Asset[]): { label: string; value: number; color?: string }[] | null {
  for (const d of datas) {
    const raw = d.content;
    if (!raw) continue;
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.every((x) => x && typeof x === 'object' && 'label' in x && 'value' in x)) {
        return parsed as { label: string; value: number; color?: string }[];
      }
    } catch {
      // skip
    }
  }
  return null;
}
