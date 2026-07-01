# Hướng dẫn đóng gói và di chuyển Quy trình Tạo Video Tiếng Việt (Vietnamese Video Generator)

Thư mục này đóng gói skill cấu hình hệ thống và hướng dẫn quy trình tạo video tiếng Việt chất lượng cao (TikTok & TVC) phục vụ cho dự án `html-video`. Khi bạn chuyển sang máy tính mới, hãy làm theo hướng dẫn dưới đây để khôi phục và tiếp tục sử dụng quy trình này.

---

## 📦 Danh sách các thành phần được đóng gói

1. **Skill Global**:
   - `vietnamese-video-generator/`: Thư mục chứa file định nghĩa kỹ năng `SKILL.md` để hướng dẫn AI cách tính toán thời lượng, đồng bộ khớp giọng đọc, mix âm thanh, áp dụng thiết kế typography, hiệu ứng animation và xuất video bằng CLI.

2. **Các Script thực thi quy trình (nằm tại thư mục gốc của dự án)**:
   - [generate_vietnamese_voiceover.py](file:///d:/AI/Repos/html-video/generate_vietnamese_voiceover.py): Script sử dụng `edge-tts` (giọng đọc AI miễn phí chất lượng cao của Microsoft) để tạo thuyết minh tiếng Việt tự động cho các cảnh, đo thời gian bằng `ffprobe`, đồng bộ hóa thời lượng vào `project.json` và trộn âm thanh bằng `ffmpeg`.
   - [generate_elevenlabs_voiceover.py](file:///d:/AI/Repos/html-video/generate_elevenlabs_voiceover.py): Script nâng cao sử dụng API của ElevenLabs để tạo giọng thuyết minh chất lượng studio chuyên nghiệp, đồng bộ và sinh file transcript dạng SRT/TXT/JSON.
   - [run_elevenlabs.ps1](file:///d:/AI/Repos/html-video/run_elevenlabs.ps1): Script PowerShell giúp chạy toàn bộ quy trình ElevenLabs (Sinh giọng đọc thuyết minh tiếng Việt + Render video) chỉ bằng một lệnh duy nhất.
   - [start-studio-gemini.ps1](file:///d:/AI/Repos/html-video/start-studio-gemini.ps1): Script PowerShell để khởi động môi trường HTML-Video Studio sử dụng API Key của Gemini.

---

## 🚀 Hướng dẫn thiết lập trên máy tính mới

### Bước 1: Cài đặt các Skill Global vào hệ thống AI của máy mới

Hãy copy thư mục `vietnamese-video-generator` trong thư mục `skillglobal` này vào thư mục chứa skill global của AI trên máy tính mới:
- **Đường dẫn thông thường**: `C:\Users\<Tên_User_Mới>\.gemini\antigravity\skills\` (hoặc thư mục global tương ứng của AI Agent của bạn).

Sau khi copy, AI Agent trên máy mới sẽ tự động nhận diện kỹ năng `@vietnamese-video-generator` và tuân thủ các quy tắc thiết kế/đồng bộ giọng đọc tiếng Việt.

### Bước 2: Cài đặt các công cụ bổ trợ (Dependencies)

Quy trình yêu cầu máy tính mới phải được cài đặt:
1. **Python**: Đảm bảo Python đã được cài đặt và thêm vào PATH.
2. **edge-tts**: Thư viện Python để tổng hợp giọng nói của Microsoft.
   ```powershell
   pip install edge-tts
   ```
3. **FFmpeg & FFprobe**:
   - Cài đặt FFmpeg đầy đủ bản build (full build).
   - Hãy chắc chắn rằng bạn cập nhật đường dẫn của `ffmpeg.exe` và `ffprobe.exe` trong các file script (`generate_vietnamese_voiceover.py` dòng 136-166, `generate_elevenlabs_voiceover.py` dòng 28-29, `run_elevenlabs.ps1` dòng 12) hoặc thêm chúng vào biến môi trường **PATH** của hệ thống.
4. **Node.js & Pnpm**:
   - Cài đặt Node.js mới nhất.
   - Chạy lệnh cài đặt các package trong dự án `html-video`:
     ```powershell
     pnpm install
     pnpm -r build
     ```

### Bước 3: Chạy quy trình tạo và render video

- **Sử dụng Edge-TTS (Miễn phí)**:
  ```powershell
  python generate_vietnamese_voiceover.py
  ```
  *(Script sẽ tự động tạo giọng đọc thuyết minh, đồng bộ độ dài của từng frame trong `project.json` để khớp với giọng nói và mix các phân đoạn thành một audio duy nhất).*

- **Sử dụng ElevenLabs (Chuyên nghiệp)**:
  ```powershell
  # Cung cấp ElevenLabs API Key để chạy quy trình
  .\run_elevenlabs.ps1 <YOUR_ELEVENLABS_API_KEY>
  ```

- **Mở Studio để chỉnh sửa giao diện trực quan**:
  ```powershell
  .\start-studio-gemini.ps1
  ```
  Sau đó truy cập địa chỉ `http://localhost:3071` trên trình duyệt để tinh chỉnh các hiệu ứng CSS, Kinetic Typography, Glassmorphism và xuất video.
