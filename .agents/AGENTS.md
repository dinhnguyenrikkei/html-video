# Quy tắc Tự động Sinh Video (Video Generation Rules)

Chào Antigravity, khi làm việc trong dự án này, bạn hãy **luôn luôn tuân thủ nghiêm ngặt** các quy tắc dưới đây mỗi khi người dùng yêu cầu tạo video mới từ kịch bản:

## 1. Cấu trúc JSON Kịch Bản (JSON Config Structure)
Mọi kịch bản đều phải được bạn dịch sang định dạng JSON mảng (JSON Array) tương thích với `batch_video_builder.py`.
- **Chủ đề & Màu sắc Toàn cục (Global Theme):** Bạn hoàn toàn tự do tạo ra tông màu cho video. Bạn có thể sử dụng các Theme có sẵn (như `Tech/Cyberpunk`, `Finance/Wealth`, `Calm/Education`, `Minimalist/Dark`, `Vibrant/Youth`, `Hook/Danger`) HOẶC tự đẻ ra một bảng màu HEX hoàn toàn mới tuỳ vào nội dung kịch bản (Truyền thẳng object `{"primary": "#...", "accent": "#...", ...}` vào trường `"theme"` của dự án).
- **Tùy chỉnh Từng Khung Hình (Per-scene Styling):** Bạn được trao quyền tự do sáng tạo cao nhất. Nếu thấy phù hợp, bạn có thể tự chèn trường `"theme"` (Tên theme hoặc Mã màu HEX tự do kiểu `{"primary":"#...","accent":"#..."}`) và hiệu ứng (`"enter_anim"`, `"exit_anim"`) thẳng vào cấu hình của **từng `scene` riêng biệt** để làm video sinh động hơn, không cần phải bị gò bó bởi một form cố định.
- **Mặc định Giọng:** `voiceGender` là `MALE` tùy ngữ cảnh.
- **Mặc định Âm thanh (Nhạc & Giọng đọc):** Bắt buộc khai báo 2 trường sau:
  - `ref_audio`: `d:/AI_rikkei/html-video-main/shared_assets/voice_preview.mp3` (Đây là file mẫu giọng mặc định. Để đổi giọng nam/nữ hoặc giọng của chính người dùng, chỉ cần thay bằng đường dẫn file MP3 mẫu giọng khác, AI TTS sẽ tự động clone 100% theo mẫu đó).
  - `backgroundMusic`: `d:/AI_rikkei/html-video-main/shared_assets/background_music.mp3` (Nhạc nền mặc định).
- **Layouts Phân cảnh (Scenes):** Phải là một trong các giá trị: `hook`, `reveal`, `learning-path`, `stats`, `cta`. Cố gắng chia kịch bản thành đúng 4-5 phân cảnh (Scenes) theo flow: Mở bài (Hook) -> Vấn đề (Reveal) -> Phân tích (Stats/Learning-path) -> Chốt (CTA).
- **Kho Icon (FontAwesome):** Khi viết nội dung trường `elements` cho các layout (`reveal`, `learning-path`, `card-list`), bạn có thể sử dụng icon từ FontAwesome 6 (ví dụ: `fa-solid fa-server`, `fa-solid fa-robot`, `fa-solid fa-chart-line`). Cú pháp: `"Tiêu đề | Mô tả | <Tên Class FontAwesome>"`. Ví dụ: `"Hiệu năng cao | Xử lý hàng triệu request | fa-solid fa-rocket"`. Nếu không có FontAwesome, hệ thống sẽ dùng Emoji mặc định.

## 2. Tiền xử lý Văn bản cho TTS (Text Pre-processing)
AI VieNeu-TTS sẽ đọc tiếng Việt rất hay nhưng dễ vấp tiếng Anh. Bắt buộc phải **việt hóa phát âm** các thuật ngữ IT trong trường `voiceover`:
- `RAM` -> `ram`
- `Gigabyte`, `GB` -> `ghi ga bai`
- `Kilobyte`, `KB` -> `ki lô bai`
- `F5` -> `ép năm`
- `Web/App` -> `web app`
- Các từ tiếng Anh khác nên viết cách ra hoặc phiên âm tương đối để AI đọc không bị ngọng.
- **TUYỆT ĐỐI CHÚ Ý:** Việc phiên âm việt hóa NÀY CHỈ ĐƯỢC ÁP DỤNG DUY NHẤT CHO TRƯỜNG `voiceover`. Tuyệt đối KHÔNG viết sai chính tả, không phiên âm ở các trường hiển thị chữ lên video như `headline`, `subtitle`, `elements` và `caption`.

