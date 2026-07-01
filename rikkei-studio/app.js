/* ═══════════════════════════════════════════════════════════
   Rikkei Video Studio — App Logic
   State management · API · Drag-drop · Preview · Editing
   ═══════════════════════════════════════════════════════════ */

// ── State ────────────────────────────────────────────────
const state = {
  projectId: 'proj_0d93e26f-9b8',
  project: null,
  currentScene: 0,
  playing: false,
  playTimer: null,
  playStart: 0,
  voiceRef: '/assets/voice_preview.mp3',
  musicSrc: '/assets/background_music.mp3',
  ttsLoaded: false,
  deletedScenesHistory: [],
};

// ── DOM refs ──────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

// ── Toast system ─────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  $('#toastContainer').appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3500);
}

// ── API helpers ──────────────────────────────────────────
async function api(path, opts = {}) {
  try {
    const res = await fetch(path, opts);
    return await res.json();
  } catch (e) {
    console.error('API error:', e);
    toast(`API Error: ${e.message}`, 'error');
    return null;
  }
}

// ── Theme colors ─────────────────────────────────────────
const THEMES = {
  hook:     { p: '#783cff', s: '#dc2626', a: '#fbbf24', pg: 'rgba(120,60,255,0.25)',  sg: 'rgba(220,38,100,0.2)',   ag: 'rgba(251,191,36,0.15)',  grad: 'linear-gradient(135deg, #fbbf24, #ef4444)' },
  reveal:   { p: '#059669', s: '#2563eb', a: '#34d399', pg: 'rgba(5,150,105,0.25)',    sg: 'rgba(37,99,247,0.2)',    ag: 'rgba(52,211,153,0.15)',  grad: 'linear-gradient(135deg, #34d399, #2563eb)' },
  stats:    { p: '#2563eb', s: '#ea580c', a: '#fb923c', pg: 'rgba(37,99,235,0.25)',    sg: 'rgba(234,88,12,0.2)',    ag: 'rgba(251,146,60,0.15)',  grad: 'linear-gradient(135deg, #fb923c, #ea580c)' },
  solution: { p: '#6366f1', s: '#f97316', a: '#fb923c', pg: 'rgba(99,102,241,0.25)',   sg: 'rgba(249,115,22,0.2)',   ag: 'rgba(251,146,96,0.15)', grad: 'linear-gradient(135deg, #6366f1, #f97316)' },
  cta:      { p: '#ea580c', s: '#dc2626', a: '#fddf47', pg: 'rgba(234,88,12,0.30)',    sg: 'rgba(220,38,38,0.2)',    ag: 'rgba(253,223,71,0.15)',  grad: 'linear-gradient(135deg, #fddf47, #ea580c, #dc2626)' },
};

const KEY_WORDS = new Set(['CNTT','DATA','PIPELINE','WAREHOUSE','ETL','BÁO','CÁO','DOANH','THU','END-TO-END','DE','LỘ','TRÌNH','GPA','CÔNG','NGHỆ','THÔNG','TIN','SPARK','KAFKA','AIRFLOW']);
const DANGER_WORDS = new Set(['ĐƠ','ẤP','ÚNG','QUÊN','THẤT','BẠI','LÝ','THUYẾT','DỐT','VẸT','HÌNH']);
const WORD_WEIGHTS = { GPA:3, ETL:3, 'END-TO-END':3, DATA:2, PIPELINE:2, CV:2, DE:2, WAREHOUSE:2, COMMENT:2, SPARK:2, KAFKA:2, AIRFLOW:3, '10':2 };

