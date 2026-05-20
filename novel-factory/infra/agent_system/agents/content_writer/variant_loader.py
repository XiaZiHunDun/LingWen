# novel-factory/infra/agent_system/agents/content_writer/variant_loader.py
"""作家变体配置加载器

根据writer_id加载对应的YAML配置，支持10个作家(A-J)。

Usage:
    from variant_loader import load_writer_variant

    config = load_writer_variant("a")  # 加载作家A配置
    config = load_writer_variant("writer_b")  # 支持full name
    config = load_writer_variant(2)  # 支持数字索引
"""
import os
from pathlib import Path
from typing import Dict, Optional, Union

import yaml

# 变体配置目录
VARIANTS_DIR = Path(__file__).parent / "variants"

# Writer ID 映射
WRITER_IDS = {
    "a": "variant_a.yaml",
    "b": "variant_b.yaml",
    "c": "variant_c.yaml",
    "d": "variant_d.yaml",
    "e": "variant_e.yaml",
    "f": "variant_f.yaml",
    "g": "variant_g.yaml",
    "h": "variant_h.yaml",
    "i": "variant_i.yaml",
    "j": "variant_j.yaml",
}

# 反向映射（支持全名如"writer_a"）
ALIASES = {
    "writer_a": "a",
    "writer_b": "b",
    "writer_c": "c",
    "writer_d": "d",
    "writer_e": "e",
    "writer_f": "f",
    "writer_g": "g",
    "writer_h": "h",
    "writer_i": "i",
    "writer_j": "j",
}

# 数字索引映射
NUMERIC_MAP = {
    1: "a", 2: "b", 3: "c", 4: "d", 5: "e",
    6: "f", 7: "g", 8: "h", 9: "i", 10: "j",
}

# 缓存
_config_cache: Dict[str, Dict] = {}


def _normalize_writer_id(writer_id: Union[str, int]) -> str:
    """标准化writer_id为单字母标识

    Args:
        writer_id: "a"/"writer_a"/1 等格式

    Returns:
        单字母标识符，如 "a"
    """
    if isinstance(writer_id, int):
        return NUMERIC_MAP.get(writer_id, WRITER_IDS[writer_id])

    # 去除空格和前缀
    wid = str(writer_id).strip().lower()

    # 检查是否是数字字符串
    if wid.isdigit():
        return NUMERIC_MAP.get(int(wid), wid)

    # 检查aliases（如 "writer_a" -> "a"）
    if wid in ALIASES:
        return ALIASES[wid]

    # 检查是否已经是单字母
    if wid in WRITER_IDS:
        return wid

    # 去除 "writer_" 前缀
    if wid.startswith("writer_"):
        wid = wid.replace("writer_", "")
        if wid in WRITER_IDS:
            return wid

    # 去除 "作家" 前缀（中文支持）
    if wid.startswith("作家"):
        wid = wid[1]  # 取第二个字符
        if wid in WRITER_IDS:
            return wid

    raise ValueError(f"Invalid writer_id: {writer_id}. Valid: a-j, writer_a-j, 1-10")


