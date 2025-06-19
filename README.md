<div align="center">

# WeiboWatchdog

_基于[WeiboBot](https://github.com/MerlinCN/WeiboBot) 开发的智能微博监控机器人_

<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Version" src="https://img.shields.io/pypi/pyversions/WeiboBot" /></a>
<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Implementation" src="https://img.shields.io/pypi/implementation/WeiboBot" /></a>
<a href="https://github.com/MerlinCN/WeiboBot/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/MerlinCN/WeiboBot"></a>

</div>

## 项目简介

`WeiboWatchdog` 是一个基于 `WeiboBot` 开发的智能微博监控机器人，具备以下核心功能：

- 🔍 **智能内容检测**：使用腾讯云图片内容安全服务自动检测微博内容
- 📱 **自动转发**：支持自动转发符合条件的微博
- 🖼️ **图片上传**：自动将检测到的图片上传到百度云
- 📹 **视频处理**：支持视频内容检测和截图
- 🤖 **AI审核**：基于AI的内容安全审核，确保内容合规
- 📊 **数据管理**：完整的数据库记录和缓存管理

## 系统要求

- Python 3.11+
- Docker & Docker Compose
- 腾讯云API密钥（用于内容检测）
- 百度云配置（用于文件上传）

## 快速开始

### 1. 环境配置

创建 `.env` 文件并配置以下参数：

```env
# 运行模式：dev（开发）或 prod（生产）
MODE=dev

# 腾讯云API配置（用于内容检测）
TENCENT_API_KEY=your_tencent_api_key
TENCENT_SECRET_KEY=your_tencent_secret_key

# 转发间隔（秒）
REPOST_INTERVAL=60

# 百度云上传服务地址
BYPY_URL=http://localhost:8000
```

### 2. 微博配置

在 `data/` 目录下放置：
- `bypy.json`：百度云配置文件(用bypy info生成)

### 3. Docker部署（推荐）

#### 使用快速启动脚本

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```powershell
.\start.ps1
```

#### 手动部署

```bash
# 构建并启动所有服务
docker compose --profile build-only build base
docker compose build weibo-main weibo-bypy
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 4. 本地开发

```bash
# 安装依赖
pip install -e .

# 运行主程序
python src/main.py

# 运行百度云上传服务
python src/bypy_main.py
```

## 配置说明

### 环境变量

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MODE` | 运行模式（dev/prod） | dev |
| `TENCENT_API_KEY` | 腾讯云API密钥 | - |
| `TENCENT_SECRET_KEY` | 腾讯云密钥 | - |
| `SPECIAL_USERS` | 特殊用户ID列表 | [] |
| `REPOST_INTERVAL` | 转发间隔（秒） | 60 |
| `BYPY_URL` | 百度云上传服务地址 | http://localhost:8000 |

### 目录结构

```
WeiboWatchdog/
├── src/                    # 源代码
│   ├── main.py            # 主程序入口
│   ├── bypy_main.py       # 百度云上传服务
│   ├── ai/                # AI检测模块
│   ├── config/            # 配置管理
│   ├── engine/            # 爬虫引擎
│   └── models/            # 数据模型
├── data/                  # 数据目录
│   ├── weibobot_cookies.json  # 微博cookies
│   └── bypy.conf          # 百度云配置
├── cache/                 # 缓存目录
├── config/                # 配置文件目录
├── logs/                  # 日志目录
└── docker-compose.yml     # Docker编排文件
```

## 功能特性

### 🤖 AI内容检测
- 使用腾讯云图片内容安全服务
- 支持图片和视频内容检测
- 自动提取视频关键帧进行分析
- 智能过滤违规内容

### 📱 微博监控
- 自动监控指定用户的微博
- 支持@回复触发转发
- 智能评论生成
- 防重复转发机制

### ☁️ 云端存储
- 自动上传检测到的图片到百度云
- 支持视频截图上传
- 完整的文件管理

### 🔧 系统管理
- 完整的日志记录
- 数据库持久化
- 缓存管理
- Docker容器化部署

## 开发说明

### 项目依赖

主要依赖包：
- `weibobot[screenshot]>=1.2.3` - 微博机器人核心
- `fastapi>=0.115.13` - Web框架
- `tencentcloud-sdk-python-ims>=3.0.1394` - 腾讯云内容安全
- `bypy>=1.8.9` - 百度云上传工具
- `tortoise-orm>=0.25.1` - 数据库ORM

### 扩展开发

项目采用模块化设计，可以轻松扩展：

1. **添加新的检测规则**：在 `src/ai/` 目录下添加新的检测模块
2. **自定义转发逻辑**：修改 `src/main.py` 中的转发处理函数
3. **增加新的存储后端**：在 `src/engine/` 目录下添加新的存储引擎

## 许可证

本项目基于 [WeiboBot](https://github.com/MerlinCN/WeiboBot) 开发，遵循相同的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 免责声明

本项目仅供学习和研究使用，请遵守相关法律法规和微博平台使用条款。使用者需自行承担使用风险。