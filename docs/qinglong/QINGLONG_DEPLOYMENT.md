# 青龙面板 Docker 部署指南

## 📋 目录

- [简介](#简介)
- [前置条件](#前置条件)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [任务配置](#任务配置)
- [常见问题](#常见问题)
- [维护与监控](#维护与监控)

---

## 简介

本文档介绍如何使用 Docker 部署包含 DrissionPage + Chrome 的自定义青龙面板，用于定时执行微信小程序爬虫任务。

### 架构说明

- **基础镜像**: `whyour/qinglong:latest`
- **浏览器**: Chromium (Debian 官方仓库)
- **Python 依赖**: DrissionPage + 项目所需全部依赖
- **任务调度**: 青龙面板 Web UI
- **数据持久化**: Docker Volume 挂载

---

## 前置条件

### 系统要求

- **操作系统**: Linux / macOS / Windows (带 Docker Desktop)
- **Docker**: 20.10+ 
- **Docker Compose**: 1.29+
- **磁盘空间**: 至少 5GB 可用空间
- **内存**: 建议 2GB+

### 软件安装

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version
```

如未安装，请访问 [Docker 官网](https://docs.docker.com/get-docker/) 下载安装。

---

## 快速开始

### 1. 构建自定义镜像

在项目根目录执行：

```bash
# 构建镜像（首次约需 10-20 分钟）
docker build -f Dockerfile.qinglong -t vue-fastapi-admin-qinglong:latest .
```

**构建过程说明**：
- 安装 Chromium 浏览器及所有依赖库
- 安装中文字体支持
- 预装项目 Python 依赖（包括 DrissionPage）
- 配置 DrissionPage 默认使用 Chromium

### 2. 配置环境变量

复制环境变量模板并修改：

```bash
cp deploy/qinglong/.env.example deploy/qinglong/.env
```

编辑 `.env` 文件，重点配置：

```env
# 数据库连接（必填）
DATABASE_URL=postgresql://your_user:your_pass@your_host:5432/your_db

# 爬虫配置
MINI_PROGRAM_SOURCE=all
MINI_PROGRAM_LIMIT=100
USE_MOCK_ON_BROWSER_FAIL=false
```

### 3. 启动容器

```bash
# 使用 docker-compose 启动
docker-compose -f docker-compose.qinglong.yml up -d

# 查看日志
docker-compose -f docker-compose.qinglong.yml logs -f qinglong
```

### 4. 访问青龙面板

- **地址**: http://localhost:5700
- **默认账号**: admin
- **默认密码**: admin

> ⚠️ 首次登录后请立即修改密码！

---

## 详细配置

### 环境变量说明

#### 数据库配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | 数据库连接字符串 | `postgresql://user:pass@host:5432/db` |

支持的数据库：
- PostgreSQL (推荐)
- MySQL
- SQLite (简单场景)

#### 爬虫配置

| 变量名 | 说明 | 可选值 | 默认值 |
|--------|------|--------|--------|
| `MINI_PROGRAM_SOURCE` | 数据源 | `all` / `wechat_official` / `third_party` | `all` |
| `MINI_PROGRAM_LIMIT` | 单次抓取数量 | 正整数 | `100` |
| `USE_MOCK_ON_BROWSER_FAIL` | 浏览器失败时使用模拟数据 | `true` / `false` | `false` |

#### ORM 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TORTOISE_ORM_MODULE` | ORM 配置模块 | `app.core.settings` |
| `PYTHONPATH` | Python 路径 | `/ql/repo/vue-fastapi-admin` |

### 目录挂载说明

```yaml
volumes:
  - ./deploy/qinglong/data:/ql/data          # 青龙数据
  - ./deploy/qinglong/config:/ql/config      # 青龙配置
  - ./deploy/qinglong/scripts:/ql/scripts    # 青龙脚本
  - ./deploy/qinglong/repo:/ql/repo          # 青龙仓库
  - ./deploy/qinglong/log:/ql/log            # 日志文件
  - ./:/ql/repo/vue-fastapi-admin:ro         # 项目代码（只读）
```

---

## 任务配置

### 方式一：使用 Web UI 配置

1. 登录青龙面板: http://localhost:5700
2. 进入 **定时任务** 菜单
3. 点击 **添加任务**

**任务配置示例**：

- **名称**: 微信小程序爬虫
- **命令**: `bash /ql/repo/vue-fastapi-admin/deploy/qinglong/run_mini_program_spider.sh`
- **定时规则**: `0 2 * * *` (每天凌晨 2 点执行)
- **备注**: 从微信官方和第三方平台抓取小程序信息

### 方式二：直接运行 Python 脚本

**命令**:
```bash
cd /ql/repo/vue-fastapi-admin && python3 demo.py
```

**定时规则**:
- `0 2 * * *` - 每天 2:00
- `0 */6 * * *` - 每 6 小时
- `0 0 * * 1` - 每周一 0:00

### Cron 表达式说明

```
┌─────────── 分钟 (0 - 59)
│ ┌───────── 小时 (0 - 23)
│ │ ┌─────── 日期 (1 - 31)
│ │ │ ┌───── 月份 (1 - 12)
│ │ │ │ ┌─── 星期 (0 - 7, 0和7都表示周日)
│ │ │ │ │
* * * * *
```

**示例**:
- `30 3 * * *` - 每天 3:30
- `0 */2 * * *` - 每 2 小时
- `0 9-17 * * 1-5` - 工作日 9:00-17:00 整点

---

## 常见问题

### 1. 浏览器启动失败

**错误信息**:
```
Failed to launch browser: Could not find Chromium
```

**解决方法**:

进入容器检查：

```bash
# 进入容器
docker exec -it qinglong_spider bash

# 检查 Chromium
which chromium
chromium --version

# 测试启动
chromium --headless --no-sandbox --dump-dom https://www.baidu.com
```

如未找到浏览器，重新构建镜像：

```bash
docker-compose -f docker-compose.qinglong.yml down
docker build --no-cache -f Dockerfile.qinglong -t vue-fastapi-admin-qinglong:latest .
docker-compose -f docker-compose.qinglong.yml up -d
```

### 2. 数据库连接失败

**错误信息**:
```
OperationalError: could not connect to server
```

**排查步骤**:

1. 检查数据库地址是否可达：
   ```bash
   docker exec -it qinglong_spider ping your_db_host
   ```

2. 验证连接字符串格式：
   ```bash
   # PostgreSQL
   DATABASE_URL=postgresql://user:password@host:5432/database
   
   # MySQL
   DATABASE_URL=mysql://user:password@host:3306/database
   ```

3. 确保数据库允许容器 IP 连接（检查防火墙和 `pg_hba.conf`）

### 3. Python 模块导入失败

**错误信息**:
```
ModuleNotFoundError: No module named 'spiders'
```

**解决方法**:

检查 `PYTHONPATH` 设置：

```bash
docker exec -it qinglong_spider bash
cd /ql/repo/vue-fastapi-admin
echo $PYTHONPATH
python3 -c "import sys; print(sys.path)"
```

确保 `docker-compose.qinglong.yml` 中设置：

```yaml
environment:
  - PYTHONPATH=/ql/repo/vue-fastapi-admin
```

### 4. 权限问题

**错误信息**:
```
PermissionError: [Errno 13] Permission denied
```

**解决方法**:

```bash
# 修复挂载目录权限
chmod -R 755 ./deploy/qinglong/
chown -R 1000:1000 ./deploy/qinglong/
```

### 5. 内存不足

**症状**: 容器频繁重启，浏览器崩溃

**解决方法**:

调整 Docker 内存限制：

```yaml
# docker-compose.qinglong.yml
services:
  qinglong:
    mem_limit: 2g
    memswap_limit: 2g
```

或修改浏览器参数：

```yaml
environment:
  - CHROMIUM_ARGS=--disable-dev-shm-usage --single-process
```

---

## 维护与监控

### 查看日志

```bash
# 实时日志
docker-compose -f docker-compose.qinglong.yml logs -f qinglong

# 任务日志（青龙面板内）
# 访问 http://localhost:5700 -> 日志管理
```

### 容器管理

```bash
# 启动
docker-compose -f docker-compose.qinglong.yml up -d

# 停止
docker-compose -f docker-compose.qinglong.yml stop

# 重启
docker-compose -f docker-compose.qinglong.yml restart

# 删除（保留数据）
docker-compose -f docker-compose.qinglong.yml down

# 删除（清空数据）
docker-compose -f docker-compose.qinglong.yml down -v
```

### 更新镜像

```bash
# 重新构建
docker build -f Dockerfile.qinglong -t vue-fastapi-admin-qinglong:latest .

# 重启容器
docker-compose -f docker-compose.qinglong.yml up -d --force-recreate
```

### 备份数据

```bash
# 备份青龙数据
tar -czf qinglong-backup-$(date +%Y%m%d).tar.gz deploy/qinglong/data/

# 备份数据库（PostgreSQL 示例）
docker exec your_postgres_container pg_dump -U user database > backup.sql
```

### 性能监控

```bash
# 容器资源使用
docker stats qinglong_spider

# 磁盘使用
docker exec -it qinglong_spider df -h
```

---

## 安全建议

1. **修改默认密码**: 首次登录后立即修改青龙面板密码
2. **限制访问**: 使用防火墙限制 5700 端口访问
3. **定期更新**: 定期更新基础镜像和依赖包
4. **数据备份**: 定期备份 `deploy/qinglong/data/` 目录
5. **日志轮转**: 配置日志文件自动清理，防止磁盘占满

---

## 进阶配置

### 使用外部 Redis

如果已有 Redis 服务，可以移除 docker-compose 中的 redis 服务：

```yaml
environment:
  - CELERY_BROKER_URL=redis://your-redis-host:6379/0
```

### 多容器部署

在生产环境中，建议将青龙和业务服务分离：

```yaml
networks:
  app_network:
    external: true  # 使用外部网络
```

### 自定义 Chrome 参数

修改 `Dockerfile.qinglong` 中的 DrissionPage 配置：

```dockerfile
RUN echo '{\n\
  "browser_path": "/usr/bin/chromium",\n\
  "arguments": [\n\
    "--headless",\n\
    "--disable-gpu",\n\
    "--no-sandbox",\n\
    "--window-size=1920,1080",\n\
    "--user-agent=Your-Custom-UA"\n\
  ]\n\
}' > /root/.DrissionPage/configs.ini
```

---

## 参考资料

- [青龙面板官方文档](https://github.com/whyour/qinglong)
- [DrissionPage 文档](https://drissionpage.cn/)
- [Docker 官方文档](https://docs.docker.com/)
- [Cron 表达式在线生成](https://crontab.guru/)

---

## 问题反馈

如遇到问题，请提供以下信息：

1. 错误日志 (`docker-compose logs qinglong`)
2. 容器状态 (`docker ps -a`)
3. 系统环境 (操作系统、Docker 版本)
4. 配置文件内容 (脱敏后)

---

**最后更新**: 2025-11-18
**版本**: 1.0.0
