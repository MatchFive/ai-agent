#!/bin/bash

# AI-Agent 服务启动脚本
# 用法: ./start_server.sh [backend|user|admin|all] [dev|prod]
# 示例:
#   ./start_server.sh all prod    # 生产模式启动所有服务
#   ./start_server.sh backend     # 开发模式启动后端
#   ./start_server.sh all dev     # 开发模式启动所有服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取服务器公网IP
get_public_ip() {
    local ip=""
    ip=$(curl -s --connect-timeout 2 ifconfig.me 2>/dev/null) || \
    ip=$(curl -s --connect-timeout 2 icanhazip.com 2>/dev/null) || \
    ip=$(curl -s --connect-timeout 2 ipecho.net/plain 2>/dev/null) || \
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

# 运行模式（开发/生产）
MODE="${2:-prod}"

# 打印帮助
print_help() {
    echo "用法: $0 [服务] [模式]"
    echo ""
    echo "服务:"
    echo "  backend    仅启动后端API服务"
    echo "  user       仅启动用户端前端服务"
    echo "  admin      仅启动管理端前端服务"
    echo "  all        启动所有服务 (默认)"
    echo ""
    echo "模式:"
    echo "  dev        开发模式 (使用 Vite 开发服务器)"
    echo "  prod       生产模式 (使用构建后的静态文件，默认)"
    echo ""
    echo "示例:"
    echo "  $0 all prod       # 生产模式启动所有服务"
    echo "  $0 backend        # 生产模式启动后端"
    echo "  $0 all dev        # 开发模式启动所有服务"
    echo "  $0 user dev       # 开发模式启动用户端"
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

# 检查并停止已运行的服务
stop_if_running() {
    local name="$1"
    local pid_file="$PID_DIR/${name}.pid"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[$name] 服务已在运行中，正在停止...${NC}"
        ./stop_server.sh "$name"
        sleep 2
    fi
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

    # 检查 conda 环境
    if command -v conda &> /dev/null; then
        echo -e "${BLUE}[后端] 检测到 conda，激活 ai_agent 环境...${NC}"
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate ai_agent 2>/dev/null || {
            echo -e "${YELLOW}[后端] 警告: ai_agent 环境不存在，使用默认 Python${NC}"
        }
    fi

    # 检查Python
    if ! command -v python &> /dev/null; then
        echo -e "${RED}[后端] 错误: 未找到Python${NC}"
        return 1
    fi

    # 检查依赖
    if ! python -c "import uvicorn" 2>/dev/null; then
        echo -e "${YELLOW}[后端] 正在安装依赖...${NC}"
        pip install -r requirements.txt
    fi

    # 启动后端服务 - 绑定到所有网络接口
    nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 \
        --workers 1 \
        --log-level info \
        >> "$log_file" 2>&1 &
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
        tail -n 20 "$log_file"
        return 1
    fi
}

# 启动用户端前端（开发模式）
start_user_dev() {
    local pid_file="$PID_DIR/user.pid"
    local log_file="$LOG_DIR/user.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[用户端] 服务已在运行中${NC}"
        return 0
    fi

    echo -e "${GREEN}[用户端] 正在启动（开发模式）...${NC}"

    cd "$PROJECT_DIR/frontend/user"

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}[用户端] 错误: 未找到 Node.js${NC}"
        return 1
    fi

    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[用户端] 正在安装依赖...${NC}"
        npm install
    fi

    # 启动 Vite 开发服务器
    nohup npm run dev -- --host 0.0.0.0 --port 3000 >> "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 3

    if is_running "$pid_file"; then
        echo -e "${GREEN}[用户端] 启动成功 (PID: $pid)${NC}"
        echo -e "${GREEN}[用户端] 本地地址: http://localhost:3000${NC}"
        echo -e "${GREEN}[用户端] 公网地址: http://${PUBLIC_IP}:3000${NC}"
    else
        echo -e "${RED}[用户端] 启动失败，请查看日志: $log_file${NC}"
        tail -n 20 "$log_file"
        return 1
    fi
}

# 启动用户端前端（生产模式）
start_user_prod() {
    local pid_file="$PID_DIR/user.pid"
    local log_file="$LOG_DIR/user.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[用户端] 服务已在运行中${NC}"
        return 0
    fi

    echo -e "${GREEN}[用户端] 正在启动（生产模式）...${NC}"

    cd "$PROJECT_DIR/frontend/user"

    # 检查 dist 目录是否存在
    if [ ! -d "dist" ]; then
        echo -e "${YELLOW}[用户端] dist 目录不存在，正在构建...${NC}"
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run build
    fi

    # 检查 serve 工具
    if ! command -v serve &> /dev/null; then
        echo -e "${YELLOW}[用户端] 正在安装 serve 工具...${NC}"
        npm install -g serve
    fi

    # 使用 serve 提供静态文件
    nohup serve -s dist -p 3000 >> "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 2

    if is_running "$pid_file"; then
        echo -e "${GREEN}[用户端] 启动成功 (PID: $pid)${NC}"
        echo -e "${GREEN}[用户端] 本地地址: http://localhost:3000${NC}"
        echo -e "${GREEN}[用户端] 公网地址: http://${PUBLIC_IP}:3000${NC}"
    else
        echo -e "${RED}[用户端] 启动失败，请查看日志: $log_file${NC}"
        tail -n 20 "$log_file"
        return 1
    fi
}

# 启动管理端前端（开发模式）
start_admin_dev() {
    local pid_file="$PID_DIR/admin.pid"
    local log_file="$LOG_DIR/admin.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[管理端] 服务已在运行中${NC}"
        return 0
    fi

    echo -e "${GREEN}[管理端] 正在启动（开发模式）...${NC}"

    cd "$PROJECT_DIR/frontend/admin"

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}[管理端] 错误: 未找到 Node.js${NC}"
        return 1
    fi

    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[管理端] 正在安装依赖...${NC}"
        npm install
    fi

    # 启动 Vite 开发服务器
    nohup npm run dev -- --host 0.0.0.0 --port 3001 >> "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 3

    if is_running "$pid_file"; then
        echo -e "${GREEN}[管理端] 启动成功 (PID: $pid)${NC}"
        echo -e "${GREEN}[管理端] 本地地址: http://localhost:3001${NC}"
        echo -e "${GREEN}[管理端] 公网地址: http://${PUBLIC_IP}:3001${NC}"
    else
        echo -e "${RED}[管理端] 启动失败，请查看日志: $log_file${NC}"
        tail -n 20 "$log_file"
        return 1
    fi
}

