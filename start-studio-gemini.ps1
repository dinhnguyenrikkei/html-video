# Hãy thay thế bằng Gemini API Key của bạn dưới đây:
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Tin tưởng thư mục hiện tại để Gemini CLI có thể chạy (Headless mode)
$env:GEMINI_CLI_TRUST_WORKSPACE = "true"

# Thêm thư mục npm toàn cục và thư mục NodeJS vào PATH để CLI có thể chạy được node
$env:Path += ";C:\Users\bmngu\AppData\Roaming\npm;C:\Program Files\nodejs"

Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Dang khoi chay html-video Studio voi Gemini CLI..." -ForegroundColor Green
Write-Host "Model mac dinh: Gemini (thong qua gemini-cli)" -ForegroundColor Green
Write-Host "Hay mo trinh duyet o dia chi: http://localhost:3071" -ForegroundColor Cyan
Write-Host "Nhan Ctrl+C de dung server." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan

& "C:\Program Files\nodejs\node.exe" packages/cli/dist/bin.js studio
