import os
import sys
import json
import hashlib
import asyncio
import subprocess
import shutil
import random
from pathlib import Path

# Set stdout/stderr encoding to UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure edge-tts is installed
try:
    import edge_tts
except ImportError:
    print("Installing edge-tts...")
    subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts"], check=True)
    import edge_tts

# Path Config (Dynamic)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE_PATH = shutil.which("ffprobe") or "ffprobe"
DEFAULT_BGM = str(WORKSPACE_ROOT / "templates" / "frame-product-promo-30s" / "assets" / "warm-pad.mp3")

PROJECTS_DIR = WORKSPACE_ROOT / ".html-video" / "projects"
EXPORTS_DIR = WORKSPACE_ROOT / "exports"

# ── Theme Colors ──────────────────────────────────────────────────────────────
THEME_COLORS = {
    "Hook/Danger": {
        "primary": "#EF4444", "primary_alpha": "rgba(239, 68, 68, 0.2)",
        "accent": "#FBBF24", "bg_radial1": "rgba(220, 38, 100, 0.22)",
        "bg_radial2": "rgba(239, 68, 68, 0.15)"
    },
    "Reveal/Answer": {
        "primary": "#34D399", "primary_alpha": "rgba(52, 211, 153, 0.2)",
        "accent": "#60A5FA", "bg_radial1": "rgba(52, 211, 153, 0.22)",
        "bg_radial2": "rgba(59, 130, 246, 0.15)"
    },
    "Stats/Data": {
        "primary": "#3B82F6", "primary_alpha": "rgba(59, 130, 246, 0.2)",
        "accent": "#34D399", "bg_radial1": "rgba(59, 130, 246, 0.22)",
        "bg_radial2": "rgba(52, 211, 153, 0.15)"
    },
    "Solution/Brand": {
        "primary": "#FF7F30", "primary_alpha": "rgba(255, 127, 48, 0.2)",
        "accent": "#3B82F6", "bg_radial1": "rgba(255, 127, 48, 0.22)",
        "bg_radial2": "rgba(59, 130, 246, 0.15)"
    },
    "CTA/Action": {
        "primary": "#EA580C", "primary_alpha": "rgba(234, 88, 12, 0.3)",
        "accent": "#EF4444", "bg_radial1": "rgba(234, 88, 12, 0.25)",
        "bg_radial2": "rgba(239, 68, 68, 0.18)"
    },
    "Tech/Cyberpunk": {
        "primary": "#06B6D4", "primary_alpha": "rgba(6, 182, 212, 0.25)",
        "accent": "#A855F7", "bg_radial1": "rgba(168, 85, 247, 0.22)",
        "bg_radial2": "rgba(6, 182, 212, 0.15)"
    },
    "Finance/Wealth": {
        "primary": "#F59E0B", "primary_alpha": "rgba(245, 158, 11, 0.25)",
        "accent": "#10B981", "bg_radial1": "rgba(245, 158, 11, 0.22)",
        "bg_radial2": "rgba(16, 185, 129, 0.15)"
    },
    "Calm/Education": {
        "primary": "#0EA5E9", "primary_alpha": "rgba(14, 165, 233, 0.25)",
        "accent": "#FFFFFF", "bg_radial1": "rgba(14, 165, 233, 0.2)",
        "bg_radial2": "rgba(255, 255, 255, 0.1)"
    },
    "Minimalist/Dark": {
        "primary": "#E5E7EB", "primary_alpha": "rgba(229, 231, 235, 0.2)",
        "accent": "#9CA3AF", "bg_radial1": "rgba(229, 231, 235, 0.1)",
        "bg_radial2": "rgba(156, 163, 175, 0.1)"
    },
    "Vibrant/Youth": {
        "primary": "#EC4899", "primary_alpha": "rgba(236, 72, 153, 0.3)",
        "accent": "#EAB308", "bg_radial1": "rgba(236, 72, 153, 0.25)",
        "bg_radial2": "rgba(234, 179, 8, 0.2)"
    }
}

# ── Dimension settings ────────────────────────────────────────────────────────
ASPECT_RATIOS = {
    "16:9": {
        "width": 1920, "height": 1080, "padding": 90, "eyebrowTop": 90,
        "titleSize": 120, "subtitleSize": 42, "gridColumns": "1fr 1fr",
        "leftBorder": "border-right: 1px solid rgba(255,255,255,0.06);",
        "statBigSize": 260, "statValSize": 120, "scaleFactor": 1.0
    },
    "9:16": {
        "width": 540, "height": 960, "padding": 40, "eyebrowTop": 72,
        "titleSize": 58, "subtitleSize": 21, "gridColumns": "1fr",
        "leftBorder": "border-bottom: 1px solid rgba(255,255,255,0.06);",
        "statBigSize": 100, "statValSize": 56, "scaleFactor": 0.5
    }
}

# ── Background Variant Pool (5 distinct visual themes) ───────────────────────
BG_VARIANTS = [
    {   # 0 — Dark radial center
        "bg_type": "radial_center",
        "grid_size": "60px 60px", "grid_opacity": 0.65,
        "orb1_pos": "top:8%;left:8%;", "orb1_size": "550px", "orb1_anim": "float1 14s infinite alternate ease-in-out",
        "orb2_pos": "bottom:8%;right:8%;", "orb2_size": "450px", "orb2_anim": "float2 16s infinite alternate ease-in-out",
        "noise_opacity": 0.05, "bg_origin": "50% 50%",
    },
    {   # 1 — Top-left radial burst
        "bg_type": "line_grid",
        "grid_size": "80px 80px", "grid_opacity": 0.4,
        "orb1_pos": "top:-5%;left:-5%;", "orb1_size": "700px", "orb1_anim": "float1 12s infinite alternate ease-in-out",
        "orb2_pos": "bottom:20%;right:20%;", "orb2_size": "350px", "orb2_anim": "float2 18s infinite alternate ease-in-out",
        "noise_opacity": 0.08, "bg_origin": "15% 15%",
    },
    {   # 2 — Dot grid with side orbs
        "bg_type": "dot_grid",
        "grid_size": "30px 30px", "grid_opacity": 0.5,
        "orb1_pos": "top:50%;left:0%;", "orb1_size": "600px", "orb1_anim": "float1 20s infinite alternate ease-in-out",
        "orb2_pos": "top:0%;right:0%;", "orb2_size": "500px", "orb2_anim": "float2 14s infinite alternate ease-in-out",
        "noise_opacity": 0.06, "bg_origin": "50% 80%",
    },
    {   # 3 — Bottom-right origin
        "bg_type": "line_grid",
        "grid_size": "50px 50px", "grid_opacity": 0.55,
        "orb1_pos": "top:30%;left:30%;", "orb1_size": "480px", "orb1_anim": "float1 16s infinite alternate ease-in-out",
        "orb2_pos": "bottom:-5%;right:-5%;", "orb2_size": "650px", "orb2_anim": "float2 13s infinite alternate ease-in-out",
        "noise_opacity": 0.04, "bg_origin": "85% 85%",
    },
    {   # 4 — Minimal dark sparse
        "bg_type": "dot_grid",
        "grid_size": "90px 90px", "grid_opacity": 0.25,
        "orb1_pos": "top:20%;left:50%;", "orb1_size": "800px", "orb1_anim": "float1 25s infinite alternate ease-in-out",
        "orb2_pos": "bottom:30%;right:50%;", "orb2_size": "300px", "orb2_anim": "float2 20s infinite alternate ease-in-out",
        "noise_opacity": 0.03, "bg_origin": "50% 40%",
    },
]

def build_bg_css(bgv, colors):
    if bgv["bg_type"] == "dot_grid":
        grid_css = f"""
.grid-floor {{
  position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,0.12) 1px, transparent 1px);
  background-size:{bgv['grid_size']};
  mask-image:radial-gradient(circle at 50% 50%, black 40%, transparent 90%);
  opacity:{bgv['grid_opacity']};
}}"""
    else:
        grid_css = f"""
.grid-floor {{
  position:absolute;inset:0;
  background-image:linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
                   linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px);
  background-size:{bgv['grid_size']};
  mask-image:radial-gradient(circle at 50% 50%, black 35%, transparent 85%);
  opacity:{bgv['grid_opacity']};
}}"""

    return f"""
.vignette{{position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse at center,transparent 30%,rgba(0,0,0,0.88) 100%);z-index:2;}}
{grid_css}
.bg-noise{{position:absolute;inset:0;pointer-events:none;opacity:{bgv['noise_opacity']};
  background-image:radial-gradient(rgba(255,255,255,0.05) 1px,transparent 1px);background-size:4px 4px;}}
.orb{{position:absolute;border-radius:50%;filter:blur(120px);opacity:0.18;will-change:transform;}}
.orb-1{{{bgv['orb1_pos']}width:{bgv['orb1_size']};height:{bgv['orb1_size']};
  background:radial-gradient(circle,{colors['bg_radial1']} 0%,transparent 70%);animation:{bgv['orb1_anim']};}}
.orb-2{{{bgv['orb2_pos']}width:{bgv['orb2_size']};height:{bgv['orb2_size']};
  background:radial-gradient(circle,{colors['bg_radial2']} 0%,transparent 70%);animation:{bgv['orb2_anim']};}}
@keyframes float1{{from{{transform:translate(0,0) scale(1);}} to{{transform:translate(45px,-35px) scale(1.1);}}}}
@keyframes float2{{from{{transform:translate(0,0) scale(1);}} to{{transform:translate(-55px,45px) scale(0.92);}}}}
"""

