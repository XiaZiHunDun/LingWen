"""批量嵌入章节脚本

将 03_内容仓库/04_正文/ 目录下的章节文件向量化并存储到 Qdrant。
支持指定章节范围（ch001-ch050），显示进度信息，支持断点续传。

Usage:
    python -m memory_system.scripts.embed_chapters                    # 嵌入所有章节
    python -m memory_system.scripts.embed_chapters --start 1 --end 50  # 只嵌入前50章
    python -m memory_system.scripts.embed_chapters --dry-run          # 仅预览不执行
    python -m memory_system.scripts.embed_chapters --resume          # 断点续传（跳过已处理的章节）
    python -m memory_system.scripts.embed_chapters --max-retries 3    # 失败重试次数
"""
import argparse
import re
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

from memory_system.vector.embedder import Embedder
from memory_system.vector.qdrant_client import QdrantClientWrapper


# 章节内容仓库路径（相对于项目根目录）
CHAPTERS_DIR = Path("03_内容仓库/04_正文")
COLLECTION_NAME = "chapters_seg"

# 分段策略：按空行分割段落，合并为约 500 字符的片段
MAX_SEGMENT_CHARS = 500


def parse_chapter_number(filename: str) -> int | None:
    """从文件名提取章节编号

    Args:
        filename: 文件名，如 ch001.md

    Returns:
        章节编号（整数），无效则返回 None
    """
    match = re.match(r"ch(\d+)\.md", filename)
    return int(match.group(1)) if match else None


def split_into_segments(text: str) -> list[str]:
    """将章节内容分割成多个片段

    按空行分割段落，合并为约 MAX_SEGMENT_CHARS 字符的片段。

    Args:
        text: 章节原始文本

    Returns:
        片段列表
    """
    # 按空行分割成段落
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    segments = []
    current_segment = ""

    for para in paragraphs:
        # 如果单个段落超过限制，独立作为一个片段
        if len(para) > MAX_SEGMENT_CHARS:
            if current_segment:
                segments.append(current_segment)
                current_segment = ""

            # 进一步拆分长段落（按句子或固定长度）
            sentences = para.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n")
            for sentence in sentences.split("\n"):
                sentence = sentence.strip()
                if not sentence:
                    continue
                if len(current_segment) + len(sentence) <= MAX_SEGMENT_CHARS:
                    current_segment += ("。" if current_segment and not current_segment.endswith(("。", "！", "？")) else "") + sentence
                else:
                    if current_segment:
                        segments.append(current_segment)
                    current_segment = sentence
        else:
            if len(current_segment) + len(para) <= MAX_SEGMENT_CHARS:
                current_segment += ("\n\n" if current_segment else "") + para
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = para

    if current_segment:
        segments.append(current_segment)

    return segments


def load_chapters(start: int | None = None, end: int | None = None) -> list[tuple[int, str, str]]:
    """加载章节文件

    Args:
        start: 起始章节号（包含），None 表示从第一个开始
        end: 结束章节号（包含），None 表示到最后一个

    Returns:
        [(chapter_num, filename, content), ...] 按章节号排序
    """
    chapters_dir = CHAPTERS_DIR

    if not chapters_dir.exists():
        raise FileNotFoundError(f"Chapters directory not found: {chapters_dir}")

    chapters = []
    for file_path in sorted(chapters_dir.glob("ch*.md")):
        chapter_num = parse_chapter_number(file_path.name)
        if chapter_num is None:
            continue

        # 检查是否在指定范围内
        if start is not None and chapter_num < start:
            continue
        if end is not None and chapter_num > end:
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 跳过元数据行（以 # 或 --- 开头的行）
        lines = content.split("\n")
        skip_pattern = re.compile(r"^(#{1,6}\s|---|\*\*第.*完\*\*|#{3,})")
        content = "\n".join(line for line in lines if not skip_pattern.match(line.strip()))

        chapters.append((chapter_num, file_path.name, content.strip()))

    return sorted(chapters, key=lambda x: x[0])


