#!/usr/bin/env python3
"""
Infra 核心模块单元测试

覆盖：schema, tool, permission, llm_cache, types, state
"""

import pytest


class TestSchema:
    """Schema 验证系统测试"""

    def test_struct_decode(self):
        from infra.schema import Struct

        class User(Struct):
            name: str
            age: int

        user = User.decode({'name': 'Alice', 'age': 25})
        assert user.name == 'Alice'
        assert user.age == 25

    def test_struct_encode(self):
        from infra.schema import Struct

        class User(Struct):
            name: str
            age: int

        user = User(name='Bob', age=30)
        encoded = user.encode()
        assert encoded == {'name': 'Bob', 'age': 30}

    def test_struct_validate(self):
        from infra.schema import Struct, validate

        class User(Struct):
            name: str
            age: int

        valid, errors = validate(User, {'name': 'Charlie', 'age': 35})
        assert valid is True
        assert errors is None

        valid, errors = validate(User, {'name': 'Charlie'})
        assert valid is False
        assert errors is not None

    def test_array_decode(self):
        from infra.schema import Array

        StringArray = Array[str]
        arr = StringArray.decode(['a', 'b', 'c'])
        assert arr == ['a', 'b', 'c']


class TestTool:
    """类型安全工具定义测试"""

    def test_make_typed_tool(self):
        from infra.schema import Struct
        from infra.tool import ToolOutput, dispatch, make

        class WeatherParams(Struct):
            city: str

        class WeatherResult(Struct):
            temperature: float
            description: str

        tool = make({
            'description': 'Get weather',
            'parameters': WeatherParams,
            'success': WeatherResult,
            'execute': lambda p, c=None: WeatherResult(temperature=22, description='Sunny'),
        })

        result = dispatch(tool, 'call_1', {'city': 'Beijing'})
        assert isinstance(result, ToolOutput)
        assert result.content['temperature'] == 22.0

    def test_make_dynamic_tool(self):
        from infra.tool import ToolOutput, dispatch, make

        tool = make({
            'description': 'Lookup',
            'json_schema': {'type': 'object', 'properties': {'query': {'type': 'string'}}},
            'execute': lambda p, c=None: {'result': f'Found: {p.get("query")}'},
        })

        result = dispatch(tool, 'call_1', {'query': 'test'})
        assert isinstance(result, ToolOutput)
        assert result.content['result'] == 'Found: test'

    def test_tools_registry(self):
        from infra.schema import Struct
        from infra.tool import ToolsRegistry, make

        class Params(Struct):
            value: str

        class Result(Struct):
            output: str

        tool = make({
            'description': 'Test',
            'parameters': Params,
            'success': Result,
            'execute': lambda p, c=None: Result(output=p.value),
        })

        registry = ToolsRegistry()
        registry.register('test_tool', tool)

        assert registry.get('test_tool') is not None
        assert 'test_tool' in registry.list()

        result = registry.execute('test_tool', 'call_1', {'value': 'hello'})
        assert result.content['output'] == 'hello'


class TestPermission:
    """权限系统测试"""

    def test_rule_matches(self):
        from infra.permission import Rule

        rule = Rule(action='tool:*', resource='*', effect='allow')
        assert rule.matches('tool:weather', 'data') is True
        assert rule.matches('read:file', 'data') is False

    def test_permission_evaluate(self):
        from infra.permission import Permission, Rule, Ruleset

        rules = Ruleset([
            Rule(action='*', resource='*', effect='allow'),
            Rule(action='tool:danger', resource='*', effect='deny'),
        ])

        permission = Permission([rules])
        assert permission.can('tool:weather', '*') is True
        assert permission.cannot('tool:danger', '*') is True

    def test_permission_manager(self):
        from infra.permission import Permission, PermissionManager, Rule, Ruleset

        rules = Ruleset([
            Rule(action='tool:*', resource='*', effect='allow'),
            Rule(action='tool:danger', resource='*', effect='deny'),
            Rule(action='tool:system:*', resource='*', effect='ask'),
        ])

        permission = Permission([rules])
        manager = PermissionManager(permission)

        # 允许的操作
        result = manager.evaluate_and_handle('tool:weather', '*')
        assert result is None

        # 拒绝的操作
        from infra.permission import BlockedError
        with pytest.raises(BlockedError):
            manager.evaluate_and_handle('tool:danger', '*')

        # 需要询问的操作
        request = manager.evaluate_and_handle('tool:system:exec', '*')
        assert request is not None
        assert hasattr(request, 'request_id')


