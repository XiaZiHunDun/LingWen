'use strict'

/**
 * no-shallowref-mutation — 禁止 shallowRef 内部属性 mutation
 *
 * 背景：
 * 1. shallowRef 只追踪 .value 引用变化，不追踪内部属性 mutation
 * 2. x.value.foo = 1 会被静默忽略，UI 不 re-render (运行时无错误)
 * 3. Phase 77+78 转换 33 wholesale-refs 到 shallowRef
 * 4. comment-based convention ('// Phase 77: shallowRef — wholesale replacement')
 *    不可靠，需要 ESLint rule enforcement
 *
 * 检测模式：
 * 1. const x = shallowRef(...)
 * 2. x.value.<prop> = ...  ← FLAGGED
 *
 * 正确用法：
 * - x.value = newObj  (wholesale replacement)
 * - const y = x.value  (read)
 * - const z = x.value.foo  (read inner)
 *
 * 错误用法：
 * - x.value.foo = 1  (mutation, silently ignored)
 */

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow inner property mutation of shallowRef values. ' +
        'shallowRef only tracks .value reference change; inner property ' +
        'mutations are silently ignored, breaking reactivity.',
      category: 'Vue 3 Performance',
      recommended: true,
    },
    messages: {
      mutateShallowRef:
        'Do not mutate inner property "{{prop}}" of shallowRef "{{name}}". ' +
        'shallowRef only tracks reference change. Use `{{name}}.value = newObj` (wholesale replacement) instead.',
    },
    schema: [],
  },

  create(context) {
    // Track declaration type per scope: Map<name, refType>
    // refType is 'shallowRef' | 'ref' | 'reactive' | etc.
    const scopeStack = [new Map()]

    function currentScope() {
      return scopeStack[scopeStack.length - 1]
    }

    // Returns 'shallowRef' if name resolves to a shallowRef in the nearest scope.
    // Returns null if name is not declared or not a shallowRef (including when
    // shadowed by an inner non-shallowRef declaration).
    function lookupRefType(name) {
      // Walk scopes inner → outer, return first match.
      for (let i = scopeStack.length - 1; i >= 0; i--) {
        if (scopeStack[i].has(name)) {
          return scopeStack[i].get(name)
        }
      }
      return null
    }

    function pushScope() {
      scopeStack.push(new Map())
    }
    function popScope() {
      scopeStack.pop()
    }

    // Extract a human-readable property name from a MemberExpression segment.
    // For computed access with a literal, returns the literal value; for
    // computed access with an arbitrary expression, returns '[computed]';
    // for non-computed Identifier access, returns the identifier name.
    function extractPropName(memberExpr) {
      if (!memberExpr || memberExpr.type !== 'MemberExpression') {
        return '?'
      }
      if (memberExpr.computed) {
        if (memberExpr.property.type === 'Literal') {
          return String(memberExpr.property.value)
        }
        return '[computed]'
      }
      if (memberExpr.property.type === 'Identifier') {
        return memberExpr.property.name
      }
      return '?'
    }

    return {
      // Track ref declarations
      VariableDeclarator(node) {
        const init = node.init
        if (
          init &&
          init.type === 'CallExpression' &&
          init.callee.type === 'Identifier'
        ) {
          const calleeName = init.callee.name
          if (calleeName === 'shallowRef' || calleeName === 'ref') {
            if (node.id.type === 'Identifier') {
              currentScope().set(node.id.name, calleeName)
            }
            // Destructured const { foo } = shallowRef(...) — skip for now
          }
        }
      },

      // Scope handling: nested blocks/functions get new scope
      BlockStatement() {
        pushScope()
      },
      'BlockStatement:exit'() {
        popScope()
      },
      FunctionDeclaration() {
        pushScope()
      },
      'FunctionDeclaration:exit'() {
        popScope()
      },
      ArrowFunctionExpression() {
        pushScope()
      },
      'ArrowFunctionExpression:exit'() {
        popScope()
      },

      // Detect mutation: x.value.foo = ... (any depth, including computed access)
      AssignmentExpression(node) {
        const left = node.left
        if (left.type !== 'MemberExpression') return
        // NOT whole replacement: x.value = newObj (Identifier + .value)
        if (
          !left.computed &&
          left.property.type === 'Identifier' &&
          left.property.name === 'value' &&
          left.object.type === 'Identifier'
        ) {
          return
        }

        // Walk up the MemberExpression chain to find a .value access.
        // For x.value.foo.bar = ... the chain is:
        //   bar ← foo ← value ← x
        // For mixed chains like x.value.foo[bar].baz = ... we keep walking
        // through computed segments; only `.value` of an Identifier terminates
        // the walk.
        let current = left
        let propName = extractPropName(current)
        while (current && current.type === 'MemberExpression') {
          if (
            !current.computed &&
            current.property.type === 'Identifier' &&
            current.property.name === 'value' &&
            current.object.type === 'Identifier'
          ) {
            const refName = current.object.name
            if (lookupRefType(refName) === 'shallowRef') {
              context.report({
                node,
                messageId: 'mutateShallowRef',
                data: { name: refName, prop: propName },
              })
            }
            return
          }
          // Continue walking up — capture next segment's property name before moving
          current = current.object
          propName = extractPropName(current)
        }
      },

      // Detect delete: delete x.value.foo (Phase 88 NEW)
      UnaryExpression(node) {
        // Only flag `delete` operator (not !, -, +, typeof, void)
        if (node.operator !== 'delete') return

        // node.argument is the expression being deleted. With optional
        // chains (`x.value?.foo`), the parser wraps the chain in a
        // `ChainExpression`; drill through to the inner MemberExpression.
        let argument = node.argument
        if (argument.type === 'ChainExpression') {
          argument = argument.expression
        }
        if (argument.type !== 'MemberExpression') return

        // Walk chain to find .value access of shallowRef
        let current = argument
        let propName = extractPropName(current)
        while (current.type === 'MemberExpression') {
          if (
            !current.computed &&
            current.property.type === 'Identifier' &&
            current.property.name === 'value'
          ) {
            if (
              current.object.type === 'Identifier' &&
              lookupRefType(current.object.name) === 'shallowRef'
            ) {
              context.report({
                node,
                messageId: 'mutateShallowRef',
                data: {
                  name: current.object.name,
                  prop: propName,
                },
              })
              return
            }
          }
          current = current.object
          propName = extractPropName(current)
        }
      },
    }
  },
}
