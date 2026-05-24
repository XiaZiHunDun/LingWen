#!/usr/bin/env python3
"""并行检查会话6: ch301-ch360"""
import os, sys, json, time
from pathlib import Path
from datetime import datetime
sys.path.insert(0, '/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory')
sys.path.insert(0, '.')
from infra.ai_service import MiniMaxProvider, ProviderConfig
from tools.minimax_batch_review import MiniMaxReviewer

log_file = '/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory/logs/minimax_review/session6.log'

def log(msg):
    print(f"[S6] {msg}", flush=True)
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

api_key = os.getenv('MINIMAX_API_KEY', '')
if not api_key:
    log("ERROR: No API key")
    sys.exit(1)

log("Starting session 6: ch301-ch360")
reviewer = MiniMaxReviewer(api_key)
results = []
start = datetime.now()

for ch in range(301, 360 + 1):
    r = reviewer.review_chapter(ch)
    results.append(r)
    if ch % 10 == 0:
        elapsed = (datetime.now() - start).total_seconds()
        total_calls = sum(x.get('llm_calls', 0) for x in results)
        log(f"ch{ch:03d} done: {total_calls} calls, {elapsed/60:.1f}min")

elapsed = (datetime.now() - start).total_seconds()
total_calls = sum(x.get('llm_calls', 0) for x in results)
log(f"COMPLETE: 60 chapters, {total_calls} calls, {elapsed/60:.1f}min")

with open('/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory/logs/minimax_review/session6_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
