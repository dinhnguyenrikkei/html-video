#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rikkei Video Studio — Lightweight Local Server
Uses Python stdlib http.server (zero external deps for serving).
VieNeu-TTS loaded lazily only when TTS is requested.
"""
import os
import sys
import json
import shutil
import hashlib
import subprocess
import re
import uuid
import threading
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = BASE_DIR / "assets"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
FRAMES_DIR = BASE_DIR / "frames"
VIENEU_PATH = Path(os.path.dirname(BASE_DIR)) / "vieneu"

# ── Lazy-loaded globals ─────────────────────────────────────────────
_tts_engine = None
_tts_lock = threading.Lock()
_ref_codes_cache = {}

PORT = 3080

def resolve_local_path(url_path):
    if not url_path:
        return None
    url_str = str(url_path).replace('\\', '/')
    if url_str.startswith('/assets/'):
        return ASSETS_DIR / url_str.replace('/assets/', '')
    elif url_str.startswith('/uploads/'):
        return UPLOADS_DIR / url_str.replace('/uploads/', '')
    elif url_str.startswith('/.html-video/'):
        return Path("D:/AI_rikkei/html-video-main") / url_str.lstrip('/')
    p = Path(url_str)
    if p.is_absolute():
        return p
    return BASE_DIR / p

# ── Multi-project Management State ─────────────────────────────
PROJECTS_ROOT = Path("D:/AI_rikkei/html-video-main/.html-video/projects")

def get_project_file(project_id):
    return PROJECTS_ROOT / project_id / "project.json"

def load_and_sanitize_project(proj_id):
    proj_file = get_project_file(proj_id)
    if not proj_file.exists():
        return None
    with open(proj_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    modified = False
    if "id" not in data:
        data["id"] = proj_id
        modified = True
    if "templateId" not in data or not data["templateId"]:
        data["templateId"] = "hyperframes"
        modified = True
    if "preferences" not in data:
        data["preferences"] = {
            "resolution": data.get("resolution", {"width": 1080, "height": 1920}),
            "aspect": data.get("aspect", "9:16"),
            "fps": 60
        }
        modified = True
    elif "resolution" not in data["preferences"]:
        data["preferences"]["resolution"] = data.get("resolution", {"width": 1080, "height": 1920})
        modified = True
        
    if modified:
        proj_file.parent.mkdir(parents=True, exist_ok=True)
        with open(proj_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    return data

def run_pipeline_generation(proj_id, data):
    tts = get_tts()
    if tts is None:
        raise Exception("VieNeu-TTS not available. Vui lòng bấm Load TTS trước!")

    speed_factor = data.get('speed_factor', 1.12)
    temperature = data.get('temperature', 0.2)
    voice_ref_raw = data.get('voice_ref', '/assets/voice_preview.mp3')
    voice_ref = resolve_local_path(voice_ref_raw)

    scenes = data.get("scenes", [])
    if not scenes:
        raise Exception("Không tìm thấy phân cảnh nào trong dự án!")

    temp_id = f"pipeline_{uuid.uuid4().hex[:8]}"
    temp_dir = UPLOADS_DIR / temp_id
    temp_dir.mkdir(exist_ok=True)

    ref_codes = encode_ref_audio(voice_ref)

    print(f"  Running background generation for {len(scenes)} scenes in project {proj_id}...")
    accumulated_delay = 0.0
    tts_paths = []
    
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("id", f"s{idx}")
        scene["id"] = scene_id
        raw_wav = temp_dir / f"{scene_id}_raw.wav"
        fast_wav = temp_dir / f"{scene_id}.wav"
        
        audio = tts.infer(text=scene["tts_text"], ref_codes=ref_codes, temperature=temperature, max_chars=120)
        tts.save(audio, str(raw_wav))

        ffmpeg = find_ffmpeg()
        cmd = [ffmpeg, "-y", "-i", str(raw_wav), "-filter:a", f"atempo={speed_factor}", str(fast_wav)]
        subprocess.run(cmd, capture_output=True, check=True)
        if raw_wav.exists():
            raw_wav.unlink()

        dur = get_audio_duration(fast_wav)
        frame_dur = round(dur + 1.5, 1) if idx == len(scenes) - 1 else round(dur, 1)
        scene["duration_sec"] = frame_dur
        scene["start_time"] = round(accumulated_delay, 2)
        accumulated_delay += frame_dur
        
        tts_paths.append((scene, fast_wav))

    PROJECT_DIR = PROJECTS_ROOT / proj_id
    proj_assets_dir = PROJECT_DIR / "assets"
    proj_frames_dir = PROJECT_DIR / "frames"
    
    proj_assets_dir.mkdir(parents=True, exist_ok=True)
    proj_frames_dir.mkdir(parents=True, exist_ok=True)

    final_wav_filename = "narration_final.wav"
    final_wav_path = proj_assets_dir / final_wav_filename
    concat_cmd = [find_ffmpeg(), "-y"]
    for _, wav_path in tts_paths:
        concat_cmd.extend(["-i", str(wav_path)])
    
    filter_complex = "".join([f"[{i}:a]" for i in range(len(tts_paths))]) + f"concat=n={len(tts_paths)}:v=0:a=1[a]"
    concat_cmd.extend(["-filter_complex", filter_complex, "-map", "[a]", str(final_wav_path)])
    subprocess.run(concat_cmd, capture_output=True, check=True)

    voice_asset_filename = "narration_final.mp3"
    voice_asset_path = proj_assets_dir / voice_asset_filename
    mp3_cmd = [find_ffmpeg(), "-y", "-i", str(final_wav_path), "-codec:a", "libmp3lame", "-qscale:a", "2", str(voice_asset_path)]
    subprocess.run(mp3_cmd, capture_output=True, check=True)
    
    if final_wav_path.exists():
        final_wav_path.unlink()
    shutil.rmtree(temp_dir, ignore_errors=True)

    if not (proj_assets_dir / "background_music.mp3").exists():
        shutil.copy2(BASE_DIR / "assets" / "background_music.mp3", proj_assets_dir / "background_music.mp3")

    sha1 = hashlib.sha1()
    with open(voice_asset_path, 'rb') as f:
        sha1.update(f.read())
    sha1 = sha1.hexdigest()

    frames_config = []
    node_ids = ["hook", "reveal", "stats", "solution", "cta"]
    html_names = ["01-hook.html", "02-reveal.html", "03-stats.html", "04-solution.html", "05-cta.html"]

    for idx, (scene, wav_path) in enumerate(tts_paths):
        chunks_data = align_chunks_to_audio(wav_path, scene["display_chunks"])
        if not chunks_data:
            chunks_data = compute_subtitles(scene["display_chunks"], scene["duration_sec"])

        visual_css, visual_elements = get_visual_elements_and_css(scene["theme"], scene["visual"])
        
        html_content = get_html_template(
            theme=scene["theme"],
            kicker=scene["kicker"],
            title=scene["title"],
            frame_dur=scene["duration_sec"],
            chunks_data=chunks_data,
            visual_html=visual_css,
            visual_elements=visual_elements,
            scene_visual=scene["visual"]
        )
        
        html_file = proj_frames_dir / html_names[idx % len(html_names)]
        with open(html_file, 'w', encoding='utf-8') as hf:
            hf.write(html_content)

        frames_config.append({
            "graphNodeId": node_ids[idx % len(node_ids)],
            "htmlPath": f".html-video/projects/{proj_id}/frames/{html_names[idx % len(html_names)]}",
            "durationSec": scene["duration_sec"],
            "order": idx
        })

    project_data = {
        "id": proj_id,
        "name": data.get("name", "Dự án kịch bản"),
        "resolution": {"width": 1080, "height": 1920},
        "aspect": "9:16",
        "speed_factor": speed_factor,
        "temperature": temperature,
        "music_volume_db": -19,
        "narration_volume_db": 3,
        "fade_out_sec": 2,
        "templateId": "hyperframes",
        "preferences": {
            "resolution": {"width": 1080, "height": 1920},
            "aspect": "9:16",
            "fps": 60
        },
        "scenes": scenes,
        "frames": frames_config,
        "assets": [
            {
                "id": sha1,
                "type": "audio",
                "path": f".html-video/projects/{proj_id}/assets/{voice_asset_filename}",
                "metadata": {
                    "filename": "narration_final.mp3",
                    "mimeType": "audio/mpeg",
                    "sizeBytes": voice_asset_path.stat().st_size
                }
            },
            {
                "id": "30f47a41ad56a1f11acd23d95bd19b8c40b7c8e8",
                "type": "audio",
                "path": f".html-video/projects/{proj_id}/assets/background_music.mp3",
                "metadata": {
                    "filename": "background_music.mp3",
                    "mimeType": "audio/mpeg",
                    "sizeBytes": (proj_assets_dir / "background_music.mp3").stat().st_size
                }
            }
        ],
        "soundtrack": {
            "musicAssetId": "30f47a41ad56a1f11acd23d95bd19b8c40b7c8e8",
            "narrationAssetId": sha1,
            "narrationText": " ".join([s["tts_text"] for s in scenes]),
            "narrationVolumeDb": 3,
            "musicVolumeDb": -19,
            "fadeOutSec": 2
        }
    }

    with open(PROJECT_DIR / "project.json", 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return project_data

def create_default_project(project_id):
    proj_dir = PROJECTS_ROOT / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets").mkdir(exist_ok=True)
    (proj_dir / "frames").mkdir(exist_ok=True)
    
    proj_json = proj_dir / "project.json"
    if not proj_json.exists():
        default = BASE_DIR / "default_project.json"
        if default.exists():
            shutil.copy2(default, proj_json)
        else:
            basic_data = {
                "name": "DE Marketing Video",
                "resolution": {"width": 1080, "height": 1920},
                "aspect": "9:16",
                "scenes": []
            }
            with open(proj_json, 'w', encoding='utf-8') as f:
                json.dump(basic_data, f, ensure_ascii=False, indent=2)

def get_project_list():
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    list_proj = []
    for d in PROJECTS_ROOT.iterdir():
        if d.is_dir() and (d / "project.json").exists():
            try:
                with open(d / "project.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    list_proj.append({
                        "id": d.name,
                        "name": data.get("name", d.name)
                    })
            except Exception:
                list_proj.append({"id": d.name, "name": d.name})
                
    if not list_proj:
        create_default_project("proj_0d93e26f-9b8")
        list_proj.append({"id": "proj_0d93e26f-9b8", "name": "DE Marketing Video"})
    return list_proj

def create_new_project(name):
    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    proj_dir = PROJECTS_ROOT / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets").mkdir(exist_ok=True)
    (proj_dir / "frames").mkdir(exist_ok=True)
    
    default = BASE_DIR / "default_project.json"
    if default.exists():
        with open(default, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data["name"] = name
    else:
        data = {
            "name": name,
            "resolution": {"width": 1080, "height": 1920},
            "aspect": "9:16",
            "scenes": []
        }
    
    with open(proj_dir / "project.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return {"id": project_id, "name": name}

def save_project():
    with open(BASE_DIR / "project.json", 'w', encoding='utf-8') as f:
        json.dump(_project, f, ensure_ascii=False, indent=2)

# ── FFmpeg helpers ───────────────────────────────────────────────
def find_ffmpeg():
    custom = os.getenv("FFMPEG_PATH", "")
    if custom and os.path.exists(custom):
        return custom
    system = shutil.which("ffmpeg")
    if system:
        return system
    return "ffmpeg"

def find_ffprobe():
    custom = os.getenv("FFPROBE_PATH", "")
    if custom and os.path.exists(custom):
        return custom
    system = shutil.which("ffprobe")
    if system:
        return system
    return "ffprobe"

def get_audio_duration(path):
    ffprobe = find_ffprobe()
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

# ── VieNeu-TTS lazy loader ───────────────────────────────────────
def get_tts():
    global _tts_engine
    if _tts_engine is not None:
        return _tts_engine
    with _tts_lock:
        if _tts_engine is not None:
            return _tts_engine
        # Add VieNeu to path
        vieneu_src = VIENEU_PATH / "src"
        if str(vieneu_src) not in sys.path:
            sys.path.insert(0, str(vieneu_src))
        try:
            from vieneu import Vieneu
            print("🔧 Loading VieNeu-TTS v3 Turbo (CPU/ONNX)...")
            _tts_engine = Vieneu(mode="v3turbo")
            print("✅ VieNeu-TTS ready!")
            return _tts_engine
        except Exception as e:
            print(f"⚠️ VieNeu-TTS load failed: {e}")
            return None

def encode_ref_audio(ref_path):
    """Encode reference audio for voice cloning, with caching."""
    ref_path = str(ref_path)
    if ref_path in _ref_codes_cache:
        return _ref_codes_cache[ref_path]
    tts = get_tts()
    if tts is None:
        return None
    try:
        codes = tts.encode_reference(ref_path)
        _ref_codes_cache[ref_path] = codes
        return codes
    except Exception as e:
        print(f"⚠️ encode_reference failed: {e}")
        return None

# ── Multipart parser (stdlib) ─────────────────────────────────────
def parse_multipart(body, content_type):
    """Parse multipart/form-data from raw body bytes."""
    boundary = None
    for part in content_type.split(';'):
        part = part.strip()
        if part.startswith('boundary='):
            boundary = part.split('=', 1)[1].strip('"')
            break
    if not boundary:
        return {}, {}

    boundary_bytes = boundary.encode()
    parts = body.split(b'--' + boundary_bytes)
    fields = {}
    files = {}

    for part in parts:
        if part in (b'', b'--\r\n', b'--'):
            continue
        part = part.strip(b'\r\n')
        if b'\r\n\r\n' not in part:
            continue
        headers_raw, data = part.split(b'\r\n\r\n', 1)
        if data.endswith(b'\r\n'):
            data = data[:-2]

        headers_str = headers_raw.decode('utf-8', errors='replace')
        cd = None
        ct = 'text/plain'
        for line in headers_str.split('\r\n'):
            lower = line.lower()
            if lower.startswith('content-disposition:'):
                cd = line
            elif lower.startswith('content-type:'):
                ct = line.split(':', 1)[1].strip()

        if not cd:
            continue

        name = None
        filename = None
        for p in cd.split(';'):
            p = p.strip()
            if p.startswith('name='):
                name = p.split('=', 1)[1].strip('"')
            elif p.startswith('filename='):
                filename = p.split('=', 1)[1].strip('"')

        if filename:
            files[name] = {'filename': filename, 'data': data, 'content_type': ct}
        else:
            fields[name] = data.decode('utf-8', errors='replace')

    return fields, files

# ── HTTP Handler ──────────────────────────────────────────────────
class StudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        # Quieter logging
        if '/api/' in str(args[0]) if args else False:
            print(f"  API: {args[0]}")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_file_response(self, path, content_type=None):
        if not os.path.exists(path):
            self.send_json({"error": "File not found"}, 404)
            return
        if content_type is None:
            content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(data))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self.send_file_response(str(BASE_DIR / 'index.html'), 'text/html; charset=utf-8')
        elif path == '/styles.css':
            self.send_file_response(str(BASE_DIR / 'styles.css'), 'text/css; charset=utf-8')
        elif path == '/app.js':
            self.send_file_response(str(BASE_DIR / 'app.js'), 'application/javascript; charset=utf-8')
        elif path.startswith('/.html-video/'):
            # Static proxy for project frames, assets, and configs
            file_path = Path("D:/AI_rikkei/html-video-main") / path.lstrip('/')
            self.send_file_response(str(file_path))
        elif path.startswith('/assets/'):
            file_path = BASE_DIR / path.lstrip('/')
            self.send_file_response(str(file_path))
        elif path.startswith('/uploads/'):
            file_path = BASE_DIR / path.lstrip('/')
            self.send_file_response(str(file_path))
        elif path.startswith('/frames/'):
            file_path = BASE_DIR / path.lstrip('/')
            self.send_file_response(str(file_path))
        elif path == '/api/projects':
            self.send_json({"projects": get_project_list()})
        elif path == '/api/project':
            query = parse_qs(parsed.query)
            proj_id = query.get('id', ['proj_0d93e26f-9b8'])[0]
            data = load_and_sanitize_project(proj_id)
            if data:
                self.send_json(data)
            else:
                self.send_json({"error": "Project not found"}, 404)
        elif path == '/api/status':
            self.send_json({
                "server": "ok",
                "tts_loaded": _tts_engine is not None,
                "ffmpeg": shutil.which("ffmpeg") is not None,
                "vieneu_path": str(VIENEU_PATH),
                "vieneu_exists": VIENEU_PATH.exists()
            })
        elif path == '/api/voices':
            tts = get_tts()
            voices = []
            if tts and hasattr(tts, '_preset_voices'):
                for name in tts._preset_voices:
                    voices.append(name)
            self.send_json({"voices": voices, "has_custom_ref": bool(_ref_codes_cache)})
        else:
            super().do_GET()

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/project':
            query = parse_qs(parsed.query)
            proj_id = query.get('id', ['proj_0d93e26f-9b8'])[0]
            body = self.read_body()
            proj_data = json.loads(body)
            proj_file = get_project_file(proj_id)
            proj_file.parent.mkdir(parents=True, exist_ok=True)
            with open(proj_file, 'w', encoding='utf-8') as f:
                json.dump(proj_data, f, ensure_ascii=False, indent=2)
            self.send_json({"status": "saved"})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        ct = self.headers.get('Content-Type', '')

        if path == '/api/projects':
            body = self.read_body()
            data = json.loads(body)
            name = data.get('name', 'Dự án mới')
            new_proj = create_new_project(name)
            self.send_json({"status": "ok", "project": new_proj})

        elif path == '/api/upload-voice':
            proj_id = query.get('project_id', ['proj_0d93e26f-9b8'])[0]
            body = self.read_body()
            fields, files = parse_multipart(body, ct)
            if 'file' not in files:
                self.send_json({"error": "No file uploaded"}, 400)
                return
            f = files['file']
            ext = Path(f['filename']).suffix or '.wav'
            fname = f"voice_{uuid.uuid4().hex[:8]}{ext}"
            
            dest_dir = PROJECTS_ROOT / proj_id / "assets"
            dest_dir.mkdir(parents=True, exist_ok=True)
            save_path = dest_dir / fname
            with open(save_path, 'wb') as out:
                out.write(f['data'])
                
            ref_codes = encode_ref_audio(save_path)
            self.send_json({
                "status": "ok",
                "filename": fname,
                "path": f"/.html-video/projects/{proj_id}/assets/{fname}",
                "encoded": ref_codes is not None
            })

        elif path == '/api/upload-music':
            proj_id = query.get('project_id', ['proj_0d93e26f-9b8'])[0]
            body = self.read_body()
            fields, files = parse_multipart(body, ct)
            if 'file' not in files:
                self.send_json({"error": "No file uploaded"}, 400)
                return
            f = files['file']
            ext = Path(f['filename']).suffix or '.mp3'
            fname = f"music_{uuid.uuid4().hex[:8]}{ext}"
            
            dest_dir = PROJECTS_ROOT / proj_id / "assets"
            dest_dir.mkdir(parents=True, exist_ok=True)
            save_path = dest_dir / fname
            with open(save_path, 'wb') as out:
                out.write(f['data'])
                
            self.send_json({
                "status": "ok",
                "filename": fname,
                "path": f"/.html-video/projects/{proj_id}/assets/{fname}"
            })

        elif path == '/api/tts':
            proj_id = query.get('project_id', ['proj_0d93e26f-9b8'])[0]
            body = self.read_body()
            data = json.loads(body)
            text = data.get('text', '')
            ref_audio_raw = data.get('ref_audio_path', '/assets/voice_preview.mp3')
            ref_audio = resolve_local_path(ref_audio_raw)
            temperature = data.get('temperature', 0.2)
            speed_factor = data.get('speed_factor', 1.12)
            max_chars = data.get('max_chars', 80)

            tts = get_tts()
            if tts is None:
                self.send_json({"error": "VieNeu-TTS not available"}, 503)
                return

            try:
                ref_codes = encode_ref_audio(ref_audio)

                raw_fname = f"tts_{uuid.uuid4().hex[:8]}.wav"
                raw_path = UPLOADS_DIR / raw_fname
                audio = tts.infer(text=text, ref_codes=ref_codes, temperature=temperature, max_chars=max_chars)
                tts.save(audio, str(raw_path))

                dest_dir = PROJECTS_ROOT / proj_id / "assets"
                dest_dir.mkdir(parents=True, exist_ok=True)

                if abs(speed_factor - 1.0) > 0.01:
                    out_fname = f"tts_{uuid.uuid4().hex[:8]}_fast.wav"
                    out_path = dest_dir / out_fname
                    ffmpeg = find_ffmpeg()
                    cmd = [ffmpeg, "-y", "-i", str(raw_path),
                           "-filter:a", f"atempo={speed_factor}", str(out_path)]
                    subprocess.run(cmd, capture_output=True, check=True)
                    os.remove(raw_path)
                    final_path = out_path
                    final_fname = out_fname
                else:
                    final_path = dest_dir / raw_fname
                    shutil.move(str(raw_path), str(final_path))
                    final_fname = raw_fname

                duration = get_audio_duration(final_path)

                self.send_json({
                    "status": "ok",
                    "path": f"/.html-video/projects/{proj_id}/assets/{final_fname}",
                    "duration": duration
                })
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == '/api/tts/init':
            # Trigger lazy loading of TTS in background thread
            def _load():
                get_tts()
            threading.Thread(target=_load, daemon=True).start()
            self.send_json({"status": "loading"})

        elif path == '/api/project/render':
            query = parse_qs(parsed.query)
            proj_id = query.get('project_id', ['proj_0d93e26f-9b8'])[0]
            PROJECT_DIR = PROJECTS_ROOT / proj_id
            if not PROJECT_DIR.exists() or not (PROJECT_DIR / "project.json").exists():
                self.send_json({"error": "Project not found or project.json is missing"}, 404)
                return

            try:
                data = load_and_sanitize_project(proj_id)
                
                needs_pipeline = False
                if "frames" not in data or not data["frames"]:
                    needs_pipeline = True
                else:
                    for f in data["frames"]:
                        p = Path("D:/AI_rikkei/html-video-main") / f["htmlPath"].lstrip('/')
                        if not p.exists():
                            needs_pipeline = True
                            break
                    voice_asset = None
                    for asset in data.get("assets", []):
                        if asset.get("type") == "audio" and "narration_final" in asset.get("path", ""):
                            voice_asset = Path("D:/AI_rikkei/html-video-main") / asset["path"].lstrip('/')
                            break
                    if not voice_asset or not voice_asset.exists():
                        needs_pipeline = True
                
                if needs_pipeline:
                    print(f"  Project {proj_id} has no rendered frames/assets. Generating them now...")
                    data = run_pipeline_generation(proj_id, data)
                
                print(f"  Exporting MP4 video for project {proj_id}...")
                output_mp4 = PROJECT_DIR / "final.mp4"
                
                node_bin = shutil.which("node") or "node"
                render_cmd = [
                    node_bin,
                    "packages/cli/dist/bin.js",
                    "project-render",
                    proj_id,
                    "--output",
                    str(output_mp4)
                ]
                
                print(f"  Executing: {' '.join(render_cmd)}")
                render_res = subprocess.run(render_cmd, cwd=str(BASE_DIR.parent), capture_output=True, text=True)
                
                if render_res.returncode != 0:
                    print(f"  ✗ Render command failed: {render_res.stderr}")
                    self.send_json({"error": f"Render failed: {render_res.stderr}"}, 500)
                    return
                    
                print("  ✓ Render complete! MP4 video compiled successfully.")
                self.send_json({
                    "status": "ok",
                    "video_url": f"/.html-video/projects/{proj_id}/final.mp4"
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({"error": str(e)}, 500)

        elif path == '/api/generate-pipeline':
            proj_id = query.get('project_id', ['proj_0d93e26f-9b8'])[0]
            body = self.read_body()
            data = json.loads(body)
            script_text = data.get('script', '')
            speed_factor = data.get('speed_factor', 1.12)
            temperature = data.get('temperature', 0.2)
            voice_ref_raw = data.get('voice_ref', '/assets/voice_preview.mp3')
            voice_ref = resolve_local_path(voice_ref_raw)

            # 1. Lazy load TTS
            tts = get_tts()
            if tts is None:
                self.send_json({"error": "VieNeu-TTS not available. Vui lòng bấm Load TTS trước!"}, 503)
                return

            try:
                # 2. Parse script
                scenes = parse_script_to_scenes(script_text)
                
                # 3. Create a temporary folder inside uploads for rendering
                temp_id = f"pipeline_{uuid.uuid4().hex[:8]}"
                temp_dir = UPLOADS_DIR / temp_id
                temp_dir.mkdir(exist_ok=True)

                # Pre-encode reference audio for VieNeu
                ref_codes = encode_ref_audio(voice_ref)

                # 4. Generate audio and compile metadata
                print(f"  Starting Pipeline Generation for {len(scenes)} scenes in project {proj_id}...")
                accumulated_delay = 0.0
                tts_paths = []
                
                for idx, scene in enumerate(scenes):
                    scene_id = scene["id"]
                    raw_wav = temp_dir / f"{scene_id}_raw.wav"
                    fast_wav = temp_dir / f"{scene_id}.wav"
                    
                    # Run VieNeu TTS
                    audio = tts.infer(text=scene["tts_text"], ref_codes=ref_codes, temperature=temperature, max_chars=120)
                    tts.save(audio, str(raw_wav))

                    # Speed up
                    ffmpeg = find_ffmpeg()
                    cmd = [ffmpeg, "-y", "-i", str(raw_wav), "-filter:a", f"atempo={speed_factor}", str(fast_wav)]
                    subprocess.run(cmd, capture_output=True, check=True)
                    if raw_wav.exists():
                        raw_wav.unlink()

                    # Measure duration
                    dur = get_audio_duration(fast_wav)
                    
                    # Pad the last scene duration a bit for video lingering
                    frame_dur = round(dur + 1.5, 1) if idx == len(scenes) - 1 else round(dur, 1)
                    
                    scene["duration_sec"] = frame_dur
                    scene["start_ms"] = int(accumulated_delay * 1000)
                    
                    # Save WAV directly inside project assets directory instead of global uploads
                    client_wav_name = f"{scene_id}.wav"
                    proj_assets_dir = PROJECTS_ROOT / proj_id / "assets"
                    proj_assets_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(fast_wav, proj_assets_dir / client_wav_name)
                    scene["audio_path"] = f"/.html-video/projects/{proj_id}/assets/{client_wav_name}"
                    
                    accumulated_delay += frame_dur
                    tts_paths.append((scene, fast_wav))

                # 5. Mix all narration tracks
                print("  Mixing voice narration tracks...")
                inputs = []
                filter_chains = []
                mix_labels = []
                for i, (scene, path_wav) in enumerate(tts_paths):
                    inputs.extend(["-i", str(path_wav)])
                    delay = scene["start_ms"]
                    filter_chains.append(f"[{i}:a]adelay={delay}|{delay}[a{i}]")
                    mix_labels.append(f"[a{i}]")

                filter_chains.append(
                    f"{''.join(mix_labels)}amix=inputs={len(tts_paths)}:duration=longest:dropout_transition=0[aout]"
                )

                mixed_temp = temp_dir / "mixed.mp3"
                cmd = [
                    ffmpeg, "-y", *inputs,
                    "-filter_complex", ";".join(filter_chains),
                    "-map", "[aout]",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(mixed_temp)
                ]
                subprocess.run(cmd, capture_output=True, check=True)

                # 6. Apply loudness normalization to mixed voice
                print("  Normalising loudness...")
                norm_temp = temp_dir / "normalized.mp3"
                ffprobe = find_ffprobe()
                stats = measure_loudness(ffmpeg, ffprobe, mixed_temp)
                normalize_audio(ffmpeg, mixed_temp, norm_temp, stats)

                # Calculate SHA1 of the final voice track
                with open(norm_temp, "rb") as f:
                    sha1 = hashlib.sha1(f.read()).hexdigest()

                # 7. Write assets and HTML frames to PROJECT_DIR
                PROJECT_DIR = PROJECTS_ROOT / proj_id
                PROJECT_DIR.mkdir(parents=True, exist_ok=True)
                proj_assets_dir = PROJECT_DIR / "assets"
                proj_assets_dir.mkdir(exist_ok=True)
                proj_frames_dir = PROJECT_DIR / "frames"
                proj_frames_dir.mkdir(exist_ok=True)

                # Save final voice file to assets
                voice_asset_filename = f"{sha1}.mp3"
                shutil.copy2(norm_temp, proj_assets_dir / voice_asset_filename)

                # Copy BGM to assets if not exists
                bgm_dest = proj_assets_dir / "background_music.mp3"
                if not bgm_dest.exists():
                    bgm_src = ASSETS_DIR / "background_music.mp3"
                    shutil.copy2(bgm_src, bgm_dest)

                # Copy Mascot to assets if not exists
                mascot_dest = proj_assets_dir / "mascot.png"
                if not mascot_dest.exists():
                    mascot_src = ASSETS_DIR / "mascot.png"
                    shutil.copy2(mascot_src, mascot_dest)

                # Update HTML frames and align subtitles
                print("  Generating HTML templates and subtitles...")
                frames_config = []
                node_ids = ["hook", "reveal", "stats", "solution", "cta"]
                html_names = ["01-hook.html", "02-reveal.html", "03-stats.html", "04-solution.html", "05-cta.html"]

                for idx, (scene, wav_path) in enumerate(tts_paths):
                    chunks_data = align_chunks_to_audio(wav_path, scene["display_chunks"])
                    if not chunks_data:
                        chunks_data = compute_subtitles(scene["display_chunks"], scene["duration_sec"])

                    # Get Visual CSS and elements
                    visual_css, visual_elements = get_visual_elements_and_css(scene["theme"], scene["visual"])
                    
                    html_content = get_html_template(
                        theme=scene["theme"],
                        kicker=scene["kicker"],
                        title=scene["title"],
                        frame_dur=scene["duration_sec"],
                        chunks_data=chunks_data,
                        visual_html=visual_css,
                        visual_elements=visual_elements,
                        scene_visual=scene["visual"]
                    )
                    
                    html_file = proj_frames_dir / html_names[idx % len(html_names)]
                    with open(html_file, 'w', encoding='utf-8') as hf:
                        hf.write(html_content)

                    # Store relative htmlPath so rendering engine resolves properly
                    frames_config.append({
                        "graphNodeId": node_ids[idx % len(node_ids)],
                        "htmlPath": f".html-video/projects/{proj_id}/frames/{html_names[idx % len(html_names)]}",
                        "durationSec": scene["duration_sec"],
                        "order": idx
                    })

                # Compile project.json structure
                project_data = {
                    "id": proj_id,
                    "name": data.get("project_name", "Dự án kịch bản"),
                    "resolution": {"width": 1080, "height": 1920},
                    "aspect": "9:16",
                    "speed_factor": speed_factor,
                    "temperature": temperature,
                    "music_volume_db": -19,
                    "narration_volume_db": 3,
                    "fade_out_sec": 2,
                    "preferences": {
                        "resolution": {"width": 1080, "height": 1920},
                        "aspect": "9:16",
                        "fps": 60
                    },
                    "scenes": scenes,
                    "frames": frames_config,
                    "assets": [
                        {
                            "id": sha1,
                            "type": "audio",
                            "path": f".html-video/projects/{proj_id}/assets/{voice_asset_filename}",
                            "metadata": {
                                "filename": "narration_final.mp3",
                                "mimeType": "audio/mpeg",
                                "sizeBytes": (proj_assets_dir / voice_asset_filename).stat().st_size
                            }
                        },
                        {
                            "id": "30f47a41ad56a1f11acd23d95bd19b8c40b7c8e8",
                            "type": "audio",
                            "path": f".html-video/projects/{proj_id}/assets/background_music.mp3",
                            "metadata": {
                                "filename": "background_music.mp3",
                                "mimeType": "audio/mpeg",
                                "sizeBytes": (proj_assets_dir / "background_music.mp3").stat().st_size
                            }
                        }
                    ],
                    "soundtrack": {
                        "musicAssetId": "30f47a41ad56a1f11acd23d95bd19b8c40b7c8e8",
                        "narrationAssetId": sha1,
                        "narrationText": " ".join([s["tts_text"] for s in scenes]),
                        "narrationVolumeDb": 3,
                        "musicVolumeDb": -19,
                        "fadeOutSec": 2
                    }
                }

                # Save project.json to target CLI project path
                with open(PROJECT_DIR / "project.json", 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, ensure_ascii=False, indent=2)

                # 8. Render the project using Playwright CLI subprocess
                print("  Rendering MP4 video via Playwright & Chromium...")
                output_mp4 = PROJECT_DIR / "final.mp4"
                
                # Check node executable
                node_bin = shutil.which("node") or "node"
                render_cmd = [
                    node_bin,
                    "packages/cli/dist/bin.js",
                    "project-render",
                    proj_id,
                    "--output",
                    str(output_mp4)
                ]
                
                print(f"  Executing: {' '.join(render_cmd)}")
                render_res = subprocess.run(render_cmd, cwd=str(BASE_DIR.parent), capture_output=True, text=True)
                
                # Clean up temporary folders
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

                if render_res.returncode != 0:
                    print(f"  ✗ Render command failed: {render_res.stderr}")
                    self.send_json({"error": f"Playwright rendering failed: {render_res.stderr}"}, 500)
                    return

                print("  ✓ Render complete! MP4 video compiled successfully.")
                self.send_json({
                    "status": "ok",
                    "video_url": f"/.html-video/projects/{proj_id}/final.mp4",
                    "project": project_data
                })

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json({"error": str(e)}, 500)

        else:
            self.send_json({"error": "Not found"}, 404)


class ThreadedHTTPServer(HTTPServer):
    """Handle requests in separate threads for non-blocking TTS."""
    def process_request(self, request, client_address):
        thread = threading.Thread(target=self._handle_request_thread,
                                  args=(request, client_address))
        thread.daemon = True
        thread.start()

    def _handle_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    get_project_list()

    # Ensure dirs exist
    UPLOADS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    FRAMES_DIR.mkdir(exist_ok=True)

    server = ThreadedHTTPServer(('0.0.0.0', PORT), StudioHandler)
    print(f"""
