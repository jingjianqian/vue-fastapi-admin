# 青龙面板部署 - 快速开始

本目录包含使用 Docker 部署青龙面板（含 DrissionPage + Chrome）的所有配置文件。

## 📁 目录结构

```
deploy/qinglong/
├── README.md                    # 本文件
├── .env.example                 # 环境变量配置模板
├── run_mini_program_spider.sh  # 爬虫任务执行脚本
├── data/                        # 青龙数据目录（自动创建）
├── config/                      # 青龙配置目录（自动创建）
├── scripts/                     # 青龙脚本目录（自动创建）
├── repo/                        # 青龙仓库目录（自动创建）
└── log/                         # 日志目录（自动创建）
```

## 🚀 三步快速部署

### 1. 构建镜像

在**项目根目录**执行：

```bash
docker build -f Dockerfile.qinglong -t vue-fastapi-admin-qinglong:latest .
```

> ⏱️ 首次构建约需 10-20 分钟，包含 Chromium 安装和依赖下载

### 2. 配置环境

复制并编辑环境变量：

```bash
# 复制模板
cp deploy/qinglong/.env.example deploy/qinglong/.env

# 编辑配置（至少修改数据库连接）
# Windows: notepad deploy\qinglong\.env
# Linux/Mac: vi deploy/qinglong/.env
```

**必填配置**：
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 3. 启动服务

在**项目根目录**执行：

```bash
# 启动容器
docker-compose -f docker-compose.qinglong.yml up -d

# 查看启动日志
docker-compose -f docker-compose.qinglong.yml logs -f qinglong
```

等待 30-60 秒后，访问 http://localhost:5700

## 🎯 配置爬虫任务

### 登录青龙面板

- **地址**: http://localhost:5700
- **默认账号**: admin
- **默认密码**: admin

### 添加定时任务

1. 进入 **定时任务** 菜单
2. 点击 **添加任务**
3. 填写任务信息：

**推荐配置（使用脚本）**：
```
名称: 微信小程序爬虫
命令: bash /ql/repo/vue-fastapi-admin/deploy/qinglong/run_mini_program_spider.sh
定时: 0 2 * * *
```

**或者直接运行 Python**：
```
名称: 微信小程序爬虫
命令: cd /ql/repo/vue-fastapi-admin && python3 demo.py
定时: 0 2 * * *
```

### 定时规则参考

| 规则 | 说明 |
|------|------|
| `0 2 * * *` | 每天 2:00 |
| `0 */6 * * *` | 每 6 小时 |
| `30 3 * * *` | 每天 3:30 |
| `0 0 * * 1` | 每周一 0:00 |

## 🔧 常用命令

### 容器管理

```bash
# 查看状态
docker-compose -f docker-compose.qinglong.yml ps

# 查看日志
docker-compose -f docker-compose.qinglong.yml logs -f qinglong

# 重启服务
docker-compose -f docker-compose.qinglong.yml restart

# 停止服务
docker-compose -f docker-compose.qinglong.yml stop

# 启动服务
docker-compose -f docker-compose.qinglong.yml start
```

### 调试命令

```bash
# 进入容器
docker exec -it qinglong_spider bash

# 手动运行爬虫测试
docker exec -it qinglong_spider bash -c "cd /ql/repo/vue-fastapi-admin && python3 demo.py"

# 检查浏览器
docker exec -it qinglong_spider chromium --version

# 查看环境变量
docker exec -it qinglong_spider env | grep MINI_PROGRAM
```

## 📖 完整文档

详细配置、故障排查、进阶使用请查看：

- **完整部署文档**: [../../docs/qinglong/QINGLONG_DEPLOYMENT.md](../../docs/qinglong/QINGLONG_DEPLOYMENT.md)
- **技术方案**: [../../docs/qinglong/qinglong_mini_program_tech_solution.md](../../docs/qinglong/qinglong_mini_program_tech_solution.md)
- **需求说明**: [../../docs/qinglong/qinglong_mini_program_requirements.md](../../docs/qinglong/qinglong_mini_program_requirements.md)

## ⚠️ 常见问题

### 浏览器启动失败

```bash
# 进入容器检查
docker exec -it qinglong_spider bash
which chromium
chromium --version
```

### 数据库连接失败

检查 `.env` 文件中的 `DATABASE_URL` 配置：

```env
# PostgreSQL
DATABASE_URL=postgresql://username:password@host:5432/database

# 确保数据库可从容器访问
docker exec -it qinglong_spider ping your_db_host
```

### 模块导入失败

确保 `PYTHONPATH` 设置正确：

```bash
docker exec -it qinglong_spider bash -c "echo \$PYTHONPATH"
# 应该输出: /ql/repo/vue-fastapi-admin
```

## 🔐 安全提示

- ✅ 首次登录后立即修改青龙面板密码
- ✅ 定期备份 `deploy/qinglong/data/` 目录
- ✅ 生产环境使用防火墙限制 5700 端口访问
- ✅ 数据库密码不要直接写在 docker-compose.yml 中，使用 `.env` 文件

## 📊 监控建议

```bash
# 查看容器资源使用
docker stats qinglong_spider

# 查看磁盘使用
docker exec -it qinglong_spider df -h

# 查看任务日志（青龙面板内）
访问: http://localhost:5700 -> 日志管理
```

## 🆘 获取帮助

如遇问题，请检查：

1. 容器日志: `docker-compose -f docker-compose.qinglong.yml logs qinglong`
2. 容器状态: `docker ps -a | grep qinglong`
3. 环境变量: `docker exec qinglong_spider env`

---

**部署时间**: 约 15-30 分钟（含镜像构建）  
**难度**: ⭐⭐☆☆☆（中等）  
**维护成本**: ⭐☆☆☆☆（低）
