#!/usr/bin/env python3
"""
合并正文工具 v2.0
用于将分章正文合并为卷正文或全文正文

修复: 跳过章节文件中的多余分隔行，只保留章节标题和正文内容

用法:
    python merge_chapters.py full              # 合并全文
    python merge_chapters.py volume 卷1 1 140  # 合并卷1 (1-140章)
    python merge_chapters.py stage 卷1_阶段1 1 20  # 合并阶段 (1-20章)
"""

import os
import sys
from pathlib import Path


def get_chapter_title(content: str) -> str:
    """从章节内容中提取标题（第一行）"""
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('='):
            return line
    return ""

def merge_chapters(chapter_dir: Path, start: int, end: int, output_file: Path, with_separators: bool = True):
    """合并指定范围的章节"""
    print(f"合并章节范围: ch{start:03d} - ch{end:03d}")
    print(f"输出文件: {output_file}")
    print()

    chapter_dir = Path(chapter_dir)
    merged_count = 0
    total = end - start + 1

    with open(output_file, 'w', encoding='utf-8') as out:
        for i in range(start, end + 1):
            fname = f"ch{i:03d}.md"
            fpath = chapter_dir / fname

            # 跳过大纲文件
            if '_大纲' in fname:
                continue

            if not fpath.exists():
                print(f"  ⚠ 缺失: {fname}")
                continue

            content = fpath.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 提取标题行（第一行，去除#后的空格）
            title_line = ""
            for line in lines:
                line = line.strip()
                if line and not line.startswith('='):
                    title_line = line
                    break

            # 提取正文（跳过前5行：分隔线+文件名+分隔线+空行+标题）
            # 章节文件结构:
            #   Line 1: ==================================================
            #   Line 2: 第xxx.md
            #   Line 3: ==================================================
            #   Line 4: (空行)
            #   Line 5: # 章节标题 或 空行
            #   Line 6+: 正文内容
            if len(lines) >= 6:
                body_lines = lines[5:]  # 从第6行开始是正文
            else:
                body_lines = lines

            # 清理正文末尾的章节标记
            while body_lines and (body_lines[-1].strip() == '' or
                                   body_lines[-1].strip() == '---' or
                                   '本章完' in body_lines[-1] or
                                   '第' in body_lines[-1] and '章' in body_lines[-1]):
                body_lines = body_lines[:-1]

            # 写入分隔符和标题
            if with_separators:
                out.write("\n\n==================================================\n\n")
                out.write(f"{title_line}\n\n")

            # 写入正文
            for line in body_lines:
                out.write(line + '\n')

            merged_count += 1
            if merged_count % 20 == 0:
                print(f"  已合并: {merged_count} / {total}")

    # 写入文件统计
    size = output_file.stat().st_size
    print()
    print("=== 合并完成 ===")
    print(f"输出文件: {output_file}")
    print(f"合并章节: {merged_count} 个")
    print(f"文件大小: {size / 1024 / 1024:.2f} MB")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chapter_dir = project_root / "03_内容仓库" / "04_正文"

    if cmd == "full":
        output_dir = project_root / "07_汇总仓库" / "全文正文"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "星陨纪元_全文正文_v9.10.md"
        merge_chapters(chapter_dir, 1, 360, output_file)

    elif cmd == "volume":
        if len(sys.argv) < 5:
            print("用法: merge_chapters.py volume 卷名 起始章 结束章")
            sys.exit(1)
        volume_name = sys.argv[2]
        start = int(sys.argv[3])
        end = int(sys.argv[4])
        output_dir = project_root / "07_汇总仓库" / "卷正文"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"星陨纪元_{volume_name}_正文_v9.10.md"
        merge_chapters(chapter_dir, start, end, output_file)

    elif cmd == "stage":
        if len(sys.argv) < 5:
            print("用法: merge_chapters.py stage 阶段名 起始章 结束章")
            sys.exit(1)
        stage_name = sys.argv[2]
        start = int(sys.argv[3])
        end = int(sys.argv[4])
        output_dir = project_root / "07_汇总仓库" / "阶段正文"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"星陨纪元_{stage_name}_正文_v9.10.md"
        merge_chapters(chapter_dir, start, end, output_file)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
