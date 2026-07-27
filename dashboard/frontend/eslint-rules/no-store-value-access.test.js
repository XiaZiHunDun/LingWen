// eslint-rules/no-store-value-access.test.js
// RuleTester unit test for custom/no-store-value-access.
// 验证规则能正确检测从 Pinia store 解构的变量上使用 .value 的错误。
// ESLint 10 flat config format.
const { RuleTester } = require('eslint')
const rule = require('./no-store-value-access.js')

const ruleTester = new RuleTester({
  languageOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
})

ruleTester.run('no-store-value-access', rule, {
  valid: [
    // 从 store 解构的变量，不访问 .value — 正确
    {
      code: `
import { useRoleStore } from './stores/useRoleStore'
const { isReviewer } = useRoleStore()
if (isReviewer) { console.log('ok') }
      `,
    },
    // 直接访问 store 属性（不经过 .value）— 正确
    {
      code: `
import { useStudioStore } from './stores/useStudioStore'
const studioStore = useStudioStore()
console.log(studioStore.summary.creation_mode)
      `,
    },
    // 普通 ref 使用 .value — 正确（不是从 store 解构的）
    {
      code: `
import { ref } from 'vue'
const count = ref(0)
console.log(count.value)
      `,
    },
    // computed 使用 .value — 正确
    {
      code: `
import { computed, ref } from 'vue'
const count = ref(0)
const doubled = computed(() => count.value * 2)
console.log(doubled.value)
      `,
    },
  ],

  invalid: [
    // 从 store 解构的变量访问 .value — 错误
    {
      code: `
import { useRoleStore } from './stores/useRoleStore'
const { isReviewer } = useRoleStore()
if (isReviewer.value) { console.log('bug') }
      `,
      errors: [{ messageId: 'unwrappedValueAccess', data: { name: 'isReviewer' } }],
    },
    // 从 store 解构的变量访问 ?.value — 错误
    {
      code: `
import { useNavStore } from './stores/useNavStore'
const { activeNav } = useNavStore()
console.log(activeNav?.value)
      `,
      errors: [{ messageId: 'unwrappedValueAccess', data: { name: 'activeNav' } }],
    },
    // store 嵌套属性访问 .value — 错误
    {
      code: `
import { useStudioStore } from './stores/useStudioStore'
const studioStore = useStudioStore()
console.log(studioStore.summary.value)
      `,
      errors: [{ messageId: 'nestedStoreValue' }],
    },
  ],
})