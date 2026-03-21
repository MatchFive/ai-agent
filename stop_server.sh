#!/bin/bash

# AI-Agent 服务停止脚本
# 用法: ./stop_server.sh [backend|user|admin|all|force]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo "  force      强制停止所有相关进程（包括未记录的）"
    echo "  status     查看服务状态"
    echo "  help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 停止所有服务"
    echo "  $0 backend      # 仅停止后端"
    echo "  $0 force        # 强制停止所有进程"
    echo ""
}

# 通过 PID 文件停止服务
stop_service() {
    local name="$1"
    local pid_file="$PID_DIR/${name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}[$name] 未找到PID文件${NC}"
        return 0
    fi

    local pid=$(cat "$pid_file")

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}[$name] 进程已不存在 (PID: $pid)${NC}"
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
        echo -e "${BLUE}[$name] 等待进程结束... ($count/10)${NC}"
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

# 通过端口停止服务
stop_by_port() {
    local port="$1"
    local name="$2"

    echo -e "${GREEN}[$name] 检查端口 $port ...${NC}"

    # 查找占用端口的进程
    local pids=$(lsof -ti:$port 2>/dev/null || true)

    if [ -z "$pids" ]; then
        echo -e "${YELLOW}[$name] 端口 $port 未被占用${NC}"
        return 0
    fi

    for pid in $pids; do
        local cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo -e "${GREEN}[$name] 发现进程 (PID: $pid, 命令: $cmd)${NC}"

        # 停止进程
        kill "$pid" 2>/dev/null || true
        sleep 2

        # 如果还在运行，强制停止
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${YELLOW}[$name] 强制停止进程 $pid${NC}"
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
        fi

        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${RED}[$name] 无法停止进程 $pid${NC}"
        else
            echo -e "${GREEN}[$name] 进程 $pid 已停止${NC}"
        fi
    done
}

# 通过进程名停止服务
stop_by_name() {
    local process_name="$1"
    local service_name="$2"

    echo -e "${GREEN}[$service_name] 查找进程: $process_name ...${NC}"

    # 查找进程
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)

    if [ -z "$pids" ]; then
        echo -e "${YELLOW}[$service_name] 未找到相关进程${NC}"
        return 0
    fi

    for pid in $pids; do
        local cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo -e "${GREEN}[$service_name] 发现进程 (PID: $pid, 命令: $cmd)${NC}"

        # 停止进程
        kill "$pid" 2>/dev/null || true
        sleep 1

        # 如果还在运行，强制停止
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${YELLOW}[$service_name] 强制停止进程 $pid${NC}"
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
        fi

        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${RED}[$service_name] 无法停止进程 $pid${NC}"
        else
            echo -e "${GREEN}[$service_name] 进程 $pid 已停止${NC}"
        fi
    done
}

# 停止后端服务
stop_backend() {
    stop_service "backend"
    # 额外检查端口
    stop_by_port 8000 "后端"
}

# 停止用户端前端
stop_user_frontend() {
    stop_service "user"
    # 额外检查端口和进程
    stop_by_port 3000 "用户端"
    stop_by_name "vite.*frontend/user" "用户端"
    stop_by_name "serve.*frontend/user" "用户端"
}

# 停止管理端前端
stop_admin_frontend() {
    stop_service "admin"
    # 额外检查端口和进程
    stop_by_port 3001 "管理端"
    stop_by_name "vite.*frontend/admin" "管理端"
    stop_by_name "serve.*frontend/admin" "管理端"
}

