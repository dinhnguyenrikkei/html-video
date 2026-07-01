# 🎨 Quy tắc Thiết kế Giao diện Video (Video UI Design System)

> Tài liệu này là bộ luật thiết kế mà Antigravity PHẢI tuân thủ khi tạo kịch bản và render Video.
> Mọi thay đổi về thiết kế cần được cập nhật vào file này.

---

## 1. Triết lý Thiết kế (Design Philosophy)

### 1.1. Tương phản Tối đa (Maximum Contrast)
- Nền Video luôn là **tối đen** (`#03050a`). Mọi phần tử hiển thị PHẢI nổi bật rõ ràng trên nền này.
- **KHÔNG BAO GIỜ** dùng nền trong suốt (transparent) hoặc semi-transparent quá nhạt cho các phần tử quan trọng (Icon Box, Badge, Button). Nền phải là **màu đặc (Solid)** hoặc **Gradient rực rỡ** để tách biệt hoàn toàn khỏi phông tối.
- Icon (`<i class="fa-...">`) bên trong hộp màu PHẢI có `color: #fff` (trắng) để đảm bảo tương phản.

### 1.2. Chuyển động có Mục đích (Purposeful Motion)
- Mọi hiệu ứng PHẢI dùng **GSAP Timeline** (`tl.to`, `tl.fromTo`). TUYỆT ĐỐI CẤM CSS `@keyframes` vô tận.
- Mỗi phần tử phải có ít nhất 2 pha chuyển động:
  1. **Entrance** (Xuất hiện): elastic, bounce, slide, zoom — tạo ấn tượng mạnh.
  2. **Living** (Sống động): pulse, glow, rotation nhẹ — tạo cảm giác nội dung "đang thở".
- Entrance và Living phải chạy bằng GSAP để renderer bắt được.

### 1.3. Thiết kế Nhất quán (Consistent Design Language)
- Font tiêu đề: **Barlow Condensed** (700/800/900).
- Font nội dung: **Be Vietnam Pro** (400/500/700) — hỗ trợ tiếng Việt tuyệt vời.
- Icon: **FontAwesome 6** (`fa-solid fa-*`, `fa-regular fa-*`).
- Bảng màu: Lấy từ Theme (xem mục 2).

---

## 2. Hệ thống Màu sắc (Color System)

### 2.1. Theme có sẵn
| Theme Name       | Primary   | Accent    | Cảm xúc / Ngữ cảnh                |
|------------------|-----------|-----------|-------------------------------------|
| Hook/Danger      | `#EF4444` | `#FBBF24` | Cảnh báo, vấn đề, thu hút chú ý    |
| Reveal/Answer    | `#34D399` | `#60A5FA` | Giải pháp, trả lời, tích cực        |
| Stats/Data       | `#3B82F6` | `#34D399` | Số liệu, phân tích, logic           |
| Solution/Brand   | `#FF7F30` | `#3B82F6` | Thương hiệu, giải pháp, năng lượng  |
| CTA/Action       | `#EA580C` | `#EF4444` | Kêu gọi hành động, khẩn cấp         |
| Tech/Cyberpunk   | `#06B6D4` | `#A855F7` | Công nghệ, AI, tương lai            |
| Finance/Wealth   | `#F59E0B` | `#10B981` | Tài chính, thành công, tiền bạc     |
| Calm/Education   | `#0EA5E9` | `#FFFFFF` | Giáo dục, bình tĩnh, học thuật      |
| Minimalist/Dark  | `#E5E7EB` | `#9CA3AF` | Tối giản, sang trọng, trung tính    |
| Vibrant/Youth    | `#EC4899` | `#EAB308` | Trẻ trung, năng động, sáng tạo      |

### 2.2. Custom Theme (Tự tạo)
Antigravity được quyền tự tạo bảng màu HEX hoàn toàn mới. Truyền thẳng Object vào trường `"theme"`:
```json
{
  "theme": {
    "primary": "#8B5CF6",
    "accent": "#F472B6",
    "primary_alpha": "rgba(139, 92, 246, 0.25)",
    "bg_radial1": "rgba(139, 92, 246, 0.22)",
    "bg_radial2": "rgba(244, 114, 182, 0.15)"
  }
}
```

