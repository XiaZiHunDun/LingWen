// tests/eslint-rules/testid-class-sync.test.cjs — Phase 8.36
// 验证 ESLint local rule testid-class-sync:
//  规则: .vue 元素加 data-testid="x" 必加 class 含 "x" (kebab-case 镜像)
//        加 class="...x..." 必加 data-testid="x"
//  镜像 Phase 8.33 no-class-selector-in-test.js pattern (Node --test runner).
// 0 .vue 单测走 vue-eslint-parser (Phase 8.36 新加 devDep).
// .cjs 后缀 0 走 ESM (tests/ dir 0 package.json, 走 frontend root "type": "module").
// filename='*.vue' 强 vue-eslint-parser 走 template branch (default 走 JS).

const { RuleTester } = require('eslint')
const rule = require('../../eslint-rules/testid-class-sync.js')
// ESLint 8.57 RuleTester 强 parser 为 espree if object (rule-tester.js:778-782),
// 必须传 absolute string path 走 require. 镜像 eslint-plugin-vue 测试 pattern.
const vueParserPath = require.resolve('vue-eslint-parser')

const ruleTester = new RuleTester({
  parser: vueParserPath,
  parserOptions: { ecmaVersion: 2022, sourceType: 'module' },
})

// 8 RuleTester cases: 5 valid + 3 invalid
ruleTester.run('testid-class-sync', rule, {
  valid: [
    // 1. testid + class mirror present
    {
      code: '<template><div data-testid="zoom-in-btn" class="zoom-in-btn"></div></template>',
      filename: 'test.vue',
    },
    // 2. testid + class with extra tokens
    {
      code: '<template><button data-testid="stat-card" class="stat-card highlight"></button></template>',
      filename: 'test.vue',
    },
    // 3. no testid, no class (rule does not apply)
    {
      code: '<template><div>hello</div></template>',
      filename: 'test.vue',
    },
    // 4. multiple testid, each with class
    {
      code: '<template><div><span data-testid="a" class="a"></span><span data-testid="b" class="b"></span></div></template>',
      filename: 'test.vue',
    },
    // 5. self-closing component root (no class, no testid, not applicable)
    {
      code: '<template><App/></template>',
      filename: 'test.vue',
    },
  ],
  invalid: [
    // 1. testid without class — error
    {
      code: '<template><div data-testid="zoom-in-btn"></div></template>',
      filename: 'test.vue',
      errors: [{ message: /data-testid="zoom-in-btn" 必须加 class 镜像/ }],
    },
    // 2. testid with class missing testid name — error
    {
      code: '<template><div data-testid="zoom-in-btn" class="different-class"></div></template>',
      filename: 'test.vue',
      errors: [{ message: /class 必须包含 "zoom-in-btn"/ }],
    },
    // 3. class without matching testid (drift: 同 SFC 内已有 testid="stat-card",
    //    此处 interactive button 复用 "stat-card" 作为 class) — error
    {
      code: '<template><div data-testid="stat-card" class="stat-card"></div><button class="stat-card"></button></template>',
      filename: 'test.vue',
      errors: [{ message: /class="stat-card" 必加 data-testid="stat-card" \(drift: 同 SFC 内已有 testid="stat-card"\)/ }],
    },
  ],
})