function getWordWeight(w) {
  const upper = w.toUpperCase().replace(/[.,!?"\u201c\u201d:;-]/g, '').trim();
  return WORD_WEIGHTS[upper] || 1;
}

// ── Subtitle timing calculator ───────────────────────────
function computeSubtitles(displayChunks, totalDur) {
  const flatWords = [];
  const chunkIndices = [];
  const wordWeights = [];
  const pausesMap = {};
  let wordCount = 0;
  let totalPauses = 0;

  displayChunks.forEach((chunk, cIdx) => {
    chunk.words.forEach((w, wIdx) => {
      flatWords.push(w);
      chunkIndices.push([cIdx, wIdx]);
      wordWeights.push(getWordWeight(w));
      wordCount++;
    });
    const pause = chunk.pause_after || 0;
    if (pause > 0) {
      pausesMap[wordCount - 1] = pause;
      totalPauses += pause;
    }
  });

  const totalWeight = wordWeights.reduce((a, b) => a + b, 0);
  let startOffset = 0.2, endOffset = 0.2;
  let availDur = totalDur - startOffset - endOffset - totalPauses;
  if (availDur <= 0) { availDur = totalDur; startOffset = 0; }
  const unitDur = totalWeight > 0 ? availDur / totalWeight : 0;

  const chunksData = displayChunks.map(() => ({ start: 0, dur: 0, words: [] }));
  let cumPause = 0, cumDur = 0;

  chunkIndices.forEach(([cIdx], i) => {
    const wStart = startOffset + cumDur + cumPause;
    const wWeight = wordWeights[i];
    const wDuration = wWeight * unitDur * 0.9;
    chunksData[cIdx].words.push({
      text: flatWords[i],
      start: Math.round(wStart * 100) / 100,
      duration: Math.round(wDuration * 100) / 100,
    });
    cumDur += wWeight * unitDur;
    if (i in pausesMap) cumPause += pausesMap[i];
  });

  chunksData.forEach((chunk) => {
    if (!chunk.words.length) return;
    const cStart = chunk.words[0].start;
    const cEnd = chunk.words[chunk.words.length - 1].start + chunk.words[chunk.words.length - 1].duration;
    chunk.start = Math.round((cStart - 0.05) * 100) / 100;
    chunk.dur = Math.round((cEnd - cStart + 0.1) * 100) / 100;
  });

  for (let i = 0; i < chunksData.length - 1; i++) {
    chunksData[i].dur = Math.round((chunksData[i + 1].start - chunksData[i].start) * 100) / 100;
  }

  return chunksData;
}

// ── Generate frame HTML ──────────────────────────────────
function generateFrameHTML(scene) {
  const theme = THEMES[scene.theme] || THEMES.hook;
  const dur = scene.duration_sec || 9;
  const chunks = computeSubtitles(scene.display_chunks, dur);

  let chunksHTML = '';
  chunks.forEach(chunk => {
    let wordsHTML = '';
    chunk.words.forEach(w => {
      const clean = w.text.toUpperCase().replace(/[.,!?"\u201c\u201d:;-]/g, '').trim();
      let cls = 'w';
      if (KEY_WORDS.has(clean)) cls = 'w key-word';
      else if (DANGER_WORDS.has(clean)) cls = 'w danger-word';
      wordsHTML += `          <span class="${cls}" style="--d: ${w.start}s; --word-duration: ${w.duration}s;">${w.text}</span>\n`;
    });
    chunksHTML += `        <div class="caption-chunk" style="--chunk-start: ${chunk.start}s; --chunk-duration: ${chunk.dur}s;">\n${wordsHTML}        </div>\n`;
  });

  const v = scene.visual || {};
  const c1 = v.card1 || { badge: '', name: '', status: '' };
  const c2 = v.card2 || { badge: '', name: '', status: '' };

  // Absolute & Relative layout offsets for drag-and-drop
  const mascotStyle = v.mascot_pos 
    ? `left: ${v.mascot_pos.x}px; top: ${v.mascot_pos.y}px; bottom: auto; right: auto;` 
    : '';
  const card1Style = v.card1_pos
    ? `position: relative; left: ${v.card1_pos.x}px; top: ${v.card1_pos.y}px;`
    : '';
  const card2Style = v.card2_pos
    ? `position: relative; left: ${v.card2_pos.x}px; top: ${v.card2_pos.y}px;`
    : '';

  return `<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${scene.theme}</title>
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Be+Vietnam+Pro:wght@400;500;600;700;800&subset=vietnamese&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary-color: ${theme.p}; --sec-color: ${theme.s}; --accent-color: ${theme.a};
      --primary-glow: ${theme.pg}; --sec-glow: ${theme.sg}; --accent-glow: ${theme.ag};
      --accent-gradient: ${theme.grad}; --duration: ${dur}s;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { width: 100vw; height: 100vh; overflow: hidden; background-color: #040814; font-family: 'Be Vietnam Pro', sans-serif; color: #fff; position: relative; }
    .bg-gradient { position: absolute; inset: 0; background: radial-gradient(ellipse 100% 70% at 50% 10%, var(--primary-glow) 0%, transparent 60%), radial-gradient(ellipse 70% 50% at 10% 60%, var(--sec-glow) 0%, transparent 60%), radial-gradient(ellipse 80% 50% at 90% 80%, var(--accent-glow) 0%, transparent 60%), linear-gradient(175deg, #040814 0%, #050208 50%, #0c0508 100%); z-index: 1; }
    .bg-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px); background-size: 80px 80px; mask-image: radial-gradient(ellipse 80% 80% at 50% 40%, black 20%, transparent 80%); z-index: 2; }
    .bg-noise { position: absolute; inset: 0; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); opacity: 0.04; z-index: 3; pointer-events: none; }
    .container { position: relative; width: 100%; height: 100%; z-index: 10; display: grid; grid-template-columns: 1fr; grid-template-rows: auto 1fr auto; gap: 3vh; padding: 5vh 5vw 8vh 5vw; }
    .video-title-card { background: rgba(255,255,255,0.03); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 2.5vh 3vw; box-shadow: 0 15px 40px rgba(0,0,0,0.3); opacity: 0; transform: translateY(-20px); animation: fadeInTitle 0.8s cubic-bezier(0.16,1,0.3,1) 0.2s forwards; }
    @keyframes fadeInTitle { to { opacity: 1; transform: translateY(0); } }
    .video-title-kicker { font-size: clamp(14px, 1.8vmax, 24px); font-weight: 700; color: var(--accent-color); text-transform: uppercase; letter-spacing: 3px; margin-bottom: 6px; }
    .video-title { font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: clamp(20px, 2.5vmax, 42px); line-height: 1.2; }
    .visual-wrapper { grid-row: 2; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; position: relative; }
    .karaoke-panel { grid-row: 3; background: rgba(255,255,255,0.02); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.08); border-radius: 36px; padding: 3vh 4vw; min-height: clamp(140px, 18vh, 260px); display: flex; align-items: center; justify-content: center; box-shadow: 0 20px 50px rgba(0,0,0,0.4); opacity: 0; animation: fadeInPanel 0.4s ease-out 0.1s forwards; }
    @keyframes fadeInPanel { to { opacity: 1; } }
    .caption-wrapper { position: relative; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; }
    .caption-chunk { position: absolute; inset: 0; display: flex; justify-content: center; align-items: center; flex-wrap: wrap; opacity: 0; pointer-events: none; animation: showChunk var(--chunk-duration) linear var(--chunk-start) forwards; text-align: center; }
    @keyframes showChunk { 0% { opacity: 0; transform: translateY(15px); } 8% { opacity: 1; transform: translateY(0); } 92% { opacity: 1; transform: translateY(0); } 100% { opacity: 0; transform: translateY(-15px); } }
    .w { display: inline-block; margin: 5px 1vw; font-size: clamp(20px, 2.8vmax, 48px); font-weight: 700; color: rgba(255,255,255,0.25); animation: activeWord var(--word-duration, 0.4s) ease var(--d) forwards; }
    @keyframes activeWord { 0% { color: rgba(255,255,255,0.25); transform: scale(1); } 20% { color: #fff; transform: scale(1.18); text-shadow: 0 0 15px rgba(255,255,255,0.8); } 80% { color: #fff; transform: scale(1.18); } 100% { color: #fff; transform: scale(1); } }
    .w.key-word { animation: activeKeyWord var(--word-duration, 0.4s) ease var(--d) forwards; }
    @keyframes activeKeyWord { 0% { color: rgba(255,255,255,0.25); transform: scale(1); } 20% { color: var(--accent-color); transform: scale(1.22); text-shadow: 0 0 25px var(--accent-color); } 80% { color: var(--accent-color); transform: scale(1.22); } 100% { color: var(--accent-color); transform: scale(1); } }
    .w.danger-word { animation: activeDangerWord var(--word-duration, 0.4s) ease var(--d) forwards; }
    @keyframes activeDangerWord { 0% { color: rgba(255,255,255,0.25); transform: scale(1); } 20% { color: #ef4444; transform: scale(1.22); text-shadow: 0 0 25px rgba(239,68,68,1); } 80% { color: #ef4444; transform: scale(1.22); } 100% { color: #ef4444; transform: scale(1); } }
    .mascot { position: absolute; bottom: calc(8vh + clamp(140px, 18vh, 260px) + 20px); right: 5vw; width: clamp(100px, 10vmax, 180px); height: auto; z-index: 15; transform-origin: bottom center; filter: drop-shadow(0 15px 30px rgba(0,0,0,0.4)); opacity: 0; animation: fadeInMascot 0.8s ease-out 1.2s forwards, dance 1.6s ease-in-out infinite alternate 2.0s; }
    @keyframes fadeInMascot { to { opacity: 1; } }
    @keyframes dance { 0% { transform: scale(1) translateY(0) rotate(0deg); } 50% { transform: scale(1.04) translateY(-10px) rotate(-3deg); } 100% { transform: scale(0.98) translateY(3px) rotate(3deg); } }
    .progress-container { position: absolute; bottom: 0; left: 0; right: 0; height: 10px; background: rgba(255,255,255,0.05); z-index: 20; }
    .progress-bar { height: 100%; background: var(--accent-gradient); width: 0%; animation: progress var(--duration) linear forwards; }
    @keyframes progress { to { width: 100%; } }
    .wrapper-inner { display: flex; gap: 4%; justify-content: center; width: 100%; height: 100%; align-items: center; }
    .partner-card-1 { width: 48%; max-width: 460px; height: clamp(300px, 45vh, 560px); background: linear-gradient(135deg, rgba(${hexToRgb(theme.p)},0.12), rgba(4,8,20,0.85)); border: 3px solid rgba(${hexToRgb(theme.p)},0.5); border-radius: clamp(20px, 2.5vmax, 40px); padding: clamp(20px, 3vh, 50px); display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 35px 70px rgba(${hexToRgb(theme.p)},0.25); opacity: 0; transform: translateX(-40px); animation: fadeInCard1 0.8s cubic-bezier(0.16,1,0.3,1) 0.6s forwards, pulseCard 3s ease-in-out infinite alternate 1.4s; }
    .partner-card-2 { width: 48%; max-width: 460px; height: clamp(300px, 45vh, 560px); background: linear-gradient(135deg, rgba(${hexToRgb(theme.s)},0.12), rgba(4,8,20,0.85)); border: 3px solid rgba(${hexToRgb(theme.s)},0.5); border-radius: clamp(20px, 2.5vmax, 40px); padding: clamp(20px, 3vh, 50px); display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 35px 70px rgba(${hexToRgb(theme.s)},0.25); opacity: 0; transform: translateX(40px); animation: fadeInCard2 0.8s cubic-bezier(0.16,1,0.3,1) 0.8s forwards, pulseCard2 3s ease-in-out infinite alternate 1.9s; }
    @keyframes fadeInCard1 { to { opacity: 1; transform: translateX(0); } }
    @keyframes fadeInCard2 { to { opacity: 1; transform: translateX(0); } }
    @keyframes pulseCard { 0% { transform: translateY(0); } 100% { transform: translateY(-15px); } }
    @keyframes pulseCard2 { 0% { transform: translateY(0); } 100% { transform: translateY(-15px); } }
    .badge-label { font-size: clamp(14px, 1.8vmax, 30px); font-weight: 800; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 2px; }
    .partner-name { font-family: 'Barlow Condensed', sans-serif; font-size: clamp(28px, 4vmax, 65px); font-weight: 900; color: var(--accent-color); text-shadow: 0 0 30px rgba(251,191,36,0.6); line-height: 1.1; margin: 2vh 0; }
    .partner-name.alt { color: #ef4444; text-shadow: 0 0 30px rgba(239,68,68,0.6); }
    .status-badge { align-self: flex-start; background: rgba(255,255,255,0.05); border: 2px solid rgba(255,255,255,0.2); color: #fff; padding: 0.8vh 2vw; border-radius: 20px; font-weight: 800; font-size: clamp(12px, 1.5vmax, 26px); }
  </style>
</head>
<body>
  <div class="bg-gradient"></div>
  <div class="bg-grid"></div>
  <div class="bg-noise"></div>
  <div class="container">
    <div class="video-title-card">
      <div class="video-title-kicker" contenteditable="true" data-field="kicker">${scene.kicker}</div>
      <div class="video-title" contenteditable="true" data-field="title">${scene.title}</div>
    </div>
    <div class="visual-wrapper">
      <div class="wrapper-inner">
        <div class="partner-card-1" style="${card1Style}">
          <div class="badge-label" contenteditable="true" data-field="visual.card1.badge">${c1.badge}</div>
          <div class="partner-name" contenteditable="true" data-field="visual.card1.name">${c1.name}</div>
          <div class="status-badge" contenteditable="true" data-field="visual.card1.status">${c1.status}</div>
        </div>
        <div class="partner-card-2" style="${card2Style}">
          <div class="badge-label" contenteditable="true" data-field="visual.card2.badge">${c2.badge}</div>
          <div class="partner-name alt" contenteditable="true" data-field="visual.card2.name">${c2.name}</div>
          <div class="status-badge" contenteditable="true" data-field="visual.card2.status">${c2.status}</div>
        </div>
      </div>
    </div>
    <div class="karaoke-panel">
      <div class="caption-wrapper">
${chunksHTML}      </div>
    </div>
  </div>
  <img class="mascot" src="/.html-video/projects/${state.projectId}/assets/mascot.png" onerror="this.src='/assets/mascot.png'" alt="Mascot" style="${mascotStyle}">
  <div class="progress-container"><div class="progress-bar"></div></div>

  <!-- Interactive Editing & Drag-and-Drop Script -->
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      // 1. Text editing
      document.querySelectorAll('[contenteditable="true"]').forEach(el => {
        el.style.outline = 'none';
        el.style.borderRadius = '4px';
        el.addEventListener('focus', () => {
          el.style.boxShadow = '0 0 10px rgba(120, 87, 255, 0.4)';
          el.style.background = 'rgba(120, 87, 255, 0.05)';
        });
        el.addEventListener('blur', () => {
          el.style.boxShadow = 'none';
          el.style.background = 'none';
          const field = el.dataset.field;
          const text = el.innerText.trim();
          if (window.parent && typeof window.parent.onIframeEdit === 'function') {
            window.parent.onIframeEdit(field, text);
          }
        });
        el.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            el.blur();
          }
        });
      });

      // 2. Generic Drag and Drop helper
      const setupDrag = (el, saveKey, isAbsolute) => {
        if (!el) return;
        
        let active = false;
        let startX = 0, startY = 0;
        let initialX = 0, initialY = 0;
        
        if (isAbsolute) {
          initialX = parseFloat(el.style.left) || el.offsetLeft || 0;
          initialY = parseFloat(el.style.top) || el.offsetTop || 0;
        } else {
          initialX = parseFloat(el.style.left) || 0;
          initialY = parseFloat(el.style.top) || 0;
        }
        
        el.style.cursor = 'grab';
        
        const dragStart = (e) => {
          if (e.target.closest('[contenteditable="true"]')) return;
          
          active = true;
          el.style.cursor = 'grabbing';
          
          const clientX = e.type === "touchstart" ? e.touches[0].clientX : e.clientX;
          const clientY = e.type === "touchstart" ? e.touches[0].clientY : e.clientY;
          
          startX = clientX - initialX;
          startY = clientY - initialY;
        };
        
        const dragEnd = () => {
          if (!active) return;
          active = false;
          el.style.cursor = 'grab';
          
          if (window.parent && typeof window.parent.onIframeMove === 'function') {
            window.parent.onIframeMove(saveKey, Math.round(initialX), Math.round(initialY));
          }
        };
        
        const drag = (e) => {
          if (!active) return;
          e.preventDefault();
          
          const clientX = e.type === "touchmove" ? e.touches[0].clientX : e.clientX;
          const clientY = e.type === "touchmove" ? e.touches[0].clientY : e.clientY;
          
          initialX = clientX - startX;
          initialY = clientY - startY;
          
          if (isAbsolute) {
            el.style.left = initialX + 'px';
            el.style.top = initialY + 'px';
            el.style.bottom = 'auto';
            el.style.right = 'auto';
          } else {
            el.style.left = initialX + 'px';
            el.style.top = initialY + 'px';
          }
        };
        
        el.addEventListener('mousedown', dragStart);
        window.addEventListener('mouseup', dragEnd);
        window.addEventListener('mousemove', drag);
        
        el.addEventListener('touchstart', dragStart, { passive: false });
        window.addEventListener('touchend', dragEnd);
        window.addEventListener('touchmove', drag, { passive: false });
      };

      // Set up drag for mascot (absolute) and cards (relative)
      setupDrag(document.querySelector('.mascot'), 'mascot', true);
      setupDrag(document.querySelector('.partner-card-1'), 'card1', false);
      setupDrag(document.querySelector('.partner-card-2'), 'card2', false);
    });
  </script>
</body>
</html>`;
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r},${g},${b}`;
}

// ── Window-level handlers for iframe interactions ─────────
window.onIframeEdit = (fieldPath, text) => {
  if (!state.project) return;
  const scene = state.project.scenes[state.currentScene];
  
  if (fieldPath === 'kicker') {
    scene.kicker = text;
  } else if (fieldPath === 'title') {
    scene.title = text;
  } else if (fieldPath.startsWith('visual.card1.')) {
    const key = fieldPath.split('.').pop();
    if (!scene.visual) scene.visual = {};
    if (!scene.visual.card1) scene.visual.card1 = {};
    scene.visual.card1[key] = text;
  } else if (fieldPath.startsWith('visual.card2.')) {
    const key = fieldPath.split('.').pop();
    if (!scene.visual) scene.visual = {};
    if (!scene.visual.card2) scene.visual.card2 = {};
    scene.visual.card2[key] = text;
  }
  
  updateTextPanel();
  renderSceneList();
  saveProject();
  toast('Đã cập nhật văn bản', 'success');
};

window.onIframeMove = (elementKey, x, y) => {
  if (!state.project) return;
  const scene = state.project.scenes[state.currentScene];
  if (!scene.visual) scene.visual = {};
  
  if (elementKey === 'mascot') {
    scene.visual.mascot_pos = { x, y };
  } else if (elementKey === 'card1') {
    scene.visual.card1_pos = { x, y };
  } else if (elementKey === 'card2') {
    scene.visual.card2_pos = { x, y };
  }
  
  saveProject();
  toast('Đã lưu vị trí kéo thả mới', 'success');
};

// ── Render scene list ────────────────────────────────────
function renderSceneList() {
  const list = $('#sceneList');
  list.innerHTML = '';
  if (!state.project) return;

  state.project.scenes.forEach((scene, i) => {
    const el = document.createElement('div');
    el.className = `scene-item${i === state.currentScene ? ' active' : ''}`;
    el.draggable = true;
    el.dataset.index = i;
    el.innerHTML = `
      <div class="drag-handle"><span></span><span></span><span></span></div>
      <div class="scene-number">SCENE ${i + 1}</div>
      <div class="scene-title">${scene.title}</div>
      <div class="scene-kicker">${scene.kicker}</div>
      <div class="scene-duration">${scene.duration_sec}s</div>
    `;
    el.addEventListener('click', () => selectScene(i));
    // Drag events for reordering
    el.addEventListener('dragstart', (e) => {
      el.classList.add('dragging');
      e.dataTransfer.setData('text/plain', i);
    });
    el.addEventListener('dragend', () => el.classList.remove('dragging'));
    el.addEventListener('dragover', (e) => { e.preventDefault(); el.style.borderTopColor = 'var(--accent)'; });
    el.addEventListener('dragleave', () => { el.style.borderTopColor = 'transparent'; });
    el.addEventListener('drop', (e) => {
      e.preventDefault();
      el.style.borderTopColor = 'transparent';
      const from = parseInt(e.dataTransfer.getData('text/plain'));
      const to = i;
      if (from !== to) {
        const [moved] = state.project.scenes.splice(from, 1);
        state.project.scenes.splice(to, 0, moved);
        state.currentScene = to;
        saveProject();
        renderAll();
        toast('Đã sắp xếp lại scenes', 'success');
      }
    });
    list.appendChild(el);
  });
}

// ── Render timeline ──────────────────────────────────────
function renderTimeline() {
  const tl = $('#timeline');
  tl.innerHTML = '';
  if (!state.project) return;

  const icons = ['🔥', '💡', '⚠️', '🔧', '👇', '🎬', '📊', '🎯'];
  state.project.scenes.forEach((scene, i) => {
    const el = document.createElement('div');
    el.className = `timeline-frame${i === state.currentScene ? ' active' : ''}`;
    el.innerHTML = `
      <div class="frame-icon">${icons[i] || '🎬'}</div>
      <div class="frame-label">S${i + 1}</div>
      <div class="frame-dur">${scene.duration_sec}s</div>
    `;
    el.addEventListener('click', () => selectScene(i));
    tl.appendChild(el);
  });
}

// ── Select scene ─────────────────────────────────────────
function selectScene(i) {
  state.currentScene = i;
  renderSceneList();
  renderTimeline();
  renderPreview();
  updateTextPanel();
  updateVoicePanel();
  updateThemeSwatches();
}

// ── Render preview ───────────────────────────────────────
function renderPreview() {
  if (!state.project) return;
  if (!state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
    const frame = $('#previewFrame');
    frame.srcdoc = `
      <body style="background:#040814; color:#a1a1aa; display:flex; align-items:center; justify-content:center; height:100vh; font-family:sans-serif;">
        <div style="text-align:center;">
          <div style="font-size:40px; margin-bottom:15px;">🎞️</div>
          <div>Không có phân cảnh nào.</div>
          <div style="font-size:12px; margin-top:8px; color:#71717a;">Hãy bấm nút "+" để thêm cảnh mới!</div>
        </div>
      </body>
    `;
    $('#timeDisplay').textContent = '0:00 / 0:00';
    return;
  }
  const scene = state.project.scenes[state.currentScene];
  const html = generateFrameHTML(scene);
  const frame = $('#previewFrame');
  frame.srcdoc = html;
  const dur = scene.duration_sec || 9;
  $('#timeDisplay').textContent = `0:00 / ${Math.floor(dur / 60)}:${String(Math.floor(dur % 60)).padStart(2, '0')}`;
}

// ── Update text panel ────────────────────────────────────
function updateTextPanel() {
  if (!state.project || !state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
    $('#editKicker').value = '';
    $('#editTitle').value = '';
    $('#editCard1Badge').value = '';
    $('#editCard1Name').value = '';
    $('#editCard1Status').value = '';
    $('#editCard2Badge').value = '';
    $('#editCard2Name').value = '';
    $('#editCard2Status').value = '';
    return;
  }
  const scene = state.project.scenes[state.currentScene];
  $('#editKicker').value = scene.kicker;
  $('#editTitle').value = scene.title;
  const v = scene.visual || {};
  const c1 = v.card1 || {};
  const c2 = v.card2 || {};
  $('#editCard1Badge').value = c1.badge || '';
  $('#editCard1Name').value = c1.name || '';
  $('#editCard1Status').value = c1.status || '';
  $('#editCard2Badge').value = c2.badge || '';
  $('#editCard2Name').value = c2.name || '';
  $('#editCard2Status').value = c2.status || '';
}

function updateVoicePanel() {
  if (!state.project || !state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
    $('#ttsText').value = '';
    return;
  }
  const scene = state.project.scenes[state.currentScene];
  $('#ttsText').value = scene.tts_text || '';
}

function updateThemeSwatches() {
  if (!state.project || !state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
    $$('.theme-swatch').forEach(sw => sw.classList.remove('active'));
    return;
  }
  const scene = state.project.scenes[state.currentScene];
  $$('.theme-swatch').forEach(sw => {
    sw.classList.toggle('active', sw.dataset.theme === scene.theme);
  });
}

// ── Save project ─────────────────────────────────────────
async function saveProject() {
  await api(`/api/project?id=${state.projectId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state.project),
  });
}

// ── Render all ───────────────────────────────────────────
function renderAll() {
  renderSceneList();
  renderTimeline();
  renderPreview();
  updateTextPanel();
  updateVoicePanel();
  updateThemeSwatches();
}

// ── Tab switching ────────────────────────────────────────
function initTabs() {
  $$('.panel-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.panel-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      $$('.panel-content').forEach(c => c.hidden = true);
      $(`#tab-${tab.dataset.tab}`).hidden = false;
    });
  });
}

