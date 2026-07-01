FROM mcr.microsoft.com/playwright:v1.44.0-jammy

# Cài đặt các công cụ hệ thống cần thiết (Python 3, FFmpeg)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy toàn bộ source code vào container
COPY . .

# 1. Cài đặt Môi trường Node.js (Playwright, React, Remotion)
RUN npm install -g pnpm
RUN pnpm install
# Build core và cli engine để sẵn sàng Render video
RUN cd packages/core && pnpm run build
RUN cd packages/cli && pnpm run build

# 2. Cài đặt Môi trường Python (Scripting, API server)
RUN pip3 install edge-tts python-dotenv

# TÙY CHỌN (OPTIONAL): 
# Nếu bạn muốn Container tự động tải và chạy cả AI VieNeu-TTS (Nhại giọng), hãy bỏ comment dòng dưới đây.
# Lưu ý: Cài đặt thêm VieNeu sẽ làm Docker image nặng thêm khoảng 3-5GB (vì chứa thư viện PyTorch). 
# Nếu máy không có NVIDIA Docker, nó sẽ chạy bằng CPU thay vì GPU.
# RUN pip3 install ./vieneu

EXPOSE 3080

# Chạy Studio API Server mặc định
CMD ["python3", "rikkei-studio/server.py"]
