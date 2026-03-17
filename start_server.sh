#!/bin/bash

# AI-Agent 服务启动脚本
# 用法: ./start_server.sh [backend|user|admin|all]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取服务器公网IP
get_public_ip() {
    local ip=""
    ip=$(curl -s ifconfig.me 2>/dev/null) || \
    ip=$(curl -s icanhazip.com 2>/dev/null) || \
    ip=$(curl -s ipecho.net/plain 2>/dev/null) || \
    ip="YOUR_SERVER_IP"
    echo "$ip"
}

PUBLIC_IP=$(get_public_ip)

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/logs"

# 创建日志和PID目录
mkdir -p "$LOG_DIR"

# 打印帮助
print_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  backend    仅启动后端API服务"
    echo "  user       仅启动用户端前端服务"
    echo "  admin      仅启动管理端前端服务"
    echo "  all        启动所有服务 (默认)"
    echo "  help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0          # 启动所有服务"
    echo "  $0 backend  # 仅启动后端"
    echo ""
}

# 检查服务是否已运行
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 启动后端服务
start_backend() {
    local pid_file="$PID_DIR/backend.pid"
    local log_file="$LOG_DIR/backend.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[后端] 服务已在运行中${NC}"
        return 0
    fi

    echo -e "${GREEN}[后端] 正在启动...${NC}"

    cd "$PROJECT_DIR"

    # 检查Python环境
    if ! command -v python &> /dev/null; then
        echo -e "${RED}[后端] 错误: 未找到Python${NC}"
        return 1
    fi

    # 启动后端服务 - 绑定到所有网络接口
    nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 >> "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 2

    if is_running "$pid_file"; then
        echo -e "${GREEN}[后端] 启动成功 (PID: $pid)${NC}"
        echo -e "${GREEN}[后端] 本地地址: http://localhost:8000${NC}"
        echo -e "${GREEN}[后端] 公网地址: http://${PUBLIC_IP}:8000${NC}"
        echo -e "${GREEN}[后端] API文档: http://${PUBLIC_IP}:8000/docs${NC}"
    else
        echo -e "${RED}[后端] 启动失败，请查看日志: $log_file${NC}"
        return 1
    fi
}

# 启动用户端前端
start_user_frontend() {
    local pid_file="$PID_DIR/user.pid"
    local log_file="$LOG_DIR/user.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[用户端] 服务已在运行中${NC}"
        return 0
    fi

    echo -e "${GREEN}[用户端] 正在启动...${NC}"

    cd "$PROJECT_DIR/frontend/user"

    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[用户端] 正在安装依赖...${NC}"
        npm install
    fi

    # 启动前端服务
    nohup npm run dev >> "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 3

    if is_running "$pid_file"; then
        echo -e "${GREEN}[用户端] 启动成功 (PID: $pid)${NC}"
        echo -e "${GREEN}[用户端] 本地地址: http://localhost:3000${NC}"
        echo -e "${GREEN}[用户端] 公网地址: http://${PUBLIC_IP}:3000${NC}"
    else
        echo -e "${RED}[用户端] 启动失败，请查看日志: $log_file${NC}"
        return 1
    fi
}

# 启动管理端前端
start_admin_frontend() {
    local pid_file="$PID_DIR/admin.pid"
    local log_file="$LOG_DIR/admin.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[管理端] 服务已在运行中${NC}"
        return 0
    fi

    echo -e "${GREEN}[管理端] 正在启动...${NC}"

    cd "$PROJECT_DIR/frontend/admin"

    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[管理端] 正在安装依赖...${NC}"
        npm install
    fi

    # 启动前端服务
    nohup npm run dev >> "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 3

    if is_running "$pid_file"; then
        echo -e "${GREEN}[管理端] 启动成功 (PID: $pid)${NC}"
        echo -e "${GREEN}[管理端] 本地地址: http://localhost:3001${NC}"
        echo -e "${GREEN}[管理端] 公网地址: http://${PUBLIC_IP}:3001${NC}"
    else
        echo -e "${RED}[管理端] 启动失败，请查看日志: $log_file${NC}"
        return 1
    fi
}

# 主函数
main() {
    local service="${1:-all}"

    case "$service" in
        backend)
            start_backend
            ;;
        user)
            start_user_frontend
            ;;
        admin)
            start_admin_frontend
            ;;
        all)
            start_backend
            start_user_frontend
            start_admin_frontend
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
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}服务地址:${NC}"
    echo -e "  后端API:  http://${PUBLIC_IP}:8000"
    echo -e "  API文档:  http://${PUBLIC_IP}:8000/docs"
    echo -e "  用户端:   http://${PUBLIC_IP}:3000"
    echo -e "  管理端:   http://${PUBLIC_IP}:3001"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${YELLOW}提示: 请确保服务器防火墙已开放 8000, 3000, 3001 端口${NC}"
    echo -e "默认管理员: admin / 123456"
    echo ""
}

main "$@"