# ── Animation Variant System ──────────────────────────────────────────────────
# NOTE: Templates use plain {T} (no quotes) — quoting is handled by _qt() helper.
# {D} = delay (enter), {H} = hold time before end (exit).
ENTER_ANIMATIONS = {
    "fadeUp":       "tl.to({T}, {opacity:1, y:0, duration:0.65, ease:'power3.out'}, {D});",
    "fadeDown":     "tl.fromTo({T}, {opacity:0, y:-40}, {opacity:1, y:0, duration:0.6, ease:'power3.out'}, {D});",
    "slideLeft":    "tl.fromTo({T}, {opacity:0, x:-60}, {opacity:1, x:0, duration:0.65, ease:'power3.out'}, {D});",
    "slideRight":   "tl.fromTo({T}, {opacity:0, x:60}, {opacity:1, x:0, duration:0.65, ease:'power3.out'}, {D});",
    "zoomIn":       "tl.fromTo({T}, {opacity:0, scale:0.72}, {opacity:1, scale:1, duration:0.7, ease:'back.out(1.8)'}, {D});",
    "zoomInBounce": "tl.fromTo({T}, {opacity:0, scale:0.5}, {opacity:1, scale:1, duration:0.8, ease:'elastic.out(1,0.5)'}, {D});",
    "glitchIn":     "tl.fromTo({T}, {opacity:0, x:-8, skewX:5}, {opacity:1, x:0, skewX:0, duration:0.5, ease:'power4.out'}, {D});\n  tl.to({T}, {x:4, duration:0.08, yoyo:true, repeat:2, ease:'none'}, {D_PLUS});",
    "typeReveal":   "tl.fromTo({T}, {opacity:0, clipPath:'inset(0 100% 0 0)'}, {opacity:1, clipPath:'inset(0 0% 0 0)', duration:0.7, ease:'power2.inOut'}, {D});",
}
EXIT_ANIMATIONS = {
    "fadeUp":    "tl.to({T}, {opacity:0, y:-35, duration:0.4, ease:'power2.in'}, SLOT-{H});",
    "slideLeft": "tl.to({T}, {opacity:0, x:-80, duration:0.45, ease:'power2.in'}, SLOT-{H});",
    "slideRight":"tl.to({T}, {opacity:0, x:80, duration:0.45, ease:'power2.in'}, SLOT-{H});",
    "zoomOut":   "tl.to({T}, {opacity:0, scale:0.75, duration:0.4, ease:'power2.in'}, SLOT-{H});",
    "dissolve":  "tl.to({T}, {opacity:0, duration:0.5, ease:'power1.in'}, SLOT-{H});",
    "glitchOut": "tl.to({T}, {x:6, skewX:-4, duration:0.08, yoyo:true, repeat:2}, SLOT-{H}-0.12);\n  tl.to({T}, {opacity:0, x:-20, duration:0.18, ease:'power3.in'}, SLOT-{H}+0.1);",
}
LAYOUT_ANIM_PREFS = {
    "hook":          [("glitchIn","glitchOut"), ("zoomInBounce","zoomOut"), ("typeReveal","fadeUp")],
    "reveal":        [("slideLeft","slideLeft"), ("fadeUp","dissolve"), ("slideRight","slideRight")],
    "stats":         [("zoomIn","fadeUp"), ("fadeDown","dissolve"), ("slideLeft","fadeUp")],
    "cta":           [("zoomInBounce","dissolve"), ("fadeUp","fadeUp"), ("slideRight","zoomOut")],
    "learning-path": [("zoomIn","fadeUp"), ("slideLeft","dissolve")],
    "card-list":     [("slideLeft","fadeUp"), ("zoomIn","dissolve"), ("slideRight","fadeUp")],
    "brand-reveal":  [("zoomInBounce","dissolve"), ("fadeDown","fadeUp")],
    "admin-report":  [("fadeUp","fadeUp"), ("slideLeft","dissolve")],
}

def pick_anim(layout, scene_idx, scene=None):
    prefs = LAYOUT_ANIM_PREFS.get(layout, [("fadeUp","fadeUp")])
    default_enter, default_exit = prefs[scene_idx % len(prefs)]
    
    if scene:
        enter = scene.get("enter_anim", default_enter)
        exit_ = scene.get("exit_anim", default_exit)
        return enter, exit_
    return default_enter, default_exit

def _qt(target):
    """Quote a CSS selector string for GSAP. Arrays and pre-quoted strings pass through."""
    t = target.strip()
    if t.startswith('[') or t.startswith("'") or t.startswith('"'):
        return t  # already an array literal or quoted
    return f"'{t}'"  # wrap single selector in quotes

def anim_enter(name, target, delay):
    t = ENTER_ANIMATIONS.get(name, ENTER_ANIMATIONS["fadeUp"])
    qt = _qt(target)
    d = str(round(delay, 2))
    d_plus = str(round(delay + 0.5, 2))
    return t.replace("{T}", qt).replace("{D_PLUS}", d_plus).replace("{D}", d)

def anim_exit(name, target, hold=0.45):
    t = EXIT_ANIMATIONS.get(name, EXIT_ANIMATIONS["fadeUp"])
    return t.replace("{T}", _qt(target)).replace("{H}", str(hold))

# ── Mascot Behaviors ──────────────────────────────────────────────────────────
MASCOT_BEHAVIORS = {
    "hook": {
        "start_css": "transform:translateX(80px) translateY(20px);opacity:0;",
        "js": """
  tl.to('#mascotContainer',{x:0,y:0,opacity:1,duration:0.5,ease:'back.out(1.4)'},0.4);
  tl.to('#mascotContainer',{rotation:-15,y:-20,duration:0.28,ease:'power2.out'},1.0);
  tl.to('#mascotContainer',{rotation:0,y:0,duration:0.28,ease:'bounce.out'},1.28);
  tl.to('#mascotContainer',{scaleX:1.2,scaleY:0.8,duration:0.1},1.6);
  tl.to('#mascotContainer',{scaleX:0.9,scaleY:1.15,y:-18,duration:0.2,ease:'power2.out'},1.7);
  tl.to('#mascotContainer',{scaleX:1,scaleY:1,y:0,duration:0.28,ease:'bounce.out'},1.9);"""
    },
    "reveal": {
        "start_css": "transform:translateY(30px);opacity:0;",
        "js": """
  tl.to('#mascotContainer',{y:0,opacity:1,duration:0.4,ease:'power3.out'},0.6);
  tl.to('#mascotContainer',{rotation:12,duration:0.22,ease:'power2.out'},1.1);
  tl.to('#mascotContainer',{rotation:-8,duration:0.22,ease:'power2.inOut'},1.32);
  tl.to('#mascotContainer',{rotation:0,duration:0.18,ease:'power2.out'},1.54);"""
    },
    "stats": {
        "start_css": "transform:scale(0.5);opacity:0;",
        "js": """
  tl.to('#mascotContainer',{scale:1,opacity:1,duration:0.5,ease:'elastic.out(1,0.5)'},0.5);
  tl.to('#mascotContainer',{y:-25,scaleX:0.88,scaleY:1.12,duration:0.25,ease:'power2.out'},1.2);
  tl.to('#mascotContainer',{y:0,scaleX:1.12,scaleY:0.88,duration:0.18,ease:'power2.in'},1.45);
  tl.to('#mascotContainer',{y:-12,scaleX:1,scaleY:1,duration:0.18,ease:'power2.out'},1.63);
  tl.to('#mascotContainer',{y:0,duration:0.2,ease:'bounce.out'},1.81);"""
    },
    "cta": {
        "start_css": "transform:translateX(60px) rotate(20deg);opacity:0;",
        "js": """
  tl.to('#mascotContainer',{x:0,rotation:0,opacity:1,duration:0.55,ease:'back.out(1.6)'},0.4);
  tl.to('#mascotContainer',{rotation:15,y:-10,duration:0.2,ease:'power2.out'},1.0);
  tl.to('#mascotContainer',{rotation:-15,duration:0.2,ease:'power2.inOut'},1.2);
  tl.to('#mascotContainer',{rotation:15,duration:0.2,ease:'power2.inOut'},1.4);
  tl.to('#mascotContainer',{rotation:0,y:0,duration:0.28,ease:'elastic.out(1,0.6)'},1.6);
  tl.to('#mascotContainer',{y:-20,scaleX:0.9,scaleY:1.1,duration:0.25,ease:'power2.out'},2.2);
  tl.to('#mascotContainer',{y:0,scaleX:1,scaleY:1,duration:0.3,ease:'bounce.out'},2.45);"""
    },
    "default": {
        "start_css": "transform:translateY(20px);opacity:0;",
        "js": """
  tl.to('#mascotContainer',{y:0,opacity:1,duration:0.5,ease:'back.out(1.4)'},0.5);
  tl.to('#mascotContainer',{y:-15,scaleX:0.95,scaleY:1.05,duration:0.3,ease:'power2.out'},1.2);
  tl.to('#mascotContainer',{y:0,scaleX:1,scaleY:1,duration:0.28,ease:'bounce.out'},1.5);"""
    }
}

