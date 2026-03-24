#!/bin/bash

# AI-Agent 环境初始化脚本
# 用法: ./init_env.sh [backend|frontend|db|all]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 打印帮助
print_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  backend    初始化后端Python环境"
    echo "  frontend   初始化前端环境 (用户端+管理端)"
    echo "  user       仅初始化用户端前端"
    echo "  admin      仅初始化管理端前端"
    echo "  db         初始化MySQL数据库"
    echo "  all        初始化所有环境 (默认)"
    echo "  check      检查环境依赖"
    echo "  help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0           # 初始化所有环境"
    echo "  $0 backend   # 仅初始化后端"
    echo "  $0 check     # 检查环境依赖"
    echo ""
}

# 打印标题
print_title() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查命令是否存在
check_command() {
    local cmd="$1"
    local name="$2"
    local url="$3"

    if command -v "$cmd" &> /dev/null; then
        local version=$($cmd --version 2>&1 | head -1)
        echo -e "${GREEN}✓ $name: $version${NC}"
        return 0
    else
        echo -e "${RED}✗ $name: 未安装${NC}"
        echo -e "  安装指南: $url"
        return 1
    fi
}

# 检查环境依赖
check_dependencies() {
    print_title "检查环境依赖"

    local all_ok=true

    echo -e "${YELLOW}必需依赖:${NC}"
    check_command "python3" "Python3" "https://www.python.org/downloads/" || all_ok=false
    check_command "pip3" "pip3" "https://pip.pypa.io/en/stable/installation/" || all_ok=false
    check_command "node" "Node.js" "https://nodejs.org/" || all_ok=false
    check_command "npm" "npm" "https://nodejs.org/" || all_ok=false

    echo ""
    echo -e "${YELLOW}可选依赖:${NC}"
    check_command "mysql" "MySQL Client" "https://dev.mysql.com/downloads/" || true
    check_command "redis-cli" "Redis Client" "https://redis.io/download" || true

    echo ""

    if [ "$all_ok" = true ]; then
        echo -e "${GREEN}所有必需依赖已安装!${NC}"
        return 0
    else
        echo -e "${RED}请先安装缺少的必需依赖${NC}"
        return 1
    fi
}

# 初始化后端环境
init_backend() {
    print_title "初始化后端环境"

    cd "$PROJECT_DIR"

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 Python3${NC}"
        return 1
    fi

    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 pip3${NC}"
        return 1
    fi

    echo -e "${GREEN}Python版本: $(python3 --version)${NC}"
    echo -e "${GREEN}pip版本: $(pip3 --version)${NC}"
    echo ""

    # 创建虚拟环境（可选）
    if [ "$USE_VENV" = "true" ]; then
        echo -e "${YELLOW}创建Python虚拟环境...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        echo -e "${GREEN}虚拟环境已激活${NC}"
    fi

    # 升级pip
    echo -e "${YELLOW}升级pip...${NC}"
    python3 -m pip install --upgrade pip -q

    # 安装依赖
    echo -e "${YELLOW}安装Python依赖...${NC}"
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt -q
        echo -e "${GREEN}✓ Python依赖安装完成${NC}"
    else
        echo -e "${RED}错误: 未找到 requirements.txt${NC}"
        return 1
    fi

    # 创建必要目录
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data"

    # 检查.env文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo -e "${YELLOW}创建 .env 配置文件...${NC}"
            cp .env.example .env
            echo -e "${GREEN}✓ .env 文件已创建，请编辑配置${NC}"
        fi
    else
        echo -e "${GREEN}✓ .env 文件已存在${NC}"
    fi

    echo ""
    echo -e "${GREEN}后端环境初始化完成!${NC}"
}

# 初始化前端通用函数
init_frontend_project() {
    local name="$1"
    local dir="$2"

    print_title "初始化${name}"

    cd "$PROJECT_DIR/$dir"

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}错误: 未找到 Node.js${NC}"
        return 1
    fi

    # 检查npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}错误: 未找到 npm${NC}"
        return 1
    fi

    echo -e "${GREEN}Node版本: $(node --version)${NC}"
    echo -e "${GREEN}npm版本: $(npm --version)${NC}"
    echo ""

    # 检查package.json
    if [ ! -f "package.json" ]; then
        echo -e "${RED}错误: 未找到 package.json${NC}"
        return 1
    fi

    # 清理旧的node_modules
    if [ -d "node_modules" ]; then
        echo -e "${YELLOW}清理旧的依赖...${NC}"
        rm -rf node_modules
    fi

    # 安装依赖
    echo -e "${YELLOW}安装${name}依赖...${NC}"
    npm install --silent

    echo ""
    echo -e "${GREEN}${name}初始化完成!${NC}"
}

