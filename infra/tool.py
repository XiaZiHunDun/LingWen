#!/usr/bin/env python3
"""
类型安全工具定义系统

参考 opencode 的 llm/tool.ts，支持两种模式：
1. 静态类型模式：使用 Pydantic Schema 定义参数和返回值
2. 动态模式：使用 JSON Schema

核心功能：
1. Tool.make() 创建工具
2. 参数验证和解码
3. 返回值编码
4. 工具定义转换
5. 错误处理（ToolFailure）
"""

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field, ValidationError
from pydantic_core import to_json

from infra.errors import wrap, BaseError
from infra.schema import Struct, decode as schema_decode, encode as schema_encode, to_json_schema

T = TypeVar('T')
P = TypeVar('P')
S = TypeVar('S')


class ToolFailure(BaseError):
    """
    工具执行失败错误

    参考 opencode 的 ToolFailure，用于表示工具执行过程中的错误。
    """
    __error_name__ = "ToolFailure"
    __error_tags__ = ["tool", "failure"]


class ToolExecuteContext(BaseModel):
    """
    工具执行上下文

    Args:
        id: 工具调用 ID
        name: 工具名称
    """
    id: str
    name: str


class ToolDefinition(BaseModel):
    """
    工具定义

    参考 opencode 的 ToolDefinition，用于生成发送给 LLM 的工具定义。
    """
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
        }
        if self.output_schema:
            result["output"] = self.output_schema
        return result


class ToolOutput(BaseModel):
    """
    工具输出

    Args:
        content: 结构化输出
        model_output: 模型输出内容列表
    """
    content: Any
    model_output: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def make(cls, content: Any, model_output: List[Dict[str, Any]] = None) -> 'ToolOutput':
        """创建工具输出"""
        return cls(
            content=content,
            model_output=model_output or []
        )


class ToolSchema(Generic[T]):
    """
    工具 Schema 类型别名
    """
    def __init__(self, model: Type[T]):
        self.model = model

    def decode(self, data: Any) -> T:
        """解码数据"""
        return self.model.decode(data)

    def encode(self, value: T) -> Any:
        """编码数据"""
        return self.model.encode(value)

    def schema(self) -> Dict[str, Any]:
        """获取 JSON Schema"""
        return self.model.schema()


class ExecutableTool(Generic[P, S]):
    """
    可执行工具接口

    参考 opencode 的 ExecutableTool，包含 execute 方法。
    """
    def execute(self, params: P, context: Optional[ToolExecuteContext] = None) -> Any:
        raise NotImplementedError


class AnyTool:
    """
    任意工具类型
    """
    pass


class AnyExecutableTool(ExecutableTool[Any, Any], AnyTool):
    """
    任意可执行工具类型
    """
    pass


