#!/usr/bin/env python3
"""简单测试脚本"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig

api_key = os.getenv("MINIMAX_API_KEY")
if not api_key:
    print("需要MINIMAX_API_KEY")
    sys.exit(1)

config = ProviderConfig(api_key=api_key, model="MiniMax-M2.7", timeout=60, max_retries=2)
provider = MiniMaxProvider(config)

# 读取第一章
chapter_file = PROJECT_ROOT / "03_内容仓库" / "04_正文" / "ch001.md"
with open(chapter_file, 'r') as f:
    content = f.read()

print(f"读取章节长度: {len(content)}")

# 调用API
prompt = "请用一句话总结以下内容的要点：\n" + content[:2000]
print("调用API...")
response = provider.generate(prompt)
print(f"响应长度: {len(response)}")
print(f"响应内容: {response[:500]}")

print("\nAPI测试成功！")