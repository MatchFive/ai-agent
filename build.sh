#!/bin/bash

# 前端构建脚本
# 用法: ./build.sh [user|admin|all]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}前端构建脚本${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 构建用户端
build_user() {
    echo -e "${GREEN}[用户端] 开始构建...${NC}"
    cd "$PROJECT_DIR/frontend/user"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[用户端] 安装依赖...${NC}"
        npm install
    fi

    npm run build

    if [ -d "dist" ]; then
        echo -e "${GREEN}[用户端] 构建成功！${NC}"
        echo -e "${GREEN}[用户端] 输出目录: $PROJECT_DIR/frontend/user/dist${NC}"
    else
        echo -e "${RED}[用户端] 构建失败！${NC}"
        return 1
    fi
}

# 构建管理端
build_admin() {
    echo -e "${GREEN}[管理端] 开始构建...${NC}"
    cd "$PROJECT_DIR/frontend/admin"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[管理端] 安装依赖...${NC}"
        npm install
    fi

    npm run build

    if [ -d "dist" ]; then
        echo -e "${GREEN}[管理端] 构建成功！${NC}"
        echo -e "${GREEN}[管理端] 输出目录: $PROJECT_DIR/frontend/admin/dist${NC}"
    else
        echo -e "${RED}[管理端] 构建失败！${NC}"
        return 1
    fi
}

# 主函数
main() {
    local target="${1:-all}"

    case "$target" in
        user)
            build_user
            ;;
        admin)
            build_admin
            ;;
        all)
            build_user
            echo ""
            build_admin
            ;;
        *)
            echo -e "${RED}错误: 未知选项 '$target'${NC}"
            echo "用法: $0 [user|admin|all]"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}构建完成！${NC}"
    echo -e "${GREEN}================================${NC}"
}

main "$@"
