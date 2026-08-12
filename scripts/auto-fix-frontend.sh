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
CHECK_SCRIPT="/home/ailearn/projects/LingWen/scripts/check-frontend.sh"

cd "$FRONTEND_DIR"

print_info "========================================"
print_info "  前端自动修复脚本"
print_info "========================================"

MAX_RETRIES=3
RETRY_COUNT=0

fix_missing_import() {
  local error_msg="$1"
  local file_path="$2"
  
  local missing_var=$(echo "$error_msg" | grep -oP "'\K[^']+(?=' is not defined)" | head -1)
  if [ -z "$missing_var" ]; then
    return 1
  fi
  
  print_info "  检测到缺失变量: $missing_var"
  
  local vue_symbols="ref,reactive,computed,onMounted,onUnmounted,onCreated,onUpdated,provide,inject,watch,nextTick,defineProps,defineEmits,defineExpose"
  
  if echo "$vue_symbols" | grep -q "$missing_var"; then
    print_info "  $missing_var 是 Vue 内置符号，尝试添加到 import"
    
    local current_import=$(cat "$file_path" | grep "^import.*from 'vue'" | head -1)
    if [ -n "$current_import" ]; then
      local new_import=$(echo "$current_import" | sed "s/from 'vue'/,$missing_var from 'vue'/")
      sed -i "s|^import.*from 'vue'|$new_import|" "$file_path"
      print_ok "  已修复: 在 Vue import 中添加 $missing_var"
      return 0
    fi
  fi
  
  return 1
}

check_vue_tags() {
  local file_path="$1"
  
  if [ ! -f "$file_path" ]; then
    return 0
  fi
  
  local content=$(cat "$file_path")
  
  local open_tags=$(echo "$content" | grep -oP '<(\w+)[^>]*>' | grep -v '</' | grep -v '<br' | grep -v '<hr' | grep -v '<img' | grep -v '<input' | grep -v '<meta' | grep -v '<link' | grep -v '<br/>' | grep -v '<hr/>' | grep -v '<img/' | grep -v '<input/' | wc -l)
  local close_tags=$(echo "$content" | grep -oP '</(\w+)>' | wc -l)
  
  if [ "$open_tags" -ne "$close_tags" ]; then
    print_warn "  标签不匹配: $file_path"
    print_warn "    开始标签: $open_tags 个"
    print_warn "    结束标签: $close_tags 个"
    print_warn "    差异: $(($open_tags - $close_tags)) 个"
    return 1
  fi
  
  return 0
}

fix_vue_errors() {
  local error_file="/tmp/frontend-errors.log"
  local fixed=0
  
  if [ -f "$error_file" ]; then
    while IFS= read -r line; do
      if echo "$line" | grep -q "is not defined"; then
        local file_path=$(echo "$line" | grep -oP "at \K[^:]+.vue" | head -1)
        if [ -n "$file_path" ] && [ -f "$file_path" ]; then
          print_info "尝试修复: $file_path"
          if fix_missing_import "$line" "$file_path"; then
            fixed=1
          fi
        fi
      fi
      
      if echo "$line" | grep -q "Module not found"; then
        print_warn "  模块未找到，请检查 import 路径"
      fi
      
      if echo "$line" | grep -q "Invalid end tag"; then
        print_warn "  Vue 模板标签不匹配，请检查 HTML 结构"
      fi
      
      if echo "$line" | grep -q "Unexpected token"; then
        print_warn "  语法错误，请检查 JavaScript 代码"
      fi
    done < "$error_file"
  fi
  
  print_info "检查最近修改的 Vue 文件标签匹配..."
  local recently_modified=$(find src -name "*.vue" -mtime -1 | head -10)
  for file in $recently_modified; do
    if ! check_vue_tags "$file"; then
      print_warn "  请手动检查 $file 的标签结构"
    fi
  done
  
  return $fixed
}

run_check() {
  print_info ""
  print_info "运行检查脚本..."
  if bash "$CHECK_SCRIPT" 2>&1 | tee /tmp/check-result.log; then
    return 0
  else
    return 1
  fi
}

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  print_info ""
  print_info "第 $((RETRY_COUNT + 1)) 次尝试..."
  
  if run_check; then
    print_ok ""
    print_ok "前端检查通过!"
    exit 0
  fi
  
  print_info ""
  print_info "检查失败，尝试自动修复..."
  
  if fix_vue_errors; then
    print_ok "自动修复成功，重新检查..."
    RETRY_COUNT=$((RETRY_COUNT + 1))
    continue
  else
    print_warn "无法自动修复，请手动检查错误"
    print_info ""
    print_info "最近的错误日志:"
    tail -20 /tmp/check-result.log
    exit 1
  fi
done

print_error "达到最大重试次数 ($MAX_RETRIES)，修复失败"
print_info ""
print_info "请手动检查以下错误:"
tail -30 /tmp/check-result.log
exit 1