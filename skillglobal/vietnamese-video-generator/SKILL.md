---
name: vietnamese-video-generator
description: Generate and design high-quality Vietnamese videos (TikTok, TVC) from raw text scripts. It handles generating edge-tts Vietnamese voiceover (MALE/FEMALE at rate -4%), parsing durations using ffprobe, dynamically adjusting frame durationSec and start_ms delay offsets in project.json, mixing audios with adelay+amix using ffmpeg, designing CSS kinetic typography text highlights and pop-in glassmorphic illustration badges with radial glows, applying Syne + Plus Jakarta Sans premium font pairing, chromatic gradient mesh backgrounds, and executing project-render CLI exports. Use this whenever the user wants to generate or design a Vietnamese video, solve audio overlapping/cutting issues, or sync text/animations with narration speech.
---

# Vietnamese Video Generator (TikTok & TVC)

A skill for generating professional, highly-synchronized Vietnamese promo videos and TikTok clips with animated text highlights and visual illustrations.

## 🛠️ Requirements & Dependencies
- **edge-tts**: Python library for neural text-to-speech. Install with `pip install edge-tts`.
- **ffmpeg** & **ffprobe**: Full build (e.g. Gyan.FFmpeg bin folder) to probe speech duration and mix audio tracks.
- **Node.js** & monorepo packages built (`pnpm build`).

---

## 📋 Standard Workflow

### Phase 1: Audio Generation & Frame Sync

1. **Voice Models**:
   - Male voiceover: `vi-VN-NamMinhNeural`
   - Female voiceover: `vi-VN-HoaiMyNeural`
   - Always slow down speech rate using `rate="-4%"` in `edge_tts.Communicate()` to ensure a natural, clear, and premium-sounding Vietnamese narration.

2. **Calculate Precise Duration**:
   - Write a python script to generate `.mp3` files for each scene.
   - Run `ffprobe` to measure the exact float duration of each generated audio file:
     ```python
     cmd = [ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
     ```

3. **Update project.json**:
   - Calculate cumulative delay offsets for each scene: `delay_i = sum(frame_durations[:i])`.
   - Set the frame duration: `durationSec = round(speech_duration + 1.0, 1)`. The `1.0s` buffer prevents truncation.
   - Write these values into the `frames` array in `project.json` so the rendering engine transitions frames exactly when the speech ends.

4. **Mix Narrations**:
   - Mix all scene tracks into a single background narration track using `ffmpeg` with `adelay` (using `scene["start_ms"]`) and `amix`:
     ```bash
     ffmpeg -i s0.mp3 -i s1.mp3 ... -filter_complex "[0:a]adelay=delay0|delay0[a0];[1:a]adelay=delay1|delay1[a1];[a0][a1]amix=inputs=2:duration=longest[aout]" -map "[aout]" narration.mp3
     ```
   - Hash the mixed file with SHA1, copy it to the project's `assets/` folder, and register it in `project.json` under `soundtrack.narrationAssetId`.

---

## Phase 2: Design Kinetic Typography & Visual Reveals

For vertical short-form content (TikTok, resolution `1080x1920`) or TVC videos, apply high-end visual styling:

### 🎨 Design System Token Set

Always apply this design system consistently across all frames:

#### Typography (Premium Font Pairing — Vietnamese-Safe)

> ⚠️ **CRITICAL**: Tiếng Việt có dấu phức tạp (ệ, ổ, ắ, ữ...). PHẢI dùng font có `subset=vietnamese`. Các font như **Syne, Space Grotesk, DM Sans** KHÔNG hỗ trợ Vietnamese → chữ lộn xộn khi render.

```html
<!-- ALWAYS use this font import in every frame — Vietnamese subset required! -->
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Be+Vietnam+Pro:wght@400;500;600;700;800&subset=vietnamese&display=swap" rel="stylesheet" />
```
- **Display / Headline**: `font-family: 'Barlow Condensed', sans-serif; font-weight: 900;` — Use for main titles, hero text, big numbers
  - Bold condensed, great for Vietnamese large-display text
  - Add `letter-spacing: -1px` to -2px for large display sizes (80px+)
  - Gradient text: `color: transparent; background: linear-gradient(...); -webkit-background-clip: text; background-clip: text;`