class Tool(Generic[P, S], AnyTool):
    """
    类型安全工具类

    参考 opencode 的 Tool，支持参数验证、执行和输出转换。

    Example:
        class WeatherParams(Struct):
            city: str

        class WeatherResult(Struct):
            temperature: float
            description: str

        weather_tool = Tool.make({
            "description": "Get current weather",
            "parameters": WeatherParams,
            "success": WeatherResult,
            "execute": lambda params: WeatherResult(temperature=22, description="Sunny"),
        })
    """

    def __init__(
        self,
        description: str,
        parameters: Any,
        success: Any,
        execute: Optional[Callable] = None,
        to_model_output: Optional[Callable] = None,
        to_structured_output: Optional[Callable] = None,
        _decode: Optional[Callable] = None,
        _encode: Optional[Callable] = None,
        _project: Optional[Callable] = None,
        _legacy_result: bool = False,
        _definition: Optional[ToolDefinition] = None,
    ):
        self.description = description
        self.parameters = parameters
        self.success = success
        self.execute = execute
        self.to_model_output = to_model_output
        self.to_structured_output = to_structured_output
        self._decode = _decode or self._default_decode
        self._encode = _encode or self._default_encode
        self._project = _project or self._default_project
        self._legacy_result = _legacy_result
        self._definition = _definition or self._default_definition()

    def _default_decode(self, input_data: Any) -> Any:
        """默认解码函数"""
        if hasattr(self.parameters, 'decode'):
            return self.parameters.decode(input_data)
        return input_data

    def _default_encode(self, value: Any) -> Any:
        """默认编码函数"""
        if hasattr(self.success, 'encode'):
            return self.success.encode(value)
        return value

    def _default_definition(self) -> ToolDefinition:
        """默认工具定义"""
        input_schema = {}
        output_schema = None

        if hasattr(self.parameters, 'schema'):
            input_schema = self.parameters.schema()
        elif isinstance(self.parameters, dict):
            input_schema = self.parameters

        if hasattr(self.success, 'schema'):
            output_schema = self.success.schema()
        elif isinstance(self.success, dict):
            output_schema = self.success

        return ToolDefinition(
            name="",
            description=self.description,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    def _default_project(
        self,
        parameters: Any,
        call_id: str,
        output: Any,
    ) -> ToolOutput:
        """默认输出投影函数"""
        structured_output = self.to_structured_output(output) if self.to_structured_output else output
        model_output = self.to_model_output({
            "callID": call_id,
            "parameters": parameters,
            "output": output,
        }) if self.to_model_output else []

        if isinstance(model_output, str):
            model_output = [{"type": "text", "text": model_output}]
        elif not isinstance(model_output, list):
            model_output = []

        return ToolOutput.make(structured_output, model_output)


class TypedToolConfig(BaseModel):
    """
    静态类型工具配置
    """
    description: str
    parameters: Type[Struct]
    success: Type[Struct]
    execute: Optional[Callable] = None
    to_model_output: Optional[Callable] = None
    to_structured_output: Optional[Callable] = None


class DynamicToolConfig(BaseModel):
    """
    动态工具配置（使用 JSON Schema）
    """
    description: str
    json_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    execute: Optional[Callable] = None
    to_model_output: Optional[Callable] = None
    to_structured_output: Optional[Callable] = None


class ToolFactory:
    """
    工具工厂类

    参考 opencode 的 Tool.make()，支持创建不同类型的工具。
    """

    @staticmethod
    def make(config: Union[TypedToolConfig, Dict[str, Any]]) -> AnyTool:
        """
        创建工具

        Args:
            config: 工具配置

        Returns:
            工具实例

        Example:
            # 静态类型模式
            tool = ToolFactory.make({
                "description": "Get weather",
                "parameters": WeatherParams,
                "success": WeatherResult,
                "execute": lambda params: WeatherResult(temperature=22),
            })

            # 动态模式（JSON Schema）
            tool = ToolFactory.make({
                "description": "Look up",
                "json_schema": {"type": "object", "properties": {...}},
                "execute": lambda params: {...},
            })
        """
        if isinstance(config, dict):
            if "json_schema" in config:
                return ToolFactory._make_dynamic(config)
            elif "parameters" in config and "success" in config:
                return ToolFactory._make_typed(config)
            else:
                raise ValueError("Invalid tool config")

        raise ValueError("Config must be a dict")

    @staticmethod
    def _make_typed(config: Dict[str, Any]) -> AnyTool:
        """
        创建静态类型工具
        """
        params_schema = config.get("parameters")
        success_schema = config.get("success")
        execute = config.get("execute")
        to_model_output = config.get("to_model_output")
        to_structured_output = config.get("to_structured_output")

        def decode_func(input_data: Any) -> Any:
            return params_schema.decode(input_data)

        def encode_func(value: Any) -> Any:
            return success_schema.encode(value)

        def project_func(parameters: Any, call_id: str, output: Any) -> ToolOutput:
            structured = to_structured_output(output) if to_structured_output else output
            model_out = to_model_output({
                "callID": call_id,
                "parameters": parameters,
                "output": output,
            }) if to_model_output else []

            if isinstance(model_out, str):
                model_out = [{"type": "text", "text": model_out}]
            elif not isinstance(model_out, list):
                model_out = []

            return ToolOutput.make(structured, model_out)

        definition = ToolDefinition(
            name="",
            description=config["description"],
            input_schema=params_schema.schema(),
            output_schema=success_schema.schema(),
        )

        tool = Tool(
            description=config["description"],
            parameters=params_schema,
            success=success_schema,
            execute=execute,
            to_model_output=to_model_output,
            to_structured_output=to_structured_output,
            _decode=decode_func,
            _encode=encode_func,
            _project=project_func,
            _legacy_result=False,
            _definition=definition,
        )

        return tool

    @staticmethod
    def _make_dynamic(config: Dict[str, Any]) -> AnyTool:
        """
        创建动态工具（使用 JSON Schema）
        """
        execute = config.get("execute")
        to_model_output = config.get("to_model_output")
        to_structured_output = config.get("to_structured_output")

        def decode_func(input_data: Any) -> Any:
            return input_data

        def encode_func(value: Any) -> Any:
            return value

        def project_func(parameters: Any, call_id: str, output: Any) -> ToolOutput:
            structured = to_structured_output(output) if to_structured_output else output
            model_out = to_model_output({
                "callID": call_id,
                "parameters": parameters,
                "output": output,
            }) if to_model_output else []

            if isinstance(model_out, str):
                model_out = [{"type": "text", "text": model_out}]
            elif not isinstance(model_out, list):
                model_out = []

            return ToolOutput.make(structured, model_out)

        definition = ToolDefinition(
            name="",
            description=config["description"],
            input_schema=config["json_schema"],
            output_schema=config.get("output_schema"),
        )

        tool = Tool(
            description=config["description"],
            parameters=config["json_schema"],
            success=config.get("output_schema") or {},
            execute=execute,
            to_model_output=to_model_output,
            to_structured_output=to_structured_output,
            _decode=decode_func,
            _encode=encode_func,
            _project=project_func,
            _legacy_result=(to_model_output is None and to_structured_output is None),
            _definition=definition,
        )

        return tool


def to_definitions(tools: Dict[str, AnyTool]) -> List[ToolDefinition]:
    """
    将工具记录转换为工具定义列表

    参考 opencode 的 toDefinitions，用于生成发送给 LLM 的工具定义。

    Args:
        tools: 工具记录（键为工具名称）

    Returns:
        工具定义列表
    """
    definitions = []
    for name, tool in tools.items():
        if hasattr(tool, '_definition'):
            definition = ToolDefinition(
                name=name,
                description=tool._definition.description,
                input_schema=tool._definition.input_schema,
                output_schema=tool._definition.output_schema,
            )
            definitions.append(definition)
    return definitions


def dispatch(tool: AnyTool, call_id: str, params: Any) -> ToolOutput:
    """
    调度工具执行

    参考 opencode 的 ToolRuntime.dispatch，处理工具调用的完整流程。

    Args:
        tool: 工具实例
        call_id: 调用 ID
        params: 参数

    Returns:
        工具输出
    """
    try:
        # 解码参数
        decoded_params = tool._decode(params)

        # 执行工具
        if tool.execute:
            definition = getattr(tool, '_definition', None)
            name = definition.name if definition else ""
            context = ToolExecuteContext(id=call_id, name=name)
            result = tool.execute(decoded_params, context)
        else:
            result = {}

        # 编码结果
        encoded_result = tool._encode(result)

        # 投影输出
        return tool._project(decoded_params, call_id, encoded_result)

    except Exception as e:
        raise ToolFailure(str(e), cause=e) from e


class ToolsRegistry:
    """
    工具注册表

    用于管理和查找工具。
    """

    def __init__(self):
        self._tools: Dict[str, AnyTool] = {}

    def register(self, name: str, tool: AnyTool) -> None:
        """
        注册工具

        Args:
            name: 工具名称
            tool: 工具实例
        """
        self._tools[name] = tool

    def register_multiple(self, tools: Dict[str, AnyTool]) -> None:
        """
        批量注册工具

        Args:
            tools: 工具记录
        """
        self._tools.update(tools)

    def get(self, name: str) -> Optional[AnyTool]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例或 None
        """
        return self._tools.get(name)

    def list(self) -> List[str]:
        """
        获取所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def get_definitions(self) -> List[ToolDefinition]:
        """
        获取所有工具定义

        Returns:
            工具定义列表
        """
        return to_definitions(self._tools)

    def execute(self, name: str, call_id: str, params: Any) -> ToolOutput:
        """
        执行工具

        Args:
            name: 工具名称
            call_id: 调用 ID
            params: 参数

        Returns:
            工具输出
        """
        tool = self.get(name)
        if not tool:
            raise ToolFailure(f"Tool '{name}' not found")
        return dispatch(tool, call_id, params)


make = ToolFactory.make

__all__ = [
    "Tool",
    "ToolFailure",
    "ToolDefinition",
    "ToolOutput",
    "ToolExecuteContext",
    "ExecutableTool",
    "AnyTool",
    "AnyExecutableTool",
    "ToolFactory",
    "ToolsRegistry",
    "make",
    "to_definitions",
    "dispatch",
]
