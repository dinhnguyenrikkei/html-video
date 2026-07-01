# Script to automate and launch marketing video campaign building
# Version: 1.0.0

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "🚀 RIKKEI EDU - CAMPAIGN VIDEO BUILDER LAUNCHER" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Check Node.js
Write-Host "🔍 Checking environment..." -ForegroundColor Yellow
try {
    $nodeVer = node -v
    Write-Host "   Node.js version: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "   [Warning] Node.js is not found. Headless rendering might fail!" -ForegroundColor Red
}

# 2. Check Python
try {
    $pyVer = python --version
    Write-Host "   Python version: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "   [Error] Python is not installed or not in PATH! Exiting." -ForegroundColor Red
    Exit 1
}

# 3. Check FFmpeg path config in python script
$builderScript = "scripts/batch_video_builder.py"
if (Test-Path $builderScript) {
    # Check if Gyan ffmpeg path exists on the machine
    $ffmpegGyanPath = "C:\Users\bmngu\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
    if (Test-Path $ffmpegGyanPath) {
        Write-Host "   FFmpeg Gyan binary confirmed at: $ffmpegGyanPath" -ForegroundColor Green
    } else {
        Write-Host "   [Warning] Configured FFmpeg path not found: $ffmpegGyanPath" -ForegroundColor Yellow
        Write-Host "   Make sure FFmpeg is installed at this location or update FFMPEG_PATH in batch_video_builder.py" -ForegroundColor DarkYellow
    }
}

# 4. Optional: Clean previous campaign MP4s in exports/
$cleanExport = Read-Host "🧹 Do you want to clean old exports in exports/ folder? (y/n)"
if ($cleanExport -eq 'y' -or $cleanExport -eq 'Y') {
    Write-Host "   Cleaning exports/proj_de_camp_ngay_*.mp4..." -ForegroundColor Yellow
    Remove-Item -Path "exports/proj_de_camp_ngay_*.mp4" -Force -ErrorAction SilentlyContinue
    Write-Host "   Clean complete." -ForegroundColor Green
}

# 5. Execute build
Write-Host "`n🎬 Executing campaign video build process..." -ForegroundColor Cyan
$jsonConfig = "scripts/inputs/ai_native_de_campaign_scripts.json"
if (Test-Path $jsonConfig) {
    Write-Host "   Configuration file found: $jsonConfig" -ForegroundColor Green
    python $builderScript $jsonConfig
} else {
    Write-Host "   [Error] Configuration file not found at: $jsonConfig" -ForegroundColor Red
    Exit 1
}

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "🎉 BATCH VIDEO BUILD SYSTEM COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