# ── HTML Boilerplate ──────────────────────────────────────────────────────────
HTML_BOILERPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Be+Vietnam+Pro:wght@400;500;700&subset=vietnamese&display=swap" rel="stylesheet"/>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet"/>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:{{width}}px;height:{{height}}px;overflow:hidden;background:#03050a;}
.stage-container{
  position:absolute;inset:0;overflow:hidden;
  background:radial-gradient(ellipse 140% 120% at {{bg_origin}},{{bg_radial1}} 0%,#03050d 65%,#000 100%);
  font-family:'Be Vietnam Pro',sans-serif;
}
{{bg_css}}
.eyebrow-tag{
  position:absolute;top:{{eyebrowTop}}px;left:50%;transform:translateX(-50%);
  font-size:17px;font-weight:700;letter-spacing:4px;text-transform:uppercase;
  color:{{primary}};border:1px solid {{primary_alpha}};
  background:rgba(255,255,255,0.025);backdrop-filter:blur(16px);
  border-radius:50px;padding:11px 26px;opacity:0;
  text-shadow:0 0 15px {{primary_alpha}};white-space:nowrap;
}
.glass-card{
  background:rgba(255,255,255,0.028);backdrop-filter:blur(24px);
  border:1px solid rgba(255,255,255,0.07);border-radius:22px;
  box-shadow:0 20px 50px rgba(0,0,0,0.35);position:relative;overflow:hidden;
}

.glass-card::before{
  content:'';position:absolute;left:0;top:0;bottom:0;width:4px;
  background:linear-gradient(180deg,{{primary}},{{accent}});
  border-radius:22px 0 0 22px;
}
.progress-bar{
  position:absolute;bottom:0;left:0;height:5px;background:linear-gradient(90deg,{{primary}},{{accent}});
  width:100%;transform:scaleX(0);transform-origin:left;
}
.mascot-container{
  position:absolute;z-index:10;pointer-events:none;
  transform-origin:bottom center;
  {{mascot_start_css}}
}
@media (max-aspect-ratio:1/1){.mascot-container{width:62px;height:62px;bottom:22px;right:18px;}}
@media (min-aspect-ratio:1/1){.mascot-container{width:125px;height:125px;bottom:35px;right:28px;}}

@keyframes mascotBob {
  0%   { transform: translateY(0)    translateX(0)    rotate(0deg)   scaleY(1)    scaleX(1);    }
  12%  { transform: translateY(-10px) translateX(-6px)  rotate(-8deg)  scaleY(1.06) scaleX(0.94); }
  25%  { transform: translateY(2px)   translateX(-3px)  rotate(-3deg)  scaleY(0.94) scaleX(1.06); }
  37%  { transform: translateY(0)     translateX(0)     rotate(0deg)   scaleY(1)    scaleX(1);    }
  50%  { transform: translateY(0)     translateX(0)     rotate(0deg)   scaleY(1)    scaleX(1);    }
  62%  { transform: translateY(-10px) translateX(6px)   rotate(8deg)   scaleY(1.06) scaleX(0.94); }
  75%  { transform: translateY(2px)   translateX(3px)   rotate(3deg)   scaleY(0.94) scaleX(1.06); }
  87%  { transform: translateY(0)     translateX(0)     rotate(0deg)   scaleY(1)    scaleX(1);    }
  100% { transform: translateY(0)     translateX(0)     rotate(0deg)   scaleY(1)    scaleX(1);    }
}
.mascot-img {
  width:100%;height:100%;display:block;transform-origin:bottom center;
  animation: mascotBob 2s infinite ease-in-out;
}
</style>
</head>
<body>
<div class="stage-container" data-composition-id="{{comp_id}}">
  <div class="vignette"></div>
  <div class="grid-floor"></div>
  <div class="bg-noise"></div>
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
  {{layout_html}}
  {{captions_html}}
  <div class="mascot-container" id="mascotContainer">
    <img src="../../../../shared_assets/mascot.png" class="mascot-img" id="mascotAvatar"/>
  </div>
  <div class="progress-bar" id="progressBar"></div>
<script>
(function(){
  var SLOT={{slot}};
  var tl=gsap.timeline({paused:true});
  tl.to('#progressBar',{scaleX:1,duration:SLOT,ease:'none'},0);
  {{layout_js}}
  {{captions_js}}
  {{mascot_js}}
  window.__hvPlayAll=function(){tl.play();};
})();
</script>
</div>
</body>
</html>
"""

# ── Layout Renderers ──────────────────────────────────────────────────────────

def render_hook(scene, dim, colors, scene_idx=0):
    enter, exit_ = pick_anim("hook", scene_idx, scene)
    html = f"""
  <div class="eyebrow-tag" id="eyebrow">{scene.get('eyebrow','⚡ GIỚI THIỆU')}</div>
  <div id="heroBlock" style="position:absolute;left:50%;top:48%;transform:translate(-50%,-50%);
    text-align:center;width:88%;opacity:0;display:flex;flex-direction:column;align-items:center;gap:28px;">
    <div id="heroTitle" style="font-family:'Barlow Condensed',sans-serif;font-size:{dim['titleSize']}px;
      font-weight:900;line-height:1.15;text-transform:uppercase;letter-spacing:-1px;padding-top:10px;
      background:linear-gradient(135deg,#fff 0%,rgba(255,255,255,0.72) 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
      {scene.get('headline','TIÊU ĐỀ LỚN')}
    </div>
    <div id="heroLine" style="width:55px;height:4px;background:linear-gradient(90deg,{colors['primary']},{colors['accent']});
      border-radius:2px;opacity:0;transform:scaleX(0);transform-origin:center;"></div>
    <div id="heroSub" style="font-size:{dim['subtitleSize']}px;font-weight:500;line-height:1.45;
      color:rgba(255,255,255,0.72);max-width:480px;opacity:0;">
      {scene.get('subtitle','')}
    </div>
  </div>"""
    js = f"""
  {anim_enter('fadeUp','#eyebrow',0.05)}
  {anim_enter(enter,'#heroBlock',0.15)}
  tl.fromTo('#heroLine',{{opacity:0,scaleX:0}},{{opacity:1,scaleX:1,duration:0.4,ease:'expo.out'}},0.25);
  {anim_enter('fadeUp','#heroSub',0.35)}
  {anim_exit(exit_,"['#eyebrow','#heroBlock','#heroLine','#heroSub']")}"""
    return html, js


def render_reveal(scene, dim, colors, scene_idx=0):
    pains = scene.get("elements", [])
    enter, exit_ = pick_anim("reveal", scene_idx, scene)
    is_vertical = dim['scaleFactor'] < 0.8

    ICON_MAP = {
        "portfolio":"💼","dự án":"💼","lương":"💰","thu nhập":"💰",
        "ai":"🤖","machine":"🤖","tiến độ":"📈","quản lý":"📈",
        "lộ trình":"🗺️","học":"🗺️","tài nguyên":"🎥","học liệu":"🎥",
        "hiệu suất":"🚀","thời gian":"🚀","kỹ năng":"⚙️","tool":"⚙️",
        "lỗi":"⚠️","sai":"⚠️",
    }

    pains_html = []
    pains_js = []
    for idx, p in enumerate(pains):
        parts = p.split("|")
        p_title = parts[0].strip()
        p_desc = parts[1].strip() if len(parts) > 1 else ""
        icon = parts[2].strip() if len(parts) > 2 else "⚡"
        
        if icon == "⚡":
            for kw, ic in ICON_MAP.items():
                if kw in p_title.lower() or kw in p_desc.lower():
                    icon = ic; break
                    
        if icon.startswith("fa-"):
            icon = f'<i class="{icon}"></i>'

        delay = 0.25 + idx * 0.1
        pains_html.append(f"""
      <div class="pain" id="p{idx}" style="display:flex;align-items:center;gap:20px;
        margin-bottom:24px;opacity:0;">
        <div id="iconBox_{idx}" class="icon-dynamic" style="width:64px;height:64px;border-radius:18px;
          background:linear-gradient(135deg, {colors['primary']}, {colors['accent']});
          border:1px solid rgba(255,255,255,0.4); display:flex;justify-content:center;align-items:center;
          font-size:28px;color:#fff;flex-shrink:0;box-shadow:0 8px 25px {colors['primary_alpha']};
          transform:scale(0.8);">{icon}</div>
        <div id="textBox_{idx}" style="display:flex;flex-direction:column;gap:4px;opacity:0;transform:translateX(-15px);">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:{int(dim['titleSize']*0.54)}px;
            font-weight:900;text-transform:uppercase;color:#fff;line-height:1.2;padding-top:4px;">{p_title}</strong>
          <span style="font-size:{dim['subtitleSize']-2}px;color:rgba(200,200,220,0.7);line-height:1.4;">{p_desc}</span>
        </div>
      </div>""")
        pains_js.append(f"  tl.to('#p{idx}',{{opacity:1,duration:0.1}},{delay});")
        pains_js.append(f"  tl.to('#iconBox_{idx}',{{scale:1,rotation:0,duration:0.5,ease:'back.out(1.5)'}},{delay});")
        pains_js.append(f"  tl.to('#textBox_{idx}',{{opacity:1,x:0,duration:0.5,ease:'expo.out'}},{delay+0.05});")

    pains_end = 0.15 + len(pains) * 0.1 + 0.1

    if is_vertical:
        html = f"""
  <div style="position:absolute;inset:0;display:flex;flex-direction:column;
    justify-content:center;padding:{dim['padding']}px;">
    <div id="lbl" style="font-size:13px;font-weight:700;letter-spacing:5px;text-transform:uppercase;
      color:{colors['primary']};margin-bottom:18px;opacity:0;">{scene.get('eyebrow','VẤN ĐỀ')}</div>
    <div id="revTitle" style="font-family:'Barlow Condensed',sans-serif;font-size:{dim['titleSize']}px;
      font-weight:900;text-transform:uppercase;color:#fff;line-height:1.15;padding-top:10px;margin-bottom:20px;opacity:0;">
      {scene.get('headline','?')}</div>
    {"".join(pains_html)}
    <div id="revSub" style="font-size:{dim['subtitleSize']}px;color:rgba(200,200,220,0.7);
      line-height:1.4;margin-top:10px;opacity:0;">{scene.get('subtitle','')}</div>
  </div>"""
        js = f"""
  {anim_enter('fadeUp','#lbl',0.05)}
  {anim_enter(enter,'#revTitle',0.1)}
  {"".join(pains_js)}
  tl.to('.icon-dynamic', {{scale:1.08, rotation:5, filter:'drop-shadow(0 0 25px {colors["primary_alpha"]})', duration:2, yoyo:true, repeat:30, ease:'sine.inOut'}}, 0.5);
  {anim_enter('fadeUp','#revSub',pains_end)}
  {anim_exit(exit_,"['[id^=\\'p\\']','#lbl','#revTitle','#revSub']")}"""
    else:
        html = f"""
  <div style="position:absolute;inset:0;display:grid;grid-template-columns:{dim['gridColumns']};">
    <div style="position:relative;display:flex;flex-direction:column;justify-content:center;
      padding:{dim['padding']}px;overflow:hidden;{dim['leftBorder']}">
      <div id="dv" style="position:absolute;right:0;top:10%;bottom:10%;width:2px;
        background:linear-gradient(180deg,transparent,{colors['primary']} 30%,{colors['primary']} 70%,transparent);
        transform:scaleY(0);transform-origin:top;"></div>
      <div id="lbl" style="font-size:14px;font-weight:700;letter-spacing:5px;text-transform:uppercase;
        color:{colors['primary']};margin-bottom:26px;opacity:0;">{scene.get('eyebrow','VẤN ĐỀ')}</div>
      {"".join(pains_html)}
    </div>
    <div style="position:relative;display:flex;flex-direction:column;justify-content:center;
      align-items:center;padding:{dim['padding']}px;">
      <div id="sr" style="text-align:center;opacity:0;display:flex;flex-direction:column;align-items:center;gap:16px;">
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:{dim['statValSize']}px;
          font-weight:900;text-transform:uppercase;letter-spacing:-1px;
          background:linear-gradient(135deg,#fff,{colors['primary']});
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1.15;padding-top:8px;">
          {scene.get('headline','70%')}</div>
        <div style="font-size:21px;color:rgba(200,200,220,0.75);line-height:1.5;max-width:560px;text-align:center;">
          {scene.get('subtitle','')}</div>
      </div>
    </div>
  </div>"""
        js = f"""
  tl.to('#dv',{{scaleY:1,duration:0.6,ease:'expo.out'}},0.1);
  {anim_enter('fadeUp','#lbl',0.05)}
  {"".join(pains_js)}
  tl.to('.icon-dynamic', {{scale:1.08, rotation:5, filter:'drop-shadow(0 0 25px {colors["primary_alpha"]})', duration:2, yoyo:true, repeat:30, ease:'sine.inOut'}}, 0.5);
  tl.fromTo('#sr',{{opacity:0,scale:0.85}},{{opacity:1,scale:1,duration:0.6,ease:'back.out(1.2)'}},{pains_end});
  {anim_exit(exit_,"['[id^=\\'p\\']','#lbl','#sr','#dv']")}"""
    return html, js


def render_brand_reveal(scene, dim, colors, scene_idx=0):
    enter, exit_ = pick_anim("brand-reveal", scene_idx, scene)
    html = f"""
  <div id="brandBox" style="position:absolute;left:50%;top:45%;
    transform:translate(-50%,-50%) scale(0.8);opacity:0;
    display:flex;flex-direction:column;align-items:center;gap:26px;">
    <div style="width:130px;height:130px;border-radius:34px;
      background:linear-gradient(135deg,{colors['primary']},{colors['accent']});
      display:flex;align-items:center;justify-content:center;font-size:66px;
      box-shadow:0 0 60px {colors['primary_alpha']};border:1px solid rgba(255,255,255,0.25);">🏫</div>
    <div style="font-family:'Barlow Condensed',sans-serif;font-size:{dim['titleSize']}px;font-weight:900;
      letter-spacing:-2px;text-transform:uppercase;color:#fff;
      text-shadow:0 0 30px {colors['primary_alpha']};line-height:1.15;padding-top:10px;text-align:center;">
      {scene.get('headline','RIKKEI')}</div>
    <div id="brandSub" style="font-size:{dim['subtitleSize']}px;font-weight:500;
      color:rgba(200,200,220,0.8);opacity:0;transform:translateY(20px);text-align:center;">
      {scene.get('subtitle','')}</div>
  </div>"""
    js = f"""
  {anim_enter(enter,'#brandBox',0.1)}
  {anim_enter('fadeUp','#brandSub',0.6)}
  {anim_exit(exit_,'#brandBox')}"""
    return html, js


def render_stats(scene, dim, colors, scene_idx=0):
    enter, exit_ = pick_anim("stats", scene_idx, scene)
    is_vertical = dim['scaleFactor'] < 0.8

    # Extract real stat value from elements
    stat_val = 78
    stat_label = "Tiến độ"
    for elem in scene.get("elements", []):
        parts = elem.split("|")
        if len(parts) >= 2 and "%" in parts[1]:
            try:
                stat_val = int(parts[1].replace("%","").strip())
                stat_label = parts[0].strip()
                break
            except: pass

    title_size = min(dim['titleSize'], 52) if is_vertical else dim['titleSize']
    html = f"""
  <div class="eyebrow-tag" id="eyebrow">{scene.get('eyebrow','⚡ TIẾN TRÌNH')}</div>
  <div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    width:85%;display:flex;flex-direction:column;gap:26px;align-items:center;">
    <div id="sTitle" style="font-family:'Barlow Condensed',sans-serif;font-size:{title_size}px;
      font-weight:900;text-transform:uppercase;letter-spacing:-1px;color:#fff;
      opacity:0;text-align:center;line-height:1.05;">
      {scene.get('headline','TIẾN TRÌNH HỌC TẬP')}</div>
    <div id="sBar" class="glass-card" style="width:100%;padding:26px;opacity:0;
      transform:translateY(26px);display:flex;flex-direction:column;gap:16px;">
      <div style="display:flex;justify-content:space-between;align-items:center;
        font-size:{int(dim['subtitleSize']*0.9)}px;font-weight:700;color:rgba(255,255,255,0.8);">
        <span>{stat_label}</span>
        <span id="counter" style="font-family:'Barlow Condensed',sans-serif;
          font-size:{int(dim['statValSize']*0.62)}px;color:{colors['primary']};font-weight:900;">0%</span>
      </div>
      <div style="width:100%;height:15px;background:rgba(255,255,255,0.06);border-radius:8px;overflow:hidden;position:relative;">
        <div id="fill" style="position:absolute;left:0;top:0;bottom:0;width:0%;
          background:linear-gradient(90deg,{colors['primary']},{colors['accent']});border-radius:8px;"></div>
      </div>
    </div>
    <div id="sDesc" style="font-size:{dim['subtitleSize']}px;color:rgba(200,200,220,0.7);
      opacity:0;text-align:center;max-width:480px;line-height:1.4;">
      {scene.get('subtitle','')}</div>
  </div>"""
    js = f"""
  {anim_enter('fadeUp','#eyebrow',0.1)}
  {anim_enter(enter,'#sTitle',0.2)}
  tl.to('#sBar',{{opacity:1,y:0,duration:0.6,ease:'power3.out'}},0.4);
  {anim_enter('fadeUp','#sDesc',0.7)}
  var po={{v:0}};
  tl.to(po,{{v:{stat_val},duration:1.5,ease:'power2.out',onUpdate:function(){{
    document.getElementById('counter').innerText=Math.round(po.v)+'%';
    document.getElementById('fill').style.width=po.v+'%';
  }}}},0.5);
  {anim_exit(exit_,"['#eyebrow','#sTitle','#sBar','#sDesc']")}"""
    return html, js


def render_learning_path(scene, dim, colors, scene_idx=0):
    steps = scene.get("elements", [])
    enter, exit_ = pick_anim("learning-path", scene_idx, scene)
    is_vertical = dim['scaleFactor'] < 0.8

    steps_html = []
    steps_js = []
    for idx, s in enumerate(steps[:4]):
        parts = s.split("|")
        s_title = parts[0].strip()
        status = parts[1].strip().lower() if len(parts) > 1 else ""
        is_locked = "khóa" in status or "lock" in status
        icon = parts[2].strip() if len(parts) > 2 else ("🔒" if is_locked else "✅")
        
        if icon.startswith("fa-"):
            icon = f'<i class="{icon}"></i>'
            
        icon_color = "#9ca3af" if is_locked else "#34d399"
        bg_color = "rgba(156,163,175,0.2)" if is_locked else "rgba(52,211,153,0.2)"
        card_id = f"lc_{idx}"

        if is_vertical:
            steps_html.append(f"""
      <div class="glass-card" id="{card_id}" style="position:relative; width:100%;padding:18px 22px;
        display:flex;flex-direction:row;align-items:center;gap:14px;
        opacity:0;transform:scale(0.85) translateY(20px);margin-bottom:12px;">
        <div id="dot_{idx}" style="position:absolute; left:-35px; top:50%; transform:translateY(-50%) scale(0); width:16px; height:16px; border-radius:50%; background:{colors['primary']}; box-shadow:0 0 10px {colors['primary']};"></div>
        <div id="icon_{idx}" class="icon-dynamic" style="font-size:24px;line-height:1;color:{icon_color};
          width:48px;height:48px;border-radius:50%;background:{bg_color};border:1px solid {icon_color};
          display:flex;align-items:center;justify-content:center;flex-shrink:0;">{icon}</div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:{int(dim['titleSize']*0.52)}px;
          font-weight:900;text-transform:uppercase;color:#fff;">{s_title}</div>
      </div>""")
            steps_js.append(f"  tl.to('#{card_id}',{{opacity:1,y:0,scale:1,duration:0.6,ease:'back.out(1.2)'}},{0.15+idx*0.1});\n")
            steps_js.append(f"  tl.to('#dot_{idx}',{{scale:1,duration:0.4,ease:'back.out(2)'}},{0.2+idx*0.1});\n")
        else:
            steps_html.append(f"""
      <div class="glass-card" id="{card_id}" style="width:275px;padding:26px;
        display:flex;flex-direction:column;align-items:center;text-align:center;
        gap:13px;opacity:0;transform:scale(0.85) translateY(20px);">
        <div id="icon_{idx}" class="icon-dynamic" style="font-size:30px;line-height:1;color:{icon_color};
          width:60px;height:60px;border-radius:50%;background:{bg_color};border:1px solid {icon_color};
          display:flex;align-items:center;justify-content:center;flex-shrink:0;">{icon}</div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:21px;
          font-weight:900;text-transform:uppercase;color:#fff;">{s_title}</div>
      </div>""")
            steps_js.append(f"  tl.to('#{card_id}',{{opacity:1,y:0,scale:1,duration:0.6,ease:'back.out(1.2)'}},{0.15+idx*0.1});\n")

        if is_locked:
            steps_js.append(f"""
  tl.to('#icon_{idx}',{{scale:1.2,rotation:10,duration:0.25,ease:'power2.out',
    onStart:function(){{document.getElementById('icon_{idx}').innerText='🔓';}}}},{0.8+idx*0.1});
  tl.to('#icon_{idx}',{{scale:1,rotation:0,duration:0.25,ease:'back.out(1.2)'}},{1.05+idx*0.1});\n""")

    title_size = min(dim['titleSize'], 52) if is_vertical else dim['titleSize']
    timeline_css = "border-left: 2px dashed rgba(255,255,255,0.2); padding-left: 26px; margin-left: 14px; width: calc(100% - 14px);" if is_vertical else "width:100%;"
    cards_layout = "flex-direction:column;" if is_vertical else "flex-direction:row;gap:18px;justify-content:center;"

    html = f"""
  <div class="eyebrow-tag" id="eyebrow">{scene.get('eyebrow','⚡ LỘ TRÌNH')}</div>
  <div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    display:flex;flex-direction:column;align-items:center;gap:26px;width:90%;">
    <div id="lpTitle" style="font-family:'Barlow Condensed',sans-serif;font-size:{title_size}px;
      font-weight:900;text-transform:uppercase;color:#fff;opacity:0;text-align:center;line-height:1.05;">
      {scene.get('headline','MỞ KHÓA BÀI HỌC')}</div>
    <div style="display:flex;align-items:stretch;{cards_layout}{timeline_css}">
      {"".join(steps_html)}</div>
    <div id="lpDesc" style="font-size:{dim['subtitleSize']}px;color:rgba(200,200,220,0.75);
      opacity:0;text-align:center;max-width:460px;line-height:1.4;">
      {scene.get('subtitle','')}</div>
  </div>"""
    js = f"""
  {anim_enter('fadeUp','#eyebrow',0.05)}
  {anim_enter(enter,'#lpTitle',0.1)}
  {"".join(steps_js)}
  tl.to('.icon-dynamic', {{scale:1.08, filter:'drop-shadow(0 0 15px {colors["primary_alpha"]})', duration:2, yoyo:true, repeat:30, ease:'sine.inOut'}}, 0.5);
  {anim_enter('fadeUp','#lpDesc',0.6)}
  {anim_exit(exit_,"['#eyebrow','#lpTitle','[id^=\\'lc_\\']','#lpDesc']")}"""
    return html, js


def render_card_list(scene, dim, colors, scene_idx=0):
    cards = scene.get("elements", [])
    enter, exit_ = pick_anim("card-list", scene_idx, scene)
    is_vertical = dim['scaleFactor'] < 0.8
    ICONS = ["🚀","⚙️","📊","💡","🎯","🔧","📈","🤖"]

    cards_html = []
    cards_js = []
    for idx, c in enumerate(cards[:3]):
        parts = c.split("|")
        c_title = parts[0].strip()
        c_desc = parts[1].strip() if len(parts) > 1 else ""
        icon = parts[2].strip() if len(parts) > 2 else ICONS[idx % len(ICONS)]
        
        if icon.startswith("fa-"):
            icon = f'<i class="{icon}"></i>'
            
        cid = f"cl_{idx}"

        if is_vertical:
            cards_html.append(f"""
      <div class="glass-card" id="{cid}" style="width:100%;padding:16px 20px;
        display:flex;flex-direction:row;align-items:flex-start;gap:12px;
        opacity:0;transform:translateX(30px);margin-bottom:12px;">
        <div style="font-size:32px;line-height:1;flex-shrink:0;
          filter:drop-shadow(0 0 10px {colors['primary_alpha']});">{icon}</div>
        <div>
          <div style="font-family:'Barlow Condensed',sans-serif;font-size:{int(dim['titleSize']*0.5)}px;
            font-weight:900;text-transform:uppercase;color:#fff;line-height:1.1;">{c_title}</div>
          <div style="font-size:{dim['subtitleSize']-3}px;color:rgba(200,200,220,0.65);line-height:1.4;margin-top:3px;">{c_desc}</div>
        </div>
      </div>""")
            cards_js.append(f"  tl.to('#{cid}',{{opacity:1,x:0,duration:0.6,ease:'expo.out'}},{0.15+idx*0.1});\n")
        else:
            cards_html.append(f"""
      <div class="glass-card" id="{cid}" style="width:310px;padding:30px 22px;
        display:flex;flex-direction:column;align-items:center;text-align:center;
        gap:15px;opacity:0;transform:translateY(25px);">
        <div style="font-size:44px;line-height:1;filter:drop-shadow(0 0 14px {colors['primary_alpha']});">{icon}</div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:24px;
          font-weight:900;text-transform:uppercase;color:#fff;line-height:1.2;">{c_title}</div>
        <div style="font-size:14px;color:rgba(200,200,220,0.65);line-height:1.45;">{c_desc}</div>
      </div>""")
            cards_js.append(f"  tl.to('#{cid}',{{opacity:1,y:0,duration:0.6,ease:'back.out(1.3)'}},{0.15+idx*0.1});\n")

    cards_layout = "flex-direction:column;" if is_vertical else "justify-content:center;gap:30px;"
    title_size = min(dim['titleSize'], 52) if is_vertical else dim['titleSize']

    html = f"""
  <div class="eyebrow-tag" id="eyebrow">{scene.get('eyebrow','⚡ TÀI NGUYÊN')}</div>
  <div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    display:flex;flex-direction:column;align-items:center;gap:26px;width:92%;">
    <div id="clTitle" style="font-family:'Barlow Condensed',sans-serif;font-size:{title_size}px;
      font-weight:900;text-transform:uppercase;color:#fff;opacity:0;text-align:center;line-height:1.05;">
      {scene.get('headline','ĐA DẠNG HỌC LIỆU')}</div>
    <div style="display:flex;align-items:stretch;{cards_layout}width:100%;">
      {"".join(cards_html)}</div>
  </div>"""
    js = f"""
  {anim_enter('fadeUp','#eyebrow',0.05)}
  {anim_enter(enter,'#clTitle',0.15)}
  {"".join(cards_js)}
  {anim_exit(exit_,"['#eyebrow','#clTitle','[id^=\\'cl_\\']']")}"""
    return html, js


def render_admin_report(scene, dim, colors, scene_idx=0):
    bars = scene.get("elements", [])
    enter, exit_ = pick_anim("admin-report", scene_idx, scene)
    bars_html = []
    bars_js = []
    for idx, b in enumerate(bars[:4]):
        parts = b.split("|")
        label = parts[0].strip()
        val = int(parts[1].replace("%","").strip()) if len(parts) > 1 else 70
        bid, fid = f"b_{idx}", f"bf_{idx}"
        bars_html.append(f"""
      <div style="display:flex;flex-direction:column;gap:6px;width:100%;opacity:0;transform:translateY(16px);" id="{bid}">
        <div style="display:flex;justify-content:space-between;font-size:{dim['subtitleSize']-2}px;
          font-weight:700;color:rgba(255,255,255,0.85);">
          <span>{label}</span><span style="color:{colors['primary']};">{val}%</span>
        </div>
        <div style="width:100%;height:12px;background:rgba(255,255,255,0.05);border-radius:6px;overflow:hidden;position:relative;">
          <div id="{fid}" style="position:absolute;left:0;top:0;bottom:0;width:0%;
            background:linear-gradient(90deg,{colors['primary']},{colors['accent']});border-radius:6px;"></div>
        </div>
      </div>""")
        bars_js.append(f"  tl.to('#{bid}',{{opacity:1,y:0,duration:0.4}},{0.8+idx*0.18});")
        bars_js.append(f"  tl.to('#{fid}',{{width:'{val}%',duration:1.2,ease:'power2.out'}},{1.0+idx*0.18});")

    html = f"""
  <div class="eyebrow-tag" id="eyebrow">{scene.get('eyebrow','⚡ BÁO CÁO')}</div>
  <div style="position:absolute;inset:0;display:grid;grid-template-columns:{dim['gridColumns']};
    padding:{dim['padding']}px;gap:38px;align-items:center;">
    <div id="arText" style="display:flex;flex-direction:column;gap:14px;opacity:0;">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:{dim['titleSize']}px;
        font-weight:900;text-transform:uppercase;color:#fff;line-height:1.0;">
        {scene.get('headline','QUẢN LÝ DỄ DÀNG')}</div>
      <div style="font-size:{dim['subtitleSize']}px;color:rgba(200,200,220,0.7);line-height:1.5;">
        {scene.get('subtitle','')}</div>
    </div>
    <div id="arChart" class="glass-card" style="padding:32px;display:flex;flex-direction:column;
      gap:20px;opacity:0;transform:scale(0.9);">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:{int(dim['subtitleSize']*1.15)}px;
        font-weight:900;text-transform:uppercase;color:#fff;
        border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:10px;">
        📊 Báo Cáo Hiệu Suất</div>
      {"".join(bars_html)}
    </div>
  </div>"""
    js = f"""
  {anim_enter('fadeUp','#eyebrow',0.3)}
  {anim_enter(enter,'#arText',0.5)}
  tl.to('#arChart',{{opacity:1,scale:1.0,duration:0.7,ease:'back.out(1.4)'}},0.65);
  {"".join(bars_js)}
  {anim_exit(exit_,"['#eyebrow','#arText','#arChart']")}"""
    return html, js


def render_cta(scene, dim, colors, scene_idx=0):
    metrics = scene.get("elements", [])
    enter, exit_ = pick_anim("cta", scene_idx, scene)
    is_vertical = dim['scaleFactor'] < 0.8

    metrics_html = []
    metrics_js = []
    for idx, m in enumerate(metrics[:3]):
        parts = m.split("|")
        number = parts[0].strip()
        lbl = parts[1].strip() if len(parts) > 1 else ""
        mid = f"m_{idx}"
        size = dim['statValSize'] if not is_vertical else int(dim['statValSize']*0.88)
        metrics_html.append(f"""
      <div id="{mid}" style="display:flex;flex-direction:column;align-items:center;
        text-align:center;opacity:0;transform:translateY(26px);{'width:100%;' if is_vertical else 'min-width:110px;'}">
        <span style="font-family:'Barlow Condensed',sans-serif;font-size:{size}px;
          font-weight:900;color:{colors['primary']};text-shadow:0 0 25px {colors['primary_alpha']};line-height:1;">
          {number}</span>
        <span style="font-size:{dim['subtitleSize']-2}px;color:rgba(200,200,220,0.7);
          font-weight:600;margin-top:4px;line-height:1.2;">{lbl}</span>
      </div>""")
        metrics_js.append(f"  tl.to('#{mid}',{{opacity:1,y:0,duration:0.5,ease:'back.out(1.3)'}},{0.9+idx*0.2});")

    title_size = min(int(dim['titleSize']*0.88), 62) if is_vertical else int(dim['titleSize']*0.88)
    m_layout = "flex-direction:column;gap:18px;" if is_vertical else "gap:36px;"

    html = f"""
  <div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    display:flex;flex-direction:column;align-items:center;gap:28px;width:92%;">
    <div id="ctaHeader" style="text-align:center;display:flex;flex-direction:column;
      gap:11px;opacity:0;transform:translateY(-22px);">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:{title_size}px;
        font-weight:900;text-transform:uppercase;color:#fff;letter-spacing:-1px;line-height:0.95;">
        {scene.get('headline','AI-NATIVE DATA ENGINEER')}</div>
      <div style="font-size:{dim['subtitleSize']}px;color:rgba(200,200,220,0.85);font-weight:500;">
        {scene.get('subtitle','')}</div>
    </div>
    <div style="display:flex;align-items:center;justify-content:center;{m_layout}
      border-top:1px solid rgba(255,255,255,0.07);border-bottom:1px solid rgba(255,255,255,0.07);
      padding:20px 0;width:100%;">
      {"".join(metrics_html)}</div>
    <div id="ctaBtn" style="opacity:0;transform:scale(0.85);display:flex;flex-direction:column;align-items:center;gap:9px;">
      <div style="font-family:'Be Vietnam Pro',sans-serif;font-weight:700;
        font-size:{int(dim['subtitleSize']*1.08)}px;color:#fff;
        background:linear-gradient(135deg,{colors['primary']},{colors['accent']});
        padding:14px 38px;border-radius:50px;
        box-shadow:0 14px 38px {colors['primary_alpha']};border:1px solid rgba(255,255,255,0.15);">
        Theo Dõi Ngay ⬇️</div>
      <span style="font-size:12px;color:rgba(200,200,220,0.5);letter-spacing:1px;">rikkei.edu.vn</span>
    </div>
  </div>"""
    js = f"""
  {anim_enter(enter,'#ctaHeader',0.35)}
  {"".join(metrics_js)}
  tl.to('#ctaBtn',{{opacity:1,scale:1.0,duration:0.7,ease:'back.out(1.4)'}},1.52);
  tl.to('#ctaBtn',{{y:-5,duration:0.65,yoyo:true,repeat:-1,ease:'sine.inOut'}},2.2);
  {anim_exit(exit_,"['#ctaHeader','[id^=\\'m_\\']','#ctaBtn']")}"""
    return html, js


# ── Audio Generation ──────────────────────────────────────────────────────────
import re

def parse_bilingual_segments(text):
    pattern = r"\{en:([^\}]+)\}"
    parts = re.split(pattern, text)
    segments = []
    is_english = False
    for p in parts:
        if p and any(c.isalnum() for c in p):
            segments.append({"text": p.strip(), "lang": "en" if is_english else "vi"})
        is_english = not is_english
    return segments

def trim_wav_silence(wav_path):
    import wave, numpy as np
    try:
        with wave.open(str(wav_path), 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            data = wf.readframes(n_frames)
            sig = np.frombuffer(data, dtype=np.int16 if sampwidth==2 else np.uint8)
            if sampwidth not in (1,2): return
        abs_sig = np.abs(sig)
        block_size = int(framerate * 0.02) * n_channels
        n_blocks = len(abs_sig) // block_size
        max_amp = np.max(abs_sig)
        if max_amp == 0: return
        threshold = max_amp * 0.015
        last_active = 0
        for i in range(n_blocks-1, -1, -1):
            block = abs_sig[i*block_size:(i+1)*block_size]
            if np.max(block) > threshold:
                last_active = min((i+5)*block_size, len(sig)); break
        if last_active == 0 or last_active >= len(sig): return
        trimmed = sig[:last_active].tobytes()
        with wave.open(str(wav_path), 'wb') as out:
            out.setnchannels(n_channels); out.setsampwidth(sampwidth)
            out.setframerate(framerate); out.writeframes(trimmed)
        print(f"      [Audio] Trimmed {(n_frames - last_active//n_channels)/framerate:.2f}s silence from {wav_path.name}")
    except Exception as e:
        print(f"      [Warning] trim_wav_silence: {e}")


# ── VoiceCloner Singleton ─────────────────────────────────────────────────────
class VoiceCloner:
    _instances = {}

    def __init__(self, vieneu_src):
        self.vieneu_src = vieneu_src
        self.client = None
        self._ref_cache = {}

    @classmethod
    def get(cls, vieneu_src):
        if vieneu_src not in cls._instances:
            inst = cls(vieneu_src)
            inst._init_client()
            cls._instances[vieneu_src] = inst
        return cls._instances[vieneu_src]

    def _init_client(self):
        if self.vieneu_src not in sys.path:
            sys.path.insert(0, self.vieneu_src)
        from vieneu import Vieneu
        print(f"    [VoiceCloner] Initializing from {self.vieneu_src}...")
        self.client = Vieneu(mode="v3turbo")
        print("    [VoiceCloner] Model ready.")

    def encode_reference(self, ref_audio_path):
        sha1 = hashlib.sha1(Path(ref_audio_path).read_bytes()).hexdigest()[:16]
        if sha1 not in self._ref_cache:
            print(f"    [VoiceCloner] Encoding reference (SHA1={sha1})...")
            self._ref_cache[sha1] = self.client.encode_reference(ref_audio_path)
            print("    [VoiceCloner] Reference cached.")
        else:
            print(f"    [VoiceCloner] Using cached reference (SHA1={sha1}).")
        return self._ref_cache[sha1]

    def infer(self, text, ref_codes, temperature=0.3):
        return self.client.infer(text, ref_codes=ref_codes, temperature=temperature)

    def save(self, audio, path):
        self.client.save(audio, path)


# ── BGMMixer ──────────────────────────────────────────────────────────────────
class BGMMixer:
    @staticmethod
    def mix_narration_tracks(scene_audios, timing_data, aspect, project_path):
        mixed_path = project_path / "narration_mixed.mp3"
        inputs, filter_parts = [], []
        for idx, t in enumerate(timing_data):
            delay_ms = t["start_ms"]
            inputs += ["-i", str(scene_audios[idx]["path"])]
            filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[a{idx}]")
        mix_inputs = "".join(f"[a{i}]" for i in range(len(timing_data)))
        lufs = -15 if aspect == "16:9" else -11
        tp = -1.0 if aspect == "16:9" else -1.5
        filter_c = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={len(timing_data)}:duration=longest,loudnorm=I={lufs}:TP={tp}:LRA=11[aout]"
        cmd = [FFMPEG_PATH, "-y"] + inputs + ["-filter_complex", filter_c, "-map", "[aout]", "-ar", "44100", "-ac", "2", str(mixed_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"      Mixed narration generated: {mixed_path.name}")
        return mixed_path

    @staticmethod
    def register_assets(proj, assets_dir, narration_path, bgm_source_path=None):
        with open(narration_path, "rb") as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()
        asset_dest = assets_dir / f"{sha1}.mp3"
        shutil.copy2(narration_path, asset_dest)
        proj["assets"].append({
            "id": sha1, "type": "audio",
            "path": str(asset_dest).replace("\\", "/"),
            "metadata": {"filename": "narration.mp3", "mimeType": "audio/mpeg", "sizeBytes": asset_dest.stat().st_size},
            "userTags": ["narration"]
        })
        print(f"      Saved narration asset: {asset_dest.name}")

        bgm_sha1 = None
        if bgm_source_path and Path(bgm_source_path).exists():
            bgm_src = Path(bgm_source_path)
            bgm_sha1 = hashlib.sha1(bgm_src.read_bytes()).hexdigest()
            bgm_dest = assets_dir / f"{bgm_sha1}.mp3"
            shutil.copy2(bgm_src, bgm_dest)
            proj["assets"].append({
                "id": bgm_sha1, "type": "audio",
                "path": str(bgm_dest).replace("\\", "/"),
                "metadata": {"filename": bgm_src.name, "mimeType": "audio/mpeg", "sizeBytes": bgm_dest.stat().st_size},
                "userTags": ["bgm"]
            })
            print(f"      Registered BGM: {bgm_src.name}")

        proj["soundtrack"] = {
            "narrationAssetId": sha1, "musicAssetId": bgm_sha1,
            "narrationVolumeDb": 0, "musicVolumeDb": -22
        }
        return sha1, bgm_sha1


async def generate_scene_audio(scene, temp_dir, voice="vi-VN-NamMinhNeural",
                                voice_cloner=None, vieneu_ref_codes=None):
    output_path = temp_dir / f"{scene['id']}.mp3"
    text = scene.get("voiceover", "")

    if voice_cloner is not None and vieneu_ref_codes is not None:
        cleaned = re.sub(r"\{en:([^\}]+)\}", r"\1", text)
        wav_path = temp_dir / f"{scene['id']}.wav"
        for attempt in range(1, 4):
            print(f"      VieNeu-TTS attempt {attempt}/3: \"{cleaned[:40]}...\"")
            try:
                loop = asyncio.get_event_loop()
                audio = await loop.run_in_executor(None, lambda: voice_cloner.infer(cleaned, vieneu_ref_codes))
                voice_cloner.save(audio, str(wav_path))
                if wav_path.exists() and wav_path.stat().st_size > 0: break
            except Exception as e:
                print(f"        Attempt {attempt} failed: {e}")
            await asyncio.sleep(1.5)
        else:
            raise Exception(f"Failed VieNeu-TTS for {scene['id']}")

        trim_wav_silence(wav_path)
        cmd = [FFMPEG_PATH, "-y", "-i", str(wav_path), "-filter:a", "atempo=1.25",
               "-c:a", "libmp3lame", "-b:a", "192k", str(output_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: raise Exception(f"FFmpeg WAV→MP3 failed: {res.stderr}")
        try: wav_path.unlink()
        except: pass
        return output_path

    # Edge-TTS fallback
    segments = parse_bilingual_segments(text)
    if not segments: raise Exception(f"No content in {scene['id']}: {text}")
    is_female = "hoaimy" in voice.lower()
    voice_en = "en-US-EmmaNeural" if is_female else "en-US-AndrewNeural"
    segment_paths = []
    for idx, seg in enumerate(segments):
        seg_voice = voice_en if seg["lang"] == "en" else voice
        seg_rate = "-5%" if seg["lang"] == "en" else "-10%"
        seg_file = temp_dir / f"{scene['id']}_seg_{idx}.mp3"
        for attempt in range(1, 6):
            print(f"      TTS Seg {idx} ({seg['lang']}) attempt {attempt}: \"{seg['text'][:35]}...\"")
            try:
                await edge_tts.Communicate(seg["text"], seg_voice, rate=seg_rate).save(str(seg_file))
                if seg_file.exists() and seg_file.stat().st_size > 0: break
            except Exception as e:
                print(f"        Attempt {attempt} failed: {e}")
            await asyncio.sleep(1.5)
        else:
            raise Exception(f"Failed TTS seg {idx} of {scene['id']}")
        segment_paths.append(seg_file)

    if len(segment_paths) == 1:
        shutil.copy2(segment_paths[0], output_path)
    else:
        inputs, filter_inputs = [], []
        for idx, path in enumerate(segment_paths):
            inputs += ["-i", str(path)]
            filter_inputs.append(f"[{idx}:a]")
        filter_c = f"{''.join(filter_inputs)}concat=n={len(segment_paths)}:v=0:a=1[aout]"
        cmd = [FFMPEG_PATH, "-y"] + inputs + ["-filter_complex", filter_c, "-map", "[aout]",
                                              "-c:a", "libmp3lame", "-b:a", "192k", str(output_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: raise Exception(f"FFmpeg segment concat failed: {res.stderr}")

    for p in segment_paths:
        try: p.unlink()
        except: pass
    return output_path


def get_audio_duration(path):
    cmd = [FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return float(res.stdout.decode('utf-8').strip())


def write_scene_html(project_path, scene, scene_idx, pid_hash, dim, base_colors, duration_sec):
    layout = scene.get("layout", "hook")
    comp_id = scene["id"]
    
    colors = base_colors.copy()
    if "theme" in scene:
        if isinstance(scene["theme"], dict):
            colors.update(scene["theme"])
        elif isinstance(scene["theme"], str) and scene["theme"] in THEME_COLORS:
            colors = THEME_COLORS[scene["theme"]]

    bg_variant_idx = (pid_hash + scene_idx) % len(BG_VARIANTS)
    bgv = BG_VARIANTS[bg_variant_idx]
    bg_css = build_bg_css(bgv, colors)
    bg_origin = bgv["bg_origin"]

    mascot_beh = MASCOT_BEHAVIORS.get(layout, MASCOT_BEHAVIORS["default"])

    if layout == "hook": layout_html, layout_js = render_hook(scene, dim, colors, scene_idx)
    elif layout == "reveal": layout_html, layout_js = render_reveal(scene, dim, colors, scene_idx)
    elif layout == "brand-reveal": layout_html, layout_js = render_brand_reveal(scene, dim, colors, scene_idx)
    elif layout == "stats": layout_html, layout_js = render_stats(scene, dim, colors, scene_idx)
    elif layout == "learning-path": layout_html, layout_js = render_learning_path(scene, dim, colors, scene_idx)
    elif layout == "card-list": layout_html, layout_js = render_card_list(scene, dim, colors, scene_idx)
    elif layout == "admin-report": layout_html, layout_js = render_admin_report(scene, dim, colors, scene_idx)
    elif layout == "cta": layout_html, layout_js = render_cta(scene, dim, colors, scene_idx)
    else: layout_html, layout_js = render_hook(scene, dim, colors, scene_idx)

    # Subtitles (Chạy chữ)
    caption_text = scene.get("caption", scene.get("subtitle", scene.get("voiceover", "")))
    words = [w.strip() for w in caption_text.split() if w.strip()]
    captions_html = ""
    captions_js = ""
    if words:
        captions_html += f'<div class="captions-container" style="position:absolute;bottom:{int(dim["height"]*0.14)}px;left:50%;transform:translateX(-50%);width:90%;text-align:center;font-size:{dim["subtitleSize"]+4}px;font-weight:700;line-height:1.4;z-index:20;">\n'
        for i, w in enumerate(words):
            captions_html += f'<span class="cap-word" id="cw_{i}" style="opacity:0.4;display:inline-block;margin:0 5px;color:#fff;transition:none;">{w}</span>\n'
        captions_html += '</div>\n'
        
        stagger_time = max(0.08, (duration_sec - 1.0) / len(words)) if len(words) > 0 else 0.1
        captions_js += f"  tl.to('.cap-word', {{opacity:1, color:'{colors['primary']}', textShadow:'0 0 15px {colors['primary_alpha']}', duration:0.15, yoyo:true, repeat:1, stagger:{stagger_time}}}, 0.1);\n"

    html_content = HTML_BOILERPLATE \
        .replace("{{width}}", str(dim["width"])) \
        .replace("{{height}}", str(dim["height"])) \
        .replace("{{bg_origin}}", bg_origin) \
        .replace("{{bg_radial1}}", colors["bg_radial1"]) \
        .replace("{{bg_radial2}}", colors["bg_radial2"]) \
        .replace("{{bg_css}}", bg_css) \
        .replace("{{primary}}", colors["primary"]) \
        .replace("{{primary_alpha}}", colors["primary_alpha"]) \
        .replace("{{accent}}", colors["accent"]) \
        .replace("{{eyebrowTop}}", str(dim["eyebrowTop"])) \
        .replace("{{comp_id}}", comp_id) \
        .replace("{{layout_html}}", layout_html) \
        .replace("{{layout_js}}", layout_js) \
        .replace("{{captions_html}}", captions_html) \
        .replace("{{captions_js}}", captions_js) \
        .replace("{{mascot_start_css}}", mascot_beh["start_css"]) \
        .replace("{{mascot_js}}", mascot_beh["js"]) \
        .replace("{{slot}}", f"{duration_sec:.2f}")

    out_dir = project_path / "compositions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{comp_id}.html"
    out_file.write_text(html_content, encoding="utf-8")
    return out_file


def update_preview_html(project_path, timing_data, total_duration, dim):
    beat_layers = []
    for idx, t in enumerate(timing_data):
        beat_layers.append(
            f'      <!-- Beat {idx+1:02d} -- {t["id"]} ({t["start"]:.1f}s - {t["start"]+t["duration"]:.1f}s) -->\n'
            f'      <div class="beat-layer"\n'
            f'        data-composition-id="{t["id"]}"\n'
            f'        data-composition-src="compositions/{t["id"]}.html"\n'
            f'        data-start="{t["start"]:.1f}" data-duration="{t["duration"]:.1f}" data-track-index="0"\n'
            f'        data-width="{dim["width"]}" data-height="{dim["height"]}"></div>'
        )
    html = f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width={dim['width']}, height={dim['height']}"/>
    <title>Preview Timeline</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      *{{margin:0;padding:0;box-sizing:border-box;}}
      html,body{{margin:0;width:{dim['width']}px;height:{dim['height']}px;overflow:hidden;background:#000;color:#fff;}}
      .beat-layer{{position:absolute;top:0;left:0;width:{dim['width']}px;height:{dim['height']}px;}}
    </style>
  </head>
  <body>
    <div id="root"
      data-composition-id="linear-promo-main"
      data-start="0"
      data-duration="{total_duration:.1f}"
      data-width="{dim['width']}"
      data-height="{dim['height']}">
{chr(10).join(beat_layers)}
    </div>
    <script>
      window.__timelines=window.__timelines||{{}};
      const tl=gsap.timeline({{paused:true}});
      tl.to({{}},{{duration:{int(total_duration)}}},0);
      window.__timelines["linear-promo-main"]=tl;
    </script>
  </body>
</html>"""
    preview_file = project_path / "preview.html"
    preview_file.write_text(html, encoding="utf-8")
    return preview_file


async def build_project(script, voice_cloner_cache=None):
    pid = script["projectId"]
    pname = script.get("projectName", "Untitled Video")
    aspect = script.get("aspectRatio", "16:9")
    theme_name = script.get("theme", "Solution/Brand")
    gender = script.get("voiceGender", "MALE")

    out_mp4 = EXPORTS_DIR / f"{pid}.mp4"
    if out_mp4.exists():
        print(f"\n✅ ALREADY RENDERED: {pname} ({pid}) — Skipping.")
        return out_mp4

    print(f"\n🚀 BUILDING PROJECT: {pname} ({pid})")

    dim = ASPECT_RATIOS.get(aspect, ASPECT_RATIOS["16:9"])
    theme_input = script.get("theme", "Solution/Brand")
    if isinstance(theme_input, dict):
        colors = THEME_COLORS["Solution/Brand"].copy()
        colors.update(theme_input)
    else:
        colors = THEME_COLORS.get(theme_input, THEME_COLORS["Solution/Brand"])
        
    voice = "vi-VN-NamMinhNeural" if gender == "MALE" else "vi-VN-HoaiMyNeural"

    # VoiceCloner (singleton, reused across projects)
    voice_cloner = None
    vieneu_ref_codes = None
    ref_audio_path = script.get("ref_audio")
    if ref_audio_path and Path(ref_audio_path).exists():
        local_vieneu = WORKSPACE_ROOT / "vieneu" / "src"
        vieneu_src = str(local_vieneu) if local_vieneu.exists() else "d:/AI/Rikkei_Edu_agent/VieNeu-TTS/src"
        try:
            voice_cloner = VoiceCloner.get(vieneu_src)
            if voice_cloner_cache is not None:
                voice_cloner_cache[vieneu_src] = voice_cloner
            vieneu_ref_codes = voice_cloner.encode_reference(str(ref_audio_path))
        except Exception as e:
            print(f"    [Warning] VoiceCloner failed, falling back to Edge-TTS: {e}")
            voice_cloner = None

    project_path = PROJECTS_DIR / pid
    project_path.mkdir(parents=True, exist_ok=True)
    temp_dir = project_path / "audio_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Audio
    scene_audios = []
    for s in script["scenes"]:
        audio_path = await generate_scene_audio(s, temp_dir, voice, voice_cloner, vieneu_ref_codes)
        dur = get_audio_duration(audio_path)
        scene_audios.append({"scene": s, "path": audio_path, "duration": dur})
        print(f"      Duration of {s['id']}: {dur:.2f}s")

    # Phase 2: Timings + HTML Compositions
    BUFFER_SEC = 0.4
    cumulative = 0.0
    timing_data = []
    pid_hash = abs(hash(pid)) % len(BG_VARIANTS)

    for scene_order_idx, item in enumerate(scene_audios):
        s = item["scene"]
        frame_dur = round(item["duration"] + BUFFER_SEC, 1)
        start_ms = int(cumulative * 1000)
        html_file = write_scene_html(project_path, s, scene_order_idx, pid_hash, dim, colors, frame_dur)
        timing_data.append({
            "id": s["id"], "start": round(cumulative, 1), "start_ms": start_ms,
            "duration": frame_dur, "text": s.get("voiceover", ""), "htmlPath": str(html_file)
        })
        cumulative += frame_dur

    total_duration = round(cumulative, 1)
    print(f"    Total Video Duration: {total_duration}s")

    # Phase 3: Preview HTML
    update_preview_html(project_path, timing_data, total_duration, dim)

    # Phase 4: Mix narration
    print("    Mixing voice tracks with EBU R128 loudnorm filter...")
    mixed_path = BGMMixer.mix_narration_tracks(scene_audios, timing_data, aspect, project_path)

    # Phase 5: project.json
    assets_dir = project_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    bgm_source = script.get("backgroundMusic", DEFAULT_BGM)

    # Copy mascot
    mascot_source = WORKSPACE_ROOT / "shared_assets" / "mascot.png"
    if mascot_source.exists():
        shutil.copy2(mascot_source, assets_dir / "mascot.png")

    proj = {
        "id": pid, "name": pname, "assets": [],
        "templateId": "frame-product-promo-30s" if aspect == "16:9" else "frame-bold-signal",
        "variables": {},
        "preferences": {"resolution": {"width": dim["width"], "height": dim["height"]}, "fps": 30},
        "status": "draft",
        "createdAt": __import__("datetime").datetime.now(__import__("datetime").UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "updatedAt": __import__("datetime").datetime.now(__import__("datetime").UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    }

    narration_sha1, bgm_sha1 = BGMMixer.register_assets(proj, assets_dir, mixed_path, bgm_source)
    proj["soundtrack"]["narrationText"] = " ".join(t["text"] for t in timing_data)
    proj["frames"] = [
        {"graphNodeId": t["id"], "htmlPath": t["htmlPath"].replace("/", "\\"),
         "durationSec": t["duration"], "order": idx}
        for idx, t in enumerate(timing_data)
    ]

    with open(project_path / "project.json", "w", encoding="utf-8") as f:
        json.dump(proj, f, ensure_ascii=False, indent=2)
    print("      Successfully generated project.json!")

    try: shutil.rmtree(temp_dir)
    except Exception as e: print(f"      Warning cleaning temp: {e}")

    # Phase 6: Render MP4
    print("    Rendering project video using packages/cli...")
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    node_exe = shutil.which("node") or "node"
    cli_js = str(WORKSPACE_ROOT / "packages" / "cli" / "dist" / "bin.js")
    render_cmd = [node_exe, cli_js, "project-render", pid, "--output", str(out_mp4)]
    env = os.environ.copy()

    result = subprocess.run(render_cmd, env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"🎉 RENDER SUCCESS: {out_mp4}")
        try:
            shutil.rmtree(project_path)
            print(f"      Cleaned up project temp workspace: {project_path}")
        except Exception as e:
            print(f"      Warning cleaning project workspace: {e}")
    else:
        print(f"❌ RENDER ERROR on {pid}:")
        print(result.stderr)
    return out_mp4


async def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_video_builder.py <path_to_script_json>")
        return
    script_path = Path(sys.argv[1])
    if not script_path.exists():
        print(f"Script file not found: {script_path}"); return

    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    voice_cloner_cache = {}
    if isinstance(data, list):
        for script in data:
            await build_project(script, voice_cloner_cache)
    else:
        await build_project(data, voice_cloner_cache)


if __name__ == "__main__":
    asyncio.run(main())
