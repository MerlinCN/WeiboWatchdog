# PowerShell快速启动脚本 - 构建并启动所有服务

Write-Host "=== WeiboWatchdog Docker 快速启动 ===" -ForegroundColor Green

# 检查Docker是否运行
Write-Host "检查Docker状态..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "Docker运行正常" -ForegroundColor Green
} catch {
    Write-Host "错误: Docker未运行，请先启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 构建基础镜像
Write-Host "构建基础镜像..." -ForegroundColor Yellow
docker compose --profile build-only build base

if ($LASTEXITCODE -ne 0) {
    Write-Host "基础镜像构建失败！" -ForegroundColor Red
    exit 1
}

# 构建应用镜像
Write-Host "构建应用镜像..." -ForegroundColor Yellow
docker compose build weibo-main weibo-bypy

if ($LASTEXITCODE -ne 0) {
    Write-Host "应用镜像构建失败！" -ForegroundColor Red
    exit 1
}

# 启动服务
Write-Host "启动所有服务..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "启动失败！" -ForegroundColor Red
    exit 1
}

Write-Host "启动成功！" -ForegroundColor Green
Write-Host ""
Write-Host "服务状态：" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "查看日志：" -ForegroundColor Cyan
Write-Host "  docker compose logs -f" -ForegroundColor White

Write-Host ""
Write-Host "停止服务：" -ForegroundColor Cyan
Write-Host "  docker compose down" -ForegroundColor White 