- **Body / UI text**: `font-family: 'Be Vietnam Pro', sans-serif;` — Use for descriptions, labels, captions
  - Designed specifically for Vietnamese typography — best support for all diacritics
  - Body: `font-weight: 500; line-height: 1.65;`
  - Labels: `font-weight: 700; letter-spacing: 2–3px; text-transform: uppercase;`
- **NEVER use for Vietnamese text**: Syne, Plus Jakarta Sans, Space Grotesk, DM Sans, Outfit — these lack Vietnamese glyph coverage

#### Color Palette
Each frame should have a distinct chromatic identity (not the same purple gradient every time):

| Frame Theme | Primary Glow | Accent |
|-------------|-------------|--------|
| Hook/Danger | `rgba(120, 60, 255, 0.22)` purple + `rgba(220, 38, 100, 0.18)` pink | Red `#EF4444`, Yellow `#FBBF24` |
| Reveal/Answer | `rgba(40, 200, 100, 0.22)` green + `rgba(30, 100, 220, 0.18)` blue | Green `#34D399`, Blue `#60A5FA` |
| Stats/Data | `rgba(59, 130, 246, 0.22)` blue + `rgba(251, 146, 60, 0.18)` orange | Blue `#60A5FA`, Green `#34D399`, Orange `#FB923C` |
| Solution/Brand | `rgba(99, 70, 255, 0.22)` indigo + `rgba(251, 100, 30, 0.18)` fire | Indigo `#6366F1`, Orange `#FB923C` |
| CTA/Action | `rgba(234, 88, 12, 0.30)` fire + `rgba(220, 40, 40, 0.18)` red | Fire gradient `#FED7AA → #FB923C → #EA580C → #DC2626` |

#### Background Architecture (use in every frame)
```css
/* Layer 1: Chromatic gradient mesh */
.bg-gradient {
  background:
    radial-gradient(ellipse 120% 80% at 50% 10%, rgba(PRIMARY_R,PRIMARY_G,PRIMARY_B,0.22) 0%, transparent 55%),
    radial-gradient(ellipse 80% 60% at 5% 60%, rgba(SEC_R,SEC_G,SEC_B,0.18) 0%, transparent 55%),
    radial-gradient(ellipse 90% 60% at 90% 80%, rgba(ACCENT_R,ACCENT_G,ACCENT_B,0.12) 0%, transparent 55%),
    linear-gradient(175deg, #040814 0%, #050208 50%, #0c0508 100%);
}
/* Layer 2: Subtle grid */
.bg-grid {
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 80px 80px;
  mask-image: radial-gradient(ellipse 100% 100% at 50% 0%, black 20%, transparent 80%);
}
/* Layer 3: Film grain noise */
.bg-noise {
  background-image: url("data:image/svg+xml,...");
  opacity: 0.6;
}
/* Floating orbs — use 2 per frame */
.orb { border-radius: 50%; background: radial-gradient(ellipse at center, COLOR 0%, transparent 65%); }
```

### 1. Structure the HTML Frames
- Split single-page templates into multiple sequential HTML files inside `frames/`.
- Every frame must import **Syne + Plus Jakarta Sans** from Google Fonts.
- Maintain a color-coded progress bar at the bottom matching the frame's theme color.

### 2. Kinetic Text Animation
- Do not display text statically. Split text into sequential phrases/spans.
- Staggered CSS `animation-delay` offsets matching speech onset (e.g. `0.2s`, `1.8s`, `3.0s`):
```css
.phrase {
  opacity: 0;
  transform: translateY(50px);
  animation: revealPhrase 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes revealPhrase { to { opacity: 1; transform: translateY(0); } }
```
- **Gradient text highlights**: Transition key words with `background: linear-gradient(...); -webkit-background-clip: text; filter: drop-shadow(0 0 20px COLOR)`.

