# PowerShell构建脚本 - 使用Docker Compose构建和运行服务

Write-Host "开始构建Docker镜像..." -ForegroundColor Green

# 先构建基础镜像
Write-Host "构建基础镜像..." -ForegroundColor Yellow
docker compose --profile build-only build base

# 使用Docker Compose构建应用镜像
Write-Host "构建应用镜像..." -ForegroundColor Yellow
docker compose build weibo-main weibo-bypy

Write-Host "构建完成！" -ForegroundColor Green
Write-Host "镜像列表：" -ForegroundColor Cyan
Write-Host "  - weibo-watchdog-base:latest (基础镜像)" -ForegroundColor White
Write-Host "  - weibo-watchdog-main:latest (主程序)" -ForegroundColor White
Write-Host "  - weibo-watchdog-bypy:latest (上传服务)" -ForegroundColor White

Write-Host ""
Write-Host "运行命令：" -ForegroundColor Cyan
Write-Host "  启动所有服务: docker compose up -d" -ForegroundColor White
Write-Host "  查看日志: docker compose logs -f" -ForegroundColor White
Write-Host "  停止服务: docker compose down" -ForegroundColor White
Write-Host "  重启服务: docker compose restart" -ForegroundColor White

Write-Host ""
Write-Host "服务说明：" -ForegroundColor Cyan
Write-Host "  - 主程序服务: weibo-watchdog-main" -ForegroundColor White
Write-Host "  - 上传服务: weibo-watchdog-bypy (内部访问: http://weibo-bypy:8000)" -ForegroundColor White
Write-Host "  - 两个服务通过内部网络通信，无需暴露端口" -ForegroundColor White 