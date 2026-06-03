"""记忆系统初始化脚本

初始化记忆系统，包括：
- 创建 Qdrant 集合
- 初始化状态文件
- 验证 Qdrant 连接

Usage:
    python -m memory_system.scripts.init_memory              # 初始化所有
    python -m memory_system.scripts.init_memory --dry-run   # 仅预览
    python -m memory_system.scripts.init_memory --reset     # 重置状态文件
"""
import argparse
import sys
from pathlib import Path

from infra.memory_system.config import load_yaml
from infra.memory_system.vector.collections import CollectionManager
from infra.memory_system.state.state_manager import MemoryStateManager


def validate_config() -> dict:
    """验证配置文件

    Returns:
        配置字典

    Raises:
        RuntimeError: 配置无效
    """
    try:
        config = load_yaml("config/memory_config.yaml")
    except FileNotFoundError as e:
        raise RuntimeError(f"Configuration file not found: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")

    # 验证必需的字段
    required_sections = ["qdrant", "embedding", "storage", "retrieval"]
    for section in required_sections:
        if section not in config:
            raise RuntimeError(f"Missing required config section: {section}")

    # 验证 Qdrant 配置
    qdrant_config = config["qdrant"]
    for field in ["host", "port", "grpc_port"]:
        if field not in qdrant_config:
            raise RuntimeError(f"Missing required Qdrant config field: {field}")

    # 验证存储配置
    storage_config = config["storage"]
    for field in ["state_file", "plot_threads_file", "timeline_file"]:
        if field not in storage_config:
            raise RuntimeError(f"Missing required storage config field: {field}")

    return config


def initialize_state_files(config: dict, reset: bool = False) -> dict:
    """初始化状态文件

    Args:
        config: 配置字典
        reset: True 则重置现有状态文件

    Returns:
        状态文件初始化结果
    """
    state_manager = MemoryStateManager(config)
    results = {
        "state_file": {"path": None, "initialized": False},
        "plot_threads_file": {"path": None, "initialized": False},
        "timeline_file": {"path": None, "initialized": False},
    }

    for key in MemoryStateManager.STATE_FILE_KEYS:
        file_path = Path(state_manager.get_state_path(key))

        if file_path.exists() and not reset:
            results[key]["path"] = str(file_path)
            results[key]["initialized"] = True
            results[key]["status"] = "already exists"
        else:
            # 创建父目录
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 初始化空状态
            initial_data = {} if key == "state_file" else (
                {"threads": []} if key == "plot_threads_file" else {"events": []}
            )
            state_manager.save(key, initial_data)

            results[key]["path"] = str(file_path)
            results[key]["initialized"] = True
            results[key]["status"] = "created" if reset else "initialized"

    return results


def initialize_collections(dry_run: bool = False) -> dict:
    """初始化 Qdrant 集合

    Args:
        dry_run: True 则只预览不执行

    Returns:
        集合初始化结果
    """
    manager = CollectionManager()
    all_collections = manager.get_all_collection_names()
    existing_collections = manager.list_collections() if not dry_run else []
    to_create = [c for c in all_collections if c not in existing_collections]

    results = {
        "total": len(all_collections),
        "existing": existing_collections,
        "to_create": to_create,
        "created": [],
        "skipped": [],
    }

    if dry_run:
        print("\n--- DRY RUN MODE ---")
        print(f"Would create {len(to_create)} collections:")
        for name in to_create:
            info = manager.get_collection_info(name)
            print(f"  - {name}: {info['description']} (vector_size={info['vector_size']}, distance={info['distance']})")
        return results

    # 创建不存在的集合
    for name in to_create:
        try:
            manager._client.create_collection(name)
            results["created"].append(name)
            print(f"  Created collection: {name}")
        except Exception as e:
            print(f"  Failed to create collection '{name}': {e}", file=sys.stderr)
            results["skipped"].append(name)

    # 已存在的集合
    for name in existing_collections:
        results["skipped"].append(name)

    return results


def check_qdrant_connection(host: str, port: int, grpc_port: int) -> dict:
    """检查 Qdrant 连接

    Args:
        host: Qdrant 主机
        port: Qdrant 端口
        grpc_port: gRPC 端口

    Returns:
        连接检查结果
    """
    from qdrant_client import QdrantClient

    try:
        client = QdrantClient(host=host, port=port, grpc_port=grpc_port)
        # 尝试获取集合列表（会失败如果服务未运行）
        client.get_collections()
        client.close()
        return {"connected": True, "host": host, "port": port, "grpc_port": grpc_port}
    except Exception as e:
        return {"connected": False, "error": str(e), "host": host, "port": port}


def main():
    parser = argparse.ArgumentParser(
        description="初始化记忆系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅预览，不执行实际操作"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="重置状态文件（慎用，会清空现有状态）"
    )
    parser.add_argument(
        "--skip-collections", action="store_true",
        help="跳过集合创建"
    )
    parser.add_argument(
        "--skip-state", action="store_true",
        help="跳过状态文件初始化"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("记忆系统初始化脚本")
    print("=" * 60)

    # 1. 验证配置
    print("\n[1/4] 验证配置文件...")
    try:
        config = validate_config()
        print(f"  Qdrant: {config['qdrant']['host']}:{config['qdrant']['port']}")
        print(f"  Embedding: {config['embedding']['model']} (dimension={config['embedding']['dimension']})")
        print("  Configuration: OK")
    except RuntimeError as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. 检查 Qdrant 连接
    print("\n[2/4] 检查 Qdrant 连接...")
    qdrant_config = config["qdrant"]
    conn_result = check_qdrant_connection(
        qdrant_config["host"],
        qdrant_config["port"],
        qdrant_config["grpc_port"]
    )

    if conn_result["connected"]:
        print(f"  Qdrant: {conn_result['host']}:{conn_result['port']} (gRPC: {conn_result['grpc_port']})")
        print("  Connection: OK")
    else:
        print(f"  WARNING: Cannot connect to Qdrant at {conn_result['host']}:{conn_result['port']}", file=sys.stderr)
        print(f"  Error: {conn_result['error']}", file=sys.stderr)
        print("  Please ensure Qdrant is running.", file=sys.stderr)
        if not args.dry_run:
            sys.exit(1)

    # 3. 初始化集合
    print("\n[3/4] 初始化 Qdrant 集合...")
    if args.skip_collections:
        print("  Skipped (--skip-collections)")
    else:
        collection_results = initialize_collections(dry_run=args.dry_run)
        print(f"  Total collections: {collection_results['total']}")
        print(f"  Existing: {len(collection_results['existing'])}")
        print(f"  To create: {len(collection_results['to_create'])}")

        if args.dry_run:
            print("  Status: Preview only (--dry-run)")
        else:
            if collection_results["created"]:
                print(f"  Created: {len(collection_results['created'])}")
            if collection_results["skipped"]:
                print(f"  Skipped (already exist): {len(collection_results['skipped'])}")

    # 4. 初始化状态文件
    print("\n[4/4] 初始化状态文件...")
    if args.skip_state:
        print("  Skipped (--skip-state)")
    else:
        state_results = initialize_state_files(config, reset=args.reset)
        for key, info in state_results.items():
            file_type = key.replace("_file", "")
            if info["initialized"]:
                print(f"  {file_type}: {info['path']} [{info['status']}]")
            else:
                print(f"  {file_type}: FAILED", file=sys.stderr)

    # 总结
    print("\n" + "=" * 60)
    if args.dry_run:
        print("dry-run 模式：仅预览，未执行实际操作")
    else:
        print("初始化完成")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())