// ── Drop zones ───────────────────────────────────────────
function initDropZone(zoneId, inputId, uploadEndpoint, onSuccess) {
  const zone = $(zoneId);
  const input = $(inputId);

  ['dragenter', 'dragover'].forEach(ev => {
    zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
  });
  ['dragleave', 'drop'].forEach(ev => {
    zone.addEventListener(ev, () => zone.classList.remove('drag-over'));
  });

  zone.addEventListener('click', () => input.click());

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length) uploadFile(files[0], uploadEndpoint, onSuccess);
  });

  input.addEventListener('change', () => {
    if (input.files.length) uploadFile(input.files[0], uploadEndpoint, onSuccess);
  });
}

async function uploadFile(file, endpoint, onSuccess) {
  toast(`Uploading ${file.name}...`, 'info');
  const fd = new FormData();
  fd.append('file', file);
  try {
    const sep = endpoint.includes('?') ? '&' : '?';
    const res = await fetch(`${endpoint}${sep}project_id=${state.projectId}`, { method: 'POST', body: fd });
    const data = await res.json();
    if (data.status === 'ok') {
      toast(`✅ ${file.name} uploaded!`, 'success');
      onSuccess(data, file.name);
    } else {
      toast(`❌ Upload failed: ${data.error}`, 'error');
    }
  } catch (e) {
    toast(`❌ Upload error: ${e.message}`, 'error');
  }
}

