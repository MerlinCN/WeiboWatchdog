#!/bin/bash

# Linux快速启动脚本 - 构建并启动所有服务

echo "=== WeiboWatchdog Docker 快速启动 ==="

# 检查Docker是否运行
echo "检查Docker状态..."
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行，请先启动Docker服务"
    exit 1
fi
echo "Docker运行正常"

# 构建基础镜像
echo "构建基础镜像..."
docker compose --profile build-only build base

if [ $? -ne 0 ]; then
    echo "基础镜像构建失败！"
    exit 1
fi

# 构建应用镜像
echo "构建应用镜像..."
docker compose build weibo-main weibo-bypy

if [ $? -ne 0 ]; then
    echo "应用镜像构建失败！"
    exit 1
fi

# 启动服务
echo "启动所有服务..."
docker compose up -d

if [ $? -ne 0 ]; then
    echo "启动失败！"
    exit 1
fi

echo "启动成功！"
echo ""
echo "服务状态："
docker compose ps

echo ""
echo "查看日志："
echo "  docker compose logs -f"

echo ""
echo "停止服务："
echo "  docker compose down" 