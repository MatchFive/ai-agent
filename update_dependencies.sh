#!/bin/bash

# 依赖更新脚本
# 用法: bash update_dependencies.sh [backend|frontend|all]

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
echo -e "${GREEN}AI-Agent 依赖更新${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 更新后端依赖
update_backend() {
    echo -e "${BLUE}[后端] 更新 Python 依赖...${NC}"
    cd "$PROJECT_DIR"

    # 检查 conda 环境
    if command -v conda &> /dev/null; then
        echo -e "${GREEN}[后端] 检测到 conda，激活 ai_agent 环境...${NC}"
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate ai_agent 2>/dev/null || {
            echo -e "${YELLOW}[后端] 警告: ai_agent 环境不存在，使用当前 Python${NC}"
        }
    fi

    # 检查 Python
    if ! command -v pip &> /dev/null; then
        echo -e "${RED}[后端] 错误: 未找到 pip${NC}"
        return 1
    fi

    # 备份当前依赖
    if [ -f "requirements.txt" ]; then
        cp requirements.txt requirements.txt.backup
        echo -e "${GREEN}[后端] 已备份 requirements.txt${NC}"
    fi

    # 更新依赖
    echo -e "${GREEN}[后端] 正在更新依赖...${NC}"
    pip install -r requirements.txt --upgrade

    # 生成锁定文件
    echo -e "${GREEN}[后端] 生成依赖锁定文件...${NC}"
    pip freeze > requirements.lock

    echo -e "${GREEN}[后端] 依赖更新完成${NC}"
    echo -e "${GREEN}[后端] 锁定文件: requirements.lock${NC}"
}

# 更新前端依赖
update_frontend() {
    echo -e "${BLUE}[前端] 更新 Node.js 依赖...${NC}"
    cd "$PROJECT_DIR"

    # 检查 Node.js
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}[前端] 错误: 未找到 npm${NC}"
        return 1
    fi

    # 更新用户端
    if [ -d "frontend/user" ]; then
        echo -e "${GREEN}[用户端] 更新依赖...${NC}"
        cd frontend/user

        # 备份 package.json
        if [ -f "package.json" ]; then
            cp package.json package.json.backup
        fi

        # 清理旧的依赖
        echo -e "${YELLOW}[用户端] 清理旧依赖...${NC}"
        rm -rf node_modules package-lock.json

        # 安装新依赖
        echo -e "${GREEN}[用户端] 安装新依赖...${NC}"
        npm install

        cd "$PROJECT_DIR"
        echo -e "${GREEN}[用户端] 依赖更新完成${NC}"
    fi

    echo ""

    # 更新管理端
    if [ -d "frontend/admin" ]; then
        echo -e "${GREEN}[管理端] 更新依赖...${NC}"
        cd frontend/admin

        # 备份 package.json
        if [ -f "package.json" ]; then
            cp package.json package.json.backup
        fi

        # 清理旧的依赖
        echo -e "${YELLOW}[管理端] 清理旧依赖...${NC}"
        rm -rf node_modules package-lock.json

        # 安装新依赖
        echo -e "${GREEN}[管理端] 安装新依赖...${NC}"
        npm install

        cd "$PROJECT_DIR"
        echo -e "${GREEN}[管理端] 依赖更新完成${NC}"
    fi
}

# 检查版本
check_versions() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}版本信息:${NC}"
    echo -e "${BLUE}================================${NC}"

    # Python 版本
    if command -v python &> /dev/null; then
        echo -e "${GREEN}Python: $(python --version)${NC}"
    fi

    # pip 版本
    if command -v pip &> /dev/null; then
        echo -e "${GREEN}pip: $(pip --version | awk '{print $2}')${NC}"
    fi

    # Node.js 版本
    if command -v node &> /dev/null; then
        echo -e "${GREEN}Node.js: $(node --version)${NC}"
    fi

    # npm 版本
    if command -v npm &> /dev/null; then
        echo -e "${GREEN}npm: $(npm --version)${NC}"
    fi

    echo ""
}

# 主函数
main() {
    local target="${1:-all}"

    check_versions

    case "$target" in
        backend)
            update_backend
            ;;
        frontend)
            update_frontend
            ;;
        all)
            update_backend
            echo ""
            update_frontend
            ;;
        *)
            echo -e "${RED}错误: 未知选项 '$target'${NC}"
            echo "用法: $0 [backend|frontend|all]"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}依赖更新完成！${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""

    echo -e "${YELLOW}建议:${NC}"
    echo -e "  1. 查看更新日志: cat DEPENDENCIES_UPDATE.md"
    echo -e "  2. 测试后端: python -m uvicorn api.main:app --reload"
    echo -e "  3. 测试前端: cd frontend/user && npm run dev"
    echo -e "  4. 构建前端: ./build.sh all"
    echo ""
}

main "$@"
