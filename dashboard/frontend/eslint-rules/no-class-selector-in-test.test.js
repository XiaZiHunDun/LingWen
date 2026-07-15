// eslint-rules/no-class-selector-in-test.test.js — Phase 8.33
// RuleTester unit test for local/no-class-selector-in-test.
// 9 cases: 6 valid (data-testid OK, non-class OK, out-of-scope OK)
// + 3 invalid (wrapper.find / findAll / MemberExpression with class).
// 走 Node --test runner (0 new devDep).
const { RuleTester } = require('eslint')
const rule = require('../eslint-local-rules.cjs')['no-class-selector-in-test']

const ruleTester = new RuleTester({
  parser: require.resolve('@typescript-eslint/parser'),
  parserOptions: { ecmaVersion: 2022, sourceType: 'module' },
})

ruleTester.run('no-class-selector-in-test', rule, {
  valid: [
    { code: `wrapper.find('[data-testid="foo"]')` },
    { code: `wrapper.findAll('[data-testid="bar"]')` },
    { code: `wrapper.find('foo')` },
    { code: `find('.foo')` },
    { code: 'wrapper.find(`.${cls}`)' },
    { code: `document.querySelector('.foo')` },
  ],
  invalid: [
    {
      code: `wrapper.find('.foo')`,
      errors: [{ messageId: 'classSelector', data: { value: '.foo' } }],
    },
    {
      code: `wrapper.findAll('.bar')`,
      errors: [{ messageId: 'classSelector', data: { value: '.bar' } }],
    },
    {
      code: `obj.find('.baz', { name: 'opt' })`,
      errors: [{ messageId: 'classSelector', data: { value: '.baz' } }],
    },
  ],
})
