#!/usr/bin/env python3
"""
AI痕迹消除第二轮 - Track B
处理ch121-ch240的AI痕迹
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.llm_polish_chapters import ChapterPolisher

LOG_FILE = PROJECT_ROOT / "logs" / "minimax_review" / "track_b_polish2.log"

def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[TrackB-P2] [{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")

def main():
    chapters = list(range(121, 241))

    log("=" * 60)
    log("AI痕迹消除第二轮 - Track B (ch121-ch240)")
    log("=" * 60)

    polisher = ChapterPolisher()

    patterns = [
        '那一刻', '突然', '紧接着',
        '首先', '其次', '最后',
        '可以看出', '值得注意的是', '实际上',
        '因此', '所以', '由于',
        '他开始', '她开始', '它开始',
        '就在这时', '就在那时', '就这样',
        '不断地', '持续地',
        '缓缓地', '慢慢地', '渐渐地',
        '瞬间', '刹那', '霎时',
        '显然', '明显地', '显而易见',
        '一般来说', '从某种意义上说',
        '值得注意的是', '实际上而言',
    ]

    modified_count = 0
    for ch in chapters:
        content = polisher.read_chapter(ch)
        if not content:
            continue

        needs_polish = False
        for pattern in patterns:
            if pattern in content:
                needs_polish = True
                break

        if needs_polish:
            polished, modified = polisher.polish_chapter(ch, patterns)
            if modified:
                polisher.write_chapter(ch, polished)
                log(f"ch{ch:03d}: AI痕迹消除完成")
                modified_count += 1
            else:
                log(f"ch{ch:03d}: 润色无变化")
        else:
            log(f"ch{ch:03d}: 无需处理")

    log("=" * 60)
    log(f"Track B 第二轮完成: {modified_count}/{len(chapters)} 章有修改")
    log("=" * 60)

if __name__ == '__main__':
    main()