// eslint-rules/no-class-selector-in-test.js — Phase 8.33
// AST visitor rule: forbid wrapper.find('..x') / wrapper.findAll('.x').
// 限定 callee MemberExpression.property.name ∈ {find, findAll} +
// 首参 Literal string startsWith '.'. 0 覆盖 querySelector / template literal
// (YAGNI, 14 spec 0 usage). 0 escape hatch (主公选 0 例外).
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description:
        'Forbid class selector (.x) in wrapper.find/findAll. Use [data-testid="x"] instead.',
      category: 'Best Practices',
    },
    schema: [],
    messages: {
      classSelector:
        'Class selector "{{value}}" forbidden. Use [data-testid="{{value}}"] instead (Phase 8.31+8.32 convention).',
    },
  },
  create(context) {
    return {
      CallExpression(node) {
        const callee = node.callee
        if (
          callee.type === 'MemberExpression' &&
          (callee.property.name === 'find' ||
            callee.property.name === 'findAll') &&
          node.arguments.length >= 1
        ) {
          const arg = node.arguments[0]
          if (
            arg.type === 'Literal' &&
            typeof arg.value === 'string' &&
            arg.value.startsWith('.')
          ) {
            context.report({
              node: arg,
              messageId: 'classSelector',
              data: { value: arg.value },
            })
          }
        }
      },
    }
  },
}
