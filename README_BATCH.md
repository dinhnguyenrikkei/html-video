# Hướng dẫn Chạy Quy Trình Build Video Chiến Dịch (Batch Campaign)

Tài liệu này hướng dẫn cách thiết lập, cài đặt và chạy hệ thống tự động sinh video ngắn (TikTok/Reels 9:16) từ kịch bản kịch bản có sẵn bằng cách sử dụng công cụ **html-video** kết hợp với bộ nhân bản giọng nói tiếng Việt **VieNeu-TTS** và phụ đề hiệu ứng Karaoke.

---

## 🛠️ Yêu cầu Hệ thống (Prerequisites)

Hệ thống hoạt động trực tiếp (Local) trên máy tính của bạn và yêu cầu cài đặt sẵn các môi trường sau:

1. **Node.js (v18 trở lên)**:
   Dùng để chạy adapter render giao diện HTML sang khung hình video (Hyperframes engine).
2. **Python (v3.10 trở lên)**:
   Dùng để chạy bộ điều phối kịch bản, sinh file âm thanh và xử lý trung gian.
3. **FFmpeg**:
   Dùng để trộn tiếng, tăng tốc giọng đọc và ghép hình ảnh thành MP4 hoàn thiện. Đường dẫn nhị phân mặc định được cấu hình sẵn trong mã nguồn.

---

## 📥 Thiết lập và Cài đặt (Setup)

Làm theo các bước sau nếu bạn là người dùng mới (User mới):

### Bước 1: Cài đặt Node Packages (Rendering Engine)
Mở PowerShell tại thư mục dự án `d:\AI\Repos\html-video` và chạy lệnh cài đặt:
```powershell
pnpm install
```

### Bước 2: Cài đặt Python Dependencies
Chạy lệnh sau để cài đặt các thư viện Python cần thiết cho bộ xử lý âm thanh, Edge-TTS và VieNeu-TTS:
```powershell
pip install edge-tts onnxruntime numpy soundfile soxr tokenizers huggingface_hub PyYAML sea-g2p
```

> [!NOTE]
> Bộ nhân bản giọng nói **VieNeu-TTS** đã được tích hợp trực tiếp bên trong thư mục [vieneu/](file:///d:/AI/Repos/html-video/vieneu). Bạn không cần phải tải thêm thư viện ngoài, giúp toàn bộ repo có tính độc lập và di động cao.

---

## 🎬 Cách chạy Sinh Video (Usage)

Để chạy tạo video cho toàn bộ chiến dịch (ví dụ chiến dịch **AI-Native Data Engineer** từ Ngày 1 đến Ngày 4), chạy lệnh điều phối sau:

```powershell
python scripts/batch_video_builder.py scripts/inputs/ai_native_de_campaign_scripts.json
```

### 📝 Cấu trúc file Kịch bản (JSON Config)
Mỗi chiến dịch được lưu trữ dưới dạng một JSON Array. Các trường quan trọng:
- `projectId`: Tên định danh của dự án video (Ví dụ: `proj_de_camp_ngay_01`).
- `aspectRatio`: Định dạng hiển thị (mặc định `9:16` cho định dạng dọc).
- `ref_audio`: Đường dẫn đến file âm thanh giọng nói mẫu dùng để clone (Ví dụ: `D:/AI/Rikkei_Edu_agent/marketing-video-maker/test_voice_clone.wav`).
- `scenes`: Danh sách các phân cảnh chứa kịch bản voiceover, layout tương ứng (`hook`, `reveal`, `learning-path`, `stats`, `cta`), tiêu đề và mô tả.

---

## 🌟 Các Tính năng Cải tiến & Layout Giao diện

Hệ thống đã được nâng cấp thiết kế đồ họa sống động và mượt mà hơn rất nhiều:

1. **Độ mượt hình ảnh & Chuyển cảnh (Visual Excellence)**:
   - Các quả cầu ánh sáng chuyển động tự do vô hạn (Float infinite path) làm nền sinh động.
   - Hiệu ứng làm mờ kính cường lực (Glassmorphism saturate) kết hợp viền sáng neon tinh tế (`.glow-border`).
   - Timings được tối ưu hóa: Chuyển cảnh ngay lập tức khi giọng nói kết thúc (`SLOT - 0.45s`).
   - Trực quan hóa dữ liệu bằng SVG (SVG circular gauge) và các node liên kết sơ đồ ống dẫn (pipeline) động.

2. **Phụ đề Karaoke Chuyên nghiệp (Karaoke Subtitles)**:
   - Thay vì đổi màu chữ thụ động, hiệu ứng Karaoke mới sẽ **stagger từng từ một**:
     - *Từ đang đọc (Active)*: Phóng to `1.12x`, đổi sang màu trắng sáng và tỏa ánh sáng neon (`textShadow`) rực rỡ theo tone chủ đạo.
     - *Từ đã đọc xong (Read)*: Thu nhỏ về `1.0` và chuyển sang màu trắng mờ `rgba(255,255,255,0.9)` dễ đọc.
     - *Từ chuẩn bị đọc (Upcoming)*: Mờ mờ ẩn hiện `rgba(255,255,255,0.25)` để người dùng tập trung.

3. **Cắt bỏ khoảng lặng (Silence Trimming)**:
   - Tự động cắt bỏ các khoảng lặng trống ở đuôi âm thanh sinh ra từ VieNeu-TTS (tránh hiện tượng video chạy không tiếng ở cuối).

4. **Tăng tốc giọng đọc tự động**:
   - Tự động điều chỉnh tốc độ clone lên `1.25x` thông qua bộ lọc FFmpeg `atempo` nhằm tăng độ lôi cuốn cho các video ngắn.