// ── Slider bindings ──────────────────────────────────────
function initSliders() {
  const bind = (sliderId, valId, format, projectKey) => {
    const slider = $(sliderId);
    const val = $(valId);
    slider.addEventListener('input', () => {
      val.textContent = format(slider.value);
      if (state.project && projectKey) {
        state.project[projectKey] = parseFloat(slider.value);
      }
    });
    slider.addEventListener('change', () => saveProject());
  };

  bind('#speedSlider', '#speedVal', v => `${v}x`, 'speed_factor');
  bind('#tempSlider', '#tempVal', v => v, 'temperature');
  bind('#narVolSlider', '#narVolVal', v => `${v > 0 ? '+' : ''}${v}`, 'narration_volume_db');
  bind('#musicVolSlider', '#musicVolVal', v => v, 'music_volume_db');
  bind('#fadeSlider', '#fadeVal', v => `${v}s`, 'fade_out_sec');
}

// ── Audio players ────────────────────────────────────────
function initAudioPlayers() {
  const togglePlay = (btnId, audioId) => {
    const btn = $(btnId);
    const audio = $(audioId);
    btn.addEventListener('click', () => {
      if (audio.paused) {
        audio.play();
        btn.textContent = '⏸';
      } else {
        audio.pause();
        btn.textContent = '▶';
      }
    });
    audio.addEventListener('ended', () => { btn.textContent = '▶'; });
  };
  togglePlay('#btnPlayVoice', '#voicePreviewAudio');
  togglePlay('#btnPlayMusic', '#musicAudio');
}

