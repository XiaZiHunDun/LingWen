'use strict'

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: '强制对 store 属性访问使用可选链 ?. 以防止空指针错误',
    },
    schema: [],
  },
  create(context) {
    const storeNames = new Set([
      'navStore',
      'roleStore',
      'studioStore',
      'connectivityStore',
      'workspaceStore',
      'workflowStore',
      'insightStore',
      'produceStore',
      'libraryStore',
      'creatorStore',
      'memoryStore',
      'volumePlanStore',
    ])

    function isStoreAccess(node) {
      if (node.type !== 'MemberExpression') return false
      let current = node.object
      while (current) {
        if (current.type === 'Identifier' && storeNames.has(current.name)) {
          return true
        }
        if (current.type !== 'MemberExpression') break
        current = current.object
      }
      return false
    }

    function needsOptionalChain(node) {
      if (!isStoreAccess(node)) return false

      let current = node
      while (current && current.type === 'MemberExpression') {
        if (!current.optional) {
          const property = current.property
          if (property.type === 'Identifier' && property.name === 'value') {
            return current
          }
        }
        current = current.object
      }
      return null
    }

    return {
      MemberExpression(node) {
        const problematicNode = needsOptionalChain(node)
        if (problematicNode) {
          context.report({
            node: problematicNode,
            message: `对 store 属性访问时建议使用可选链 ?. 以防止空指针错误，例如: store?.data?.value`,
          })
        }
      },
    }
  },
}
