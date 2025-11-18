# 爬虫脚本平台使用说明

## 📖 概述

爬虫脚本平台已简化为统一项目依赖模式，提供脚本管理、执行、日志查看、动态参数和循环执行等功能。

## ✨ 核心特性

- ✅ **统一依赖环境**：所有脚本使用项目依赖，无需管理独立运行时
- ✅ **动态参数传递**：支持脚本默认参数和运行时参数覆盖
- ✅ **循环执行**：可配置循环次数和间隔
- ✅ **进程管理**：启动、停止、日志查看
- ✅ **运行历史**：完整的执行记录和日志
- 🔮 **预留定时任务**：为后续扩展定时调度功能

---

## 🚀 快速开始

### 1. 安装依赖

在项目虚拟环境中安装脚本所需的库（如 DrissionPage）：

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 安装依赖
pip install DrissionPage
```

### 2. 创建脚本

**API:** `POST /api/v1/crawler/script/create`

```json
{
  "name": "简单爬虫示例",
  "desc": "使用 DrissionPage 打开网页",
  "code": "from DrissionPage import ChromiumPage\nimport json\nimport os\n\n# 读取参数\nparams = json.loads(os.environ.get('SCRIPT_PARAMS', '{}'))\nurl = params.get('url', 'https://www.baidu.com')\n\npage = ChromiumPage()\npage.get(url)\nprint(f'标题: {page.title}')\npage.quit()\n",
  "enabled": true,
  "params": {
    "url": "https://www.baidu.com"
  },
  "loop_enabled": false,
  "loop_interval_sec": 60,
  "loop_count": 0
}
```

### 3. 运行脚本

**API:** `POST /api/v1/crawler/script/run`

**单次运行：**
```json
{
  "id": 1,
  "timeout_sec": 300,
  "params": {
    "url": "https://www.example.com"
  }
}
```

**循环运行（使用脚本配置）：**
```json
{
  "id": 1,
  "use_loop": true
}
```

**循环运行（临时覆盖）：**
```json
{
  "id": 1,
  "loop": {
    "enabled": true,
    "interval_sec": 30,
    "count": 10
  }
}
```

### 4. 查看运行状态

**API:** `GET /api/v1/crawler/script/run_status?run_id=123`

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": 123,
    "script_id": 1,
    "status": "success",
    "started_at": "2025-11-12T15:30:00",
    "ended_at": "2025-11-12T15:30:05",
    "exit_code": 0,
    "pid": 12345,
    "duration_ms": 5000
  }
}
```

**状态说明：**
- `queued`: 排队中
- `running`: 运行中
- `success`: 成功完成
- `error`: 执行失败
- `timeout`: 超时
- `stopped`: 被用户停止

### 5. 查看日志

**API:** `GET /api/v1/crawler/script/run_logs?run_id=123`

**响应：**
```json
{
  "code": 200,
  "data": {
    "stdout": "标题: 百度一下，你就知道\n",
    "stderr": ""
  }
}
```

### 6. 停止运行中的脚本

**API:** `POST /api/v1/crawler/script/stop`

```json
{
  "run_id": 123
}
```

### 7. 查看运行历史

**API:** `GET /api/v1/crawler/script/runs?script_id=1&page=1&page_size=20`

---

## 📝 脚本编写指南

### 参数接收方式

脚本可通过两种方式接收参数：

**方式一：环境变量（推荐）**
```python
import json
import os

params = json.loads(os.environ.get('SCRIPT_PARAMS', '{}'))
url = params.get('url', 'default_value')
```

**方式二：读取 params.json 文件**
```python
import json
from pathlib import Path

params_file = Path(__file__).parent / 'params.json'
if params_file.exists():
    params = json.loads(params_file.read_text(encoding='utf-8'))
else:
    params = {}

url = params.get('url', 'default_value')
```

