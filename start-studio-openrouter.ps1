# Script khởi chạy html-video Studio cấu hình OpenRouter
# Hãy thay thế "sk-or-v1-YOUR_ACTUAL_KEY_HERE" bằng API Key OpenRouter của bạn dưới đây:
$env:ANTHROPIC_BASE_URL = "https://openrouter.ai/api"
$env:ANTHROPIC_API_KEY = "sk-or-v1-YOUR_ACTUAL_KEY_HERE"
$env:HV_AGENT_MODEL = "anthropic/claude-3.5-sonnet"

Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Dang khoi chay html-video Studio voi OpenRouter..." -ForegroundColor Green
Write-Host "Model mac dinh: anthropic/claude-3.5-sonnet" -ForegroundColor Green
Write-Host "Hay mo trinh duyet o dia chi: http://localhost:3071" -ForegroundColor Cyan
Write-Host "Nhan Ctrl+C de dung server." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan

& "C:\Program Files\nodejs\node.exe" packages/cli/dist/bin.js studio
