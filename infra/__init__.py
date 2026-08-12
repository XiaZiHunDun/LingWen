# 统一导出 - 简化导入路径

# 分组导出（推荐：按需导入，减少启动负担）

# 子包导出

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
from lingwen_pipeline.state_machine import (
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

__all__ = [
    # 分组导出
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
    # Health
    "HealthStatus", "HealthCheck", "CompositeHealthCheck", "DatabaseHealthCheck",
    "LLMHealthCheck", "VectorDBHealthCheck", "CacheHealthCheck", "HealthManager",
    "get_health_manager", "register_health_check", "health_status", "health_endpoint",
    # Cache
    "CheckerCache",
    # LLM Service
    "LLMService", "LLMTask", "TaskType",
]
