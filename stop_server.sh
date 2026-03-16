#!/bin/bash

# AI-Agent 服务停止脚本
# 用法: ./stop_server.sh [backend|user|admin|all]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_DIR/logs"

# 打印帮助
print_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  backend    仅停止后端API服务"
    echo "  user       仅停止用户端前端服务"
    echo "  admin      仅停止管理端前端服务"
    echo "  all        停止所有服务 (默认)"
    echo "  help       显示此帮助信息"
    echo ""
}

# 停止服务
stop_service() {
    local name="$1"
    local pid_file="$PID_DIR/${name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}[$name] 未找到PID文件${NC}"
        return 0
    fi

    local pid=$(cat "$pid_file")

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}[$name] 进程已不存在${NC}"
        rm -f "$pid_file"
        return 0
    fi

    echo -e "${GREEN}[$name] 正在停止 (PID: $pid)...${NC}"

    # 发送TERM信号
    kill "$pid" 2>/dev/null || true

    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    # 如果进程还在运行，强制杀死
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}[$name] 强制停止...${NC}"
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi

    # 检查是否停止成功
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${RED}[$name] 停止失败${NC}"
        return 1
    else
        echo -e "${GREEN}[$name] 已停止${NC}"
        rm -f "$pid_file"
        return 0
    fi
}

# 停止后端服务
stop_backend() {
    stop_service "backend"
}

# 停止用户端前端
stop_user_frontend() {
    stop_service "user"
}

# 停止管理端前端
stop_admin_frontend() {
    stop_service "admin"
}

# 停止所有服务
stop_all() {
    stop_backend
    stop_user_frontend
    stop_admin_frontend
}

# 查看服务状态
show_status() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}服务状态:${NC}"

    for name in backend user admin; do
        local pid_file="$PID_DIR/${name}.pid"
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                echo -e "  $name: ${GREEN}运行中${NC} (PID: $pid)"
            else
                echo -e "  $name: ${RED}已停止${NC} (PID文件存在但进程不存在)"
            fi
        else
            echo -e "  $name: ${YELLOW}未运行${NC}"
        fi
    done

    echo -e "${GREEN}================================${NC}"
}

# 主函数
main() {
    local service="${1:-all}"

    # 如果PID目录不存在，创建它
    mkdir -p "$PID_DIR"

    case "$service" in
        backend)
            stop_backend
            ;;
        user)
            stop_user_frontend
            ;;
        admin)
            stop_admin_frontend
            ;;
        all)
            stop_all
            ;;
        status)
            show_status
            exit 0
            ;;
        help|--help|-h)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知选项 '$service'${NC}"
            print_help
            exit 1
            ;;
    esac

    echo ""
    show_status
}

main "$@"
