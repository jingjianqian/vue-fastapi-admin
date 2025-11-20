# 青龙 Docker 部署任务清单

## 任务概述
创建包含 DrissionPage + Chrome 的自定义青龙 Docker 镜像，实现微信小程序爬虫的定时调度。

## 任务列表

### 1. 准备工作
- [ ] 更新 requirements.txt 添加 DrissionPage 和相关依赖
- [ ] 检查 demo.py 的青龙运行入口是否完整

### 2. Docker 相关文件
- [ ] 创建 Dockerfile.qinglong（青龙基础镜像 + Chrome + Python依赖）
- [ ] 创建 docker-compose.qinglong.yml（青龙容器编排配置）
- [ ] 创建 deploy/qinglong/ 目录存放青龙部署相关文件

### 3. 青龙配置文件
- [ ] 创建青龙任务示例脚本（qinglong_tasks.sh）
- [ ] 创建环境变量配置模板（.env.qinglong.example）

### 4. 部署文档
- [ ] 创建 QINGLONG_DEPLOYMENT.md（部署指南）
  - Docker 镜像构建步骤
  - 容器启动配置
  - 环境变量说明
  - 任务配置方法
  - 常见问题排查

### 5. 验证
- [ ] 确保 Dockerfile 可以成功构建
- [ ] 验证 docker-compose 配置正确性

## 关键技术点

### Chrome 安装方案
- 使用 Chromium 官方包（适配 Debian）
- 配置无头模式运行参数
- 处理中文字体支持

### DrissionPage 配置
- 指定 Chrome 路径
- 配置浏览器启动参数
- 处理容器内权限问题

### 青龙集成
- 挂载项目目录到容器
- 配置 PYTHONPATH
- 设置数据库连接环境变量