# 强制停止所有相关进程
force_stop_all() {
    echo -e "${RED}================================${NC}"
    echo -e "${RED}强制停止所有相关进程${NC}"
    echo -e "${RED}================================${NC}"
    echo ""

    # 停止后端
    echo -e "${GREEN}[后端] 停止所有 uvicorn 进程...${NC}"
    stop_by_name "uvicorn.*api.main" "后端"
    stop_by_port 8000 "后端"

    echo ""

    # 停止用户端
    echo -e "${GREEN}[用户端] 停止所有相关进程...${NC}"
    stop_by_name "vite.*frontend/user" "用户端"
    stop_by_name "serve.*frontend/user" "用户端"
    stop_by_port 3000 "用户端"

    echo ""

    # 停止管理端
    echo -e "${GREEN}[管理端] 停止所有相关进程...${NC}"
    stop_by_name "vite.*frontend/admin" "管理端"
    stop_by_name "serve.*frontend/admin" "管理端"
    stop_by_port 3001 "管理端"

    # 清理 PID 文件
    echo ""
    echo -e "${GREEN}[清理] 删除所有 PID 文件...${NC}"
    rm -f "$PID_DIR"/*.pid
    echo -e "${GREEN}[清理] PID 文件已清理${NC}"
}

# 停止所有服务
stop_all() {
    stop_backend
    echo ""
    stop_user_frontend
    echo ""
    stop_admin_frontend
}

# 查看服务状态
show_status() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}服务状态:${NC}"
    echo -e "${GREEN}================================${NC}"

    # 检查后端
    echo -e "${BLUE}后端服务 (端口 8000):${NC}"
    if [ -f "$PID_DIR/backend.pid" ]; then
        local pid=$(cat "$PID_DIR/backend.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "  状态: ${GREEN}运行中${NC} (PID: $pid)"
        else
            echo -e "  状态: ${RED}已停止${NC} (PID文件存在但进程不存在)"
        fi
    else
        echo -e "  状态: ${YELLOW}未运行${NC} (无PID文件)"
    fi

    # 检查端口占用
    local port_pids=$(lsof -ti:8000 2>/dev/null || true)
    if [ -n "$port_pids" ]; then
        echo -e "  端口占用: ${YELLOW}是${NC} (PIDs: $port_pids)"
    else
        echo -e "  端口占用: ${GREEN}否${NC}"
    fi

    echo ""

    # 检查用户端
    echo -e "${BLUE}用户端服务 (端口 3000):${NC}"
    if [ -f "$PID_DIR/user.pid" ]; then
        local pid=$(cat "$PID_DIR/user.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "  状态: ${GREEN}运行中${NC} (PID: $pid)"
        else
            echo -e "  状态: ${RED}已停止${NC} (PID文件存在但进程不存在)"
        fi
    else
        echo -e "  状态: ${YELLOW}未运行${NC} (无PID文件)"
    fi

    # 检查端口占用
    local port_pids=$(lsof -ti:3000 2>/dev/null || true)
    if [ -n "$port_pids" ]; then
        echo -e "  端口占用: ${YELLOW}是${NC} (PIDs: $port_pids)"
    else
        echo -e "  端口占用: ${GREEN}否${NC}"
    fi

    echo ""

    # 检查管理端
    echo -e "${BLUE}管理端服务 (端口 3001):${NC}"
    if [ -f "$PID_DIR/admin.pid" ]; then
        local pid=$(cat "$PID_DIR/admin.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "  状态: ${GREEN}运行中${NC} (PID: $pid)"
        else
            echo -e "  状态: ${RED}已停止${NC} (PID文件存在但进程不存在)"
        fi
    else
        echo -e "  状态: ${YELLOW}未运行${NC} (无PID文件)"
    fi

    # 检查端口占用
    local port_pids=$(lsof -ti:3001 2>/dev/null || true)
    if [ -n "$port_pids" ]; then
        echo -e "  端口占用: ${YELLOW}是${NC} (PIDs: $port_pids)"
    else
        echo -e "  端口占用: ${GREEN}否${NC}"
    fi

    echo ""
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${YELLOW}提示:${NC}"
    echo -e "  - 如果有端口被占用但无PID文件，可使用 './stop_server.sh force' 强制清理"
    echo -e "  - 查看日志: tail -f $PROJECT_DIR/logs/*.log"
    echo ""
}

# 主函数
main() {
    local service="${1:-all}"

    # 如果PID目录不存在，创建它
    mkdir -p "$PID_DIR"

    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}AI-Agent 服务管理${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""

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
        force)
            force_stop_all
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