def get_existing_point_ids(qdrant: QdrantClientWrapper, collection_name: str) -> set[str]:
    """获取集合中已存在的所有 point_id

    Args:
        qdrant: Qdrant 客户端实例
        collection_name: 集合名称

    Returns:
        已存在的 point_id 集合
    """
    existing_ids = set()

    # 使用 scroll API 遍历所有点
    try:
        results, _ = qdrant.client.scroll(
            collection_name=collection_name,
            limit=1000,
            with_payload=False,
            with_vectors=False,
        )

        for point in results:
            existing_ids.add(point.id)

        # 如果超过1000条，继续获取下一页
        while len(results) == 1000:
            results, _ = qdrant.client.scroll(
                collection_name=collection_name,
                limit=1000,
                offset=len(results),
                with_payload=False,
                with_vectors=False,
            )
            for point in results:
                existing_ids.add(point.id)

    except Exception:
        # 集合不存在或为空时返回空集合
        pass

    return existing_ids


def embed_chapters(
    chapters: list[tuple[int, str, str]],
    embedder: Embedder,
    qdrant: QdrantClientWrapper,
    dry_run: bool = False,
    resume: bool = False,
    batch_size: int = 20,
    max_retries: int = 3,
) -> dict:
    """批量嵌入章节到 Qdrant

    Args:
        chapters: [(chapter_num, filename, content), ...]
        embedder: 嵌入模型实例
        qdrant: Qdrant 客户端实例
        dry_run: True 则只预览不执行
        resume: True 则跳过已存在的向量（断点续传）
        batch_size: 每批嵌入的片段数量
        max_retries: 单章失败最大重试次数

    Returns:
        {
            "total_chapters": int,
            "total_segments": int,
            "embeddings_generated": int,
            "success_count": int,
            "fail_count": int,
            "skipped_count": int,
            "elapsed_time": float,
        }
    """
    results = {
        "total_chapters": len(chapters),
        "total_segments": 0,
        "embeddings_generated": 0,
        "success_count": 0,
        "fail_count": 0,
        "skipped_count": 0,
        "elapsed_time": 0.0,
    }

    start_time = time.time()

    # 断点续传：获取已存在的 point_id
    existing_point_ids = set()
    if resume and not dry_run:
        print("[Resume] Checking existing points in Qdrant...")
        existing_point_ids = get_existing_point_ids(qdrant, COLLECTION_NAME)
        print(f"[Resume] Found {len(existing_point_ids)} existing points")

    total_chapters = len(chapters)
    for idx, (chapter_num, filename, content) in enumerate(chapters):
        # 进度显示
        elapsed = time.time() - start_time
        avg_time = elapsed / max(idx, 1)
        remaining = avg_time * (total_chapters - idx - 1)
        remaining_str = str(timedelta(seconds=int(remaining))) if remaining > 0 else "--:--"

        print(f"\n[{idx + 1}/{total_chapters}] Processing {filename} | "
              f"Elapsed: {timedelta(seconds=int(elapsed))} | "
              f"ETA: {remaining_str}")

        segments = split_into_segments(content)
        results["total_segments"] += len(segments)

        if dry_run:
            print(f"  [DRY-RUN] {filename}: {len(segments)} segments")
            continue

        # 断点续传：检查本章是否已处理（通过 segment 0 判断）
        chapter_processed = True
        for j in range(len(segments)):
            point_id = f"ch{chapter_num:03d}_seg{j:03d}"
            if point_id not in existing_point_ids:
                chapter_processed = False
                break

        if resume and chapter_processed:
            print(f"  [SKIP] Chapter {chapter_num} already processed, skipping")
            results["skipped_count"] += 1
            continue

        # 重试机制
        retry_count = 0
        chapter_success = False
        points_to_insert = []

        while retry_count < max_retries and not chapter_success:
            try:
                # 批量嵌入（每批 batch_size 条）
                for i in range(0, len(segments), batch_size):
                    batch = segments[i:i + batch_size]
                    embeddings = embedder.embed_texts(batch)
                    results["embeddings_generated"] += len(embeddings)

                    for j, (segment, embedding) in enumerate(zip(batch, embeddings)):
                        seg_index = i + j
                        point_id = f"ch{chapter_num:03d}_seg{seg_index:03d}"

                        # 断点续传：跳过已存在的点
                        if resume and point_id in existing_point_ids:
                            continue

                        payload = {
                            "chapter": chapter_num,
                            "filename": filename,
                            "segment_index": seg_index,
                            "text": segment[:200],  # 只存储前200字符作为预览
                        }
                        points_to_insert.append({
                            "id": point_id,
                            "vector": embedding,
                            "payload": payload,
                        })

                # 每批嵌入后立即插入（减少内存占用）
                if points_to_insert:
                    qdrant.upsert(COLLECTION_NAME, points_to_insert)
                    print(f"  [INSERT] {len(points_to_insert)} points inserted to Qdrant")

                chapter_success = True
                results["success_count"] += 1
                print(f"  [OK] Chapter {chapter_num} completed ({len(segments)} segments)")

            except Exception as e:
                retry_count += 1
                print(f"  [ERROR] Chapter {chapter_num} failed (attempt {retry_count}/{max_retries}): {e}")

                if retry_count >= max_retries:
                    results["fail_count"] += 1
                    print(f"  [FATAL] Chapter {chapter_num} failed after {max_retries} attempts, continuing to next chapter")
                else:
                    # 重试前等待一下
                    time.sleep(2 ** retry_count)

    results["elapsed_time"] = time.time() - start_time
    return results