### 2.3. Quy tắc Chọn Theme cho Từng Cảnh
- **Hook (Mở bài):** Dùng màu mạnh, gây chú ý → `Hook/Danger`, `Tech/Cyberpunk`, `Vibrant/Youth`
- **Reveal (Vấn đề):** Dùng màu cảnh báo hoặc đối lập → `Hook/Danger`, Custom đỏ-vàng
- **Learning-path / Stats (Phân tích):** Dùng màu bình tĩnh, logic → `Calm/Education`, `Minimalist/Dark`, `Stats/Data`
- **CTA (Chốt):** Dùng màu năng lượng cao, thúc đẩy hành động → `CTA/Action`, `Vibrant/Youth`, `Solution/Brand`

---

## 3. Thành phần Giao diện (UI Components)

### 3.1. Eyebrow Tag (Nhãn phía trên)
- Viên thuốc bo tròn (`border-radius: 50px`), viền mỏng màu primary.
- Nền blur trong suốt (`backdrop-filter: blur(16px)`).
- Font: 17px, UPPERCASE, letter-spacing: 4px.
- Luôn nằm ở **top-center** của khung hình.

### 3.2. Icon Box (Hộp Icon — Dùng trong Reveal)
- Kích thước: **70×70px**, `border-radius: 20px`.
- Nền: `linear-gradient(135deg, primary, accent)` — **MÀU ĐẬM, RỰC RỠ**.
- Viền: `2px solid rgba(255,255,255,0.5)` — tạo tách biệt với nền tối.
- Đổ bóng: `box-shadow: 0 10px 30px primary` — bóng nổi đồng màu.
- Icon bên trong: `color: #fff`, `font-size: 32px`.
- **GSAP Entrance:** `scale: 0 → 1` + `rotation: 0 → 360` bằng `elastic.out(1, 0.5)`.
- **GSAP Living:** `scale: 1 ↔ 1.15` + `rotation: ±10deg` + `drop-shadow glow` chớp sáng liên tục bằng `yoyo: true, repeat: 30`.

### 3.3. Icon Badge (Huy hiệu Icon — Dùng trong Learning-path)
- Hình tròn (`border-radius: 50%`), kích thước `48×48px` (dọc) / `60×60px` (ngang).
- Nền: `rgba(icon_color, 0.2)` — nền pha lê nhạt của chính màu Icon.
- Viền: `1px solid icon_color`.
- Icon bên trong: `color: icon_color`, `font-size: 24px` (dọc) / `30px` (ngang).
- Màu icon: `#34d399` (xanh lá — đã mở khóa) hoặc `#9ca3af` (xám — chưa mở khóa).

### 3.4. Glass Card (Thẻ Kính)
- Nền: `rgba(255,255,255,0.028)`, `backdrop-filter: blur(24px)`.
- Viền: `1px solid rgba(255,255,255,0.07)`, `border-radius: 22px`.
- Đổ bóng: `box-shadow: 0 20px 50px rgba(0,0,0,0.35)`.
- Thanh accent bên trái: `4px`, gradient từ `primary → accent`.

### 3.5. Progress Bar (Thanh Tiến trình)
- Nằm ở **đáy khung hình**, chiều cao `5px`.
- Gradient: `primary → accent`, `scaleX: 0 → 1` theo thời gian GSAP.

### 3.6. Timeline Bar (Trục lộ trình — Dùng trong Learning-path dọc)
- Đường dọc bên trái: `border-left: 2px dashed rgba(255,255,255,0.2)`.
- Glow Dot ở đầu mỗi thẻ: hình tròn 16px, màu `primary`, `box-shadow glow`.
- GSAP: Dot nảy từ `scale(0)` → `scale(1)` bằng `back.out(2)`.

---

## 4. Layout (Bố cục Khung hình)

### 4.1. Danh sách Layout có sẵn
| Layout ID        | Mục đích                                   | Số elements tối đa |
|------------------|---------------------------------------------|---------------------|
| `hook`           | Mở bài, gây chú ý, đặt vấn đề              | 0 (chỉ headline)    |
| `reveal`         | Trình bày vấn đề, so sánh, liệt kê         | 4                   |
| `learning-path`  | Lộ trình học, các bước tuần tự              | 5                   |
| `stats`          | Số liệu, thanh tiến trình, phần trăm       | 1 (stat chính)      |
| `cta`            | Kêu gọi hành động, chốt sales              | 3 (USP pills)       |
| `card-list`      | Danh sách tài nguyên, tính năng             | 3                   |
| `brand-reveal`   | Giới thiệu thương hiệu / logo              | 0                   |
| `admin-report`   | Bảng báo cáo, biểu đồ ngang                | 4 (thanh bar)       |