# 初始化用户端前端
init_user_frontend() {
    init_frontend_project "用户端前端" "frontend/user"
}

# 初始化管理端前端
init_admin_frontend() {
    init_frontend_project "管理端前端" "frontend/admin"
}

# 初始化所有前端
init_frontend() {
    init_user_frontend
    init_admin_frontend
}

# 初始化数据库
init_database() {
    print_title "初始化数据库"

    # 加载.env文件
    if [ -f "$PROJECT_DIR/.env" ]; then
        echo -e "${YELLOW}加载配置文件...${NC}"
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi

    # 数据库配置
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-3306}"
    DB_USER="${DB_USER:-root}"
    DB_PASSWORD="${DB_PASSWORD:-}"
    DB_DATABASE="${DB_DATABASE:-ai_agent}"

    echo -e "${YELLOW}数据库配置:${NC}"
    echo "  主机: $DB_HOST:$DB_PORT"
    echo "  用户: $DB_USER"
    echo "  数据库: $DB_DATABASE"
    echo ""

    # 检查MySQL客户端
    if ! command -v mysql &> /dev/null; then
        echo -e "${YELLOW}警告: 未找到MySQL客户端，跳过数据库创建${NC}"
        echo -e "${YELLOW}请手动创建数据库:${NC}"
        echo ""
        echo "  CREATE DATABASE $DB_DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        echo ""
        return 0
    fi

    # 检查密码
    if [ -z "$DB_PASSWORD" ]; then
        echo -e "${YELLOW}警告: 未设置数据库密码 (DB_PASSWORD)${NC}"
        echo -e "${YELLOW}请在 .env 文件中设置数据库密码${NC}"
        return 1
    fi

    # 测试连接
    echo -e "${YELLOW}测试数据库连接...${NC}"
    if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" &>/dev/null; then
        echo -e "${RED}错误: 数据库连接失败${NC}"
        echo -e "${YELLOW}请检查数据库配置${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ 数据库连接成功${NC}"

    # 创建数据库
    echo -e "${YELLOW}创建数据库 (如果不存在)...${NC}"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e \
        "CREATE DATABASE IF NOT EXISTS $DB_DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

    echo -e "${GREEN}✓ 数据库创建成功${NC}"
    echo ""
    echo -e "${GREEN}数据库初始化完成!${NC}"
    echo -e "${YELLOW}注意: 数据表将在首次启动服务时自动创建${NC}"
}

# 初始化所有
init_all() {
    print_title "AI-Agent 环境初始化"

    echo -e "${YELLOW}即将初始化以下环境:${NC}"
    echo "  1. 后端 Python 环境"
    echo "  2. 用户端前端环境"
    echo "  3. 管理端前端环境"
    echo "  4. MySQL 数据库"
    echo ""

    read -p "是否继续? [y/N] " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}已取消${NC}"
        exit 0
    fi

    # 执行初始化
    init_backend
    init_user_frontend
    init_admin_frontend
    init_database

    print_title "初始化完成"

    echo -e "${GREEN}所有环境已初始化完成!${NC}"
    echo ""
    echo -e "${YELLOW}下一步:${NC}"
    echo "  1. 编辑 .env 文件配置数据库连接"
    echo "  2. 运行 ./start_server.sh 启动服务"
    echo ""
    echo -e "${GREEN}默认管理员: admin / 123456${NC}"
    echo ""
}

# 主函数
main() {
    local target="${1:-all}"

    # 解析参数
    case "$target" in
        backend)
            init_backend
            ;;
        frontend)
            init_frontend
            ;;
        user)
            init_user_frontend
            ;;
        admin)
            init_admin_frontend
            ;;
        db|database)
            init_database
            ;;
        all)
            init_all
            ;;
        check)
            check_dependencies
            ;;
        help|--help|-h)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知选项 '$target'${NC}"
            print_help
            exit 1
            ;;
    esac
}

# 运行
main "$@"
