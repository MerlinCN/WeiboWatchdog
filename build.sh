#!/bin/bash

# 构建脚本 - 使用Docker Compose构建和运行服务

echo "开始构建Docker镜像..."

# 先构建基础镜像
echo "构建基础镜像..."
docker compose --profile build-only build base

# 使用Docker Compose构建应用镜像
echo "构建应用镜像..."
docker compose build weibo-main weibo-bypy

echo "构建完成！"
echo "镜像列表："
echo "  - weibo-watchdog-base:latest (基础镜像)"
echo "  - weibo-watchdog-main:latest (主程序)"
echo "  - weibo-watchdog-bypy:latest (上传服务)"

echo ""
echo "运行命令："
echo "  启动所有服务: docker compose up -d"
echo "  查看日志: docker compose logs -f"
echo "  停止服务: docker compose down"
echo "  重启服务: docker compose restart"

echo ""
echo "服务说明："
echo "  - 主程序服务: weibo-watchdog-main"
echo "  - 上传服务: weibo-watchdog-bypy (内部访问: http://weibo-bypy:8000)"
echo "  - 两个服务通过内部网络通信，无需暴露端口" 