### 4.2. Flow Kịch bản Chuẩn (4-5 cảnh)
```
Hook → Reveal → Learning-path / Stats → CTA
```
- **Hook:** Tóm tắt chủ đề bằng 1 câu giật tít (5-8 từ).
- **Reveal:** Trình bày vấn đề / so sánh bằng 2-3 bullet points có icon.
- **Learning-path / Stats:** Đi sâu phân tích, chia bước hoặc đưa số liệu.
- **CTA:** Kêu gọi hành động, nêu USP (Unique Selling Proposition).

### 4.3. Responsive (Tự động chuyển Layout)
- `9:16` (Dọc / TikTok / Reels): `scaleFactor = 0.5`, elements xếp dọc.
- `16:9` (Ngang / YouTube): `scaleFactor = 1.0`, elements xếp grid 2 cột.

---

## 5. Typography (Quy tắc Chữ)

### 5.1. Line-height cho Tiếng Việt
- Tiêu đề lớn (`Barlow Condensed`, `text-transform: uppercase`): **`line-height: 1.15`** + **`padding-top: 10px`**.
- Tiêu đề phụ trong Icon Box / Card: **`line-height: 1.2`** + **`padding-top: 4px`**.
- Nội dung / mô tả: **`line-height: 1.4`**.
- **LÝ DO:** Tiếng Việt có dấu mũ (Ấ, Ế, Ố, Ừ) cần nhiều không gian phía trên so với Latin thuần. `line-height < 1.1` sẽ bị cắt ngọn dấu!

### 5.2. Kích thước Font theo Aspect Ratio
| Loại             | 16:9 (1920×1080) | 9:16 (540×960)    |
|------------------|-------------------|-------------------|
| Tiêu đề chính    | 120px             | 58px              |
| Phụ đề           | 42px              | 21px              |
| Stat lớn         | 120px             | 56px              |
| Icon Box title   | 54% of titleSize  | 54% of titleSize  |

### 5.3. Phiên âm TTS vs Hiển thị
- **Chữ hiển thị** (`headline`, `subtitle`, `elements`): LUÔN LUÔN viết đúng chuẩn tiếng Anh/IT. Ví dụ: `RAM`, `Gigabyte`, `F5`, `Core i7`, `ARM`.
- **Giọng đọc** (`voiceover`): Phiên âm Việt hóa để AI TTS đọc không bị ngọng. Ví dụ: `ram`, `ghi ga bai`, `ép năm`, `a rờ mờ`.

---

## 6. Hiệu ứng Chuyển động (Animation Patterns)

### 6.1. Đồng bộ hóa Tốc độ (Speed & Synchronization)
- **Hình ảnh phải xuất hiện tức thì:** Tuyệt đối không được Delay sự xuất hiện của các layout quá lâu. Các thành phần chính (tiêu đề, thẻ bài, icons) phải bắt đầu animate trong khoảng thời gian từ `0.05s` đến `0.25s` đầu tiên của mỗi scene. 
- **Lý do:** Điều này giúp hình ảnh luôn bắt kịp ngay lập tức với voiceover và phụ đề chạy chữ (captions). Nếu hình ảnh delay quá 0.5s, người xem sẽ có cảm giác hình ảnh bị chậm hơn tiếng, gây trải nghiệm đứt gãy.

### 6.2. Nguyên tắc "Snappy & Minimalist" (Độ nảy & Tối giản)
- **Đường cong Easing:** Luôn ưu tiên dùng `back.out(1.2)` đến `back.out(2)` cho các chuyển động xuất hiện (Enter Animations). Sự đàn hồi tạo cảm giác giao diện "sống động" như đang bật nảy.
- **Stagger Cực Ngắn:** Khi xuất hiện danh sách/thẻ bài, khoảng chờ `stagger` giữa các phần tử chỉ nên từ `0.1s` đến `0.15s`. Nó sẽ tạo hiệu ứng làn sóng mượt mà, "nảy" liên tục mà không bắt người xem chờ đợi.
- **Biên độ biến đổi mượt (Subtle Scale):** Tránh phóng to phần tử từ 0 hoặc xoay 360 độ lố lăng. Hãy xuất hiện từ `scale(0.85)` hoặc `scale(0.95)` kết hợp dịch chuyển nhỏ (`y: 20`) để hiệu ứng pop-in tinh tế và chuyên nghiệp.

