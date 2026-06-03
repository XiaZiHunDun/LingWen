"""章节范围解析器"""
from typing import List


class RangeParser:
    """章节范围解析器

    支持格式:
        "1-5"      → [1, 2, 3, 4, 5]
        "3"        → [3]
        "1,3,5"    → [1, 3, 5]
        "1-3,5,7-9" → [1, 2, 3, 5, 7, 8, 9]
        "all"      → list(range(1, 361))
    """

    def __init__(self, all_chapters: int = 360):
        self.all_chapters = all_chapters

    def parse(self, range_str: str) -> List[int]:
        """
        解析范围字符串

        Args:
            range_str: 范围字符串

        Returns:
            章节编号列表

        Raises:
            ValueError: 范围格式错误
        """
        range_str = range_str.strip()

        if range_str.lower() == "all":
            return list(range(1, self.all_chapters + 1))

        result = set()
        parts = range_str.split(",")

        for part in parts:
            part = part.strip()
            if "-" in part:
                range_parts = part.split("-")
                if len(range_parts) != 2:
                    raise ValueError(f"Invalid range format: {part}")
                try:
                    start = int(range_parts[0].strip())
                    end = int(range_parts[1].strip())
                except ValueError:
                    raise ValueError(f"Invalid range format: {part}")
                if start > end:
                    raise ValueError(f"Invalid range: start ({start}) > end ({end})")
                if start < 1 or end > self.all_chapters:
                    raise ValueError(f"Range ({start}-{end}) exceeds valid chapter range (1-{self.all_chapters})")
                result.update(range(start, end + 1))
            else:
                try:
                    num = int(part)
                except ValueError:
                    raise ValueError(f"Invalid number format: {part}")
                if num < 1 or num > self.all_chapters:
                    raise ValueError(f"Chapter number ({num}) exceeds valid range (1-{self.all_chapters})")
                result.add(num)

        return sorted(list(result))
