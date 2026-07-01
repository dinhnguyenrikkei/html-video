# Hướng Dẫn Sử Dụng & Thiết Lập Dự Án Sinh Video Tự Động (Với Antigravity)

Bản hướng dẫn này giúp bạn dễ dàng cài đặt môi trường và kết xuất video tiếp thị ngắn (dọc & ngang) chất lượng cao sử dụng **giọng nói thuyết minh nhân bản** và **hệ thống tự động hóa hoàn toàn**.

Hệ thống giờ đây đã được nâng cấp để làm việc trực tiếp với trợ lý AI **Antigravity**. Bạn không cần phải chạy từng lệnh thủ công nữa!

---

## 🗃️ 1. Cấu Trúc Tài Nguyên (Portable Assets)

Để dự án có thể chạy ngay khi tải sang máy mới, các tài nguyên cốt lõi đã được đặt sẵn trong kho mã nguồn:
* **Thư mục tài nguyên chung:** `shared_assets/`
* **Giọng mẫu mặc định:** `shared_assets/voice_preview.mp3` (Giọng chuẩn, truyền cảm để nhân bản).
* **Nhạc nền mặc định:** `shared_assets/background_music.mp3`
* **Ảnh Mascot (Tùy chọn):** `shared_assets/mascot.png`
* **Bộ quy tắc thiết kế:** `.agents/skills/video_design_system/SKILL.md` (Antigravity sẽ tự đọc file này để thiết kế video).

---

## 🚀 2. Prompt Tự Động Setup Môi Trường Bằng AI (Khuyên dùng)

Khi bạn chuyển dự án sang máy tính mới, **bạn không cần phải tự gõ lệnh cài đặt**. Hãy mở chat với **Antigravity**, copy và dán chính xác đoạn Prompt sau để AI tự động cấu hình toàn bộ máy cho bạn:

```markdown
Chào Antigravity, tôi vừa tải dự án này sang máy tính mới và chưa cài đặt môi trường. Hãy tự động thực hiện các bước sau trên hệ thống của tôi:

1. Thiết lập Node.js & Cài đặt thư viện:
   - Chạy lệnh `pnpm install` và `pnpm build` tại thư mục gốc dự án để chuẩn bị bộ kết xuất hình ảnh.
2. Kiểm tra FFmpeg & FFprobe:
   - Xác minh xem `ffmpeg` và `ffprobe` đã có sẵn trong PATH chưa. Nếu chưa, hãy tìm cách cài đặt (qua winget) hoặc hướng dẫn tôi tải.
3. Tạo môi trường ảo Python & Cài thư viện AI:
   - Tạo một môi trường ảo Python `.venv` tại thư mục gốc dự án: `python -m venv .venv`
   - Kích hoạt `.venv` và cài đặt các thư viện: `edge-tts`, `vieneu` và `onnxruntime-gpu` (nếu máy tôi có card NVIDIA, nếu không thì dùng `onnxruntime`).
4. Kiểm tra mã nguồn:
   - Đảm bảo file `scripts/batch_video_builder.py` và thư mục `shared_assets/` tồn tại.

Hãy tự động thực thi các bước trên và báo cáo kết quả khi môi trường đã sẵn sàng để render video!
```

---

## 🎬 3. Prompt Yêu Cầu Antigravity Tạo Video (Từ A-Z)

Hệ thống mới sử dụng `batch_video_builder.py` để tự động hóa toàn bộ quy trình (sinh giọng nói -> đo thời lượng -> tạo HTML -> kết xuất MP4).

Bạn chỉ cần quăng kịch bản thô hoặc chủ đề cho Antigravity bằng Prompt sau:

```markdown
@antigravity Hãy giúp tôi tạo một video từ [Chủ đề / Kịch bản sau].

Yêu cầu:
1. Đọc kịch bản, phân tích đối tượng và chọn Theme màu sắc / Layout phù hợp từ `SKILL.md`.
2. Chuyển đổi kịch bản sang định dạng JSON mảng đúng chuẩn của hệ thống (chia 4-5 phân cảnh: Hook, Reveal, Analysis, CTA).
3. Đảm bảo tuân thủ nghiêm ngặt các quy tắc Anti-AI-Slop trong `AGENTS.md` (phiên âm việt hóa voiceover, font chữ tương phản, GSAP animation).
4. Lưu file JSON vào `scripts/inputs/<ten_du_an>.json`.
5. Tự động chạy lệnh: `.\.venv\Scripts\python.exe scripts/batch_video_builder.py scripts/inputs/<ten_du_an>.json`
6. Trả về đường dẫn file MP4 trong thư mục `exports/` khi hoàn thành.

[Dán chủ đề hoặc kịch bản chữ thô của bạn tại đây]
```

---

## 🛠️ 4. Hướng Dẫn Cài Đặt Thủ Công (Dành cho Dev)

Nếu bạn muốn tự tay cài đặt thay vì dùng AI:

1. **Cài Node.js & pnpm:**
   ```bash
   npm install -g pnpm
   pnpm install
   pnpm build
   ```
2. **Cài FFmpeg:** Tải và thêm `ffmpeg/bin` vào System PATH.
3. **Cài Python & VieNeu:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install edge-tts vieneu
   ```
4. **Chạy Render:**
   Tạo file `scripts/inputs/my_video.json` theo cấu trúc mảng.
   ```powershell
   .\.venv\Scripts\python.exe scripts/batch_video_builder.py scripts/inputs/my_video.json
   ```
   Video sẽ được xuất ra tại thư mục `exports/`.

---

## ⚡ 5. Tối Ưu Hóa Hiệu Năng (GPU)

Quá trình sinh giọng nói bằng VieNeu-TTS tốn khá nhiều CPU. Nếu máy bạn có card đồ họa **NVIDIA**:

1. Mở môi trường ảo `.venv`:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. Gỡ bản CPU, cài bản GPU của ONNX:
   ```powershell
   pip uninstall onnxruntime -y
   pip install onnxruntime-gpu
   ```
Việc này sẽ giảm 90% tải CPU và tăng tốc độ sinh giọng nói lên 5-10 lần!
