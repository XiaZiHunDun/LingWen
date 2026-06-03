#!/usr/bin/env python3
"""
Regression Tracking System

Provides regression enforcement when chapters are fixed. When a chapter is fixed,
identifies related chapters that need to be re-reviewed based on:
- Same volume (卷)
- Chapters within ±20 of the fixed chapter
- Same plot thread / scene (based on issues_found)

This prevents new inconsistencies from being introduced into related chapters.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Constants
WORKFLOW_STATE_PATH = Path(__file__).parent.parent / "workflow_state.json"
VOLUME_DEFINITIONS = {
    "卷1": {"name": "废土星火", "chapters": (1, 120)},
    "卷2": {"name": "星际争锋", "chapters": (121, 240)},
    "卷3": {"name": "宇宙守护", "chapters": (241, 360)},
}
NEIGHBORHOOD_RANGE = 20


def parse_chapter_id(chapter_id: str) -> Optional[int]:
    """
    Parse a chapter ID string to extract the chapter number.

    Args:
        chapter_id: Chapter ID like "ch001", "ch050", "ch360"

    Returns:
        Chapter number as integer, or None if invalid
    """
    if not chapter_id:
        return None
    match = re.match(r"^ch(\d+)$", chapter_id.lower())
    if match:
        return int(match.group(1))
    return None


def get_volume_for_chapter(chapter_num: int) -> Optional[str]:
    """
    Determine which volume a chapter belongs to.

    Args:
        chapter_num: Chapter number

    Returns:
        Volume key like "卷1", "卷2", "卷3", or None if outside range
    """
    for volume_key, definition in VOLUME_DEFINITIONS.items():
        start, end = definition["chapters"]
        if start <= chapter_num <= end:
            return volume_key
    return None


def get_chapters_in_volume(volume_key: str) -> List[int]:
    """
    Get all chapter numbers in a volume.

    Args:
        volume_key: Volume key like "卷1"

    Returns:
        List of chapter numbers in the volume
    """
    if volume_key not in VOLUME_DEFINITIONS:
        return []
    start, end = VOLUME_DEFINITIONS[volume_key]["chapters"]
    return list(range(start, end + 1))


def get_neighbor_chapters(chapter_num: int, range_size: int = NEIGHBORHOOD_RANGE) -> List[int]:
    """
    Get chapters within ±range_size of the given chapter.

    Args:
        chapter_num: Reference chapter number
        range_size: How many chapters on each side (default 20)

    Returns:
        List of chapter numbers in the neighborhood
    """
    effective_min = max(1, chapter_num - range_size)
    effective_max = min(360, chapter_num + range_size)
    chapters = list(range(effective_min, effective_max + 1))
    # Exclude the chapter itself if it was in the range
    if chapter_num in chapters:
        chapters.remove(chapter_num)
    return chapters


def extract_plot_threads_from_issues() -> Dict[str, List[str]]:
    """
    Extract plot threads from the workflow state's issues_found section.

    A plot thread is identified by shared issues or proximity in the issues_found
    structure. Chapters that appear together in issue batches are considered
    to share a plot thread.

    Returns:
        Dict mapping chapter_id to list of related chapter_ids based on plot threads
    """
    issues_found = load_workflow_state().get("issues_found", {})

    # Build a graph of chapter relationships based on issue batches
    chapter_to_threads: Dict[str, Set[str]] = {}

    for batch_key, issues in issues_found.items():
        if not issues:  # Skip batches with no issues (they're marked "无问题，通过")
            continue

        # Extract chapter numbers from batch key like "ch001-ch010"
        match = re.match(r"ch(\d+)-ch(\d+)", batch_key)
        if match:
            batch_chapters = list(range(int(match.group(1)), int(match.group(2)) + 1))
        else:
            # Single chapter batch like "ch360"
            single_match = re.match(r"ch(\d+)", batch_key)
            if single_match:
                batch_chapters = [int(single_match.group(1))]
            else:
                continue

        # Add relationships between all chapters in the batch
        for ch_num in batch_chapters:
            ch_id = f"ch{ch_num:03d}"
            if ch_id not in chapter_to_threads:
                chapter_to_threads[ch_id] = set()

            # Link to all other chapters in the batch
            for other_ch_num in batch_chapters:
                if other_ch_num != ch_num:
                    other_ch_id = f"ch{other_ch_num:03d}"
                    chapter_to_threads[ch_id].add(other_ch_id)
                    # Also add reverse relationship
                    if other_ch_id not in chapter_to_threads:
                        chapter_to_threads[other_ch_id] = set()
                    chapter_to_threads[other_ch_id].add(ch_id)

    # Convert sets to lists
    return {k: list(v) for k, v in chapter_to_threads.items()}


def load_workflow_state() -> Dict:
    """Load the workflow state from JSON file."""
    if not WORKFLOW_STATE_PATH.exists():
        return {}
    with open(WORKFLOW_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_regression_queue() -> Dict:
    """Load the regression queue from workflow state."""
    state = load_workflow_state()
    return state.get("regression_queue", {})


def save_regression_queue(queue: Dict) -> None:
    """Save the regression queue to workflow state."""
    state = load_workflow_state()
    state["regression_queue"] = queue

    # Ensure atomic write
    temp_path = WORKFLOW_STATE_PATH.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    temp_path.replace(WORKFLOW_STATE_PATH)


def register_regression_check(chapter_id: str, reason: str = "") -> List[str]:
    """
    Register that a chapter has been fixed and track regression requirements.

    When a chapter is fixed, this function:
    1. Identifies related chapters based on volume, proximity, and plot threads
    2. Adds them to the regression queue
    3. Returns the list of chapters that need re-review

    Args:
        chapter_id: The fixed chapter ID (e.g., "ch050")
        reason: Optional description of what was fixed

    Returns:
        List of chapter IDs that need regression review
    """
    chapter_num = parse_chapter_id(chapter_id)
    if chapter_num is None:
        raise ValueError(f"Invalid chapter ID: {chapter_id}")

    # Get related chapters
    related = get_regression_chapters(chapter_id)

    # Load current queue
    queue = load_regression_queue()

    if "pending" not in queue:
        queue["pending"] = []

    # Add each related chapter to the queue if not already there
    for rel_id in related:
        # Check if already in queue
        if not any(item["chapter_id"] == rel_id for item in queue["pending"]):
            queue["pending"].append({
                "chapter_id": rel_id,
                "triggered_by": chapter_id,
                "reason": reason or f"Proximity/plot regression from {chapter_id}",
                "registered_at": datetime.now().strftime("%Y-%m-%d"),
            })

    save_regression_queue(queue)

    return related


def get_regression_chapters(chapter_id: str) -> List[str]:
    """
    Get all chapters that need regression review when the given chapter is fixed.

    Related chapters are determined by:
    1. Same volume (卷) - chapters in the same book volume
    2. Proximity - chapters within ±20 of the fixed chapter
    3. Plot threads - chapters that share issue batches in workflow state

    Args:
        chapter_id: The fixed chapter ID (e.g., "ch050")

    Returns:
        List of related chapter IDs that should be reviewed
    """
    chapter_num = parse_chapter_id(chapter_id)
    if chapter_num is None or chapter_num < 1 or chapter_num > 360:
        return []

    related: Set[str] = set()

    # 1. Same volume chapters
    volume = get_volume_for_chapter(chapter_num)
    if volume:
        volume_chapters = get_chapters_in_volume(volume)
        for ch_num in volume_chapters:
            if ch_num != chapter_num:
                related.add(f"ch{ch_num:03d}")

    # 2. Neighbor chapters (±20)
    neighbors = get_neighbor_chapters(chapter_num, NEIGHBORHOOD_RANGE)
    for ch_num in neighbors:
        related.add(f"ch{ch_num:03d}")

    # 3. Plot thread related chapters
    plot_threads = extract_plot_threads_from_issues()
    if chapter_id.lower() in plot_threads:
        for related_chapter in plot_threads[chapter_id.lower()]:
            related.add(related_chapter)

    # Sort for consistent output
    return sorted(related, key=lambda x: parse_chapter_id(x) or 0)


def get_pending_regression_checks() -> List[Dict]:
    """
    Get all pending regression checks from the queue.

    Returns:
        List of pending regression check items
    """
    queue = load_regression_queue()
    return queue.get("pending", [])


def clear_regression_check(chapter_id: str) -> bool:
    """
    Clear a specific regression check after it has been completed.

    Args:
        chapter_id: Chapter ID to clear from the queue

    Returns:
        True if the item was found and removed, False otherwise
    """
    queue = load_regression_queue()
    pending = queue.get("pending", [])

    original_len = len(pending)
    queue["pending"] = [item for item in pending if item["chapter_id"] != chapter_id]

    if len(queue["pending"]) < original_len:
        save_regression_queue(queue)
        return True
    return False


def clear_all_regression_checks() -> None:
    """Clear all pending regression checks."""
    queue = load_regression_queue()
    queue["pending"] = []
    save_regression_queue(queue)


# CLI interface for testing and manual operations
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Regression Tracking System")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # get-regression
    get_parser = subparsers.add_parser("get-regression", help="Get related chapters for regression")
    get_parser.add_argument("chapter_id", help="Chapter ID (e.g., ch050)")

    # register
    reg_parser = subparsers.add_parser("register", help="Register a chapter fix and track regression")
    reg_parser.add_argument("chapter_id", help="Chapter ID (e.g., ch050)")
    reg_parser.add_argument("--reason", default="", help="Reason for the fix")

    # pending
    subparsers.add_parser("pending", help="List pending regression checks")

    # clear
    clear_parser = subparsers.add_parser("clear", help="Clear a regression check")
    clear_parser.add_argument("chapter_id", help="Chapter ID to clear")

    args = parser.parse_args()

    if args.command == "get-regression":
        related = get_regression_chapters(args.chapter_id)
        print(f"Related chapters for {args.chapter_id}: {len(related)} total")
        for ch in related:
            print(f"  - {ch}")

    elif args.command == "register":
        related = register_regression_check(args.chapter_id, args.reason)
        print(f"Registered regression for {args.chapter_id}")
        print(f"Related chapters ({len(related)}): {', '.join(related[:10])}{'...' if len(related) > 10 else ''}")

    elif args.command == "pending":
        pending = get_pending_regression_checks()
        print(f"Pending regression checks: {len(pending)}")
        for item in pending:
            print(f"  - {item['chapter_id']} (triggered by {item['triggered_by']})")

    elif args.command == "clear":
        if clear_regression_check(args.chapter_id):
            print(f"Cleared regression check for {args.chapter_id}")
        else:
            print(f"No regression check found for {args.chapter_id}")

    else:
        parser.print_help()