// ── Play/pause preview ───────────────────────────────────
let playAllActive = false;
let currentVoiceAudio = null;

function initPlayControls() {
  $('#btnPlay').addEventListener('click', () => {
    if (!state.project || !state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
      toast('Không có phân cảnh nào để phát!', 'error');
      return;
    }
    const scene = state.project.scenes[state.currentScene];
    if (state.playing) {
      if (playAllActive) stopPlayAll();
      else stopPlay();
    } else {
      state.playing = true;
      $('#btnPlay').textContent = '⏸';
      renderPreview();
      
      // Play scene audio if available
      if (currentVoiceAudio) {
        currentVoiceAudio.pause();
        currentVoiceAudio = null;
      }
      if (scene.audio_path) {
        currentVoiceAudio = new Audio(scene.audio_path);
        const db = state.project.narration_volume_db || 3;
        currentVoiceAudio.volume = Math.min(1.0, Math.max(0.0, Math.pow(10, db / 20)));
        currentVoiceAudio.play().catch(e => console.log('Speech playback error:', e));
      }

      state.playStart = Date.now();
      const dur = (scene.duration_sec || 9) * 1000;
      state.playTimer = setTimeout(() => stopPlay(), dur);
    }
  });

  $('#btnPrev').addEventListener('click', () => {
    if (!state.project || !state.project.scenes || state.project.scenes.length === 0) return;
    if (state.currentScene > 0) selectScene(state.currentScene - 1);
  });
  
  $('#btnNext').addEventListener('click', () => {
    if (!state.project || !state.project.scenes || state.project.scenes.length === 0) return;
    if (state.currentScene < state.project.scenes.length - 1) selectScene(state.currentScene + 1);
  });

  $('#btnPlayAll').addEventListener('click', () => {
    if (!state.project || !state.project.scenes || state.project.scenes.length === 0) {
      toast('Không có phân cảnh nào để phát!', 'error');
      return;
    }
    if (playAllActive) {
      stopPlayAll();
    } else {
      playAll();
    }
  });
}

function playAll() {
  if (!state.project || !state.project.scenes.length) return;
  playAllActive = true;
  $('#btnPlayAll').textContent = '⏸ Pause All';
  $('#btnPlayAll').classList.add('btn-primary');
  
  // Play background music
  const music = $('#musicAudio');
  if (music) {
    music.currentTime = 0;
    const db = state.project.music_volume_db || -19;
    music.volume = Math.min(1.0, Math.max(0.0, Math.pow(10, db / 20)));
    music.play().catch(e => console.log('Music playback error:', e));
  }
  
  // Start sequence play from the first scene
  playSceneSequence(0);
}

function playSceneSequence(sceneIndex) {
  if (!playAllActive) return;
  
  if (sceneIndex >= state.project.scenes.length) {
    stopPlayAll();
    toast('Đã hoàn thành xem trước toàn bộ video!', 'success');
    return;
  }
  
  selectScene(sceneIndex);
  
  const scene = state.project.scenes[sceneIndex];
  const dur = (scene.duration_sec || 9) * 1000;
  
  state.playing = true;
  $('#btnPlay').textContent = '⏸';
  state.playStart = Date.now();
  
  // Play speech voice for this scene
  if (currentVoiceAudio) {
    currentVoiceAudio.pause();
    currentVoiceAudio = null;
  }
  if (scene.audio_path) {
    currentVoiceAudio = new Audio(scene.audio_path);
    const db = state.project.narration_volume_db || 3;
    currentVoiceAudio.volume = Math.min(1.0, Math.max(0.0, Math.pow(10, db / 20)));
    currentVoiceAudio.play().catch(e => console.log('Speech playback error:', e));
  }
  
  state.playTimer = setTimeout(() => {
    state.playing = false;
    $('#btnPlay').textContent = '▶';
    playSceneSequence(sceneIndex + 1);
  }, dur);
}

