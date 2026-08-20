'use strict'

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: '检测重复的 Vue 生命周期钩子和 watch 定义',
    },
    schema: [],
  },
  create(context) {
    const hooks = new Set([
      'onMounted',
      'onUnmounted',
      'onCreated',
      'onUpdated',
      'onBeforeMount',
      'onBeforeUnmount',
      'onBeforeUpdate',
      'onActivated',
      'onDeactivated',
    ])

    const registeredHooks = new Map()
    const registeredWatchers = new Map()

    function getKey(node) {
      if (node.callee?.name) {
        return node.callee.name
      }
      if (node.callee?.object?.name && node.callee?.property?.name) {
        return `${node.callee.object.name}.${node.callee.property.name}`
      }
      return null
    }

    function getWatcherKey(node) {
      if (node.callee?.name !== 'watch') return null
      const args = node.arguments
      if (args.length === 0) return null

      const firstArg = args[0]
      if (firstArg.type === 'Identifier') {
        return `watch(${firstArg.name})`
      }
      if (firstArg.type === 'ArrowFunctionExpression') {
        const body = firstArg.body
        if (body.type === 'MemberExpression') {
          let path = []
          let current = body
          while (current) {
            if (current.property?.name) path.unshift(current.property.name)
            if (current.object?.name) {
              path.unshift(current.object.name)
              break
            }
            current = current.object
          }
          return `watch(${path.join('.')})`
        }
        if (body.type === 'CallExpression' && body.callee?.name) {
          return `watch(${body.callee.name})`
        }
      }
      return `watch(${node.loc.start.line})`
    }

    return {
      CallExpression(node) {
        const key = getKey(node)
        if (hooks.has(key)) {
          if (registeredHooks.has(key)) {
            context.report({
              node,
              message: `发现重复的 ${key} 调用，第 ${registeredHooks.get(key)} 行已有定义`,
            })
          } else {
            registeredHooks.set(key, node.loc.start.line)
          }
        }

        const watcherKey = getWatcherKey(node)
        if (watcherKey) {
          if (registeredWatchers.has(watcherKey)) {
            context.report({
              node,
              message: `发现重复的 watch 定义: ${watcherKey}，第 ${registeredWatchers.get(watcherKey)} 行已有定义`,
            })
          } else {
            registeredWatchers.set(watcherKey, node.loc.start.line)
          }
        }
      },
    }
  },
}