### 6.3. Entrance Animations (Có sẵn)
| Tên              | Mô tả                                       | Phù hợp cho              |
|------------------|----------------------------------------------|---------------------------|
| `fadeUp`         | Mờ dần lên từ dưới                           | Mọi phần tử              |
| `fadeDown`       | Mờ dần xuống từ trên                         | Subtitle, mô tả          |
| `slideLeft`      | Trượt từ trái                                | Reveal, card-list         |
| `slideRight`     | Trượt từ phải                                | Reveal, card-list         |
| `zoomIn`         | Phóng to từ nhỏ                              | Stats, learning-path      |
| `zoomInBounce`   | Phóng to + nẩy đàn hồi                      | CTA, brand-reveal         |
| `glitchIn`       | Nhấp nháy glitch                             | Hook (công nghệ)          |
| `typeReveal`     | Hiệu ứng đánh máy (clip-path)               | Hook                      |

### 6.2. Exit Animations (Có sẵn)
| Tên              | Mô tả                                       |
|------------------|----------------------------------------------|
| `fadeUp`         | Mờ dần bay lên                               |
| `slideLeft`      | Trượt mất sang trái                          |
| `slideRight`     | Trượt mất sang phải                          |
| `zoomOut`        | Thu nhỏ biến mất                             |
| `dissolve`       | Tan biến tại chỗ                             |
| `glitchOut`      | Glitch rung rồi biến mất                     |

### 6.3. Living Animations (GSAP liên tục)
- **Pulse Glow:** `tl.to('.icon-dynamic', {scale:1.15, rotation:10, filter:'drop-shadow(0 0 35px primary)', duration:1.5, yoyo:true, repeat:30, ease:'sine.inOut'})` — Áp dụng cho Icon Box và Icon Badge.
- **Breathing:** `tl.to(target, {scale:1.05, opacity:0.8, duration:2, yoyo:true, repeat:20})` — Áp dụng cho nền hoặc accent.

---

## 7. Nền & Phông (Background System)

### 7.1. Cấu trúc Nền 5 Lớp
1. **Base:** Radial gradient đen (`#03050a → #000`).
2. **Grid Floor:** Dot grid hoặc Line grid (opacity 0.25-0.65).
3. **Orbs:** 2 quả cầu sáng blur (gradient từ `bg_radial1` / `bg_radial2`).
4. **Noise:** Texture hạt nhỏ (opacity 0.03-0.08).
5. **Vignette:** Gradient tối từ biên vào giữa.

### 7.2. Quy tắc
- Có 5 variant nền được chọn ngẫu nhiên cho mỗi cảnh.
- Orbs dùng CSS `@keyframes` (ngoại lệ duy nhất được phép vì chúng là nền, không ảnh hưởng timeline chính).

---

## 8. Mascot (Nhân vật phụ)
- Hình ảnh mascot (`mascot.png`) nằm ở góc dưới-phải.
- Kích thước: 62px (dọc) / 125px (ngang).
- Mỗi layout có một hành vi GSAP riêng (nhảy, lắc, nẩy, vẫy).
- Mascot KHÔNG CHE nội dung chính.

---

## Phụ lục: Checklist Thiết kế Trước Khi Render

- [ ] Mọi tiêu đề có `line-height >= 1.15` + `padding-top >= 8px`?
- [ ] Mọi Icon Box có nền Solid Gradient (KHÔNG trong suốt)?
- [ ] Icon bên trong có `color: #fff`?
- [ ] Chữ hiển thị (`elements`) viết đúng chính tả tiếng Anh/IT?
- [ ] Chữ voiceover đã phiên âm Việt hóa?
- [ ] Mọi hiệu ứng động dùng GSAP (KHÔNG CSS @keyframes)?
- [ ] Stagger và Easing đã áp dụng chuẩn "Snappy & Minimalist" (`back.out`, delay `0.1s`)?
- [ ] Flow kịch bản đúng: Hook → Reveal → Analysis → CTA?