class TestLLMCache:
    """LLM 缓存策略测试"""

    def test_cache_hit(self):
        from infra.llm_cache import LLMCache

        cache = LLMCache()
        call_count = [0]

        def api(req):
            call_count[0] += 1
            return {'resp': call_count[0]}

        # 第一次请求（无缓存）
        cache.wrap_request({'model': 'test'}, api)
        assert call_count[0] == 1

        # 第二次请求（命中缓存）
        cache.wrap_request({'model': 'test'}, api)
        assert call_count[0] == 1

    def test_cache_policy(self):
        from infra.llm_cache import CachePolicy, MessageRole, apply_cache_policy

        request = {
            'model': 'gpt-4',
            'messages': [
                {'role': MessageRole.SYSTEM, 'content': 'You are helpful'},
                {'role': MessageRole.USER, 'content': 'Hello'},
            ],
            'tools': [{'name': 'get_weather'}],
        }

        marked = apply_cache_policy(request, 'auto')
        assert '_cache_hint' in marked['tools'][0]
        assert '_cache_hint' in marked['messages'][-1]

    def test_cache_key_generation(self):
        from infra.llm_cache import LLMCache

        cache = LLMCache()
        key1 = cache.make_key('a', 'b', 'c')
        key2 = cache.make_key('a', 'b', 'c')
        key3 = cache.make_key('x', 'y', 'z')

        assert key1 == key2
        assert key1 != key3


class TestTypes:
    """Newtype 类型系统测试"""

    def test_string_id(self):
        from infra.types import StringID, UserID

        user_id = UserID('550e8400-e29b-41d4-a716-446655440000')
        assert user_id.value == '550e8400-e29b-41d4-a716-446655440000'
        assert str(user_id) == '550e8400-e29b-41d4-a716-446655440000'

    def test_uuid_validation(self):
        from infra.types import UUIDID, NewtypeValidationError, SessionID

        # 有效 UUID
        session_id = SessionID('550e8400-e29b-41d4-a716-446655440000')
        assert session_id is not None

        # 无效 UUID
        with pytest.raises(NewtypeValidationError):
            SessionID('invalid-uuid')

    def test_email_validation(self):
        from infra.types import Email, NewtypeValidationError

        # 有效邮箱
        email = Email('test@example.com')
        assert email.value == 'test@example.com'

        # 无效邮箱
        with pytest.raises(NewtypeValidationError):
            Email('invalid-email')

    def test_newtype_factory(self):
        from infra.types import integer_id, newtype

        ProductID = newtype('ProductID', str)
        prod_id = ProductID('prod-123')
        assert prod_id.value == 'prod-123'

        OrderID = integer_id('OrderID')
        order_id = OrderID(42)
        assert order_id.value == 42

    def test_newtype_equality(self):
        from infra.types import UserID

        user1 = UserID('550e8400-e29b-41d4-a716-446655440000')
        user2 = UserID('550e8400-e29b-41d4-a716-446655440000')
        user3 = UserID('550e8400-e29b-41d4-a716-446655440001')

        assert user1 == user2
        assert user1 != user3