def main():
    parser = argparse.ArgumentParser(
        description="批量嵌入章节内容到 Qdrant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--start", type=int, default=None,
        help="起始章节号（如 1 表示 ch001）"
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="结束章节号（如 50 表示 ch050）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅预览不执行（显示将处理多少章节和片段）"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="断点续传模式，跳过已处理的章节"
    )
    parser.add_argument(
        "--batch-size", type=int, default=20,
        help="每批嵌入的片段数量（默认 20）"
    )
    parser.add_argument(
        "--max-retries", type=int, default=3,
        help="单章失败最大重试次数（默认 3）"
    )
    parser.add_argument(
        "--create-collection", action="store_true",
        help="如果集合不存在则创建"
    )

    args = parser.parse_args()

    print(f"=" * 60)
    print(f"批量嵌入章节到 Qdrant")
    print(f"=" * 60)
    print(f"Loading chapters from {CHAPTERS_DIR}")
    if args.start is not None or args.end is not None:
        print(f"  Range: ch{args.start or 1:03d} - ch{args.end or 'end':03d}")

    if args.resume:
        print(f"  Resume mode: ON (will skip existing points)")

    try:
        chapters = load_chapters(start=args.start, end=args.end)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not chapters:
        print("No chapters found in the specified range.")
        sys.exit(0)

    print(f"\nFound {len(chapters)} chapters")

    # 初始化组件
    if args.dry_run:
        print("\n--- DRY RUN MODE ---")
        embedder = None
        qdrant = None
    else:
        print("\nInitializing embedder and Qdrant client...")
        embedder = Embedder()
        qdrant = QdrantClientWrapper()

        # 可选：创建集合
        if args.create_collection:
            if not qdrant.collection_exists(COLLECTION_NAME):
                print(f"Creating collection: {COLLECTION_NAME}")
                qdrant.create_collection(COLLECTION_NAME)
            else:
                print(f"Collection '{COLLECTION_NAME}' already exists.")

    # 执行嵌入
    results = embed_chapters(
        chapters,
        embedder,
        qdrant,
        dry_run=args.dry_run,
        resume=args.resume,
        batch_size=args.batch_size,
        max_retries=args.max_retries,
    )

    # 显示结果和性能统计
    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"[Dry-run] Would process:")
        print(f"  - {results['total_chapters']} chapters")
        print(f"  - {results['total_segments']} segments")
    else:
        print(f"Completed:")
        print(f"  - {results['total_chapters']} chapters found")
        print(f"  - {results['success_count']} succeeded")
        print(f"  - {results['fail_count']} failed")
        print(f"  - {results['skipped_count']} skipped (resume mode)")
        print(f"  - {results['total_segments']} segments created")
        print(f"  - {results['embeddings_generated']} embeddings stored")
        print(f"\nPerformance Statistics:")
        print(f"  - Total time: {timedelta(seconds=int(results['elapsed_time']))}")
        if results['success_count'] > 0:
            avg_time = results['elapsed_time'] / results['success_count']
            print(f"  - Avg time per chapter: {avg_time:.2f}s")

        # 关闭连接
        qdrant.close()

    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())