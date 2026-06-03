"""伏笔追踪模块

追踪伏笔（plot threads/foreshadow）的：
- 状态 (pending/in_progress/recycled/invalid)
- 引入章节 (planted_chapter)
- 关键提及章节 (mentions)
- 预期回收章节 (expected_recycle_chapter)
- 实际回收章节 (recycled_chapter)
"""
from typing import Any, Dict, List, Optional

from infra.memory_system.state.state_manager import MemoryStateManager


class PlotThreadTracker:
    """伏笔追踪器

    管理所有伏笔的状态信息，基于 MemoryStateManager 提供持久化存储。
    伏笔状态：
    - pending: 待回收
    - in_progress: 进行中
    - recycled: 已回收
    - invalid: 已失效
    """

    VALID_STATUSES = {"pending", "in_progress", "recycled", "invalid"}
    VALID_EVENT_TYPES = {"mention", "activate", "recycle", "invalidate"}

    def __init__(self, config: Dict[str, Any]):
        """初始化伏笔追踪器

        Args:
            config: 配置字典，需包含 storage 字段
        """
        self.state_manager = MemoryStateManager(config)

    def plant_foreshadow(self, fp_id: str, metadata: Dict[str, Any]) -> None:
        """登记伏笔

        Args:
            fp_id: 伏笔唯一标识
            metadata: 伏笔元数据，包含以下字段（均为可选）：
                - title: str - 伏笔标题
                - description: str - 伏笔描述
                - planted_chapter: int - 引入章节
                - expected_recycle_chapter: int - 预期回收章节
                - status: str - 状态 (pending/in_progress/recycled/invalid)
                - mentions: List[int] - 提及章节列表
        """
        all_data = self.state_manager.load("plot_threads_file")

        if "foreshadows" not in all_data:
            all_data["foreshadows"] = {}

        fp_data = all_data["foreshadows"].get(fp_id, {})

        # 合并元数据
        for key, value in metadata.items():
            fp_data[key] = value

        # 设置默认状态
        if "status" not in fp_data:
            fp_data["status"] = "pending"

        # 初始化提及列表
        if "mentions" not in fp_data:
            fp_data["mentions"] = []

        # 如果有 planted_chapter 但没有 mentions 包含它，自动添加
        if "planted_chapter" in fp_data and fp_data["planted_chapter"] not in fp_data["mentions"]:
            fp_data["mentions"].append(fp_data["planted_chapter"])

        all_data["foreshadows"][fp_id] = fp_data
        self.state_manager.save("plot_threads_file", all_data)

    def update_foreshadow(
        self, fp_id: str, chapter: int, event_type: str
    ) -> None:
        """更新伏笔状态

        Args:
            fp_id: 伏笔唯一标识
            chapter: 事件发生章节
            event_type: 事件类型 (mention/activate/recycle/invalidate)
                - mention: 添加到提及章节列表，不改变状态
                - activate: 状态变为 in_progress
                - recycle: 状态变为 recycled，记录实际回收章节
                - invalidate: 状态变为 invalid
        """
        if event_type not in self.VALID_EVENT_TYPES:
            return

        all_data = self.state_manager.load("plot_threads_file")
        foreshadows = all_data.get("foreshadows", {})

        if fp_id not in foreshadows:
            return

        fp_data = foreshadows[fp_id]

        # 初始化提及列表
        if "mentions" not in fp_data:
            fp_data["mentions"] = []

        # 添加到提及章节列表
        if chapter not in fp_data["mentions"]:
            fp_data["mentions"].append(chapter)

        # 根据事件类型更新状态
        if event_type == "mention":
            pass  # 仅添加提及，不改变状态
        elif event_type == "activate":
            fp_data["status"] = "in_progress"
        elif event_type == "recycle":
            fp_data["status"] = "recycled"
            fp_data["recycled_chapter"] = chapter
        elif event_type == "invalidate":
            fp_data["status"] = "invalid"

        foreshadows[fp_id] = fp_data
        all_data["foreshadows"] = foreshadows
        self.state_manager.save("plot_threads_file", all_data)

    def get_foreshadow(self, fp_id: str) -> Optional[Dict[str, Any]]:
        """获取伏笔信息

        Args:
            fp_id: 伏笔唯一标识

        Returns:
            伏笔信息字典，如果不存在则返回 None
        """
        all_data = self.state_manager.load("plot_threads_file")
        foreshadows = all_data.get("foreshadows", {})
        return foreshadows.get(fp_id)

    def get_all_foreshadows(self) -> Dict[str, Dict[str, Any]]:
        """获取所有伏笔

        Returns:
            所有伏笔字典，键为伏笔ID，值为伏笔信息
        """
        all_data = self.state_manager.load("plot_threads_file")
        return all_data.get("foreshadows", {})

    def get_pending_foreshadows(self) -> Dict[str, Dict[str, Any]]:
        """获取待回收伏笔（pending 和 in_progress 状态）

        Returns:
            待回收伏笔字典，键为伏笔ID，值为伏笔信息
        """
        all_data = self.state_manager.load("plot_threads_file")
        foreshadows = all_data.get("foreshadows", {})

        return {
            fp_id: fp_data
            for fp_id, fp_data in foreshadows.items()
            if fp_data.get("status") in ("pending", "in_progress")
        }