'use strict'

/**
 * no-store-value-access — 禁止在已解包的响应式属性上使用 .value
 *
 * 背景：
 * 1. Pinia store（defineStore 定义的）的属性在解构或直接访问时已被自动解包，
 *    不需要 .value。错误使用 .value 会导致运行时错误
 *    "Cannot read properties of null (reading 'value')"。
 * 2. Wrapper composables（如 useStudioProject、useDashboardNav）返回的是已解包的值，
 *    不是原始 ref，不需要 .value。
 * 3. Reactive-wrapped injection contexts（如 createCreatorWriteContext 返回的对象）
 *    中的 ref 属性会自动解包，不需要 .value。
 *
 * 检测模式：
 * 1. destructuredVariable.value — 从 store 解构出的变量访问 .value
 * 2. storeVariable.property.value — store 变量上的嵌套 .value 访问
 * 3. assignedVariable.value — 从 store 属性直接赋值得到的变量访问 .value
 * 4. wrapperComposable.property.value — 从 wrapper composable 访问的属性使用 .value
 * 5. reactiveContext.property.value — 从 reactive-wrapped context 访问的属性使用 .value
 *
 * 正确用法：
 * - studioStore.summary.creation_mode  （直接访问，store 已自动解包）
 * - isReviewer                          （解构后的值是普通值，不是 ref）
 * - activeNav                           （同上）
 * - studio.activeSlug                   （wrapper composable 返回的已解包值）
 * - w.chapterBodyDraft                  （reactive context 中的已解包 ref）
 * - wb.creationMode                     （reactive 对象中的嵌套已解包 ref）
 *
 * 错误用法：
 * - studioStore.summary.value           （.value 多余）
 * - isReviewer?.value                   （解构后不是 ref）
 * - activeNav?.value                    （解构后不是 ref）
 * - studio.activeSlug.value             （wrapper composable 已解包）
 * - w.chapterBodyDraft.value            （reactive context 已解包）
 * - wb.creationMode.value               （reactive 对象已解包）
 */

// 已验证的 Pinia store 实例变量名（用 defineStore 定义的，Ref 会自解包）
const STORE_VARIABLE_NAMES = new Set([
  'navStore',
  'roleStore',
  'studioStore',
  'connectivityStore',
])

// 已验证的 Pinia store 工厂函数名
const PINIA_STORE_FACTORIES = new Set([
  'useNavStore',
  'useRoleStore',
  'useStudioStore',
  'useConnectivityStore',
])

// Wrapper composables — 返回已解包的值（从 Pinia store 解构后返回），不需要 .value
const WRAPPER_COMPOSABLES = new Set([
  'useStudioProject',
  'useDashboardNav',
  'useDashboardRole',
])

// Reactive-wrapped injection key symbols — 通过 inject() 获取的是 reactive 对象，ref 属性已解包
const REACTIVE_INJECTION_KEYS = new Set([
  'CREATOR_WRITE_KEY',
  'CREATOR_PAGE_CHROME_KEY',
  'CREATOR_PRODUCT_TOOLS_KEY',
  'CREATOR_VOLUME_PLAN_KEY',
  'CREATOR_ONBOARDING_KEY',
  'CREATOR_BATCH_HISTORY_KEY',
  'CREATOR_SETTINGS_KEY',
  'CREATOR_MODE_GUIDE_KEY',
])

