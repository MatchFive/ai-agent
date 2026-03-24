#!/bin/bash

# bcrypt 兼容性修复脚本
# 解决 passlib 与 bcrypt 4.1+ 不兼容的问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}bcrypt 兼容性修复${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 检查 conda 环境
if command -v conda &> /dev/null; then
    echo -e "${GREEN}[1/3] 激活 conda 环境...${NC}"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate ai_agent 2>/dev/null || {
        echo -e "${YELLOW}警告: ai_agent 环境不存在，使用当前环境${NC}"
    }
fi

# 显示当前版本
echo -e "${BLUE}[2/3] 检查当前版本...${NC}"
echo -e "当前 bcrypt 版本:"
pip show bcrypt 2>/dev/null | grep Version || echo "未安装"
echo -e "当前 passlib 版本:"
pip show passlib 2>/dev/null | grep Version || echo "未安装"
echo ""

# 修复 bcrypt 版本
echo -e "${GREEN}[3/3] 修复 bcrypt 版本...${NC}"
echo -e "${YELLOW}降级 bcrypt 到 4.0.1（兼容版本）${NC}"

# 卸载当前版本
pip uninstall -y bcrypt 2>/dev/null || true

# 安装兼容版本
pip install 'bcrypt>=4.0.1,<4.1.0'

echo ""

# 验证安装
echo -e "${BLUE}验证安装:${NC}"
BCRYPT_VERSION=$(pip show bcrypt | grep Version | awk '{print $2}')
PASSLIB_VERSION=$(pip show passlib | grep Version | awk '{print $2}')

echo -e "✓ bcrypt 版本: ${GREEN}$BCRYPT_VERSION${NC}"
echo -e "✓ passlib 版本: ${GREEN}$PASSLIB_VERSION${NC}"
echo ""

# 测试兼容性
echo -e "${BLUE}测试兼容性...${NC}"
python3 << 'EOF'
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash("test123")
    verified = pwd_context.verify("test123", hashed)
    if verified:
        print("✓ bcrypt 和 passlib 兼容性测试通过")
    else:
        print("✗ 验证失败")
        exit(1)
except Exception as e:
    print(f"✗ 测试失败: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}修复完成！${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${YELLOW}下一步:${NC}"
    echo -e "  1. 重启后端服务: ./stop_server.sh backend && ./start_server.sh backend"
    echo -e "  2. 查看日志: tail -f logs/backend.log"
    echo ""
else
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}修复失败！${NC}"
    echo -e "${RED}================================${NC}"
    echo ""
    echo -e "${YELLOW}请尝试手动修复:${NC}"
    echo -e "  pip uninstall -y bcrypt"
    echo -e "  pip install 'bcrypt>=4.0.1,<4.1.0'"
    echo ""
    exit 1
fi
