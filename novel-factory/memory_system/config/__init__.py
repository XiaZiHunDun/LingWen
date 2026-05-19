"""配置模块"""
import yaml
from pathlib import Path


def load_yaml(file_path: str) -> dict:
    """加载 YAML 配置文件

    Args:
        file_path: 配置文件路径（相对于项目根目录）

    Returns:
        解析后的配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        RuntimeError: 配置加载失败
    """
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / file_path

        with open(full_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Config file not found: {file_path}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Failed to parse YAML {file_path}: {e}")