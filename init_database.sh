#!/bin/bash

# 数据库初始化脚本
# 用法: bash init_database.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}AI-Agent 数据库初始化${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${RED}错误: .env 文件不存在${NC}"
    echo -e "${YELLOW}请先创建 .env 文件:${NC}"
    echo -e "  cp .env.example .env"
    echo -e "  vi .env"
    exit 1
fi

# 从 .env 文件读取配置
source .env

# 数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-ai_agent}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-ai_agent}"

echo -e "${BLUE}数据库配置:${NC}"
echo -e "  主机: $DB_HOST"
echo -e "  端口: $DB_PORT"
echo -e "  用户: $DB_USER"
echo -e "  数据库: $DB_NAME"
echo ""

# 提示输入 root 密码
echo -e "${YELLOW}请输入 MySQL root 用户密码:${NC}"
read -s MYSQL_ROOT_PASSWORD
echo ""

# 测试 root 连接
echo -e "${BLUE}[1/4] 测试 MySQL root 连接...${NC}"
if ! mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1;" &>/dev/null; then
    echo -e "${RED}错误: 无法连接到 MySQL，请检查 root 密码${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MySQL root 连接成功${NC}"
echo ""

# 创建数据库
echo -e "${BLUE}[2/4] 创建数据库 '$DB_NAME'...${NC}"
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
echo -e "${GREEN}✓ 数据库已创建${NC}"
echo ""

# 创建用户并授权
echo -e "${BLUE}[3/4] 创建用户并授权...${NC}"
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS '${DB_USER}'@'${DB_HOST}' IDENTIFIED BY '${DB_PASSWORD}';

-- 授予权限
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'${DB_HOST}';

-- 刷新权限
FLUSH PRIVILEGES;
EOF
echo -e "${GREEN}✓ 用户已创建并授权${NC}"
echo ""

# 测试用户连接
echo -e "${BLUE}[4/4] 测试用户连接...${NC}"
if [ -n "$DB_PASSWORD" ]; then
    if mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" -e "SELECT 1;" &>/dev/null; then
        echo -e "${GREEN}✓ 用户连接成功${NC}"
    else
        echo -e "${YELLOW}⚠ 用户连接失败，请检查配置${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 密码为空，跳过连接测试${NC}"
fi
echo ""

# 完成
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}数据库初始化完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

echo -e "${YELLOW}下一步:${NC}"
echo -e "  1. 检查 .env 文件中的数据库配置"
echo -e "  2. 启动后端服务: ./start_server.sh backend"
echo -e "  3. 查看日志: tail -f logs/backend.log"
echo ""

# 显示数据库信息
echo -e "${BLUE}数据库信息:${NC}"
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
SELECT
    user,
    host,
    CONCAT('GRANT ', GROUP_CONCAT(privilege_type SEPARATOR ', '), ' ON ', table_schema, '.* TO ', user, '@', host) AS grants
FROM mysql.user
JOIN information_schema.schema_privileges
    ON mysql.user.user = information_schema.schema_privileges.grantee
WHERE user = '${DB_USER}' AND table_schema = '${DB_NAME}'
GROUP BY user, host, table_schema;
EOF