## 2.5 Subtitles (Chạy Chữ)
Hệ thống nay đã hỗ trợ hiệu ứng "chạy chữ" (karaoke-style subtitles) cho mỗi phân cảnh để video sinh động hơn và không bị nhàm chán khi Audio dài.
- Bạn phải LUÔN LUÔN tạo thêm trường `"caption"` trong JSON của từng `scene` chứa **nguyên văn chuẩn (không phiên âm)** nội dung mà voiceover sẽ đọc. 
- Nếu không có trường `caption`, hệ thống sẽ lấy `voiceover` làm chữ chạy, dẫn đến việc hiện các chữ phiên âm ngớ ngẩn (như `ghi ga bai`) lên màn hình!

## 3. Quy trình Tự động (Execution Workflow)
Khi người dùng đưa một kịch bản thô hoặc chỉ đưa một CHỦ ĐỀ:
1. **Phân tích & Thiết kế:** Tự động phân tích, nghĩ ra các Hook hấp dẫn, chọn Theme phù hợp và thiết kế kịch bản chi tiết (chia thành 4-5 cảnh: Hook, Reveal, Learning-path, CTA).
2. **Review:** Trình bày kịch bản đã thiết kế (dạng Markdown hoặc Artifact) để người dùng ĐỌC VÀ DUYỆT.
3. **Thực thi Một lèo (One-shot Execution):** CHỈ KHI người dùng đồng ý kịch bản, bạn sẽ tự động chạy 1 vòng hoàn thiện từ A-Z mà KHÔNG HỎI THÊM:
   - Định danh `projectId` (trong JSON) phải là viết liền không dấu, có ý nghĩa (vd: `"video_bao_mat"`).
   - Tạo file JSON lưu vào thư mục `scripts/inputs/` (vd: `scripts/inputs/video_bao_mat.json`).
   - Gọi lệnh `python scripts/batch_video_builder.py scripts/inputs/...` chạy ngầm.
4. **Ngoại lệ (Exceptions):** CHỈ dừng lại hỏi ý kiến người dùng khi có những vấn đề RẤT KHẨN CẤP (như: sửa file core hệ thống, cảnh báo bộ nhớ/phần cứng, thay đổi cấu trúc data quan trọng).
5. **Kết quả:** Khi kết xuất xong, trả về link file MP4 trong thư mục `exports/` cho người dùng xem.

## 4. Kiến trúc Hoạt ảnh (Animation Architecture)
- **TUYỆT ĐỐI KHÔNG DÙNG CSS `@keyframes` (Infinite Animations):** Vì hệ thống render Video (Remotion/Playwright) sẽ tua thời gian bằng cách can thiệp vào `gsap.timeline`. Bất kỳ hiệu ứng CSS nào (như nhấp nháy, lướt sáng) sẽ bị đóng băng hoặc không chụp lại được trong Video.
- **GSAP Là Bắt Buộc:** Mọi hiệu ứng động (từ entrance animation đến vòng lặp vô tận như tỏa sáng/nhịp thở) phải được viết bằng GSAP và nhúng vào biến `tl` của timeline chính. Ví dụ: `tl.to('.icon', {scale: 1.1, repeat: 10, yoyo: true}, 0);`.

## 5. Hệ thống Thiết kế Giao diện (UI Design System)
Tài liệu thiết kế đầy đủ được lưu tại: `.agents/skills/video_design_system/SKILL.md`.
**BẮT BUỘC** tham khảo file đó trước khi render bất kỳ Video nào. File đó chứa:
- Bảng màu Theme (10 preset + custom HEX)
- Quy tắc Typography cho Tiếng Việt (line-height, padding-top)
- Đặc tả Component (Icon Box, Icon Badge, Glass Card, Timeline Bar)
- Checklist thiết kế bắt buộc trước khi render

