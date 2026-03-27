#!/bin/bash

# AI-Agent 服务重启脚本
# 用法: ./restart_server.sh [backend|user|admin|all] [dev|prod]

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

SERVICE="${1:-all}"
MODE="${2:-prod}"

echo -e "\033[0;33m================================\033[0m"
echo -e "\033[0;33mAI-Agent 服务重启\033[0m"
echo -e "\033[0;33m服务: $SERVICE | 模式: $MODE\033[0m"
echo -e "\033[0;33m================================\033[0m"
echo ""

# 停止
echo -e "\033[0;32m[1/2] 停止服务...\033[0m"
"$PROJECT_DIR/stop_server.sh" "$SERVICE"
echo ""

# 等待端口释放
sleep 2

# 启动
echo -e "\033[0;32m[2/2] 启动服务...\033[0m"
"$PROJECT_DIR/start_server.sh" "$SERVICE" "$MODE"
