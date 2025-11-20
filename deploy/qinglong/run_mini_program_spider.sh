#!/bin/bash
# 微信小程序爬虫任务脚本
# 用于在青龙面板中定时执行

# 设置错误时退出
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}微信小程序爬虫任务开始执行${NC}"
echo -e "${GREEN}========================================${NC}"
echo "执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 进入项目目录
cd /ql/repo/vue-fastapi-admin

# 显示环境信息
echo -e "${YELLOW}[信息]${NC} Python 版本:"
python3 --version

echo -e "${YELLOW}[信息]${NC} 当前工作目录:"
pwd

echo -e "${YELLOW}[信息]${NC} 环境变量:"
echo "  - MINI_PROGRAM_SOURCE: ${MINI_PROGRAM_SOURCE:-all}"
echo "  - MINI_PROGRAM_LIMIT: ${MINI_PROGRAM_LIMIT:-100}"
echo "  - USE_MOCK_ON_BROWSER_FAIL: ${USE_MOCK_ON_BROWSER_FAIL:-true}"
echo ""

# 检查浏览器是否可用
echo -e "${YELLOW}[检查]${NC} Chromium 浏览器状态:"
if command -v chromium &> /dev/null; then
    chromium --version
    echo -e "${GREEN}✓${NC} 浏览器检查通过"
else
    echo -e "${RED}✗${NC} 浏览器未找到"
    exit 1
fi
echo ""

# 检查必要的依赖
echo -e "${YELLOW}[检查]${NC} Python 依赖:"
python3 -c "import DrissionPage; print(f'DrissionPage version: {DrissionPage.__version__}')" || {
    echo -e "${RED}✗${NC} DrissionPage 未安装"
    exit 1
}
echo -e "${GREEN}✓${NC} 依赖检查通过"
echo ""

# 执行爬虫脚本
echo -e "${YELLOW}[执行]${NC} 开始运行爬虫..."
python3 demo.py

# 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ 爬虫任务执行成功${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ 爬虫任务执行失败${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
