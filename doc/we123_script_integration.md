# we123 小程序采集器 - 脚本集成说明

## 📖 概述

we123 小程序采集器现已集成到脚本平台，可以在脚本列表中查看、编辑和运行。

## ✨ 功能特性

- ✅ 自动出现在脚本列表中（名称：`we123小程序采集器`）
- ✅ 支持通过脚本平台直接运行
- ✅ 支持编辑参数配置
- ✅ 支持查看运行日志和历史
- ✅ 支持停止运行中的任务
- ✅ 每次应用启动自动同步最新代码

## 🎯 如何使用

### 1. 查找脚本

启动应用后，在脚本列表中会自动创建名为 **"we123小程序采集器"** 的脚本。

### 2. 编辑参数

点击"编辑"按钮，配置参数（JSON格式）：

```json
{
  "start_id": 1,
  "loop": false,
  "max_404_span": 500,
  "delay_sec": 3.0,
  "ua": "",
  "proxy": ""
}
```

**参数说明：**
- `start_id`: 起始ID，从哪个小程序ID开始采集
- `loop`: 是否循环模式，达到连续404上限后是否从头开始
- `max_404_span`: 连续404的上限，超过此值停止（循环模式下会重新开始）
- `delay_sec`: 每次请求的延迟秒数（建议3-5秒）
- `ua`: 自定义User-Agent，留空使用默认
- `proxy`: 代理地址，格式：`http://host:port` 或 `http://user:pass@host:port`

### 3. 运行脚本

1. 点击"运行"按钮
2. 脚本将启动 we123 采集任务
3. 在右侧面板查看实时日志
4. 任务完成或出错时会输出最终统计

### 4. 停止脚本

如果需要中途停止，点击右侧日志面板的"停止"按钮。

### 5. 查看历史

点击"历史"按钮可以查看所有运行记录。

## 🔍 脚本工作原理

### 脚本代码结构

```python
#!/usr/bin/env python3
# 1. 读取环境变量中的参数（SCRIPT_PARAMS）
# 2. 解析配置（start_id、loop、max_404_span等）
# 3. 导入 we123_task 模块
# 4. 构造 We123Config 对象
# 5. 启动任务 we123_task.start(config)
# 6. 等待任务完成
# 7. 输出最终统计
```

### 与原 we123 API 的关系

- **原 API 接口**：`/api/v1/crawler/task/we123/*` 仍然保留，可以独立使用
- **脚本模式**：通过脚本平台运行，底层调用相同的 `we123_task` 单例
- **共享状态**：两种方式共享相同的任务状态和断点数据

## ⚙️ 自动初始化

应用启动时会自动执行以下逻辑（`app/core/init_app.py` 中的 `ensure_we123_scripts()`）：

1. **首次启动**：自动创建"we123小程序采集器"脚本
2. **后续启动**：自动更新脚本代码（保留用户修改的参数）

### 初始化代码位置

- **模板定义**：`app/crawler/we123_script_template.py`
- **初始化函数**：`app/core/init_app.py` → `ensure_we123_scripts()`
- **调用时机**：`app/__init__.py` → `lifespan()` → `init_data()`

## 📝 脚本模板

脚本模板定义在 `app/crawler/we123_script_template.py`：

```python
WE123_SCRIPT_NAME = "we123小程序采集器"
WE123_SCRIPT_DESC = "自动采集we123.com小程序数据，支持断点续爬和循环模式"

WE123_DEFAULT_PARAMS = {
    "start_id": 1,
    "loop": False,
    "max_404_span": 500,
    "delay_sec": 3.0,
    "ua": "",
    "proxy": ""
}

WE123_SCRIPT_CODE = '''
#!/usr/bin/env python3
# ... 完整脚本代码 ...
'''
```

## 🔧 自定义和扩展

### 修改默认参数

编辑 `app/crawler/we123_script_template.py` 中的 `WE123_DEFAULT_PARAMS`，重启应用后会更新到数据库。

### 修改脚本代码

1. **方式一**：直接在界面编辑（仅临时修改，下次启动会被覆盖）
2. **方式二**：编辑 `app/crawler/we123_script_template.py` 中的 `WE123_SCRIPT_CODE`（永久修改）

### 添加更多 we123 相关脚本

可以在 `ensure_we123_scripts()` 函数中添加更多脚本，例如：
- we123 数据清洗脚本
- we123 数据导出脚本
- we123 统计分析脚本

## 🎯 使用场景

### 场景1：一次性全量采集

```json
{
  "start_id": 1,
  "loop": false,
  "max_404_span": 500,
  "delay_sec": 3.0
}
```

从 ID=1 开始采集，遇到连续 500 个 404 后停止。

### 场景2：循环增量更新

```json
{
  "start_id": 1,
  "loop": true,
  "max_404_span": 200,
  "delay_sec": 5.0
}
```

循环采集，达到连续 200 个 404 后从头开始。适合定时任务持续更新。

### 场景3：使用代理采集

```json
{
  "start_id": 1,
  "loop": false,
  "max_404_span": 500,
  "delay_sec": 3.0,
  "proxy": "http://proxy.example.com:8080"
}
```

通过代理服务器采集，避免IP被封。

## ⚠️ 注意事项

1. **依赖要求**：需要安装 DrissionPage
   ```bash
   pip install DrissionPage
   ```

2. **数据库表**：确保 `ods_wechat_mini_program` 表已创建

3. **任务互斥**：同时只能运行一个 we123 任务（通过单例模式保证）

4. **断点续爬**：任务状态保存在 `app_runtime/we123_xcx/state.json`

5. **XPath配置**：XPath 选择器配置在 `app_runtime/we123_xcx/xpaths.json`

6. **停止机制**：停止脚本会终止子进程，但 we123_task 单例会收到信号并优雅退出

## 📊 日志输出示例

```
[we123] 启动采集任务
  start_id: 1
  loop: False
  max_404_span: 500
  delay_sec: 3.0
  ua: default
  proxy: none
[we123] 任务已启动
[we123] 任务完成
  成功: 1234
  404: 500
  错误: 5
  最后ID: 1739
```

## 🔗 相关文件

- **脚本模板**：`app/crawler/we123_script_template.py`
- **初始化逻辑**：`app/core/init_app.py`
- **任务实现**：`app/crawler/strategies/we123_xcx.py`
- **API 接口**：`app/api/v1/crawler/we123.py`

## 🚀 后续计划

- [ ] 支持多任务并行（不同起始ID段）
- [ ] 更详细的进度统计和可视化
- [ ] 数据质量检查和清洗
- [ ] 导出为 CSV/Excel
- [ ] 定时任务调度集成

---

**最后更新：** 2025-11-13
**文档版本：** 1.0
