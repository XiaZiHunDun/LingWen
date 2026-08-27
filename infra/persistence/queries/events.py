#!/usr/bin/env python3
"""
事件相关SQL查询模板

集中管理事件存储相关的SQL查询。
"""

from infra.persistence.queries import Query, register_queries

# 事件查询定义 - 与 event_sourcing.store.py 数据库结构匹配
EVENT_QUERIES = [
    Query(
        name="get_by_aggregate",
        sql="""
            SELECT * FROM events
            WHERE aggregate_id = :aggregate_id
            ORDER BY seq ASC
        """,
        params_schema={"aggregate_id": str},
        description="按聚合ID查询事件",
        namespace="events",
    ),
    Query(
        name="get_by_aggregate_since_seq",
        sql="""
            SELECT * FROM events
            WHERE aggregate_id = :aggregate_id
            AND seq > :after_seq
            ORDER BY seq ASC
        """,
        params_schema={"aggregate_id": str, "after_seq": int},
        description="按聚合ID和序列号查询事件",
        namespace="events",
    ),
    Query(
        name="get_latest_seq",
        sql="""
            SELECT seq FROM event_sequences
            WHERE aggregate_id = :aggregate_id
        """,
        params_schema={"aggregate_id": str},
        description="获取聚合最新序列号",
        namespace="events",
    ),
    Query(
        name="insert_event",
        sql="""
            INSERT INTO events (
                event_id,
                event_type,
                aggregate_id,
                aggregate_type,
                payload,
                metadata,
                timestamp,
                version,
                seq,
                owner_id
            ) VALUES (
                :event_id,
                :event_type,
                :aggregate_id,
                :aggregate_type,
                :payload,
                :metadata,
                :timestamp,
                :version,
                :seq,
                :owner_id
            )
        """,
        params_schema={
            "event_id": str,
            "event_type": str,
            "aggregate_id": str,
            "aggregate_type": str,
            "payload": str,
            "metadata": str,
            "timestamp": str,
            "version": int,
            "seq": int,
            "owner_id": str,
        },
        description="插入事件",
        namespace="events",
    ),
    Query(
        name="insert_or_replace_sequence",
        sql="""
            INSERT OR REPLACE INTO event_sequences (aggregate_id, seq, owner_id)
            VALUES (:aggregate_id, :seq, :owner_id)
        """,
        params_schema={"aggregate_id": str, "seq": int, "owner_id": str},
        description="插入或更新序列号",
        namespace="events",
    ),
    Query(
        name="get_by_type",
        sql="""
            SELECT * FROM events
            WHERE event_type = :event_type
            ORDER BY timestamp ASC
        """,
        params_schema={"event_type": str},
        description="按事件类型查询",
        namespace="events",
    ),
    Query(
        name="get_since_timestamp",
        sql="""
            SELECT * FROM events
            WHERE timestamp >= :timestamp
            ORDER BY timestamp ASC
        """,
        params_schema={"timestamp": str},
        description="按时间戳查询事件",
        namespace="events",
    ),
    Query(
        name="count_by_aggregate",
        sql="""
            SELECT COUNT(*) as count
            FROM events
            WHERE aggregate_id = :aggregate_id
        """,
        params_schema={"aggregate_id": str},
        description="统计聚合事件数量",
        namespace="events",
    ),
    Query(
        name="count_all",
        sql="SELECT COUNT(*) FROM events",
        description="统计所有事件数量",
        namespace="events",
    ),
    Query(
        name="delete_by_aggregate",
        sql="""
            DELETE FROM events
            WHERE aggregate_id = :aggregate_id
        """,
        params_schema={"aggregate_id": str},
        description="删除聚合所有事件",
        namespace="events",
    ),
    Query(
        name="delete_sequence",
        sql="""
            DELETE FROM event_sequences
            WHERE aggregate_id = :aggregate_id
        """,
        params_schema={"aggregate_id": str},
        description="删除聚合序列号",
        namespace="events",
    ),
    Query(
        name="get_aggregate_ids",
        sql="SELECT DISTINCT aggregate_id FROM events",
        description="获取所有聚合ID",
        namespace="events",
    ),
    Query(
        name="get_aggregate_ids_by_type",
        sql="""
            SELECT DISTINCT aggregate_id FROM events
            WHERE aggregate_type = :aggregate_type
        """,
        params_schema={"aggregate_type": str},
        description="按聚合类型获取聚合ID",
        namespace="events",
    ),
    Query(
        name="get_event_by_id",
        sql="SELECT * FROM events WHERE event_id = :event_id",
        params_schema={"event_id": str},
        description="按事件ID查询",
        namespace="events",
    ),
    Query(
        name="get_event_by_aggregate_seq",
        sql="""
            SELECT * FROM events
            WHERE aggregate_id = :aggregate_id
            AND seq = :seq
        """,
        params_schema={"aggregate_id": str, "seq": int},
        description="按聚合ID和序列号查询事件",
        namespace="events",
    ),
    Query(
        name="get_sequence",
        sql="""
            SELECT seq, owner_id FROM event_sequences
            WHERE aggregate_id = :aggregate_id
        """,
        params_schema={"aggregate_id": str},
        description="获取序列号和拥有者",
        namespace="events",
    ),
    Query(
        name="insert_snapshot",
        sql="""
            INSERT OR REPLACE INTO snapshots (
                snapshot_id,
                aggregate_id,
                aggregate_type,
                state,
                version,
                seq,
                timestamp
            ) VALUES (
                :snapshot_id,
                :aggregate_id,
                :aggregate_type,
                :state,
                :version,
                :seq,
                :timestamp
            )
        """,
        params_schema={
            "snapshot_id": str,
            "aggregate_id": str,
            "aggregate_type": str,
            "state": str,
            "version": int,
            "seq": int,
            "timestamp": str,
        },
        description="插入快照",
        namespace="events",
    ),
    Query(
        name="get_latest_snapshot",
        sql="""
            SELECT * FROM snapshots
            WHERE aggregate_id = :aggregate_id
            ORDER BY seq DESC LIMIT 1
        """,
        params_schema={"aggregate_id": str},
        description="获取最新快照",
        namespace="events",
    ),
    Query(
        name="delete_snapshot",
        sql="""
            DELETE FROM snapshots
            WHERE aggregate_id = :aggregate_id
        """,
        params_schema={"aggregate_id": str},
        description="删除聚合快照",
        namespace="events",
    ),
]


# 注册查询
register_queries(EVENT_QUERIES)

__all__ = ["EVENT_QUERIES"]