## 6. Chống AI-Slop (Anti-AI-Default Rules)
Những bài học rút ra từ Taste-Skill v2 và HTML-Anything để đảm bảo Video không bị "máy móc", "template hóa":

### 6.1. Brief Inference — Đọc hiểu Kịch bản Trước
Trước khi nhảy vào code, phải **suy luận** ngữ cảnh:
- **Loại nội dung:** Giáo dục / So sánh / Quảng cáo / Tuyển dụng / Tin tức?
- **Đối tượng:** Sinh viên / Dev chuyên nghiệp / Quản lý / Người mới?
- **Cảm xúc mục tiêu:** Tò mò / Lo lắng / Hứng khởi / Tin tưởng?
→ Từ đó mới chọn Theme, Animation intensity, và giọng văn phù hợp.

### 6.2. Chống Mặc định Lười (Anti-Default Discipline)
Những thứ KHÔNG ĐƯỢC làm tự động vì chúng là "dấu hiệu AI":
- ❌ Luôn luôn dùng cùng một Theme cho mọi video.
- ❌ Mọi Icon đều dùng Emoji mặc định thay vì FontAwesome.
- ❌ Mọi cảnh đều dùng cùng enter/exit animation (`fadeUp`/`fadeUp`).
- ❌ Headline quá dài (> 8 từ) hoặc quá chung chung ("Hãy bắt đầu ngay!").
- ❌ Subtitle dài dằng dặc, phải cắt gọn ≤ 25 từ.
- ❌ Dùng số liệu giả mạo (92%, 4.1x) mà không có nguồn.

### 6.3. Đa dạng Layout (Layout Diversification)
- **KHÔNG lặp Layout:** Trong 1 video 4-5 cảnh, KHÔNG được dùng cùng 1 layout 2 lần liên tiếp.
- **Xen kẽ ngang-dọc:** Nếu cảnh 2 là liệt kê dọc, cảnh 3 nên là thanh ngang hoặc grid.
- **Mỗi cảnh 1 trọng tâm duy nhất:** Không nhồi nhét quá nhiều elements vào 1 cảnh.

### 6.4. Motion phải có Lý do (Motivated Motion) & Phong cách "Snappy"
Trước khi thêm hiệu ứng, tự hỏi: "Animation này TRUYỀN ĐẠT điều gì?"
- ✅ **Hợp lệ:** Thu hút chú ý (Hook glitch), Tiết lộ tuần tự (Learning-path stagger), Nhấn mạnh số liệu (Stats counter).
- ❌ **Không hợp lệ:** "Vì trông nó cool" — cái đó là AI-slop.
- **Phong cách Snappy:** Mọi animation xuất hiện phải ưu tiên dùng đường cong `back.out(1.2)` hoặc `expo.out` và khoảng trễ (stagger) cực ngắn `~0.1s` để luồng nội dung trôi chảy, nảy (bouncy) nhưng dứt khoát như UI hiện đại, tuyệt đối không dùng easing chậm chạp rề rà.

### 6.5. Tương phản Tối đa (Maximum Contrast — Quy tắc Sắt)
- Nền Video luôn tối đen (`#03050a`). Mọi nội dung PHẢI nổi bật rõ ràng.
- Icon Box: Nền **Solid Gradient rực rỡ** (primary → accent), KHÔNG trong suốt.
- Icon: `color: #fff`, KHÔNG để mặc định.
- Đổ bóng: `box-shadow` đồng màu Primary, KHÔNG dùng `rgba(0,0,0,...)`.

### 6.6. Nội dung hiển thị PHẢI chuẩn mực
- Chữ trên màn hình (`headline`, `subtitle`, `elements`) viết ĐÚNG chính tả tiếng Anh/IT.
- Phiên âm Việt hóa CHỈ cho trường `voiceover` (dành cho TTS đọc).
- Không dùng filler words: "Tuyệt vời", "Siêu đỉnh", "Cực kỳ". Dùng động từ cụ thể.