╔══════════════════════════════════════════════════╗
║       🎬 Rikkei Video Studio                     ║
║       ──────────────────────────                 ║
║       Server:  http://localhost:{PORT}             ║
║       VieNeu:  {'✅ Found' if VIENEU_PATH.exists() else '❌ Missing'}                           ║
║       FFmpeg:  {'✅ Found' if shutil.which('ffmpeg') else '❌ Missing'}                           ║
║       ──────────────────────────                 ║
║       Press Ctrl+C to stop                       ║
╚══════════════════════════════════════════════════╝
    """)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        server.shutdown()


# ── Pipeline helper functions copied from generate_de_video.py ────

KEY_WORDS = {"CNTT","DATA","PIPELINE","WAREHOUSE","ETL","BÁO","CÁO","DOANH","THU","END-TO-END","DE","LỘ","TRÌNH","GPA","CÔNG","NGHỆ","THÔNG","TIN","SPARK","KAFKA","AIRFLOW"}
DANGER_WORDS = {"ĐƠ","ẤP","ÚNG","QUÊN","THẤT","BẠI","LÝ","THUYẾT","DỐT","VẸT","HÌNH"}
WORD_WEIGHTS = { "GPA":3, "ETL":3, "END-TO-END":3, "DATA":2, "PIPELINE":2, "CV":2, "DE":2, "WAREHOUSE":2, "COMMENT":2, "SPARK":2, "KAFKA":2, "AIRFLOW":3, "10":2 }

def get_word_weight(word: str) -> int:
    upper_w = word.upper().strip(".,!?-\"\u201c\u201d:;")
    return WORD_WEIGHTS.get(upper_w, 1)

def compute_subtitles(display_chunks, total_dur):
    flat_display_words = []
    chunk_word_indices = []
    pauses_map = {}
    word_weights = []

    word_count = 0
    total_pauses = 0.0

    for c_idx, chunk_data in enumerate(display_chunks):
        words = chunk_data["words"]
        pause = chunk_data.get("pause_after", 0.0)
        for w in words:
            flat_display_words.append(w)
            chunk_word_indices.append((c_idx, len(flat_display_words) - 1))
            word_weights.append(get_word_weight(w))
            word_count += 1
        if pause > 0.0:
            pauses_map[word_count - 1] = pause
            total_pauses += pause

    total_weight = sum(word_weights)
    start_offset = 0.2
    end_offset = 0.2
    available_dur = total_dur - start_offset - end_offset - total_pauses
    if available_dur <= 0:
        available_dur = total_dur
        start_offset = 0.0
        pauses_map = {}
        total_pauses = 0.0

    unit_dur = available_dur / total_weight if total_weight > 0 else 0
    chunks_data = [{"start": 0.0, "dur": 0.0, "words": []} for _ in range(len(display_chunks))]

    cumulative_pause = 0.0
    cumulative_dur = 0.0
    for i, (c_idx, w_idx) in enumerate(chunk_word_indices):
        w_start = start_offset + cumulative_dur + cumulative_pause
        w_weight = word_weights[i]
        w_duration = w_weight * unit_dur * 0.9
        w_text = flat_display_words[i]

        chunks_data[c_idx]["words"].append({
            "text": w_text,
            "start": round(w_start, 2),
            "duration": round(w_duration, 2)
        })

        cumulative_dur += w_weight * unit_dur
        if i in pauses_map:
            cumulative_pause += pauses_map[i]

    for chunk in chunks_data:
        if not chunk["words"]:
            continue
        c_start = chunk["words"][0]["start"]
        c_end = chunk["words"][-1]["start"] + chunk["words"][-1]["duration"]
        chunk["start"] = round(c_start - 0.05, 2)
        chunk["dur"] = round(c_end - c_start + 0.1, 2)

    for i in range(len(chunks_data) - 1):
        next_start = chunks_data[i + 1]["start"]
        chunks_data[i]["dur"] = round(next_start - chunks_data[i]["start"], 2)

    return chunks_data

def align_chunks_to_audio(audio_path, display_chunks):
    try:
        import numpy as np
        import soundfile as sf

        data, samplerate = sf.read(str(audio_path))
        if len(data.shape) > 1:
            data = data[:, 0]

        win_size = int(samplerate * 0.01)
        num_windows = len(data) // win_size
        energies = np.array([
            np.sqrt(np.mean(data[i * win_size:(i + 1) * win_size] ** 2))
            for i in range(num_windows)
        ])

        energies = np.convolve(energies, np.ones(20) / 20, mode='same')
        energies = energies / (np.max(energies) + 1e-8)

        expected_segments = 1
        segment_grouping = []
        current_group = [0]
        for idx, chunk in enumerate(display_chunks[:-1]):
            if "pause_after" in chunk:
                expected_segments += 1
                segment_grouping.append(current_group)
                current_group = [idx + 1]
            else:
                current_group.append(idx + 1)
        segment_grouping.append(current_group)

        def _detect_segments(threshold, min_gap=0.18, min_len=0.12):
            active = energies > threshold
            segs, in_seg, start_f = [], False, 0
            for i, val in enumerate(active):
                if val and not in_seg:
                    in_seg, start_f = True, i
                elif not val and in_seg:
                    in_seg = False
                    segs.append((start_f * 0.01, i * 0.01))
            if in_seg:
                segs.append((start_f * 0.01, len(active) * 0.01))

            merged = []
            for seg in segs:
                if merged and seg[0] - merged[-1][1] < min_gap:
                    merged[-1] = (merged[-1][0], seg[1])
                else:
                    merged.append(list(seg))

            return [tuple(s) for s in merged if s[1] - s[0] > min_len]

        best_segments = []
        best_diff = float("inf")
        for threshold in np.linspace(0.005, 0.25, 500):
            filtered = _detect_segments(threshold)
            diff = abs(len(filtered) - expected_segments)
            if diff < best_diff:
                best_diff = diff
                best_segments = filtered
            if diff == 0:
                break

        if abs(len(best_segments) - expected_segments) > 1 or len(best_segments) == 0:
            return None

        while len(best_segments) > expected_segments:
            last = best_segments.pop()
            best_segments[-1] = (best_segments[-1][0], last[1])

        if len(best_segments) < expected_segments:
            audio_end = num_windows * 0.01
            for _ in range(expected_segments - len(best_segments)):
                prev_end = best_segments[-1][1]
                best_segments.append((prev_end, audio_end))

        chunks_timed = []
        for s_idx, seg in enumerate(best_segments):
            start_time, end_time = seg
            chunk_indices = segment_grouping[s_idx]

            group_words = []
            word_weights = []
            for c_idx in chunk_indices:
                for w in display_chunks[c_idx]["words"]:
                    group_words.append((c_idx, w))
                    word_weights.append(get_word_weight(w))

            total_weight = sum(word_weights)
            unit_dur = (end_time - start_time) / total_weight if total_weight > 0 else 0

            words_by_chunk = {c_idx: [] for c_idx in chunk_indices}
            cumulative_dur = 0.0
            for i, (c_idx, w_text) in enumerate(group_words):
                w_weight = word_weights[i]
                words_by_chunk[c_idx].append({
                    "text": w_text,
                    "start": round(start_time + cumulative_dur, 2),
                    "duration": round(w_weight * unit_dur * 0.9, 2)
                })
                cumulative_dur += w_weight * unit_dur

            for c_idx in chunk_indices:
                c_words = words_by_chunk[c_idx]
                c_start = c_words[0]["start"]
                c_end = c_words[-1]["start"] + c_words[-1]["duration"]
                chunks_timed.append({
                    "start": round(c_start - 0.05, 2),
                    "dur": round(c_end - c_start + 0.1, 2),
                    "words": c_words
                })

        for i in range(len(chunks_timed) - 1):
            next_start = chunks_timed[i + 1]["start"]
            chunks_timed[i]["dur"] = round(next_start - chunks_timed[i]["start"], 2)

        return chunks_timed
    except Exception as e:
        print(f"    VAD alignment failed: {e}")
        return None

def parse_script_to_scenes(script_text):
    # Try parsing as JSON first
    try:
        parsed_json = json.loads(script_text)
        if isinstance(parsed_json, list):
            return parsed_json
        elif isinstance(parsed_json, dict) and "scenes" in parsed_json:
            return parsed_json["scenes"]
    except Exception:
        pass

    # Fallback to text parsing
    parts = re.split(r'(?i)\bscene\s*\d+\b|---|\n\s*\n', script_text)
    scenes_text = [p.strip() for p in parts if p.strip()]
    if not scenes_text:
        scenes_text = [script_text.strip()]
        
    scenes = []
    themes = ['hook', 'reveal', 'stats', 'solution', 'cta']
    for i, text in enumerate(scenes_text):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        tts_text = text
        
        kicker = f"CẢNH {i+1}"
        title = sentences[0][:30] if sentences else "GIỚI THIỆU"
        if title.endswith('.'): title = title[:-1]
        
        words = text.split()
        display_chunks = []
        chunk_size = 6
        for j in range(0, len(words), chunk_size):
            chunk_words = words[j:j+chunk_size]
            display_chunks.append({
                "words": chunk_words,
                "pause_after": 0.4 if j+chunk_size < len(words) else 0.8
            })
            
        scenes.append({
            "id": f"s{i}",
            "kicker": f"🔥 {kicker.upper()} 🔥",
            "title": title.upper(),
            "tts_text": tts_text,
            "display_chunks": display_chunks,
            "theme": themes[i % len(themes)],
            "visual": {
                "card1": {"badge": "Ý chính", "name": title, "status": "Cảnh " + str(i+1)},
                "card2": {"badge": "Thực tế", "name": "Nội dung", "status": "Chi tiết"}
            },
            "duration_sec": 8.0
        })
    return scenes

def measure_loudness(ffmpeg, ffprobe, input_path):
    cmd = [
        ffmpeg, "-y",
        "-i", str(input_path),
        "-filter:a", "loudnorm=I=-11.0:TP=-1.5:LRA=11.0:print_format=json",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr
    match = re.search(r'\{[^{}]+\}', output, re.DOTALL)
    if not match:
        raise RuntimeError("Failed to parse loudnorm JSON")
    return json.loads(match.group())

def normalize_audio(ffmpeg, input_path, output_path, stats):
    loudnorm_filter = (
        f"loudnorm=I=-11.0:TP=-1.5:LRA=11.0"
        f":measured_I={stats['input_i']}"
        f":measured_TP={stats['input_tp']}"
        f":measured_LRA={stats['input_lra']}"
        f":measured_thresh={stats['input_thresh']}"
        f":offset={stats.get('target_offset', 0)}"
        f":linear=true"
    )
    cmd = [
        ffmpeg, "-y",
        "-i", str(input_path),
        "-filter:a", loudnorm_filter,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def get_visual_elements_and_css(theme, visual_config):
    c1 = visual_config.get("card1", {"badge": "Ý chính", "name": "BẮT ĐẦU", "status": "Khởi tạo"})
    c2 = visual_config.get("card2", {"badge": "Thực tế", "name": "THỰC HÀNH", "status": "Hoàn thành"})
    
    if theme == "hook" or theme == "reveal":
        return "", ""
        
    elif theme == "stats":
        visual_html = """
    .pipeline-container {
      width: 100%;
      height: clamp(260px, 32vh, 500px);
      background: rgba(255, 255, 255, 0.02);
      border: 2px solid rgba(255, 255, 255, 0.06);
      border-radius: 36px;
      position: relative;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 4%;
      overflow: hidden;
      opacity: 0;
      animation: fadeInPipeline 0.8s ease-out 0.6s forwards;
    }
    @keyframes fadeInPipeline { to { opacity: 1; } }

    .node {
      width: clamp(100px, 13vmax, 190px);
      height: clamp(100px, 13vmax, 190px);
      border-radius: 50%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      font-weight: 900;
      font-size: clamp(14px, 1.8vmax, 30px);
      color: #ffffff;
      box-shadow: 0 15px 35px rgba(0,0,0,0.5);
      position: relative;
      z-index: 5;
      text-align: center;
      line-height: 1.2;
    }
    .node-num {
      font-family: 'Barlow Condensed', sans-serif;
      font-size: clamp(24px, 3.2vmax, 55px);
      color: #fb923c;
    }
    .node-label {
      font-size: clamp(11px, 1.4vmax, 24px);
      font-weight: 700;
      margin-top: 5px;
    }
    .node.start {
      background: linear-gradient(135deg, #475569, #1e293b);
      border: 4px solid #94a3b8;
    }
    .node.study {
      background: linear-gradient(135deg, #1d4ed8, #1e3a8a);
      border: 4px solid #3b82f6;
      box-shadow: 0 0 35px rgba(59, 130, 246, 0.4);
    }
    .node.intern {
      background: linear-gradient(135deg, #b45309, #78350f);
      border: 4px solid #f59e0b;
      box-shadow: 0 0 35px rgba(245, 158, 11, 0.4);
    }
    .node.job {
      background: linear-gradient(135deg, #047857, #064e3b);
      border: 4px solid #10b981;
      box-shadow: 0 0 35px rgba(16, 185, 129, 0.4);
    }
    .connector {
      flex: 1;
      height: 6px;
      background: rgba(255, 255, 255, 0.1);
      position: relative;
      margin: 0 -10px;
      z-index: 1;
    }
    .connector-flow {
      position: absolute;
      left: 0; top: 0; bottom: 0; width: 0%;
      background: linear-gradient(90deg, #3b82f6, #f59e0b, #10b981);
      animation: fillFlow 5s linear forwards 1.2s infinite;
    }
    @keyframes fillFlow {
      0% { width: 0%; left: 0; }
      50% { width: 100%; left: 0; }
      100% { width: 0%; left: 100%; }
    }
"""
        elements = f"""
      <div class="pipeline-container">
        <div class="node start">
          <div class="node-num">Web</div>
          <div class="node-label">{c1.get('badge', 'Nguồn Web')}</div>
        </div>
        <div class="connector"><div class="connector-flow"></div></div>
        <div class="node intern">
          <div class="node-num">?</div>
          <div class="node-label">{c1.get('name', 'Pipeline')}</div>
        </div>
        <div class="connector"><div class="connector-flow"></div></div>
        <div class="node study">
          <div class="node-num">DB</div>
          <div class="node-label">{c1.get('status', 'Warehouse')}</div>
        </div>
        <div class="connector"><div class="connector-flow"></div></div>
        <div class="node job">
          <div class="node-num">BI</div>
          <div class="node-label">{c2.get('name', 'Báo Cáo')}</div>
        </div>
      </div>
"""
        return visual_html, elements
        
    elif theme == "solution":
        visual_html = """
    .cols-container {
      display: flex;
      gap: 3%;
      width: 100%;
      justify-content: center;
      opacity: 0;
      animation: fadeInCols 0.8s ease-out 0.6s forwards;
    }
    @keyframes fadeInCols { to { opacity: 1; } }

    .module-card {
      width: 32%;
      max-width: 300px;
      height: clamp(300px, 42vh, 520px);
      background: rgba(255, 255, 255, 0.03);
      border: 3px solid rgba(99, 102, 241, 0.3);
      border-radius: 28px;
      padding: 2.5vh 1.5vw;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      box-shadow: 0 15px 35px rgba(0,0,0,0.4);
      transition: border-color 0.3s;
    }
    .module-card:hover {
      border-color: #6366f1;
    }
    .module-card.m2 {
      border-color: rgba(249, 115, 22, 0.3);
    }
    .module-card.m2:hover {
      border-color: #f97316;
    }
    .module-card.m3 {
      border-color: rgba(251, 146, 96, 0.3);
    }
    .module-card.m3:hover {
      border-color: #fb923c;
    }
    .m-num {
      font-family: 'Barlow Condensed', sans-serif;
      font-size: clamp(15px, 2vmax, 32px);
      font-weight: 800;
      color: #6366f1;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    .m2 .m-num { color: #f97316; }
    .m3 .m-num { color: #fb923c; }
    
    .m-title {
      font-size: clamp(14px, 1.8vmax, 30px);
      font-weight: 800;
      margin-bottom: 2vh;
      line-height: 1.2;
    }
    .tech-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.8vh 0.8vw;
      justify-content: center;
    }
    .chip {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.15);
      padding: 0.6vh 1.2vw;
      border-radius: 16px;
      font-size: clamp(11px, 1.3vmax, 24px);
      font-weight: 700;
    }
"""
        elements = f"""
      <div class="cols-container">
        <div class="module-card">
          <div class="m-num">Bước 1</div>
          <div class="m-title">{c1.get('badge', 'Thu Thập')}</div>
          <div class="tech-chips">
            <div class="chip">API / Webhook</div>
            <div class="chip">Kafka / CDC</div>
            <div class="chip">{c1.get('name', 'Đơn hàng')}</div>
          </div>
        </div>
        <div class="module-card m2">
          <div class="m-num">Bước 2</div>
          <div class="m-title">{c1.get('status', 'Xử Lý')}</div>
          <div class="tech-chips">
            <div class="chip">Spark / Python</div>
            <div class="chip">Airflow (ETL)</div>
            <div class="chip">Warehouse</div>
          </div>
        </div>
        <div class="module-card m3">
          <div class="m-num">Bước 3</div>
          <div class="m-title">{c2.get('name', 'Báo Cáo')}</div>
          <div class="tech-chips">
            <div class="chip">BI Tools</div>
            <div class="chip">Doanh Thu</div>
            <div class="chip">{c2.get('status', 'Dashboard')}</div>
          </div>
        </div>
      </div>
"""
        return visual_html, elements
        
    else: # cta
        visual_html = """
    .cta-container {
      width: 100%;
      height: clamp(280px, 35vh, 540px);
      background: rgba(255, 255, 255, 0.02);
      border: 2px solid rgba(255, 255, 255, 0.06);
      border-radius: 36px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      gap: 3.5vh;
      position: relative;
      overflow: hidden;
      opacity: 0;
      animation: fadeInCTA 0.8s ease-out 0.6s forwards;
    }
    @keyframes fadeInCTA { to { opacity: 1; } }

    .hust-badge {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.25));
      border: 3px solid #ef4444;
      border-radius: 28px;
      padding: 2vh 4vw;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      box-shadow: 0 15px 35px rgba(239, 68, 68, 0.2);
    }
    .badge-title {
      font-size: clamp(12px, 1.4vmax, 26px);
      font-weight: 700;
      letter-spacing: 2px;
      color: rgba(255,255,255,0.85);
      text-transform: uppercase;
    }
    .badge-content {
      font-family: 'Barlow Condensed', sans-serif;
      font-size: clamp(22px, 2.8vmax, 48px);
      font-weight: 900;
      color: #fddf47;
      text-shadow: 0 0 20px rgba(253, 223, 71, 0.6);
      margin-top: 8px;
    }
    .cta-button {
      padding: 2.2vh 5vw;
      font-family: 'Barlow Condensed', sans-serif;
      font-size: clamp(26px, 3.5vmax, 60px);
      font-weight: 900;
      color: #ffffff;
      background: linear-gradient(135deg, #ea580c, #dc2626);
      border: 4px solid rgba(255,255,255,0.3);
      border-radius: 40px;
      box-shadow: 0 20px 50px rgba(220, 38, 38, 0.4);
      text-transform: uppercase;
      letter-spacing: 3px;
      animation: pulseBtn 1.5s ease-in-out infinite alternate;
      cursor: pointer;
    }
    @keyframes pulseBtn {
      0% { transform: scale(1); box-shadow: 0 20px 50px rgba(220, 38, 38, 0.4); }
      100% { transform: scale(1.08); box-shadow: 0 25px 65px rgba(220, 38, 38, 0.6), 0 0 30px #ea580c; }
    }
"""
        elements = f"""
      <div class="cta-container">
        <div class="hust-badge">
          <div class="badge-title">{c1.get('badge', 'Lộ trình')}</div>
          <div class="badge-content">{c1.get('name', 'Data Engineer')}</div>
        </div>
        <button class="cta-button">{c2.get('name', 'Comment DE nhận ngay')}</button>
      </div>
"""
        return visual_html, elements

def get_html_template(theme, kicker, title, frame_dur, chunks_data, visual_html, visual_elements, scene_visual):
    chunks_html = ""
    for chunk in chunks_data:
        words_html = ""
        for w in chunk["words"]:
            clean_w = re.sub(r'[^\w\s-]', '', w["text"].upper()).strip()
            if clean_w in KEY_WORDS:
                w_class = "w key-word"
            elif clean_w in DANGER_WORDS:
                w_class = "w danger-word"
            else:
                w_class = "w"
            words_html += f'          <span class="{w_class}" style="--d: {w["start"]}s; --word-duration: {w["duration"]}s;">{w["text"]}</span>\n'
            
        chunks_html += f"""        <!-- Chunk starting at {chunk["start"]}s -->
        <div class="caption-chunk" style="--chunk-start: {chunk["start"]}s; --chunk-duration: {chunk["dur"]}s;">
{words_html}        </div>\n"""

    if theme == "hook":
        p_col, s_col, a_col = "#783cff", "#dc2626", "#fbbf24"
        p_glow, s_glow, a_glow = "rgba(120, 60, 255, 0.25)", "rgba(220, 38, 100, 0.2)", "rgba(251, 191, 36, 0.15)"
        grad = "linear-gradient(135deg, #fbbf24, #ef4444)"
    elif theme == "reveal":
        p_col, s_col, a_col = "#059669", "#2563eb", "#34d399"
        p_glow, s_glow, a_glow = "rgba(5, 150, 105, 0.25)", "rgba(37, 99, 247, 0.2)", "rgba(52, 211, 153, 0.15)"
        grad = "linear-gradient(135deg, #34d399, #2563eb)"
    elif theme == "stats":
        p_col, s_col, a_col = "#2563eb", "#ea580c", "#fb923c"
        p_glow, s_glow, a_glow = "rgba(37, 99, 235, 0.25)", "rgba(234, 88, 12, 0.2)", "rgba(251, 146, 60, 0.15)"
        grad = "linear-gradient(135deg, #fb923c, #ea580c)"
    elif theme == "solution":
        p_col, s_col, a_col = "#6366f1", "#f97316", "#fb923c"
        p_glow, s_glow, a_glow = "rgba(99, 102, 241, 0.25)", "rgba(249, 115, 22, 0.2)", "rgba(251, 146, 96, 0.15)"
        grad = "linear-gradient(135deg, #6366f1, #f97316)"
    else: # cta
        p_col, s_col, a_col = "#ea580c", "#dc2626", "#fddf47"
        p_glow, s_glow, a_glow = "rgba(234, 88, 12, 0.30)", "rgba(220, 38, 38, 0.2)", "rgba(253, 223, 71, 0.15)"
        grad = "linear-gradient(135deg, #fddf47, #ea580c, #dc2626)"

    c1 = scene_visual.get("card1", {"badge": "", "name": "", "status": ""})
    c2 = scene_visual.get("card2", {"badge": "", "name": "", "status": ""})

    def hex_to_rgb(h):
        h = h.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return f"{rgb[0]},{rgb[1]},{rgb[2]}"

    mascotStyle = ""
    card1Style = ""
    card2Style = ""
    if "mascot_pos" in scene_visual:
        mascotStyle = f'left: {scene_visual["mascot_pos"]["x"]}px; top: {scene_visual["mascot_pos"]["y"]}px; bottom: auto; right: auto;'
    if "card1_pos" in scene_visual:
        card1Style = f'position: relative; left: {scene_visual["card1_pos"]["x"]}px; top: {scene_visual["card1_pos"]["y"]}px;'
    if "card2_pos" in scene_visual:
        card2Style = f'position: relative; left: {scene_visual["card2_pos"]["x"]}px; top: {scene_visual["card2_pos"]["y"]}px;'

    if theme in ("hook", "reveal"):
        visual_elements_in_wrapper = f"""
      <div class="wrapper-inner">
        <div class="partner-card-1" style="{card1Style}">
          <div class="badge-label" contenteditable="true" data-field="visual.card1.badge">{c1.get('badge','')}</div>
          <div class="partner-name" contenteditable="true" data-field="visual.card1.name">{c1.get('name','')}</div>
          <div class="status-badge" contenteditable="true" data-field="visual.card1.status">{c1.get('status','')}</div>
        </div>
        <div class="partner-card-2" style="{card2Style}">
          <div class="badge-label" contenteditable="true" data-field="visual.card2.badge">{c2.get('badge','')}</div>
          <div class="partner-name alt" contenteditable="true" data-field="visual.card2.name">{c2.get('name','')}</div>
          <div class="status-badge" contenteditable="true" data-field="visual.card2.status">{c2.get('status','')}</div>
        </div>
      </div>
"""
    else:
        visual_elements_in_wrapper = visual_elements

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{theme}</title>
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Be+Vietnam+Pro:wght@400;500;600;700;800&subset=vietnamese&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --primary-color: {p_col};
      --sec-color: {s_col};
      --accent-color: {a_col};
      --primary-glow: {p_glow};
      --sec-glow: {s_glow};
      --accent-glow: {a_glow};
      --accent-gradient: {grad};
      --duration: {frame_dur}s;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      width: 100vw; height: 100vh; overflow: hidden;
      background-color: #040814;
      font-family: 'Be Vietnam Pro', sans-serif;
      color: #ffffff;
      position: relative;
    }}

    .bg-gradient {{
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 100% 70% at 50% 10%, var(--primary-glow) 0%, transparent 60%),
        radial-gradient(ellipse 70% 50% at 10% 60%, var(--sec-glow) 0%, transparent 60%),
        radial-gradient(ellipse 80% 50% at 90% 80%, var(--accent-glow) 0%, transparent 60%),
        linear-gradient(175deg, #040814 0%, #050208 50%, #0c0508 100%);
      z-index: 1;
    }}
    .bg-grid {{
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
      background-size: 80px 80px;
      mask-image: radial-gradient(ellipse 80% 80% at 50% 40%, black 20%, transparent 80%);
      -webkit-mask-image: radial-gradient(ellipse 80% 80% at 50% 40%, black 20%, transparent 80%);
      z-index: 2;
    }}
    .bg-noise {{
      position: absolute;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
      opacity: 0.04;
      z-index: 3;
      pointer-events: none;
    }}

    .container {{
      position: relative;
      width: 100%;
      height: 100%;
      z-index: 10;
      display: grid;
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr auto;
      gap: 3vh;
      padding: 5vh 5vw 8vh 5vw;
    }}

    .video-title-card {{
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(15px);
      -webkit-backdrop-filter: blur(15px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 24px;
      padding: 2.5vh 3vw;
      box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
      opacity: 0;
      transform: translateY(-20px);
      animation: fadeInTitle 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards;
    }}
    @keyframes fadeInTitle {{ to {{ opacity: 1; transform: translateY(0); }} }}

    .video-title-kicker {{
      font-size: clamp(14px, 1.8vmax, 24px);
      font-weight: 700;
      color: var(--accent-color);
      text-transform: uppercase;
      letter-spacing: 3px;
      margin-bottom: 6px;
    }}
    .video-title {{
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 800;
      font-size: clamp(20px, 2.5vmax, 42px);
      line-height: 1.2;
    }}

    .visual-wrapper {{
      grid-row: 2;
      grid-column: 1;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }}

    .karaoke-panel {{
      grid-row: 3;
      grid-column: 1;
      background: rgba(255, 255, 255, 0.02);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 36px;
      padding: 3vh 4vw;
      min-height: clamp(140px, 18vh, 260px);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 20px 50px rgba(0,0,0,0.4);
      position: relative;
      opacity: 0;
      animation: fadeInPanel 0.4s ease-out 0.1s forwards;
    }}
    @keyframes fadeInPanel {{ to {{ opacity: 1; }} }}

    .caption-wrapper {{
      position: relative;
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
    }}

    .caption-chunk {{
      position: absolute;
      inset: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      opacity: 0;
      pointer-events: none;
      animation: showChunk var(--chunk-duration) linear var(--chunk-start) forwards;
      text-align: center;
    }}

    @keyframes showChunk {{
      0% {{ opacity: 0; transform: translateY(15px); }}
      8% {{ opacity: 1; transform: translateY(0); }}
      92% {{ opacity: 1; transform: translateY(0); }}
      100% {{ opacity: 0; transform: translateY(-15px); }}
    }}

    .w {{
      display: inline-block;
      margin: 5px 1vw;
      font-size: clamp(20px, 2.8vmax, 48px);
      font-weight: 700;
      color: rgba(255, 255, 255, 0.25);
      transition: color 0.15s ease, transform 0.15s ease;
      animation: activeWord var(--word-duration, 0.4s) ease var(--d) forwards;
    }}

    @keyframes activeWord {{
      0% {{ color: rgba(255, 255, 255, 0.25); transform: scale(1); }}
      20% {{ color: #ffffff; transform: scale(1.18); text-shadow: 0 0 15px rgba(255, 255, 255, 0.8); }}
      80% {{ color: #ffffff; transform: scale(1.18); }}
      100% {{ color: #ffffff; transform: scale(1); }}
    }}

    .w.key-word {{
      animation: activeKeyWord var(--word-duration, 0.4s) ease var(--d) forwards;
    }}
    @keyframes activeKeyWord {{
      0% {{ color: rgba(255, 255, 255, 0.25); transform: scale(1); }}
      20% {{ color: var(--accent-color); transform: scale(1.22); text-shadow: 0 0 25px var(--accent-color); }}
      80% {{ color: var(--accent-color); transform: scale(1.22); }}
      100% {{ color: var(--accent-color); transform: scale(1); }}
    }}

    .w.danger-word {{
      animation: activeDangerWord var(--word-duration, 0.4s) ease var(--d) forwards;
    }}
    @keyframes activeDangerWord {{
      0% {{ color: rgba(255, 255, 255, 0.25); transform: scale(1); }}
      20% {{ color: #ef4444; transform: scale(1.22); text-shadow: 0 0 25px rgba(239, 68, 68, 1); }}
      80% {{ color: #ef4444; transform: scale(1.22); }}
      100% {{ color: #ef4444; transform: scale(1); }}
    }}

    .mascot {{
      position: absolute;
      bottom: calc(8vh + clamp(140px, 18vh, 260px) + 20px);
      right: 5vw;
      width: clamp(100px, 10vmax, 180px);
      height: auto;
      z-index: 15;
      transform-origin: bottom center;
      filter: drop-shadow(0 15px 30px rgba(0, 0, 0, 0.4));
      opacity: 0;
      animation: fadeInMascot 0.8s ease-out 1.2s forwards, dance 1.6s ease-in-out infinite alternate 2.0s;
    }}
    @keyframes fadeInMascot {{ to {{ opacity: 1; }} }}
    @keyframes dance {{
      0% {{ transform: scale(1) translateY(0) rotate(0deg); }}
      50% {{ transform: scale(1.04) translateY(-10px) rotate(-3deg); }}
      100% {{ transform: scale(0.98) translateY(3px) rotate(3deg); }}
    }}

    .progress-container {{
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 10px;
      background: rgba(255, 255, 255, 0.05);
      z-index: 20;
    }}
    .progress-bar {{
      height: 100%;
      background: var(--accent-gradient);
      width: 0%;
      animation: progress var(--duration) linear forwards;
    }}
    @keyframes progress {{ to {{ width: 100%; }} }}

    .wrapper-inner {{ display: flex; gap: 4%; justify-content: center; width: 100%; height: 100%; align-items: center; }}
    .partner-card-1 {{ width: 48%; max-width: 460px; height: clamp(300px, 45vh, 560px); background: linear-gradient(135deg, rgba({hex_to_rgb(p_col)},0.12), rgba(4,8,20,0.85)); border: 3px solid rgba({hex_to_rgb(p_col)},0.5); border-radius: clamp(20px, 2.5vmax, 40px); padding: clamp(20px, 3vh, 50px); display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 35px 70px rgba({hex_to_rgb(p_col)},0.25); opacity: 0; transform: translateX(-40px); animation: fadeInCard1 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards, pulseCard 3s ease-in-out infinite alternate 1.4s; }}
    .partner-card-2 {{ width: 48%; max-width: 460px; height: clamp(300px, 45vh, 560px); background: linear-gradient(135deg, rgba({hex_to_rgb(s_col)},0.12), rgba(4,8,20,0.85)); border: 3px solid rgba({hex_to_rgb(s_col)},0.5); border-radius: clamp(20px, 2.5vmax, 40px); padding: clamp(20px, 3vh, 50px); display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 35px 70px rgba({hex_to_rgb(s_col)},0.25); opacity: 0; transform: translateX(40px); animation: fadeInCard2 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.8s forwards, pulseCard2 3s ease-in-out infinite alternate 1.9s; }}
    @keyframes fadeInCard1 {{ to {{ opacity: 1; transform: translateX(0); }} }}
    @keyframes fadeInCard2 {{ to {{ opacity: 1; transform: translateX(0); }} }}
    @keyframes pulseCard {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-15px); }} }}
    @keyframes pulseCard2 {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-15px); }} }}
    .badge-label {{ font-size: clamp(14px, 1.8vmax, 30px); font-weight: 800; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 2px; }}
    .partner-name {{ font-family: 'Barlow Condensed', sans-serif; font-size: clamp(28px, 4vmax, 65px); font-weight: 900; color: var(--accent-color); text-shadow: 0 0 30px rgba(251,191,36,0.6); line-height: 1.1; margin: 2vh 0; }}
    .partner-name.alt {{ color: #ef4444; text-shadow: 0 0 30px rgba(239,68,68,0.6); }}
    .status-badge {{ align-self: flex-start; background: rgba(255,255,255,0.05); border: 2px solid rgba(255,255,255,0.2); color: #fff; padding: 0.8vh 2vw; border-radius: 20px; font-weight: 800; font-size: clamp(12px, 1.5vmax, 26px); }}

    {visual_html}
  </style>
</head>
<body>
  <div class="bg-gradient"></div>
  <div class="bg-grid"></div>
  <div class="bg-noise"></div>

  <div class="container">
    <div class="video-title-card">
      <div class="video-title-kicker" contenteditable="true" data-field="kicker">{kicker}</div>
      <div class="video-title" contenteditable="true" data-field="title">{title}</div>
    </div>
    
    <div class="visual-wrapper">
      {visual_elements_in_wrapper}
    </div>

    <div class="karaoke-panel">
      <div class="caption-wrapper">
{chunks_html}      </div>
    </div>
  </div>

  <img class="mascot" src="/assets/mascot.png" alt="Mascot" style="{mascotStyle}" />
  <div class="progress-container"><div class="progress-bar"></div></div>

  <!-- Interactive script -->
  <script>
    document.addEventListener('DOMContentLoaded', () => {{
      document.querySelectorAll('[contenteditable="true"]').forEach(el => {{
        el.style.outline = 'none';
        el.style.borderRadius = '4px';
        el.addEventListener('focus', () => {{
          el.style.boxShadow = '0 0 10px rgba(120, 87, 255, 0.4)';
          el.style.background = 'rgba(120, 87, 255, 0.05)';
        }});
        el.addEventListener('blur', () => {{
          el.style.boxShadow = 'none';
          el.style.background = 'none';
          const field = el.dataset.field;
          const text = el.innerText.trim();
          if (window.parent && typeof window.parent.onIframeEdit === 'function') {{
            window.parent.onIframeEdit(field, text);
          }}
        }});
        el.addEventListener('keydown', (e) => {{
          if (e.key === 'Enter') {{
            e.preventDefault();
            el.blur();
          }}
        }});
      }});

      const setupDrag = (el, saveKey, isAbsolute) => {{
        if (!el) return;
        let active = false;
        let startX = 0, startY = 0;
        let initialX = 0, initialY = 0;
        
        if (isAbsolute) {{
          initialX = parseFloat(el.style.left) || el.offsetLeft || 0;
          initialY = parseFloat(el.style.top) || el.offsetTop || 0;
        }} else {{
          initialX = parseFloat(el.style.left) || 0;
          initialY = parseFloat(el.style.top) || 0;
        }}
        
        el.style.cursor = 'grab';
        
        const dragStart = (e) => {{
          if (e.target.closest('[contenteditable="true"]')) return;
          active = true;
          el.style.cursor = 'grabbing';
          const clientX = e.type === "touchstart" ? e.touches[0].clientX : e.clientX;
          const clientY = e.type === "touchstart" ? e.touches[0].clientY : e.clientY;
          startX = clientX - initialX;
          startY = clientY - initialY;
        }};
        
        const dragEnd = () => {{
          if (!active) return;
          active = false;
          el.style.cursor = 'grab';
          if (window.parent && typeof window.parent.onIframeMove === 'function') {{
            window.parent.onIframeMove(saveKey, Math.round(initialX), Math.round(initialY));
          }}
        }};
        
        const drag = (e) => {{
          if (!active) return;
          e.preventDefault();
          const clientX = e.type === "touchmove" ? e.touches[0].clientX : e.clientX;
          const clientY = e.type === "touchmove" ? e.touches[0].clientY : e.clientY;
          initialX = clientX - startX;
          initialY = clientY - startY;
          if (isAbsolute) {{
            el.style.left = initialX + 'px';
            el.style.top = initialY + 'px';
            el.style.bottom = 'auto';
            el.style.right = 'auto';
          }} else {{
            el.style.left = initialX + 'px';
            el.style.top = initialY + 'px';
          }}
        }};
        
        el.addEventListener('mousedown', dragStart);
        window.addEventListener('mouseup', dragEnd);
        window.addEventListener('mousemove', drag);
        el.addEventListener('touchstart', dragStart, {{ passive: false }});
        window.addEventListener('touchend', dragEnd);
        window.addEventListener('touchmove', drag, {{ passive: false }});
      }};

      setupDrag(document.querySelector('.mascot'), 'mascot', true);
      setupDrag(document.querySelector('.partner-card-1'), 'card1', false);
      setupDrag(document.querySelector('.partner-card-2'), 'card2', false);
    }});
  </script>
</body>
</html>"""
    return html_content

if __name__ == '__main__':
    main()