function stopPlayAll() {
  playAllActive = false;
  state.playing = false;
  $('#btnPlayAll').textContent = '🎞️ Play All';
  $('#btnPlayAll').classList.remove('btn-primary');
  $('#btnPlay').textContent = '▶';
  if (state.playTimer) {
    clearTimeout(state.playTimer);
    state.playTimer = null;
  }
  
  // Stop music & voice
  const music = $('#musicAudio');
  if (music) {
    music.pause();
  }
  if (currentVoiceAudio) {
    currentVoiceAudio.pause();
    currentVoiceAudio = null;
  }
}

function stopPlay() {
  state.playing = false;
  $('#btnPlay').textContent = '▶';
  if (currentVoiceAudio) {
    currentVoiceAudio.pause();
    currentVoiceAudio = null;
  }
  if (state.playTimer) { clearTimeout(state.playTimer); state.playTimer = null; }
}

// ── Theme switching ──────────────────────────────────────
// ── Theme switching ──────────────────────────────────────
function initThemes() {
  $$('.theme-swatch').forEach(sw => {
    sw.addEventListener('click', () => {
      if (!state.project || !state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
        toast('Không có phân cảnh nào để đổi theme!', 'error');
        return;
      }
      const theme = sw.dataset.theme;
      state.project.scenes[state.currentScene].theme = theme;
      saveProject();
      renderPreview();
      updateThemeSwatches();
      toast(`Theme changed to ${theme}`, 'success');
    });
  });
}

// ── Text editing ─────────────────────────────────────────
function initTextEditing() {
  $('#btnApplyText').addEventListener('click', () => {
    if (!state.project || !state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
      toast('Không có phân cảnh nào để chỉnh sửa!', 'error');
      return;
    }
    const scene = state.project.scenes[state.currentScene];
    scene.kicker = $('#editKicker').value;
    scene.title = $('#editTitle').value;
    if (!scene.visual) scene.visual = {};
    scene.visual.card1 = {
      badge: $('#editCard1Badge').value,
      name: $('#editCard1Name').value,
      status: $('#editCard1Status').value,
    };
    scene.visual.card2 = {
      badge: $('#editCard2Badge').value,
      name: $('#editCard2Name').value,
      status: $('#editCard2Status').value,
    };
    saveProject();
    renderPreview();
    renderSceneList();
    toast('✅ Text updated!', 'success');
  });
}

// ── TTS generation ───────────────────────────────────────
function initTTS() {
  $('#btnGenVoice').addEventListener('click', async () => {
    if (!state.project || !state.project.scenes || state.project.scenes.length === 0 || state.currentScene === -1) {
      toast('Không có phân cảnh nào để sinh giọng nói!', 'error');
      return;
    }
    const text = $('#ttsText').value.trim();
    if (!text) { toast('Nhập kịch bản trước!', 'error'); return; }

    const btn = $('#btnGenVoice');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating...';

    const data = await api(`/api/tts?project_id=${state.projectId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        ref_audio_path: state.voiceRef,
        temperature: parseFloat($('#tempSlider').value),
        speed_factor: parseFloat($('#speedSlider').value),
      }),
    });

    btn.disabled = false;
    btn.innerHTML = '🎤 Generate Voice';

    if (data && data.status === 'ok') {
      toast(`✅ Voice generated! Duration: ${data.duration.toFixed(1)}s`, 'success');
      // Update scene duration
      state.project.scenes[state.currentScene].duration_sec = Math.round(data.duration * 10) / 10;
      state.project.scenes[state.currentScene].tts_text = text;
      state.project.scenes[state.currentScene].audio_path = data.path;
      saveProject();
      renderTimeline();
      renderPreview();
      // Play the generated audio
      const audio = new Audio(data.path);
      audio.play();
    } else {
      toast(`❌ TTS failed: ${data?.error || 'Unknown error'}`, 'error');
    }
  });

  $('#btnLoadTTS').addEventListener('click', async () => {
    toast('🔧 Loading VieNeu-TTS...', 'info');
    $('#btnLoadTTS').disabled = true;
    const data = await api('/api/tts/init', { method: 'POST' });
    if (data) {
      toast('VieNeu-TTS đang tải... (có thể mất 10-30s)', 'info');
      // Poll status
      const poll = setInterval(async () => {
        const st = await api('/api/status');
        if (st && st.tts_loaded) {
          clearInterval(poll);
          state.ttsLoaded = true;
          $('#btnLoadTTS').disabled = false;
          $('#btnLoadTTS').textContent = '✅ TTS Ready';
          updateStatus();
          toast('✅ VieNeu-TTS sẵn sàng!', 'success');
        }
      }, 2000);
    }
  });
}

// ── Project name ─────────────────────────────────────────
function initProjectName() {
  const input = $('#projectName');
  input.addEventListener('change', () => {
    state.project.name = input.value;
    saveProject();
  });
}

// ── Export ────────────────────────────────────────────────
function initExport() {
  $('#btnExport').addEventListener('click', async () => {
    const loading = $('#pipelineLoading');
    const statusText = $('#pipelineStatusText');
    const player = $('#pipelineVideoPlayer');
    const downloadBtn = $('#btnDownloadPipelineVideo');
    const resultArea = $('#pipelineResultArea');
    const btn = $('#btnExport');

    btn.disabled = true;
    loading.style.display = 'flex';
    statusText.textContent = '🎥 Đang render video MP4 qua Playwright Chromium (có thể mất 15-30 giây)...';

    try {
      const data = await api(`/api/project/render?project_id=${state.projectId}`, {
        method: 'POST'
      });

      loading.style.display = 'none';
      btn.disabled = false;

      if (data && data.status === 'ok') {
        toast('🎉 Đã xuất video MP4 thành công!', 'success');
        
        player.src = data.video_url + '?t=' + Date.now();
        downloadBtn.href = data.video_url;
        resultArea.style.display = 'block';

        // Trigger direct browser download
        const a = document.createElement('a');
        a.href = data.video_url;
        a.download = `${state.project.name || 'video'}.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        toast('❌ Thất bại: ' + (data?.error || 'Lỗi không xác định'), 'error');
      }
    } catch (e) {
      loading.style.display = 'none';
      btn.disabled = false;
      toast('❌ Lỗi hệ thống: ' + e.message, 'error');
    }
  });
}

// ── Status check ─────────────────────────────────────────
async function updateStatus() {
  const data = await api('/api/status');
  if (data) {
    const dot = $('#statusDot');
    const label = $('#statusLabel');
    if (data.server === 'ok') {
      dot.className = 'status-dot ok';
      label.textContent = data.tts_loaded ? 'TTS Ready' : 'Server OK';
      state.ttsLoaded = data.tts_loaded;
      if (data.tts_loaded) {
        $('#btnLoadTTS').textContent = '✅ TTS Ready';
      }
    }
  }
}

// ── Add scene ────────────────────────────────────────────
function initAddScene() {
  $('#btnAddScene').addEventListener('click', () => {
    const themes = ['hook', 'reveal', 'stats', 'solution', 'cta'];
    const idx = state.project.scenes.length;
    const theme = themes[idx % themes.length];
    state.project.scenes.push({
      id: `s${idx}`,
      kicker: '📝 NEW SCENE',
      title: 'TIÊU ĐỀ MỚI',
      tts_text: '',
      display_chunks: [{ words: ['Nội', 'dung', 'mới'] }],
      theme,
      visual: {
        card1: { badge: 'Card 1', name: 'Name', status: 'Status' },
        card2: { badge: 'Card 2', name: 'Name', status: 'Status' },
      },
      duration_sec: 8,
    });
    saveProject();
    selectScene(idx);
    toast('Added new scene', 'success');
  });
}

