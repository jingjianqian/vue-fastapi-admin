# we123 脚本超时问题修复说明

## 🔧 问题原因

**错误信息：** `timeout of 12000ms exceeded`

**原因：**
- 原脚本设计为同步等待任务完成（可能需要几小时）
- 前端 API 请求有 12 秒超时限制
- 导致脚本启动后等待期间前端超时

## ✅ 解决方案

### 改为异步后台运行模式

**修改前：**
```python
# 启动任务
await we123_task.start(config)

# 等待任务完成（会阻塞很长时间）
while True:
    status = await we123_task.status()
    if not status.get('running'):
        break
    await asyncio.sleep(5)

# 输出最终结果
```

**修改后：**
```python
# 启动任务（立即返回）
await we123_task.start(config)
print(f"[we123] 任务已启动（后台运行）")

# 输出提示信息
print(f"任务在后台运行中，可以查看原 we123 界面区域获取实时状态")
return 0  # 立即返回，任务继续在后台运行
```

## 📝 使用方式

### 1. 运行脚本

点击"运行"按钮后：
- ✅ 脚本立即返回（不再等待）
- ✅ 任务在后台继续运行
- ✅ 输出启动成功提示

### 2. 查看实时状态

有三种方式查看任务状态：

#### 方式一：原 we123 界面区域
在爬虫平台页面下方的"we123 爬虫"卡片中：
- 点击"刷新状态"按钮
- 查看运行状态、成功数、404数、错误数等

#### 方式二：查看状态文件
```bash
# 状态文件路径
cat app_runtime/we123_xcx/state.json
```

内容示例：
```json
{
  "running": true,
  "last_id": 1523,
  "last_ok_id": 1520,
  "consecutive_404": 3,
  "ok_count": 1456,
  "not_found_count": 67,
  "error_count": 0
}
```

#### 方式三：API 接口
```bash
curl http://localhost:9999/api/v1/crawler/task/we123/status
```

### 3. 停止任务

有两种方式停止任务：

#### 方式一：脚本平台
如果记录了 run_id，可以在日志面板点击"停止"按钮

#### 方式二：原 we123 界面
在"we123 爬虫"卡片中点击"停止"按钮

#### 方式三：API 接口
```bash
curl -X POST http://localhost:9999/api/v1/crawler/task/we123/stop
```

## 🔍 脚本输出示例

运行成功后会看到：

```
[we123] 启动采集任务
  start_id: 1
  loop: False
  max_404_span: 500
  delay_sec: 3.0
  ua: default
  proxy: none
[we123] 任务已启动（后台运行）
  运行中: True
  起始ID: 1
  循环模式: False
  连续404上限: 500

💡 提示：任务在后台运行中，可以：
  1. 查看实时状态：访问原 we123 界面区域
  2. 停止任务：点击停止按钮或访问 /api/v1/crawler/task/we123/stop
  3. 查看进度：任务状态会定期更新到 app_runtime/we123_xcx/state.json

任务将持续运行直到：
  - 达到连续404上限: 500
  - 手动停止
  - 发生错误
```

## ⚠️ 特殊情况处理

### 重复启动
如果任务已在运行中，再次点击"运行"会提示：

```
[提示] 任务已在运行中，无需重复启动
  如需重启，请先停止当前任务
```

### 启动失败
如果启动失败（如缺少依赖），会显示错误信息：

```
[错误] 无法导入 we123_xcx 模块: No module named 'DrissionPage'
```

解决方法：
```bash
pip install DrissionPage
```

## 🔄 更新脚本

脚本代码已更新，有两种方式应用：

### 方式一：重启应用（自动更新）
```bash
# 停止应用
Ctrl+C

# 重启应用
python run.py
```

### 方式二：手动更新（无需重启）
```bash
python scripts/update_we123_script.py
```

输出：
```
✅ 已更新脚本: we123小程序采集器
   ID: 11
   描述: 自动采集we123.com小程序数据，支持断点续爬和循环模式
   代码行数: 94

💡 现在可以在界面中重新运行脚本
```

## 📊 优势对比

### 修改前（同步模式）
- ❌ 运行时间过长导致前端超时
- ❌ 无法在运行期间关闭界面
- ❌ 日志需要等任务完成才能看到

### 修改后（异步模式）
- ✅ 立即返回，不会超时
- ✅ 任务在后台持续运行
- ✅ 可随时查看实时状态
- ✅ 可随时停止任务
- ✅ 界面和任务完全解耦

## 🎯 最佳实践

1. **启动任务**：在脚本平台点击"运行"
2. **监控进度**：在原 we123 界面区域查看实时状态
3. **完成检查**：当状态显示 `running: false` 时任务完成
4. **查看结果**：在数据库或 ODS 表中查看采集数据

## 🔗 相关文件

- **脚本模板**：`app/crawler/we123_script_template.py`
- **更新工具**：`scripts/update_we123_script.py`
- **状态文件**：`app_runtime/we123_xcx/state.json`
- **完整文档**：`doc/we123_script_integration.md`

---

**修复时间：** 2025-11-13
**问题状态：** ✅ 已解决