# 启动管理端前端（生产模式）
start_admin_prod() {
    local pid_file="$PID_DIR/admin.pid"
    local log_file="$LOG_DIR/admin.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[管理端] 服务已在运行中${NC}"
        return 0
    fi

    echo -e "${GREEN}[管理端] 正在启动（生产模式）...${NC}"

    cd "$PROJECT_DIR/frontend/admin"

    # 检查 dist 目录是否存在
    if [ ! -d "dist" ]; then
        echo -e "${YELLOW}[管理端] dist 目录不存在，正在构建...${NC}"
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run build
    fi

    # 检查 serve 工具
    if ! command -v serve &> /dev/null; then
        echo -e "${YELLOW}[管理端] 正在安装 serve 工具...${NC}"
        npm install -g serve
    fi

    # 使用 serve 提供静态文件
    nohup serve -s dist -p 3001 >> "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 2

    if is_running "$pid_file"; then
        echo -e "${GREEN}[管理端] 启动成功 (PID: $pid)${NC}"
        echo -e "${GREEN}[管理端] 本地地址: http://localhost:3001${NC}"
        echo -e "${GREEN}[管理端] 公网地址: http://${PUBLIC_IP}:3001${NC}"
    else
        echo -e "${RED}[管理端] 启动失败，请查看日志: $log_file${NC}"
        tail -n 20 "$log_file"
        return 1
    fi
}

# 启动用户端前端
start_user_frontend() {
    if [ "$MODE" = "dev" ]; then
        start_user_dev
    else
        start_user_prod
    fi
}

# 启动管理端前端
start_admin_frontend() {
    if [ "$MODE" = "dev" ]; then
        start_admin_dev
    else
        start_admin_prod
    fi
}

# 显示服务地址
show_service_info() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}服务地址 (模式: $MODE):${NC}"
    echo -e "  后端API:  http://${PUBLIC_IP}:8000"
    echo -e "  API文档:  http://${PUBLIC_IP}:8000/docs"
    echo -e "  用户端:   http://${PUBLIC_IP}:3000"
    echo -e "  管理端:   http://${PUBLIC_IP}:3001"
    echo -e "${GREEN}================================${NC}"
    echo ""

    if [ "$MODE" = "prod" ]; then
        echo -e "${BLUE}提示: 生产模式使用 Nginx 反向代理${NC}"
        echo -e "${BLUE}      用户端: http://${PUBLIC_IP}${NC}"
        echo -e "${BLUE}      管理端: http://${PUBLIC_IP}:3001${NC}"
        echo ""
    else
        echo -e "${YELLOW}提示: 开发模式直接访问端口${NC}"
        echo ""
    fi

    echo -e "${YELLOW}注意事项:${NC}"
    echo -e "  1. 确保防火墙已开放相应端口 (8000, 3000, 3001)"
    echo -e "  2. 日志文件位置: $LOG_DIR"
    echo -e "  3. 停止服务: ./stop_server.sh all"
    echo -e "  4. 查看状态: ./stop_server.sh status"
    echo ""
}

# 主函数
main() {
    local service="${1:-all}"

    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}AI-Agent 服务启动${NC}"
    echo -e "${GREEN}模式: $MODE${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""

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
            echo ""
            start_user_frontend
            echo ""
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

    show_service_info
}

main "$@"