// ── Delete scene ─────────────────────────────────────────
function showConfirmModal() {
  return new Promise((resolve) => {
    const modal = $('#confirmModal');
    const okBtn = $('#btnConfirmOK');
    const cancelBtn = $('#btnConfirmCancel');
    const card = modal.querySelector('.modal-card');
    
    modal.style.display = 'flex';
    setTimeout(() => {
      modal.classList.add('visible');
      card.style.transform = 'scale(1)';
    }, 10);

    const cleanup = (value) => {
      modal.classList.remove('visible');
      card.style.transform = 'scale(0.9)';
      setTimeout(() => {
        modal.style.display = 'none';
      }, 150);
      okBtn.removeEventListener('click', onOk);
      cancelBtn.removeEventListener('click', onCancel);
      resolve(value);
    };

    function onOk() { cleanup(true); }
    function onCancel() { cleanup(false); }

    okBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancel);
  });
}

function initDeleteScene() {
  $('#btnDeleteScene').addEventListener('click', async () => {
    if (!state.project || !state.project.scenes || state.project.scenes.length === 0) {
      toast('Không có phân cảnh nào để xóa!', 'error');
      return;
    }
    
    const confirmDelete = await showConfirmModal();
    if (confirmDelete) {
      const idx = state.currentScene;
      const removedScene = state.project.scenes[idx];
      
      // Store to history
      state.deletedScenesHistory.push({ scene: removedScene, index: idx });
      
      // Remove scene
      state.project.scenes.splice(idx, 1);
      
      // Select new index
      if (state.project.scenes.length === 0) {
        state.currentScene = -1;
      } else {
        state.currentScene = Math.min(idx, state.project.scenes.length - 1);
      }
      
      saveProject();
      renderAll();
      showUndoToast('Đã xóa phân cảnh.');
    }
  });

  // Global keydown for Ctrl+Z Undo
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      const active = document.activeElement;
      if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.contentEditable === 'true')) {
        return; // Prevent overriding browser text editing undo
      }
      e.preventDefault();
      if (state.deletedScenesHistory.length > 0) {
        undoLastDelete();
        // Remove toast if any
        const toastUndo = $('#btnUndoDelete');
        if (toastUndo) {
          toastUndo.closest('.toast').remove();
        }
      }
    }
  });
}

function showUndoToast(msg) {
  const el = document.createElement('div');
  el.className = 'toast success';
  el.innerHTML = `
    <span>${msg}</span>
    <button style="background:transparent; border:none; color:#c084fc; font-weight:700; margin-left:12px; cursor:pointer; text-decoration:underline; outline:none;" id="btnUndoDelete">Hoàn tác (Undo)</button>
  `;
  $('#toastContainer').appendChild(el);
  
  const undoBtn = el.querySelector('#btnUndoDelete');
  undoBtn.addEventListener('click', () => {
    undoLastDelete();
    el.remove();
  });
  
  setTimeout(() => {
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 300);
  }, 7000); // 7s to undo
}

function undoLastDelete() {
  if (state.deletedScenesHistory.length === 0) return;
  const { scene, index } = state.deletedScenesHistory.pop();
  
  state.project.scenes.splice(index, 0, scene);
  state.currentScene = index;
  
  saveProject();
  renderAll();
  toast('🔄 Đã hoàn tác xóa phân cảnh', 'success');
}

// ── Pipeline E2E Workflow ────────────────────────────────
const SCRIPT_TEMPLATES = {
  de: `Cảnh 1: Có phải bạn đang tìm kiếm một lộ trình học Data Engineer thực tế?
---
Cảnh 2: Hầu hết các tài liệu trên mạng đều lý thuyết suông và không có dự án thực tế.
---
Cảnh 3: Đây là thống kê về cơ hội việc làm của ngành kỹ sư dữ liệu trong năm nay.
---
Cảnh 4: Rikkei Academy mang đến giải pháp học End-to-End với chuyên gia hàng đầu.
---
Cảnh 5: Hãy comment DE ngay để nhận lộ trình chi tiết Data Engineer 2026!`,

  iot: `Cảnh 1: Nhà thông minh không chỉ là bật tắt thiết bị bằng giọng nói.
---
Cảnh 2: Đó là sự kết hợp đồng bộ giữa các cảm biến tự động hóa IoT.
---
Cảnh 3: Tiết kiệm đến 30% điện năng tiêu thụ nhờ các kịch bản tự động thông minh.
---
Cảnh 4: Giải pháp Smart Home trọn gói chuẩn quốc tế từ Rikkei Academy.
---
Cảnh 5: Hãy liên hệ ngay hôm nay để nhận thiết kế hệ thống miễn phí!`
};

