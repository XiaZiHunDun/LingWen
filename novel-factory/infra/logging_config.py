"""灵文系统结构化日志配置"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """JSON格式日志，便于日志分析"""

    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        })


def setup_logging(name="lingwen", log_dir="logs", level=logging.INFO):
    """初始化日志配置

    Args:
        name: 日志文件名（不含扩展名）
        log_dir: 日志目录
        level: 日志级别

    Returns:
        配置好的logger实例
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 文件handler - 结构化JSON
    file_handler = logging.FileHandler(log_path / f"{name}.json")
    file_handler.setFormatter(StructuredFormatter())
    file_handler.setLevel(level)

    # 控制台handler - 人类可读
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    console.setLevel(logging.WARNING)  # 默认只显示WARNING以上

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console)

    return logging.getLogger(name)


# 导出logger实例
logger = setup_logging()
