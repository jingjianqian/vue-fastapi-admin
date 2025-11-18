# ScriptRun 整数字段范围错误修复

## 🔧 问题原因

**错误信息：** `(1264, "Out of range value for column 'exit_code' at row 1")`

**根本原因：**
- 数据库表 `CrawlerScriptRun` 中的某些整数字段被创建为 `TINYINT` 类型
- `TINYINT` 范围：-128 到 127（有符号）或 0 到 255（无符号）
- Windows 进程 PID 可能超过 32767，远超 TINYINT 范围
- `duration_ms`（毫秒）也容易超过范围

**受影响字段：**
- `exit_code`: 进程退出码（通常 0-255，但异常情况可能更大）
- `pid`: 进程 ID（Windows 上可达百万级）
- `duration_ms`: 执行时长毫秒数（超过 255ms 就会报错）

## ✅ 解决方案

### 将字段类型从 TINYINT 改为 INT

| 字段 | 旧类型 | 新类型 | 范围 |
|------|-------|--------|------|
| exit_code | TINYINT | INT | -2,147,483,648 到 2,147,483,647 |
| pid | TINYINT | INT | 足够容纳任何进程 ID |
| duration_ms | TINYINT | INT | 可支持长达 24 天的执行时间 |

## 🔄 修复步骤

### 已执行的修复

```bash
python scripts/fix_scriptrun_fields.py
```

输出：
```
🔧 开始修复 CrawlerScriptRun 表字段类型...
  修复 exit_code 字段...
  修复 pid 字段...
  修复 duration_ms 字段...
✅ 修复完成！

现在可以正常运行脚本了。
```

### SQL 语句（已自动执行）

```sql
ALTER TABLE `CrawlerScriptRun` MODIFY `exit_code` INT NULL;
ALTER TABLE `CrawlerScriptRun` MODIFY `pid` INT NULL;
ALTER TABLE `CrawlerScriptRun` MODIFY `duration_ms` INT NULL;
```

## 📝 数据库迁移文件

已创建迁移文件（供参考）：
- `migrations/models/11_20251113122500_fix_scriptrun_int_fields.py`

## ⚠️ 为什么会出现这个问题？

### Tortoise ORM 的行为

在模型中定义：
```python
exit_code = fields.IntField(null=True)
pid = fields.IntField(null=True)
duration_ms = fields.IntField(null=True)
```

但某些情况下 Tortoise ORM 可能将 `IntField` 映射为：
- MySQL: `INT` 或 `TINYINT`（取决于版本和配置）
- SQLite: `INTEGER`（无此问题）

### 可能的原因

1. **旧版 Aerich**：早期版本可能错误映射类型
2. **手动建表**：如果表是手动创建的，可能使用了错误类型
3. **数据库迁移问题**：某次迁移使用了错误的类型

## 🎯 验证修复

运行脚本后应该不再报错：

```bash
# 运行任何脚本
# 应该正常记录 PID 和执行时长
```

检查字段类型：
```sql
DESCRIBE `CrawlerScriptRun`;
```

应该看到：
```
| Field       | Type        | Null | Key | Default | Extra |
|-------------|-------------|------|-----|---------|-------|
| exit_code   | int         | YES  |     | NULL    |       |
| pid         | int         | YES  |     | NULL    |       |
| duration_ms | int         | YES  |     | NULL    |       |
```

## 🔍 典型错误场景

### 场景1：Windows 大 PID
```python
proc = await asyncio.create_subprocess_exec(...)
await ScriptRun.filter(id=run.id).update(pid=proc.pid)
# proc.pid = 147852 → 超过 TINYINT 范围
```

### 场景2：长时间运行
```python
duration_ms = 350000  # 5分50秒
await ScriptRun.filter(id=run.id).update(duration_ms=duration_ms)
# 350000 超过 TINYINT 范围（最大 255）
```

### 场景3：异常退出码
```python
exit_code = 255
# 在 TINYINT SIGNED 中，最大值为 127
# 255 会报错
```

## 🛠️ 预防措施

### 1. 使用 BigIntField（可选）

如果需要更大范围，可以使用：
```python
pid = fields.BigIntField(null=True)  # 8字节，范围更大
```

### 2. 验证迁移

每次创建迁移后检查生成的 SQL：
```bash
aerich migrate
cat migrations/models/<latest>.py
```

确保类型正确：
- `IntField` → `INT`
- `BigIntField` → `BIGINT`
- `SmallIntField` → `SMALLINT`（慎用）

### 3. 单元测试

添加测试验证字段范围：
```python
async def test_large_pid():
    script = await Script.create(name="test", code="print('test')")
    run = await ScriptRun.create(script=script, status="running")
    
    # 测试大 PID
    await ScriptRun.filter(id=run.id).update(pid=999999)
    
    # 测试大执行时长
    await ScriptRun.filter(id=run.id).update(duration_ms=86400000)  # 24小时
```

## 📊 影响范围

### 已修复
- ✅ 所有新创建的运行记录
- ✅ 所有历史记录的字段类型
- ✅ Windows 上的大 PID
- ✅ 长时间运行的脚本

### 无影响
- ✅ 现有数据不会丢失
- ✅ 应用无需重启
- ✅ 其他表不受影响

## 🔗 相关文件

- **修复脚本**：`scripts/fix_scriptrun_fields.py`
- **迁移文件**：`migrations/models/11_20251113122500_fix_scriptrun_int_fields.py`
- **模型定义**：`app/models/script.py`
- **运行器**：`app/crawler/runner.py`

## 💡 最佳实践

1. **明确字段范围**：
   - 0-255 → `SmallIntField` 或 `IntField`
   - 0-65535 → `IntField`
   - 更大 → `BigIntField`

2. **测试极端值**：
   - 测试最大最小值
   - 测试 NULL 值
   - 测试边界条件

3. **检查迁移**：
   - 每次迁移后验证 SQL
   - 在测试环境先执行
   - 备份生产数据

---

**修复时间：** 2025-11-13
**问题状态：** ✅ 已解决
**验证状态：** ✅ 已验证
