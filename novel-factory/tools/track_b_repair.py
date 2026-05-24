#!/usr/bin/env python3
"""
修复流水线 Track B: ch121-ch240
执行顺序：世界观统一 → AI痕迹消除 → 角色一致性
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.fix_worldview import WorldviewUnifier
from tools.llm_polish_chapters import ChapterPolisher
from tools.fix_character_consistency import CharacterConsistencyFixer

LOG_FILE = PROJECT_ROOT / "logs" / "minimax_review" / "track_b.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[TrackB] [{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")

def main():
    api_key = os.getenv('MINIMAX_API_KEY', '')
    if not api_key:
        log("ERROR: No API key")
        sys.exit(1)

    chapters = list(range(121, 241))  # ch121-ch240

    log("=" * 60)
    log("Track B 修复流水线启动 (ch121-ch240)")
    log("=" * 60)

    start_time = datetime.now()

    # Step 1: 世界观统一
    log("\n[Step 1/3] 世界观统一开始")
    unifier = WorldviewUnifier()

    for ch_num in chapters:
        content = unifier.read_chapter(ch_num)
        if not content:
            continue
        new_content, count = unifier.replace_worldview(content)
        if count > 0:
            unifier.write_chapter(ch_num, new_content)
            log(f"ch{ch_num:03d}: 替换 {count} 处")

    log("[Step 1/3] 世界观统一完成")

    # Step 2: AI痕迹消除
    log("\n[Step 2/3] AI痕迹消除开始")
    polisher = ChapterPolisher()
    patterns = [
        "他感到", "她感到", "它感到",
        "像枯叶", "像星辰", "像风中的",
        "那一刻", "突然", "紧接着",
        "首先", "其次", "最后",
        "可以看出", "值得注意的是", "实际上",
        "因此", "所以", "由于",
    ]

    polish_count = 0
    for ch_num in chapters:
        content = unifier.read_chapter(ch_num)
        if not content:
            continue

        needs_polish = False
        for pattern in patterns:
            if pattern in content:
                needs_polish = True
                break

        if needs_polish:
            polished, modified = polisher.polish_chapter(ch_num, patterns)
            if modified:
                polisher.write_chapter(ch_num, polished)
                log(f"ch{ch_num:03d}: AI痕迹消除完成")
                polish_count += 1

    log(f"[Step 2/3] AI痕迹消除完成 ({polish_count} 章有修改)")

    # Step 3: 角色一致性
    log("\n[Step 3/3] 角色一致性开始")
    fixer = CharacterConsistencyFixer(api_key=api_key)

    for ch_num in chapters:
        content = unifier.read_chapter(ch_num)
        if not content:
            continue

        issues = fixer.analyze_character_issues(ch_num, content)
        issue_count = len(issues) if isinstance(issues, list) else 0

        if issue_count > 0:
            fixer.fix_chapter(ch_num, issues)
            log(f"ch{ch_num:03d}: 修复 {issue_count} 个角色问题")

    log("[Step 3/3] 角色一致性完成")

    elapsed = (datetime.now() - start_time).total_seconds()
    log("\n" + "=" * 60)
    log(f"Track B 完成 - 耗时 {elapsed/60:.1f} 分钟")
    log("=" * 60)

    result = {
        "track": "B",
        "chapters": "ch121-ch240",
        "elapsed_minutes": elapsed / 60,
        "timestamp": datetime.now().isoformat()
    }
    result_file = PROJECT_ROOT / "logs" / "minimax_review" / "track_b_result.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()