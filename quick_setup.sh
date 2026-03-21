#!/bin/bash

# 快速部署脚本 - 在服务器上运行
# 用法: bash quick_setup.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}AI-Agent 快速部署脚本${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 1. 检查环境
echo -e "${BLUE}[1/6] 检查环境...${NC}"

# 检查 Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python: $(python --version)${NC}"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js${NC}"
    echo -e "${YELLOW}请安装 Node.js: https://nodejs.org/${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js: $(node --version)${NC}"
echo -e "${GREEN}✓ npm: $(npm --version)${NC}"

echo ""

# 2. 安装 Python 依赖
echo -e "${BLUE}[2/6] 安装 Python 依赖...${NC}"
cd "$PROJECT_DIR"

# 检查 conda
if command -v conda &> /dev/null; then
    echo -e "${GREEN}检测到 conda，激活环境...${NC}"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate ai_agent 2>/dev/null || {
        echo -e "${YELLOW}ai_agent 环境不存在，使用当前环境${NC}"
    }
fi

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Python 依赖安装完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到 requirements.txt${NC}"
fi

echo ""

# 3. 构建前端
echo -e "${BLUE}[3/6] 构建前端...${NC}"
cd "$PROJECT_DIR"

if [ -f "build.sh" ]; then
    chmod +x build.sh
    bash build.sh all
    echo -e "${GREEN}✓ 前端构建完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到构建脚本${NC}"
fi

echo ""

# 4. 设置脚本权限
echo -e "${BLUE}[4/6] 设置脚本权限...${NC}"
cd "$PROJECT_DIR"

chmod +x start_server.sh
chmod +x stop_server.sh
chmod +x build.sh
chmod +x quick_setup.sh

echo -e "${GREEN}✓ 脚本权限设置完成${NC}"
echo ""

# 5. 创建必要目录
echo -e "${BLUE}[5/6] 创建必要目录...${NC}"

mkdir -p logs
mkdir -p data

echo -e "${GREEN}✓ 目录创建完成${NC}"
echo ""

# 6. 配置文件检查
echo -e "${BLUE}[6/6] 检查配置文件...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env 文件不存在${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}请复制 .env.example 并修改配置${NC}"
        echo -e "${YELLOW}命令: cp .env.example .env${NC}"
    fi
else
    echo -e "${GREEN}✓ .env 文件存在${NC}"
fi

echo ""

# 完成
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}部署准备完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

echo -e "${BLUE}下一步操作:${NC}"
echo ""
echo -e "1. 配置环境变量（如果还没有）:"
echo -e "   ${YELLOW}cp .env.example .env${NC}"
echo -e "   ${YELLOW}vi .env${NC}"
echo ""
echo -e "2. 启动服务:"
echo -e "   ${YELLOW}./start_server.sh all prod${NC}"
echo ""
echo -e "3. 查看状态:"
echo -e "   ${YELLOW}./stop_server.sh status${NC}"
echo ""
echo -e "4. 查看日志:"
echo -e "   ${YELLOW}tail -f logs/*.log${NC}"
echo ""