def load_writer_variant(writer_id: Union[str, int]) -> Dict:
    """加载作家变体配置

    Args:
        writer_id: 作家标识，支持以下格式：
            - 单字母: "a", "b", ..., "j"
            - 全名: "writer_a", "writer_b", ..., "writer_j"
            - 数字索引: 1, 2, ..., 10

    Returns:
        包含作家配置信息的字典，包含：
        - writer_id: 标准化ID
        - name: 作家名称
        - department: 所属部门
        - specialization: 专长领域
        - writing_style: 写作风格
        - sentence_preferences: 句式偏好
        - character_pacing: 角色节奏
        - system_prompt_additions: 系统提示补充
        - historical_performance: 历史表现
        - quality_targets: 质量目标

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: writer_id格式无效
    """
    normalized = _normalize_writer_id(writer_id)
    filename = WRITER_IDS[normalized]
    filepath = VARIANTS_DIR / filename

    # 检查缓存
    if normalized in _config_cache:
        return _config_cache[normalized].copy()

    if not filepath.exists():
        raise FileNotFoundError(f"Variant config not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 缓存
    _config_cache[normalized] = config

    return config.copy()


def get_writer_specialty(writer_id: Union[str, int]) -> Dict[str, list]:
    """获取作家专长领域

    Args:
        writer_id: 作家标识

    Returns:
        {"primary": [...], "secondary": [...], "adapted_scenes": [...]}
    """
    config = load_writer_variant(writer_id)
    return config.get("specialization", {})


def get_writer_style(writer_id: Union[str, int]) -> Dict[str, str]:
    """获取作家写作风格

    Args:
        writer_id: 作家标识

    Returns:
        {"tone": "...", "dialogue_ratio": "...", ...}
    """
    config = load_writer_variant(writer_id)
    return config.get("writing_style", {})


def get_writer_system_prompt_additions(writer_id: Union[str, int]) -> list:
    """获取作家特定系统提示补充

    Args:
        writer_id: 作家标识

    Returns:
        系统提示补充列表
    """
    config = load_writer_variant(writer_id)
    return config.get("system_prompt_additions", [])


def get_writer_name(writer_id: Union[str, int]) -> str:
    """获取作家名称

    Args:
        writer_id: 作家标识

    Returns:
        作家名称，如 "作家A"
    """
    config = load_writer_variant(writer_id)
    return config.get("name", f"作家{_normalize_writer_id(writer_id).upper()}")


def list_available_writers() -> list:
    """列出所有可用作家

    Returns:
        [{writer_id: "a", name: "作家A", specialty: ["玄幻", "战斗"]}, ...]
    """
    writers = []
    for wid in WRITER_IDS.keys():
        try:
            config = load_writer_variant(wid)
            writers.append({
                "writer_id": wid,
                "name": config.get("name", f"作家{wid.upper()}"),
                "specialty": config.get("specialization", {}).get("primary", []),
            })
        except FileNotFoundError:
            continue
    return writers


def reload_cache():
    """重新加载配置缓存"""
    global _config_cache
    _config_cache = {}


def get_variant_for_scene(scene_type: str) -> Optional[str]:
    """根据场景类型推荐最适合的作家

    Args:
        scene_type: 场景类型，如 "战斗"、"情感"、"推理"

    Returns:
        最适合的writer_id，如 "a"，或None
    """
    scene_to_writer = {
        # 战斗/玄幻
        "比武": "a", "战斗": "a", "升级": "a", "爽文": "a",
        "宗门": "a", "生死对决": "a",
        # 情感/都市
        "情感": "b", "都市": "b", "职场": "b", "家庭": "b",
        # 科幻/设定
        "科幻": "c", "设定": "c", "末世": "c", "星际": "c", "世界观": "c",
        # 悬疑/节奏
        "悬疑": "d", "节奏": "d", "惊悚": "d", "反转": "d",
        # 古言/文笔
        "古言": "e", "文笔": "e", "仙侠": "e", "武侠": "e", "意境": "e",
        # 奇幻/魔法
        "奇幻": "f", "魔法": "f", "异世界": "f", "西幻": "f",
        # 现实/职场
        "现实": "g", "职场": "g", "社会": "g", "人性": "g",
        # 校园/青春
        "校园": "h", "青春": "h", "成长": "h",
        # 推理/悬疑
        "推理": "i", "侦探": "i", "犯罪": "i", "逻辑": "i",
        # 历史/战争
        "历史": "j", "战争": "j", "军事": "j", "权谋": "j",
    }

    return scene_to_writer.get(scene_type)


if __name__ == "__main__":
    # 测试代码
    print("=== 作家变体配置加载器测试 ===\n")

    # 测试加载单个配置
    print("1. 加载作家A配置:")
    config_a = load_writer_variant("a")
    print(f"   名称: {config_a['name']}")
    print(f"   专长: {config_a['specialization']['primary']}")
    print(f"   风格: {config_a['writing_style']['tone']}")
    print()

    # 测试不同格式
    print("2. 测试不同writer_id格式:")
    for wid in ["b", "writer_b", "2"]:
        config = load_writer_variant(wid)
        print(f"   {wid!r} -> {config['name']}")
    print()

    # 列出所有作家
    print("3. 所有可用作家:")
    for w in list_available_writers():
        print(f"   {w['writer_id']}: {w['name']} - {w['specialty']}")
    print()

    # 场景推荐
    print("4. 场景推荐:")
    for scene in ["战斗", "情感", "推理", "历史"]:
        writer = get_variant_for_scene(scene)
        print(f"   {scene} -> 作家{writer.upper()}")