function initPipeline() {
  const btn = $('#btnRunPipeline');
  const scriptInput = $('#pipelineScript');
  const loading = $('#pipelineLoading');
  const statusText = $('#pipelineStatusText');
  const resultArea = $('#pipelineResultArea');
  const player = $('#pipelineVideoPlayer');
  const downloadBtn = $('#btnDownloadPipelineVideo');
  const charCount = $('#scriptCharCount');

  // Live character counter
  scriptInput.addEventListener('input', () => {
    const chars = scriptInput.value.length;
    charCount.innerHTML = `<span class="scene-badge-indicator" style="background: rgba(120, 87, 255, 0.1); color: #a855f7; border: 1px solid rgba(120, 87, 255, 0.2); padding: 2px 6px; border-radius: 12px; font-weight: 600;">${chars} ký tự</span>`;
  });

  // Template Quick Select click handlers
  $$('.template-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      const type = tag.dataset.type;
      if (SCRIPT_TEMPLATES[type]) {
        scriptInput.value = SCRIPT_TEMPLATES[type];
        // Trigger input event to update char counter
        scriptInput.dispatchEvent(new Event('input'));
        toast('Đã nạp kịch bản mẫu ' + tag.textContent.trim(), 'info');
        
        // Highlight active template
        $$('.template-tag').forEach(t => {
          t.style.background = 'rgba(255,255,255,0.03)';
          t.style.borderColor = 'rgba(255,255,255,0.1)';
        });
        if (type === 'de') {
          tag.style.background = 'rgba(120, 87, 255, 0.25)';
          tag.style.borderColor = '#c084fc';
        } else {
          tag.style.background = 'rgba(239, 68, 68, 0.25)';
          tag.style.borderColor = '#f87171';
        }
      }
    });
  });

  btn.addEventListener('click', async () => {
    const scriptText = scriptInput.value.trim();
    if (!scriptText) {
      toast('Vui lòng nhập kịch bản trước!', 'error');
      return;
    }

    btn.disabled = true;
    loading.style.display = 'flex';
    resultArea.style.display = 'none';
    
    const steps = [
      '🎤 Đang sinh thuyết minh VieNeu-TTS local...',
      '🎛️ Đang trộn nhạc nền và chuẩn hóa âm lượng...',
      '📄 Đang dựng khung hình và phụ đề karaoke...',
      '🎥 Đang render video MP4 qua Playwright Chromium (có thể mất 15-30 giây)...',
      '🚀 Hoàn tất!'
    ];

    let currentStep = 0;
    statusText.textContent = steps[0];
    
    const progressInterval = setInterval(() => {
      if (currentStep < steps.length - 2) {
        currentStep++;
        statusText.textContent = steps[currentStep];
      }
    }, 8000);

    try {
      const data = await api(`/api/generate-pipeline?project_id=${state.projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: state.project.name || 'Untitled Project',
          script: scriptText,
          speed_factor: parseFloat($('#speedSlider').value),
          temperature: parseFloat($('#tempSlider').value),
          voice_ref: state.voiceRef,
        })
      });

      clearInterval(progressInterval);
      loading.style.display = 'none';
      btn.disabled = false;

      if (data && data.status === 'ok') {
        toast('🎉 Đã xuất video MP4 thành công!', 'success');
        
        player.src = data.video_url + '?t=' + Date.now();
        downloadBtn.href = data.video_url;
        resultArea.style.display = 'block';
        
        state.project = data.project;
        state.currentScene = 0;
        renderAll();
      } else {
        toast('❌ Thất bại: ' + (data?.error || 'Lỗi không xác định'), 'error');
      }
    } catch (e) {
      clearInterval(progressInterval);
      loading.style.display = 'none';
      btn.disabled = false;
      toast('❌ Lỗi hệ thống: ' + e.message, 'error');
    }
  });
}

// ── Project Management Selector ──────────────────────────
function showPromptModal() {
  return new Promise((resolve) => {
    const modal = $('#promptModal');
    const okBtn = $('#btnPromptOK');
    const cancelBtn = $('#btnPromptCancel');
    const input = $('#txtNewProjectName');
    const card = modal.querySelector('.modal-card');
    
    input.value = '';
    modal.style.display = 'flex';
    setTimeout(() => {
      modal.classList.add('visible');
      card.style.transform = 'scale(1)';
      input.focus();
    }, 10);

    const cleanup = (value) => {
      modal.classList.remove('visible');
      card.style.transform = 'scale(0.9)';
      setTimeout(() => {
        modal.style.display = 'none';
      }, 150);
      okBtn.removeEventListener('click', onOk);
      cancelBtn.removeEventListener('click', onCancel);
      input.removeEventListener('keydown', onKeyDown);
      resolve(value);
    };

    function onOk() {
      const val = input.value.trim();
      if (!val) {
        toast('Vui lòng nhập tên dự án!', 'error');
        return;
      }
      cleanup(val);
    }
    function onCancel() { cleanup(null); }
    function onKeyDown(e) {
      if (e.key === 'Enter') onOk();
      else if (e.key === 'Escape') onCancel();
    }

    okBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancel);
    input.addEventListener('keydown', onKeyDown);
  });
}

async function initProjectSelector() {
  const selector = $('#projectSelector');
  const btnNew = $('#btnNewProject');

  async function loadList(selectId = null) {
    const data = await api('/api/projects');
    if (data && data.projects) {
      selector.innerHTML = '';
      data.projects.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.name;
        selector.appendChild(opt);
      });
      if (selectId) {
        selector.value = selectId;
        state.projectId = selectId;
      } else if (data.projects.length > 0) {
        state.projectId = data.projects[0].id;
        selector.value = state.projectId;
      }
    }
  }

  await loadList();

  selector.addEventListener('change', async () => {
    state.projectId = selector.value;
    toast('Đang tải dự án...', 'info');
    await loadProjectData();
  });

  btnNew.addEventListener('click', async () => {
    const name = await showPromptModal();
    if (!name) return;
    const res = await api('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (res && res.project) {
      toast('Đã tạo dự án mới!', 'success');
      await loadList(res.project.id);
      await loadProjectData();
    } else {
      toast('Tạo dự án thất bại', 'error');
    }
  });
}

async function loadProjectData() {
  state.project = await api(`/api/project?id=${state.projectId}`);
  if (!state.project) {
    toast('Không thể tải dữ liệu dự án', 'error');
    return;
  }

  // Defensive scene initialization for legacy projects
  if (!state.project.scenes || state.project.scenes.length === 0) {
    state.project.scenes = [
      {
        id: "s0",
        kicker: "🔥 BẮT ĐẦU 🔥",
        title: state.project.name || "DỰ ÁN MỚI",
        tts_text: "Chào mừng bạn đến với Rikkei Video Studio.",
        display_chunks: [
          { "words": ["Chào", "mừng", "bạn", "đến", "với"], "pause_after": 0.3 },
          { "words": ["Rikkei", "Video", "Studio."] }
        ],
        theme: "hook",
        visual: {
          card1: { badge: "Khởi tạo", name: "Dự án mới", status: "Sẵn sàng" },
          card2: { badge: "VieNeu", name: "TTS Engine", status: "Local" }
        },
        duration_sec: 5.0
      }
    ];
    saveProject();
  }
  
  $('#projectName').value = state.project.name || 'Untitled';
  $('#speedSlider').value = state.project.speed_factor || 1.12;
  $('#speedVal').textContent = `${state.project.speed_factor || 1.12}x`;
  $('#tempSlider').value = state.project.temperature || 0.2;
  $('#tempVal').textContent = state.project.temperature || 0.2;
  $('#narVolSlider').value = state.project.narration_volume_db || 3;
  $('#narVolVal').textContent = `+${state.project.narration_volume_db || 3}`;
  $('#musicVolSlider').value = state.project.music_volume_db || -19;
  $('#musicVolVal').textContent = state.project.music_volume_db || -19;
  $('#fadeSlider').value = state.project.fade_out_sec || 2;
  $('#fadeVal').textContent = `${state.project.fade_out_sec || 2}s`;
  
  // Reset reference voice to default preview
  state.voiceRef = '/assets/voice_preview.mp3';
  $('#voiceFileName').hidden = true;
  $('#voicePreviewName').textContent = 'voice_preview.mp3 (default)';
  $('#voicePreviewAudio').src = '/assets/voice_preview.mp3';
  
  state.currentScene = 0;
  renderAll();
  updateStatus();
}

// ── Init ─────────────────────────────────────────────────
async function init() {
  initTabs();
  initSliders();
  initAudioPlayers();
  initPlayControls();
  initThemes();
  initTextEditing();
  initTTS();
  initProjectName();
  initExport();
  initAddScene();
  initDeleteScene();
  initPipeline();

  // Initialize projects selector and load initial project data
  await initProjectSelector();
  await loadProjectData();

  // Drop zones
  initDropZone('#voiceDropZone', '#voiceFileInput', '/api/upload-voice', (data, name) => {
    $('#voiceFileName').textContent = `✅ ${name}`;
    $('#voiceFileName').hidden = false;
    $('#voicePreviewName').textContent = name;
    if (data.path) {
      state.voiceRef = data.path;
      $('#voicePreviewAudio').src = data.path;
    }
  });

  initDropZone('#musicDropZone', '#musicFileInput', '/api/upload-music', (data, name) => {
    $('#musicFileName').textContent = `✅ ${name}`;
    $('#musicFileName').hidden = false;
    $('#musicName').textContent = name;
    if (data.path) {
      state.musicSrc = data.path;
      $('#musicAudio').src = data.path;
    }
  });
}

document.addEventListener('DOMContentLoaded', init);