module.exports = {
  meta: {
    type: 'error',
    docs: {
      description:
        '禁止在 Pinia Store 属性或已解包变量上使用 .value，防止 "Cannot read properties of null" 运行时错误',
      category: 'Best Practices',
      recommended: true,
    },
    schema: [],
    messages: {
      unwrappedValueAccess:
        '变量 "{{name}}" 已从 Pinia store 解包，不是 ref，不需要 .value。请直接使用 {{name}}。',
      nestedStoreValue:
        'Store 属性 "{{name}}" 已自动解包，请使用 {{name}} 而非 {{name}}.value。',
    },
  },

  create(context) {
    // 收集从 store 解构出的变量名
    const destructuredFromStore = new Set()
    // 收集 store 实例变量名（包括通过 useXxxStore() 赋值得到的）
    const storeInstanceNames = new Set(STORE_VARIABLE_NAMES)
    // 收集 wrapper composable 返回的变量名（如 const studio = useStudioProject()）
    const wrapperComposableNames = new Set()
    // 收集 reactive-wrapped injection context 变量名（如 const w = inject(CREATOR_WRITE_KEY)）
    const reactiveContextNames = new Set()

    return {
      // 追踪赋值：const xxx = useXxxStore() → xxx 是 store 实例
      VariableDeclarator(node) {
        if (!node.init) return

        // 模式 1: const roleStore = useRoleStore()
        // 将赋值的目标变量名加入 store 实例集合
        if (
          node.id.type === 'Identifier' &&
          node.init.type === 'CallExpression' &&
          node.init.callee.type === 'Identifier' &&
          PINIA_STORE_FACTORIES.has(node.init.callee.name)
        ) {
          storeInstanceNames.add(node.id.name)
        }

        // 模式 1b: const studio = useStudioProject() (wrapper composable)
        // wrapper composable 返回的对象中的属性已解包，不需要 .value
        if (
          node.id.type === 'Identifier' &&
          node.init.type === 'CallExpression' &&
          node.init.callee.type === 'Identifier' &&
          WRAPPER_COMPOSABLES.has(node.init.callee.name)
        ) {
          wrapperComposableNames.add(node.id.name)
        }

        // 模式 1c: const w = inject(CREATOR_WRITE_KEY) (reactive-wrapped context)
        // reactive() 包裹的对象中，顶层和嵌套的 ref 都会自动解包
        if (
          node.id.type === 'Identifier' &&
          node.init.type === 'CallExpression' &&
          node.init.callee.type === 'Identifier' &&
          node.init.callee.name === 'inject' &&
          node.init.arguments.length > 0
        ) {
          const injectArg = node.init.arguments[0]
          if (
            injectArg.type === 'Identifier' &&
            REACTIVE_INJECTION_KEYS.has(injectArg.name)
          ) {
            reactiveContextNames.add(node.id.name)
          }
        }

        // 模式 2: const { x, y } = someStore / useSomeStore()
        if (node.id.type === 'ObjectPattern') {
          let isStoreSource = false

          if (
            node.init.type === 'Identifier' &&
            storeInstanceNames.has(node.init.name)
          ) {
            // const { x } = navStore (store 实例变量)
            isStoreSource = true
          } else if (
            node.init.type === 'CallExpression' &&
            node.init.callee.type === 'Identifier' &&
            PINIA_STORE_FACTORIES.has(node.init.callee.name)
          ) {
            // const { x } = useRoleStore() (直接解构)
            isStoreSource = true
          }

          if (isStoreSource) {
            for (const prop of node.id.properties) {
              if (prop.type === 'Property' && prop.key.type === 'Identifier') {
                destructuredFromStore.add(prop.key.name)
              }
            }
          }
        }

        // 模式 3: const x = someStore.property (直接赋值，x 是普通值，不是 ref)
        if (
          node.id.type === 'Identifier' &&
          node.init.type === 'MemberExpression' &&
          !node.init.computed
        ) {
          let root = node.init
          while (root.type === 'MemberExpression' && !root.optional) {
            root = root.object
          }
          if (root.type === 'Identifier' && storeInstanceNames.has(root.name)) {
            destructuredFromStore.add(node.id.name)
          }
        }

        // 模式 4: const wb = w.wb (从 reactive context 解构出嵌套对象)
        // reactive 对象中的嵌套对象也是 reactive 的，其 ref 属性也已解包
        if (
          node.id.type === 'Identifier' &&
          node.init.type === 'MemberExpression' &&
          !node.init.computed
        ) {
          let root = node.init
          while (root.type === 'MemberExpression' && !root.optional) {
            root = root.object
          }
          if (root.type === 'Identifier' && reactiveContextNames.has(root.name)) {
            reactiveContextNames.add(node.id.name)
          }
        }
      },

      // 检测 MemberExpression: 访问 .value
      MemberExpression(node) {
        if (
          node.property.type !== 'Identifier' ||
          node.property.name !== 'value'
        ) {
          return
        }
        if (node.computed) return

        const object = node.object

        // 情况 1: storeVariable.property.value
        if (
          object.type === 'MemberExpression' &&
          !object.computed &&
          object.property.type === 'Identifier'
        ) {
          let root = object
          while (root.type === 'MemberExpression' && !root.optional) {
            root = root.object
          }
          if (root.type === 'Identifier' && storeInstanceNames.has(root.name)) {
            context.report({
              node,
              messageId: 'nestedStoreValue',
              data: {
                name: `${root.name}.${object.property.name}`,
                prop: object.property.name,
              },
            })
            return
          }
        }

        // 情况 2: destructuredVariable.value
        if (object.type === 'Identifier') {
          if (destructuredFromStore.has(object.name)) {
            context.report({
              node,
              messageId: 'unwrappedValueAccess',
              data: { name: object.name },
            })
            return
          }
        }

        // 情况 3: 可选链访问 store 属性
        if (
          object.type === 'MemberExpression' &&
          object.optional &&
          object.property.type === 'Identifier'
        ) {
          let root = object.object
          while (root.type === 'MemberExpression') {
            root = root.object
          }
          if (root.type === 'Identifier' && storeInstanceNames.has(root.name)) {
            context.report({
              node,
              messageId: 'nestedStoreValue',
              data: {
                name: `${root.name}.${object.property.name}`,
                prop: object.property.name,
              },
            })
            return
          }
        }

        // 情况 4: wrapperComposable.property.value (如 studio.activeSlug.value)
        if (
          object.type === 'MemberExpression' &&
          !object.computed &&
          object.property.type === 'Identifier'
        ) {
          let root = object
          while (root.type === 'MemberExpression' && !root.optional) {
            root = root.object
          }
          if (root.type === 'Identifier' && wrapperComposableNames.has(root.name)) {
            context.report({
              node,
              messageId: 'nestedStoreValue',
              data: {
                name: `${root.name}.${object.property.name}`,
                prop: object.property.name,
              },
            })
            return
          }
        }

        // 情况 5: wrapperComposable.property?.value (可选链，如 studio.activeSlug?.value)
        if (
          object.type === 'MemberExpression' &&
          object.optional &&
          object.property.type === 'Identifier'
        ) {
          let root = object.object
          while (root.type === 'MemberExpression') {
            root = root.object
          }
          if (root.type === 'Identifier' && wrapperComposableNames.has(root.name)) {
            context.report({
              node,
              messageId: 'nestedStoreValue',
              data: {
                name: `${root.name}.${object.property.name}`,
                prop: object.property.name,
              },
            })
            return
          }
        }

        // 情况 6: reactiveContext.property.value (如 w.chapterBodyDraft.value)
        // reactive() 包裹的对象中，顶层和嵌套的 ref 都会自动解包
        if (
          object.type === 'MemberExpression' &&
          !object.computed &&
          object.property.type === 'Identifier'
        ) {
          let root = object
          while (root.type === 'MemberExpression' && !root.optional) {
            root = root.object
          }
          if (root.type === 'Identifier' && reactiveContextNames.has(root.name)) {
            context.report({
              node,
              messageId: 'nestedStoreValue',
              data: {
                name: `${root.name}.${object.property.name}`,
                prop: object.property.name,
              },
            })
            return
          }
        }

        // 情况 7: reactiveContext.property?.value (可选链，如 w.chapterBodyDraft?.value)
        if (
          object.type === 'MemberExpression' &&
          object.optional &&
          object.property.type === 'Identifier'
        ) {
          let root = object.object
          while (root.type === 'MemberExpression') {
            root = root.object
          }
          if (root.type === 'Identifier' && reactiveContextNames.has(root.name)) {
            context.report({
              node,
              messageId: 'nestedStoreValue',
              data: {
                name: `${root.name}.${object.property.name}`,
                prop: object.property.name,
              },
            })
            return
          }
        }
      },
    }
  },
}
