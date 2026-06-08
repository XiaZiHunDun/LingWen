// .eslintrc-vue.cjs — Phase 8.42
// .vue 模板 lint 独立 config (跟 .eslintrc-testid-sync.cjs 同 pattern).
// 镜像 Phase 8.36 .eslintrc-testid-sync.cjs 独立 config 模式, 0 混 .eslintrc.cjs.

module.exports = {
  root: false,
  env: { node: true, es2022: true, browser: true },
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  extends: ['plugin:vue/vue3-recommended'],
  plugins: ['eslint-plugin-local-rules'],
  rules: {
    'vue/multi-word-component-names': 'error',
    // WorkflowGraph.vue 用 mermaid 库输出 SVG (v-html=svg), mermaid render 是 trusted,
    // 但 rule 视角是 XSS 表面. 留 warn (非 error) 提醒 0 阻塞 baseline.
    'vue/no-v-html': 'warn',
    'vue/require-default-prop': 'error',
    // WorkflowGraph.vue: 'mermaid' 同名 prop + import, 实际渲染 OK (import 在 props 后续用),
    // 但 rule 报 name collision. 留 warn 提醒 0 阻塞.
    'vue/no-dupe-keys': 'warn',
    // Phase 8.36 testid-class-sync rule 复用, 但 .vue 文件配置在独立 config 里
    // 跟 .eslintrc-testid-sync.cjs 配合, 各管各范围
  },
}
