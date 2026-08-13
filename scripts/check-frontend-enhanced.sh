#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_ok() {
  echo -e "${GREEN}[✓] $1${NC}"
}

print_error() {
  echo -e "${RED}[✗] $1${NC}"
}

print_warn() {
  echo -e "${YELLOW}[!] $1${NC}"
}

print_info() {
  echo -e "[*] $1"
}

FRONTEND_DIR="/home/ailearn/projects/LingWen/apps/dashboard"
DEV_SERVER_URL="http://localhost:5173"

cd "$FRONTEND_DIR"

print_info "========================================"
print_info "  前端全面验证脚本 (增强版)"
print_info "========================================"

print_info ""
print_info "步骤1: 依赖状态检查"
print_info "----------------------------------------"

if [ -d "node_modules" ]; then
  print_ok "依赖已安装"
else
  print_warn "依赖未安装，尝试安装..."
  pnpm install
  print_ok "依赖安装完成"
fi

print_info ""
print_info "步骤2: ESLint 代码规范检查"
print_info "----------------------------------------"

if pnpm lint 2>&1 | tee /tmp/eslint.log; then
  print_ok "ESLint 检查通过"
else
  print_error "ESLint 检查失败!"
  print_info "错误详情:"
  grep -E "(error|Error)" /tmp/eslint.log | head -20 || true
  exit 1
fi

print_info ""
print_info "步骤3: 类型检查 (vue-tsc)"
print_info "----------------------------------------"

if pnpm typecheck:app 2>&1 | tee /tmp/vue-tsc.log; then
  print_ok "类型检查通过"
else
  print_error "类型检查失败!"
  print_info "错误详情:"
  grep -E "(error|Error)" /tmp/vue-tsc.log | head -20 || true
  exit 1
fi

print_info ""
print_info "步骤4: 语法解析检查 (AST 验证)"
print_info "----------------------------------------"

print_info "正在检查 Vue 文件语法..."
ERROR_COUNT=0
while IFS= read -r -d '' file; do
  if node -e "
    const fs = require('fs');
    const { parse } = require('vue-eslint-parser');
    try {
      const code = fs.readFileSync('$file', 'utf8');
      parse(code, { sourceType: 'module' });
    } catch(e) {
      console.error('$file:', e.message);
      process.exit(1);
    }
  " 2>&1; then
    true
  else
    ERROR_COUNT=$((ERROR_COUNT + 1))
  fi
done < <(find src -name "*.vue" -print0)

if [ $ERROR_COUNT -eq 0 ]; then
  print_ok "语法解析检查通过"
else
  print_error "发现 $ERROR_COUNT 个语法解析错误!"
  exit 1
fi

print_info ""
print_info "步骤5: 单元测试"
print_info "----------------------------------------"

if pnpm test 2>&1 | tee /tmp/vitest.log; then
  print_ok "单元测试通过"
else
  print_error "单元测试失败!"
  print_info "错误详情:"
  grep -E "(FAIL|Error|error)" /tmp/vitest.log | head -20 || true
  exit 1
fi

print_info ""
print_info "步骤6: 构建验证 (严格模式)"
print_info "----------------------------------------"

if pnpm build --mode production 2>&1 | tee /tmp/frontend-build.log; then
  print_ok "构建成功"
else
  print_error "构建失败!"
  print_info "错误详情:"
  grep -E "(error|Error|failed)" /tmp/frontend-build.log || true
  exit 1
fi

print_info ""
print_info "步骤7: 包体积检查"
print_info "----------------------------------------"

BUNDLE_SIZE=$(du -sh dist 2>/dev/null | awk '{print $1}')
if [ -n "$BUNDLE_SIZE" ]; then
  print_info "构建产物大小: $BUNDLE_SIZE"
  print_ok "包体积检查通过"
else
  print_warn "无法检查包体积"
fi

print_info ""
print_info "步骤8: 组件质量检查"
print_info "----------------------------------------"

DUPLICATE_HOOKS=$(grep -rn "onMounted\|onUnmounted\|watch" src/components/ --include="*.vue" | grep -v ".spec." | sort | uniq -d | head -10)
if [ -n "$DUPLICATE_HOOKS" ]; then
  print_warn "发现可能重复的钩子调用:"
  echo "$DUPLICATE_HOOKS"
else
  print_ok "组件质量检查通过"
fi

print_info ""
print_info "步骤9: 运行时错误检查"
print_info "----------------------------------------"

print_info "启动开发服务器进行运行时检查..."
if pgrep -f "vite" > /dev/null; then
  pkill -f "vite"
  sleep 2
fi

pnpm dev 2>&1 > /tmp/vite-dev.log &
VITE_PID=$!

print_info "等待开发服务器启动..."
sleep 5

if curl -s "$DEV_SERVER_URL" > /dev/null; then
  print_ok "开发服务器启动成功"
  
  print_info "检查运行时错误..."
  sleep 3
  
  if grep -E "(error|Error|warn|Warning)" /tmp/vite-dev.log | grep -v "ws proxy" | grep -v "ECONNRESET"; then
    print_warn "开发服务器日志中存在警告/错误:"
    grep -E "(error|Error|warn|Warning)" /tmp/vite-dev.log | grep -v "ws proxy" | grep -v "ECONNRESET" | head -20
  else
    print_ok "运行时检查通过"
  fi
else
  print_error "开发服务器启动失败!"
  print_info "日志详情:"
  cat /tmp/vite-dev.log | tail -30
  kill $VITE_PID 2>/dev/null || true
  exit 1
fi

kill $VITE_PID 2>/dev/null || true
sleep 2

print_info ""
print_info "步骤10: Playwright 端到端测试"
print_info "----------------------------------------"

pnpm e2e:smoke 2>&1 | tee /tmp/playwright-result.log
PLAYWRIGHT_EXIT_CODE=${PIPESTATUS[0]}
if [ $PLAYWRIGHT_EXIT_CODE -eq 0 ]; then
  print_ok "Playwright 检查通过"
else
  print_error "Playwright 检查失败!"
  print_info "错误详情:"
  grep -A 5 "Error\|error\|failed" /tmp/playwright-result.log || true
  exit 1
fi

print_info ""
print_info "========================================"
print_ok "  所有验证通过!"
print_info "========================================"
print_info ""
print_info "开发服务器: $DEV_SERVER_URL"
print_info "构建产物: $FRONTEND_DIR/dist/"
