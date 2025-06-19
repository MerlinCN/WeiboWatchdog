# 转发队列功能说明

## 功能概述

转发队列功能将微博转发操作封装到 `SpiderEngine` 中，提供以下特性：

1. **队列管理**: 所有转发任务进入队列，按顺序处理
2. **转发限制**: 可配置的转发间隔（默认60秒）
3. **持久化**: 队列数据保存到SQLite数据库，重启后可从上次位置继续
4. **重试机制**: 转发失败时自动重试（最多3次）
5. **异步处理**: 转发操作在后台异步执行，不影响主程序
6. **历史记录**: 完整的转发历史记录，包括成功和失败状态
7. **ORM支持**: 使用Tortoise ORM进行数据库操作，代码更简洁

## 配置说明

在 `.env` 文件中添加转发间隔配置：

```env
REPOST_INTERVAL=60  # 转发间隔（秒）
```

## 数据库结构

### 转发任务表 (repost_tasks)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| weibo_mid | VARCHAR(50) | 微博ID |
| content | TEXT | 转发内容 |
| created_at | FLOAT | 创建时间戳 |
| retry_count | INTEGER | 重试次数 |
| max_retries | INTEGER | 最大重试次数 |
| status | VARCHAR(20) | 任务状态（pending/completed/failed） |

### 转发历史表 (repost_history)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| weibo_mid | VARCHAR(50) | 微博ID |
| content | TEXT | 转发内容 |
| created_at | FLOAT | 创建时间戳 |
| executed_at | FLOAT | 执行时间戳 |
| status | VARCHAR(20) | 执行状态（success/failed） |

## 文件结构

```
weibo_bot.db  # SQLite数据库文件
src/
  ├── models.py      # Tortoise ORM模型定义
  ├── engine.py      # SpiderEngine实现
  └── main.py        # 主程序
db_manager.py        # 数据库管理工具
```

## 主要变更

### 1. Tortoise ORM模型 (src/models.py)

- `RepostTask`: 转发任务模型
- `RepostHistory`: 转发历史模型
- 自动生成Pydantic模型用于序列化

### 2. SpiderEngine 新增功能

- `add_repost_task(weibo_mid, content)`: 添加转发任务到队列（异步）
- `get_queue_status()`: 获取队列状态信息
- `get_repost_history(limit)`: 获取转发历史记录（异步）
- `_repost_worker()`: 后台转发工作线程
- `_execute_repost(task)`: 执行转发任务
- `_init_database()`: 初始化Tortoise ORM数据库
- `_load_queue()` / `_save_queue()`: 队列数据库操作（异步）
- `_record_repost_history(task, status)`: 记录转发历史（异步）
- `close()`: 关闭数据库连接

### 3. 配置更新

- 在 `config/__init__.py` 中添加 `repost_interval` 配置项

### 4. 主程序修改

- `main.py` 中使用 `await wd.add_repost_task()` 替代直接调用 `bot.repost_weibo()`
- 添加了资源清理功能

## 使用方法

### 基本使用

```python
from src.engine import SpiderEngine
from src.WeiboBot import Bot

bot = Bot()
# 创建SpiderEngine实例，设置转发间隔为60秒
wd = SpiderEngine(bot, repost_interval=60)

# 添加转发任务（异步）
await wd.add_repost_task("weibo_mid", "转发内容")

# 获取队列状态
status = wd.get_queue_status()
print(f"队列大小: {status['queue_size']}")

# 获取转发历史（异步）
history = await wd.get_repost_history(limit=10)
for record in history:
    print(f"微博ID: {record['weibo_mid']}, 状态: {record['status']}")

# 清理资源
await wd.close()
```

### 队列状态信息

```python
status = wd.get_queue_status()
# 返回格式：
{
    "queue_size": 5,                    # 队列中待处理任务数
    "last_repost_time": 1640995200.0,   # 上次转发时间戳
    "repost_interval": 60,              # 转发间隔（秒）
    "next_repost_available": True       # 是否可以立即转发
}
```

### 转发历史信息

```python
history = await wd.get_repost_history(limit=5)
# 返回格式：
[
    {
        "weibo_mid": "1234567890",
        "content": "转发内容",
        "created_at": 1640995200.0,
        "executed_at": 1640995260.0,
        "status": "success"
    }
]
```

## 工作流程

1. **任务添加**: 调用 `await add_repost_task()` 将转发任务加入队列
2. **数据库持久化**: 任务立即保存到SQLite数据库（通过Tortoise ORM）
3. **后台处理**: `_repost_worker()` 在后台持续检查队列
4. **间隔控制**: 确保两次转发之间间隔不小于配置的时间
5. **执行转发**: 调用 `bot.repost_weibo()` 执行实际转发
6. **历史记录**: 记录转发结果到历史表（通过Tortoise ORM）
7. **错误处理**: 转发失败时自动重试，最多3次
8. **状态更新**: 转发完成后更新队列状态并重新保存

## 数据库操作

### 使用管理工具

```bash
# 查看队列状态
python db_manager.py --action status

# 查看转发历史
python db_manager.py --action history --limit 20

# 查看统计信息
python db_manager.py --action stats

# 清理30天前的历史记录
python db_manager.py --action clear --days 30

# 重置失败的任务
python db_manager.py --action reset
```

### 使用Tortoise ORM查询

```python
from tortoise import Tortoise
from src.models import RepostTask, RepostHistory

# 初始化数据库连接
await Tortoise.init(
    db_url="sqlite://weibo_bot.db",
    modules={"models": ["src.models"]}
)

# 查询待处理任务
pending_tasks = await RepostTask.filter(status="pending").order_by("created_at")

# 查询转发历史
history = await RepostHistory.all().order_by("-executed_at").limit(10)

# 统计成功转发数量
success_count = await RepostHistory.filter(status="success").count()

# 关闭连接
await Tortoise.close_connections()
```

## 优势

1. **避免频率限制**: 通过间隔控制避免触发微博的频率限制
2. **数据安全**: SQLite数据库确保重启后不丢失任务
3. **历史追踪**: 完整的转发历史记录，便于分析和调试
4. **错误恢复**: 自动重试机制提高转发成功率
5. **性能优化**: 异步处理不影响主程序性能
6. **可配置性**: 转发间隔可通过配置文件调整
7. **数据完整性**: SQLite提供ACID特性，确保数据一致性
8. **代码简洁**: 使用Tortoise ORM，代码更易维护
9. **类型安全**: ORM提供类型检查和自动补全

## 注意事项

1. 确保程序有创建和写入 `weibo_bot.db` 文件的权限
2. 转发间隔建议不小于60秒以避免被限制
3. 重启程序时会自动加载之前的队列
4. 数据库文件会随着使用逐渐增大，建议定期清理历史数据
5. 所有数据库操作都是异步的，需要使用 `await` 关键字
6. 程序退出时会自动关闭数据库连接
7. Tortoise ORM会自动创建数据库表结构 