### 3. Glassmorphic Cards & Pills
```css
/* Standard card style */
.card {
  background: rgba(255, 255, 255, 0.035);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 28px;
  box-shadow: 0 20px 60px rgba(COLOR, 0.15), inset 0 1px 0 rgba(255,255,255,0.05);
}
/* Left accent strip for data cards */
.card::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  background: linear-gradient(180deg, COLOR_TOP, COLOR_BOTTOM);
  border-radius: 28px 0 0 28px;
}
/* Round pill style */
.pill {
  border-radius: 64px; padding: 28px 48px;
  background: rgba(255, 255, 255, 0.035);
  backdrop-filter: blur(20px);
}
```

### 4. Floating Illustration Badges (Glassmorphic)
```css
.illustration-box {
  position: absolute;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 36px;
  transform: scale(0) rotate(0deg);
  animation: popIn 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  box-shadow: 0 20px 60px rgba(COLOR, 0.3), inset 0 1px 0 rgba(255,255,255,0.1);
}
@keyframes popIn { to { transform: scale(1) rotate(7deg); } }
@keyframes popInAlt { to { transform: scale(1) rotate(-7deg); } }
```

### 5. Animation Easing Standards (from ui-ux-pro-max)
- **Enter animations**: `cubic-bezier(0.16, 1, 0.3, 1)` — smooth deceleration (ease-out)
- **Bounce/Pop effects**: `cubic-bezier(0.34, 1.56, 0.64, 1)` — spring overshoot
- **Exit animations**: Should be 60–70% of enter duration
- **Stagger timing**: 30–50ms between list items

### 6. Eyebrow Tags (scene labels)
```html
<div class="eyebrow-tag">⚡ Short Label Here</div>
```
```css
.eyebrow-tag {
  font-size: 22px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase;
  border: 1px solid rgba(COLOR, 0.35); background: rgba(COLOR, 0.08);
  border-radius: 50px; padding: 14px 36px; backdrop-filter: blur(10px);
}
```

---

## Phase 3: Export & Render

1. Ensure the required paths are loaded into `Path` (especially the Gyan.FFmpeg bin and Node.js paths).
2. Propose running the project-render command:
   ```powershell
   $env:Path = "C:\Users\bmngu\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin;" + $env:Path
   & "C:\Program Files\nodejs\node.exe" packages/cli/dist/bin.js project-render <PROJECT_ID> --output <OUTPUT_MP4_PATH>
   ```

---

## Phase 4: Verification

1. Verify that the rendered MP4 file has a matching duration to the total frame sequence.
2. Verify that there is zero overlap between adjacent audio clips.
3. Check that visual highlights and badges pop-up precisely in sync with the audio speaker.
4. Confirm `Syne` font renders correctly for all display text (large headings, numbers).
5. Confirm `Plus Jakarta Sans` renders correctly for all body text.

---

## 📐 Quick Design Checklist

Before finalizing any frame, verify:
- [ ] `Syne` font for all display/headline text (not Outfit, not Inter)
- [ ] `Plus Jakarta Sans` for all body text (not Be Vietnam Pro)
- [ ] Gradient mesh background (3 overlapping radial-gradient orbs)
- [ ] Subtle grid layer with mask-image fade
- [ ] Film grain noise overlay (opacity 0.6)
- [ ] 2 floating orbs per frame with animation
- [ ] All text animations use `cubic-bezier(0.16, 1, 0.3, 1)` or `cubic-bezier(0.34, 1.56, 0.64, 1)` (no linear easing)
- [ ] Gradient text via `-webkit-background-clip: text` for key display words
- [ ] Progress bar color matches frame theme
- [ ] Dynamic duration: `document.documentElement.style.setProperty('--duration', dur + 's')`