### 完整示例脚本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 DrissionPage 爬虫脚本示例
"""
import json
import os
import sys
from pathlib import Path

def get_params():
    """获取运行参数"""
    # 优先从环境变量读取
    params_str = os.environ.get('SCRIPT_PARAMS')
    if params_str:
        return json.loads(params_str)
    
    # 回退到 params.json 文件
    params_file = Path(__file__).parent / 'params.json'
    if params_file.exists():
        return json.loads(params_file.read_text(encoding='utf-8'))
    
    return {}

def main():
    """主函数"""
    params = get_params()
    
    url = params.get('url', 'https://www.baidu.com')
    timeout = params.get('timeout', 30)
    
    print(f'开始访问: {url}')
    
    try:
        from DrissionPage import ChromiumPage
        
        page = ChromiumPage()
        page.get(url, timeout=timeout)
        
        title = page.title
        print(f'页面标题: {title}')
        
        # 执行爬取逻辑
        # ...
        
        page.quit()
        print('执行成功！')
        return 0
        
    except Exception as e:
        print(f'执行失败: {e}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

---

## 🔧 API 接口完整列表

### 脚本管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/crawler/script/list` | GET | 脚本列表（分页） |
| `/api/v1/crawler/script/get` | GET | 获取单个脚本详情 |
| `/api/v1/crawler/script/create` | POST | 创建脚本 |
| `/api/v1/crawler/script/update` | POST | 更新脚本 |
| `/api/v1/crawler/script/delete` | DELETE | 删除脚本 |

### 脚本执行

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/crawler/script/run` | POST | 运行脚本 |
| `/api/v1/crawler/script/stop` | POST | 停止运行中的脚本 |
| `/api/v1/crawler/script/run_status` | GET | 查询运行状态 |
| `/api/v1/crawler/script/run_logs` | GET | 查询运行日志 |
| `/api/v1/crawler/script/runs` | GET | 查询脚本运行历史 |

### 系统设置

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/crawler/settings/get` | GET | 获取平台设置 |
| `/api/v1/crawler/settings/update` | POST | 更新平台设置 |
| `/api/v1/crawler/maintenance/cleanup_runs` | POST | 手动清理过期运行记录 |

---

## 🎯 使用场景

### 场景1：简单的网页抓取

```python
from DrissionPage import ChromiumPage

page = ChromiumPage()
page.get('https://example.com')
content = page.html
print(content)
page.quit()
```

**脚本参数：**
```json
{
  "url": "https://example.com"
}
```

### 场景2：定时循环抓取

设置脚本配置：
```json
{
  "loop_enabled": true,
  "loop_interval_sec": 300,
  "loop_count": 0
}
```

每5分钟执行一次，无限循环（直到手动停止）。

### 场景3：批量处理

```python
import json
import os

params = json.loads(os.environ.get('SCRIPT_PARAMS', '{}'))
urls = params.get('urls', [])

for url in urls:
    print(f'处理: {url}')
    # 处理逻辑...
```

**运行时参数：**
```json
{
  "id": 1,
  "params": {
    "urls": [
      "https://example1.com",
      "https://example2.com",
      "https://example3.com"
    ]
  }
}
```

---

## ⚙️ 平台设置

**API:** `GET /api/v1/crawler/settings/get`

```json
{
  "retention_days": 30,
  "default_timeout_sec": 600,
  "max_log_bytes": 1048576
}
```

**参数说明：**
- `retention_days`: 运行日志保留天数（默认30天）
- `default_timeout_sec`: 默认超时秒数（默认600秒）
- `max_log_bytes`: 单次运行日志最大字节数（默认1MB）

---

## 📌 注意事项

1. **依赖安装**：所有脚本依赖需在项目虚拟环境中手动安装
2. **日志大小**：单次运行日志超过 `max_log_bytes` 会被截断（保留尾部）
3. **循环执行**：
   - `loop_count=0` 表示无限循环
   - 每次循环会生成独立的 ScriptRun 记录
   - 可通过 `/script/stop` 随时终止
4. **进程管理**：
   - 停止脚本会强制终止子进程
   - Windows 使用 `taskkill`，Linux/macOS 使用 `kill` 信号
5. **定时任务**：`scheduled_enabled` 和 `cron_expression` 字段已预留，后续版本实现

---

## 🔮 后续规划

- [ ] 定时任务调度器（基于 APScheduler）
- [ ] 脚本执行队列和并发控制
- [ ] 更详细的监控统计和可视化
- [ ] 脚本版本管理
- [ ] 脚本模板市场

---

## 🆘 常见问题

**Q: 脚本运行失败，如何排查？**

A: 
1. 查看运行日志 `/script/run_logs`
2. 检查 stderr 输出
3. 检查依赖是否已安装
4. 在本地调试脚本

**Q: 如何传递复杂参数？**

A: 使用 JSON 格式，支持嵌套对象和数组：
```json
{
  "params": {
    "config": {
      "headers": {"User-Agent": "..."},
      "proxies": ["proxy1", "proxy2"]
    }
  }
}
```

**Q: 循环执行是否会阻塞 API 响应？**

A: 不会。循环在后台异步执行，API 会立即返回首次运行的 run_id。

**Q: 如何停止无限循环的脚本？**

A: 使用 `/script/stop` 接口，传入任意一次循环的 run_id 即可终止整个循环进程。

---

## 📄 变更记录

### 2025-11-12
- ✅ 移除独立依赖管理（requirements 字段和 pip 接口）
- ✅ 新增动态参数传递（params 字段）
- ✅ 新增循环执行支持
- ✅ 新增停止脚本功能
- ✅ 新增运行历史查询接口
- ✅ 预留定时任务字段
