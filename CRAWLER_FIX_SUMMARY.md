# 爬虫模块修复总结

## 🔧 问题原因

前端界面仍在调用后端已删除的 pip 管理接口，并且使用旧的 `requirements` 字段，导致 404 错误。

## ✅ 已修复内容

### 1. 后端 API 接口 (已完成)
- ✅ 删除 `/pip/list`、`/pip/show`、`/pip/install` 接口
- ✅ 新增 `/script/stop` 停止脚本接口
- ✅ 新增 `/script/runs` 运行历史接口
- ✅ 修改 `/script/create`、`/script/update`、`/script/get`、`/script/run` 支持新字段

### 2. 前端 API 定义 (`web/src/api/index.js`)
**修复：**
- ✅ 删除 `crawlerPipList`、`crawlerPipShow`、`crawlerPipInstall` 方法
- ✅ 新增 `crawlerScriptStop` 方法
- ✅ 新增 `crawlerScriptRuns` 方法

### 3. 前端界面 (`web/src/views/system/crawler/index.vue`)
**修复：**
- ✅ 移除 pip 管理相关代码（pipList、pipQuery、pipInfo、pipLoading 等变量和函数）
- ✅ 编辑器字段从 `requirements` 改为 `params`、`loop_enabled`、`loop_interval_sec`、`loop_count` 等
- ✅ 新增参数 JSON 编辑器（paramsText）
- ✅ 新增停止脚本功能（stopScript）
- ✅ 新增查看运行历史功能（viewHistory）
- ✅ 表格列增加"循环"标识
- ✅ 操作列增加"历史"按钮
- ✅ 移除"依赖管理"卡片，改为说明提示（手动安装依赖）
- ✅ 编辑器增加循环执行配置项

## 📝 界面变更对比

### 旧界面功能
- ❌ pip 依赖列表查询
- ❌ pip 包搜索和安装
- ❌ requirements 字段编辑

### 新界面功能
- ✅ 脚本参数 JSON 编辑（params）
- ✅ 循环执行配置（启用/间隔/次数）
- ✅ 停止运行中的脚本
- ✅ 查看脚本运行历史
- ✅ 依赖安装说明提示

## 🎨 界面布局调整

### 脚本列表表格
```
ID | 名称 | 启用 | 循环 | 更新时间 | 操作
                                   [运行] [历史] [编辑] [删除]
```

### 运行与日志卡片
```
标题右侧：[停止] [刷新日志]
内容：STDOUT | STDERR
底部：状态 + 用时
```

### 平台设置
```
- 依赖管理说明（提示手动安装）
- 脚本平台设置（保留天数、超时、日志大小）
```

### 编辑脚本弹窗
```
- 名称
- 描述
- 启用（开关）
---
- 代码（textarea）
- 参数 JSON（textarea）
---
- 启用循环执行（开关）
- 循环间隔(秒)（条件显示）
- 循环次数（条件显示，0=无限）
```

### 运行历史弹窗（新增）
```
列表显示每次运行记录：
- Run ID
- 状态（success/error/timeout/stopped）
- 开始/结束时间
- 用时
- 退出码
- [查看日志] 按钮
```

## 🚀 使用流程

### 1. 安装依赖
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装脚本所需库
pip install DrissionPage
```

### 2. 创建脚本
- 点击"新建脚本"
- 填写名称、描述
- 编写代码（可读取 `SCRIPT_PARAMS` 环境变量或 `params.json`）
- 配置参数 JSON：`{"url": "https://example.com"}`
- 可选：启用循环执行，设置间隔和次数

### 3. 运行脚本
- 单次运行：点击"运行"按钮
- 查看日志：自动显示在右侧面板
- 停止运行：点击"停止"按钮

### 4. 查看历史
- 点击"历史"按钮
- 查看所有运行记录
- 点击"查看日志"可切换到该次运行的日志

## 🔍 脚本示例

### 简单示例
```python
import json
import os

# 读取参数
params = json.loads(os.environ.get('SCRIPT_PARAMS', '{}'))
url = params.get('url', 'https://www.baidu.com')

print(f'访问: {url}')
# 执行爬取逻辑...
```

### DrissionPage 示例
```python
import json
import os
from DrissionPage import ChromiumPage

params = json.loads(os.environ.get('SCRIPT_PARAMS', '{}'))
url = params.get('url', 'https://www.baidu.com')

page = ChromiumPage()
page.get(url)
print(f'标题: {page.title}')
page.quit()
```

## ⚠️ 注意事项

1. **依赖安装**：所有脚本依赖需在项目虚拟环境手动安装，前端界面仅显示说明
2. **参数格式**：params 必须是合法的 JSON 格式，否则保存时会报错
3. **循环执行**：启用后按配置自动重复运行，每次生成独立记录
4. **停止功能**：仅对运行中的脚本有效，会强制终止进程
5. **日志查看**：历史记录中可查看任意一次运行的日志

## 🎯 已验证功能

- [x] 脚本列表加载
- [x] 创建脚本（新字段）
- [x] 编辑脚本（新字段）
- [x] 删除脚本
- [x] 运行脚本
- [x] 停止脚本
- [x] 查看日志
- [x] 查看运行历史
- [x] 循环执行配置
- [x] 参数 JSON 编辑
- [x] 平台设置
- [x] we123 爬虫（保持原样）

## 📊 数据库迁移

迁移文件：`migrations/models/10_20251112233456_update.py`

**变更：**
- 新增字段：`params`、`loop_enabled`、`loop_interval_sec`、`loop_count`、`scheduled_enabled`、`cron_expression`
- 删除字段：`requirements`

**迁移状态：已应用**

## 🔗 相关文件

### 后端
- `app/models/script.py` - 模型定义
- `app/crawler/runner.py` - 运行器
- `app/api/v1/crawler/scripts.py` - API 接口
- `app/schemas/crawler.py` - Schema 定义

### 前端
- `web/src/api/index.js` - API 方法
- `web/src/views/system/crawler/index.vue` - 主界面

### 文档
- `doc/crawler_script_usage.md` - 使用文档

## ✨ 后续可扩展

- [ ] 定时任务调度（cron_expression 字段已预留）
- [ ] 脚本执行队列管理
- [ ] 更详细的监控和统计
- [ ] 脚本版本控制
- [ ] 脚本模板市场

---

**修复完成时间：** 2025-11-13
**修复人：** AI Assistant
**验证状态：** ✅ 已完成