class TestState:
    """状态转换系统测试"""

    def test_counter_state(self):
        from lingwen_pipeline.state_machine import CounterState

        counter = CounterState(0)
        assert counter.value == 0

        counter = counter.apply('increment', 5)
        assert counter.value == 5
        assert counter.version == 2

        counter = counter.apply('decrement', 2)
        assert counter.value == 3

        counter = counter.apply('reset')
        assert counter.value == 0

    def test_toggle_state(self):
        from lingwen_pipeline.state_machine import ToggleState

        toggle = ToggleState(False)
        assert toggle.value is False

        toggle = toggle.apply('toggle')
        assert toggle.value is True

        toggle = toggle.apply('off')
        assert toggle.value is False

    def test_list_state(self):
        from lingwen_pipeline.state_machine import ListState

        list_state = ListState(['a', 'b'])
        assert list_state.items == ['a', 'b']
        assert list_state.length == 2

        list_state = list_state.apply('add', 'c')
        assert list_state.items == ['a', 'b', 'c']

        list_state = list_state.apply('remove', 0)
        assert list_state.items == ['b', 'c']

        list_state = list_state.apply('clear')
        assert list_state.items == []

    def test_state_create(self):
        from lingwen_pipeline.state_machine import State

        state = State.create({
            'initial': {'count': 10},
            'transformers': [
                State.transform('add', lambda s, n: {'count': s['count'] + n}),
            ]
        })

        state = state.apply('add', 5)
        assert state.state == {'count': 15}

    def test_state_batch_apply(self):
        from lingwen_pipeline.state_machine import State

        state = State.create({
            'initial': {'x': 0},
            'transformers': [
                State.transform('add', lambda s, n: {'x': s['x'] + n}),
            ]
        })

        state = state.apply_many([('add', 1), ('add', 2), ('add', 3)])
        assert state.state == {'x': 6}

    def test_state_snapshot(self):
        from lingwen_pipeline.state_machine import CounterState

        counter = CounterState(0)
        counter = counter.apply('increment', 10)

        snapshot = counter.snapshot()
        assert snapshot.state == {'value': 10}
        assert snapshot.version == 2

        restored = counter.restore(snapshot)
        assert restored.state == {'value': 10}


class TestResult:
    """Result 类型测试"""

    def test_ok(self):
        from infra.result import Ok, ok

        result = Ok(42)
        assert result.is_ok() is True
        assert result.is_err() is False
        assert result.unwrap() == 42

        result2 = ok(42)
        assert result2.unwrap() == 42

    def test_err(self):
        from infra.result import Err, err

        result = Err('error message')
        assert result.is_ok() is False
        assert result.is_err() is True

        with pytest.raises(ValueError):
            result.unwrap()

        assert result.unwrap_or('default') == 'default'

    def test_map(self):
        from infra.result import Err, Ok

        result = Ok(42)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 84

        error_result = Err('error')
        mapped_err = error_result.map(lambda x: x * 2)
        assert mapped_err.is_err() is True

    def test_flat_map(self):
        from infra.result import Err, Ok, ok

        result = Ok(42)
        flat_mapped = result.flat_map(lambda x: ok(x * 2))
        assert flat_mapped.unwrap() == 84

    def test_wrap(self):
        from infra.result import wrap

        @wrap
        def success_func():
            return 42

        @wrap
        def fail_func():
            raise ValueError('oops')

        result1 = success_func()
        assert result1.is_ok() is True
        assert result1.unwrap() == 42

        result2 = fail_func()
        assert result2.is_err() is True

    def test_combine(self):
        from infra.result import Err, Ok, combine

        results = [Ok(1), Ok(2), Ok(3)]
        combined = combine(results)
        assert combined.unwrap() == [1, 2, 3]

        results_with_err = [Ok(1), Err('error'), Ok(3)]
        combined_err = combine(results_with_err)
        assert combined_err.is_err() is True


class TestDI:
    """依赖注入系统测试"""

    def test_layer_basic(self):
        from infra.di.layer import Layer, Runtime, Tag

        # 创建标签
        DbTag = Tag(str, 'Database')
        ConfigTag = Tag(dict, 'Config')

        # 创建层
        config_layer = Layer(
            provides=[ConfigTag],
            dependencies=[],
            build=lambda env: {ConfigTag: {'db_url': 'sqlite:///test.db'}}
        )

        db_layer = Layer(
            provides=[DbTag],
            dependencies=[ConfigTag],
            build=lambda env: {DbTag: f"Connected to: {env[ConfigTag]['db_url']}"}
        )

        # 创建运行时
        runtime = Runtime()
        runtime.add_layers(config_layer, db_layer)
        runtime.load()

        assert runtime.get(DbTag) == 'Connected to: sqlite:///test.db'

    def test_layer_zip(self):
        from infra.di.layer import Layer, Tag

        TagA = Tag(str, 'A')
        TagB = Tag(int, 'B')

        layer_a = Layer(provides=[TagA], dependencies=[], build=lambda e: {TagA: 'value_a'})
        layer_b = Layer(provides=[TagB], dependencies=[], build=lambda e: {TagB: 42})

        combined = layer_a.zip(layer_b)
        result = combined.build({})

        assert result[TagA] == 'value_a'
        assert result[TagB] == 42


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
