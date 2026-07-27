# 统一导出 - 简化导入路径

# 分组导出（推荐：按需导入，减少启动负担）
import infra.exports as exports

# 子包导出
from infra.creator import *
from infra.studio import *
from infra.prose import *
from infra.project import *
from infra.core import *

# 核心模块导出（保持向后兼容）
from infra.result import Ok, Err, Result, ok, err, wrap, from_optional, combine, either
from infra.errors import (
    BaseError,
    ValidationError,
    NotFoundError,
    NetworkError,
    TimeoutError,
    ServiceUnavailableError,
    ConflictError,
    RetryableError,
    create,
    is_instance,
)
from infra.schema import (
    Struct,
    Array,
    String,
    Number,
    Integer,
    Boolean,
    OptionalSchema,
    optional,
    PositiveInt,
    NonNegativeInt,
    decode,
    encode,
    validate,
    to_json_schema,
)
from infra.tool import (
    Tool,
    ToolFailure,
    ToolDefinition,
    ToolOutput,
    ToolExecuteContext,
    ExecutableTool,
    AnyTool,
    AnyExecutableTool,
    ToolFactory,
    ToolsRegistry,
    make,
    to_definitions,
    dispatch,
)
from infra.permission import (
    Permission,
    PermissionManager,
    PermissionRules,
    Rule,
    Ruleset,
    Wildcard,
    BlockedError,
    PermissionRequiredError,
    PermissionRequest,
    PermissionReply,
    evaluate,
    assert_permission,
)
from infra.llm_cache import (
    CacheHint,
    CachePolicy,
    CachePolicyObject,
    CacheEntry,
    CacheStorage,
    MemoryCacheStorage,
    FileCacheStorage,
    LLMCache,
    CacheHintMarker,
    apply_cache_policy,
    MessageRole,
    NamespacedStorage,
    UnifiedCacheManager,
    get_cache_manager,
    get_cache,
)
from infra.types import (
    Newtype,
    StringID,
    UUIDID,
    IntegerID,
    PositiveID,
    NonEmptyString,
    Email,
    URL,
    SessionID,
    UserID,
    ProjectID,
    WorkspaceID,
    DocumentID,
    ToolID,
    ModelID,
    newtype,
    string_id,
    uuid_id,
    integer_id,
)
from infra.state_machine import (
    State,
    StructuredState,
    CounterState,
    ToggleState,
    ListState,
    Transform,
    StateEvent,
    StateSnapshot,
)

# DI 系统
from infra.di.layer import Tag, Layer, Runtime

# 健康检查
from infra.health import (
    HealthStatus,
    HealthCheck,
    CompositeHealthCheck,
    DatabaseHealthCheck,
    LLMHealthCheck,
    VectorDBHealthCheck,
    CacheHealthCheck,
    HealthManager,
    get_health_manager,
    register_health_check,
    health_status,
    health_endpoint,
)

# 常用工具
from infra.cache import CheckerCache, CacheEntry
from infra.llm_service import LLMService, LLMTask, TaskType

# 事件溯源系统
from infra.event_sourcing.models import DomainEvent, EventSerializer, EventStream, EventType, Snapshot, versioned_type
from infra.event_sourcing.store import EventExistsError, EventStore, EventStoreError, OwnerMismatchError, ReplayDivergedError, SequenceConflictError, create_event, create_snapshot

__all__ = [
    # 分组导出
    "exports",
    # Result 类型
    "Ok", "Err", "Result", "ok", "err", "wrap", "from_optional", "combine", "either",
    # 错误类型
    "BaseError", "ValidationError", "NotFoundError", "NetworkError", "TimeoutError",
    "ServiceUnavailableError", "ConflictError", "RetryableError",
    "create", "is_instance",
    # Schema
    "Struct", "Array", "String", "Number", "Integer", "Boolean", "OptionalSchema",
    "optional", "PositiveInt", "NonNegativeInt", "decode", "encode", "validate", "to_json_schema",
    # Tool
    "Tool", "ToolFailure", "ToolDefinition", "ToolOutput", "ToolExecuteContext",
    "ExecutableTool", "AnyTool", "AnyExecutableTool", "ToolFactory", "ToolsRegistry",
    "make", "to_definitions", "dispatch",
    # Permission
    "Permission", "PermissionManager", "PermissionRules", "Rule", "Ruleset", "Wildcard",
    "BlockedError", "PermissionRequiredError", "PermissionRequest", "PermissionReply",
    "evaluate", "assert_permission",
    # LLM Cache
    "CacheHint", "CachePolicy", "CachePolicyObject", "CacheEntry", "CacheStorage",
    "MemoryCacheStorage", "FileCacheStorage", "LLMCache", "CacheHintMarker",
    "apply_cache_policy", "MessageRole",
    "NamespacedStorage", "UnifiedCacheManager", "get_cache_manager", "get_cache",
    # Types
    "Newtype", "StringID", "UUIDID", "IntegerID", "PositiveID", "NonEmptyString",
    "Email", "URL", "SessionID", "UserID", "ProjectID", "WorkspaceID", "DocumentID",
    "ToolID", "ModelID", "newtype", "string_id", "uuid_id", "integer_id",
    # State
    "State", "StructuredState", "CounterState", "ToggleState", "ListState",
    "Transform", "StateEvent", "StateSnapshot",
    # DI
    "Tag", "Layer", "Runtime",
    # Health
    "HealthStatus", "HealthCheck", "CompositeHealthCheck", "DatabaseHealthCheck",
    "LLMHealthCheck", "VectorDBHealthCheck", "CacheHealthCheck", "HealthManager",
    "get_health_manager", "register_health_check", "health_status", "health_endpoint",
    # Cache
    "CheckerCache",
    # LLM Service
    "LLMService", "LLMTask", "TaskType",
    # Event Sourcing
    "DomainEvent", "EventSerializer", "EventStream", "EventType", "Snapshot", "versioned_type",
    "EventExistsError", "EventStore", "EventStoreError", "OwnerMismatchError",
    "ReplayDivergedError", "SequenceConflictError", "create_event", "create_snapshot",
]
