#!/usr/bin/env python3
"""并行批量审核脚本 - 统一入口

用法:
    python tools/parallel_batch.py --session 1 --start 1 --end 60
    python tools/parallel_batch.py --session 2 --start 61 --end 120

示例会话配置:
    Session 1: --session 1 --start 1 --end 60     (ch001-ch060)
    Session 2: --session 2 --start 61 --end 120    (ch061-ch120)
    Session 3: --session 3 --start 121 --end 180   (ch121-ch180)
    Session 4: --session 4 --start 181 --end 240    (ch181-ch240)
    Session 5: --session 5 --start 241 --end 300    (ch241-ch300)
    Session 6: --session 6 --start 301 --end 360    (ch301-ch360)
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path('/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, '.')

from infra.ai_service import MiniMaxProvider, ProviderConfig
from tools.minimax_batch_review import MiniMaxReviewer


def main():
    parser = argparse.ArgumentParser(description='并行批量审核脚本')
    parser.add_argument('--session', type=int, required=True, help='会话编号 (1-6)')
    parser.add_argument('--start', type=int, required=True, help='起始章节')
    parser.add_argument('--end', type=int, required=True, help='结束章节')
    args = parser.parse_args()

    session_id = args.session
    start_ch = args.start
    end_ch = args.end

    # 日志文件
    log_dir = PROJECT_ROOT / 'logs' / 'minimax_review'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f'session{session_id}.log'
    results_file = log_dir / f'session{session_id}_results.json'

    def log(msg):
        print(f"[S{session_id}] {msg}", flush=True)
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

    # 检查 API key
    api_key = os.getenv('MINIMAX_API_KEY', '')
    if not api_key:
        log("ERROR: No API key")
        sys.exit(1)

    # 验证范围
    if start_ch < 1 or end_ch > 360 or start_ch > end_ch:
        log(f"ERROR: Invalid range {start_ch}-{end_ch}, must be 1-360 and start <= end")
        sys.exit(1)

    log(f"Starting session {session_id}: ch{start_ch:03d}-ch{end_ch:03d}")
    reviewer = MiniMaxReviewer(api_key)
    results = []
    start_time = datetime.now()

    for ch in range(start_ch, end_ch + 1):
        r = reviewer.review_chapter(ch)
        results.append(r)
        if ch % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            total_calls = sum(x.get('llm_calls', 0) for x in results)
            log(f"ch{ch:03d} done: {total_calls} calls, {elapsed/60:.1f}min")

    elapsed = (datetime.now() - start_time).total_seconds()
    total_calls = sum(x.get('llm_calls', 0) for x in results)
    chapter_count = end_ch - start_ch + 1
    log(f"COMPLETE: {chapter_count} chapters, {total_calls} calls, {elapsed/60:.1f}min")

    with open(results_file, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log(f"Results saved to {results_file}")


if __name__ == '__main__':
    main()