# Hướng Dẫn Chạy & Tùy Biến Video Marketing (Tiếng Việt)

Tài liệu này hướng dẫn bạn cách clone dự án này từ GitHub về, điền kịch bản mới của bạn vào và kết xuất (render) thành video MP4 dọc hoàn chỉnh (tỷ lệ 9:16 cho TikTok/Reels) một cách tự động.

---

## 🛠️ 1. Các công nghệ & công cụ đã sử dụng để tạo ra video
Video marketing này được xây dựng trên bộ công cụ mã nguồn mở **html-video** kết hợp trí tuệ nhân tạo:
* **TTS (Text-to-Speech) Giọng Nói:** Sử dụng thư viện **VieNeu-TTS** để sinh giọng đọc thuyết minh tiếng Việt tự nhiên chất lượng cao, clone từ file giọng nói mẫu.
* **Giao diện & Đồ họa chuyển động:** Viết hoàn toàn bằng **HTML5 & CSS3** (mesh gradients, grid/flex layout, keyframe animations, dynamic data flow pipelines, active word highlights) chạy mượt mà 60fps trên trình duyệt.
* **Engine Kết xuất (Rendering):** Trình duyệt không đầu **Playwright Chromium** để quay màn hình trang HTML thành định dạng WebM.
* **Xử lý Đa phương tiện:** **FFmpeg & FFprobe** để đo thời lượng âm thanh, tăng tốc giọng thuyết minh (atempo), chuẩn hóa âm lượng (loudnorm EBU R128), cắt lead-in và ghép (concat) các phân cảnh thành video MP4 hoàn chỉnh kèm nhạc nền.
* **Điều phối & Tự động hóa:** Script **Python** (`generate_video.py`) kết nối toàn bộ quy trình: TTS -> sync duration -> update HTML/project.json -> audio mix.

---

## 🚀 2. Các bước dành cho người khác để tải về và chạy

### Bước 1: Chuẩn bị môi trường hệ thống
Đảm bảo máy tính của bạn đã cài đặt các công cụ sau:
1. **Node.js** (Phiên bản >= 22)
2. **pnpm** (Trình quản lý package của Node.js: `npm install -g pnpm`)
3. **Python** (Phiên bản >= 3.10)
4. **FFmpeg & FFprobe** (Đã được thêm vào biến môi trường `PATH` của hệ thống)
5. Thư viện **VieNeu-TTS** (Được tải về từ kho lưu trữ của bạn)

### Bước 2: Clone dự án và Cài đặt dependencies
Tải mã nguồn về máy và cài đặt các thư viện cần thiết:
```bash
# Cài đặt các package Node.js (bao gồm Playwright Chromium)
pnpm install

# Build các adapter local
pnpm build
```

### Bước 3: Cấu hình biến môi trường
1. Nhân bản file `.env.example` thành `.env`:
   ```bash
   cp .env.example .env
   ```
2. Mở file `.env` lên và điền đường dẫn tới thư mục **VieNeu-TTS** trên máy của bạn:
   ```env
   VIENEU_TTS_PATH=D:\Đường_dẫn_tới\VieNeu-TTS
   ```

### Bước 4: Tùy biến kịch bản
Nếu bạn muốn đổi nội dung thoại và phụ đề:
1. **Sửa file HTML phân cảnh (nếu cần):** Các file HTML nằm trong thư mục `.html-video/projects/proj_0d93e26f-9b8/frames/` (từ `01-hook.html` đến `05-cta.html`). Sửa lại các chữ trong thẻ `<span class="w">` để khớp với nội dung kịch bản mới của bạn.
2. **Sửa kịch bản trong Script Python:** Mở file `generate_video.py` ra và tìm biến `PROJECT_CONFIG["scenes"]`. Thay đổi các câu thoại `text` của từng scene tương ứng với chữ bạn đã viết trong HTML.

### Bước 5: Chạy đồng bộ và Kết xuất Video
1. **Chạy script Python** để sinh giọng đọc thuyết minh mới và tự động cập nhật thời lượng cho video:
   ```bash
   python generate_video.py
   ```
2. **Chạy lệnh render** để xuất video MP4 dọc cuối cùng:
   ```bash
   node packages/cli/dist/bin.js project-render proj_0d93e26f-9b8 --output output.mp4
   ```
Video thành phẩm sẽ được lưu tại file `output.mp4` ở thư mục gốc của dự án.
