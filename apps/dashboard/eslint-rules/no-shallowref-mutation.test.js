'use strict'

// eslint-rules/no-shallowref-mutation.test.js
// RuleTester unit test for custom/no-shallowref-mutation.

const { RuleTester } = require('eslint')
const rule = require('./no-shallowref-mutation.js')

const ruleTester = new RuleTester({
  languageOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
})

ruleTester.run('no-shallowref-mutation', rule, {
  valid: [
    // Wholesale replacement — OK
    { code: `const x = shallowRef({foo: 1}); x.value = {foo: 2};` },
    // Read — OK
    { code: `const x = shallowRef({foo: 1}); const y = x.value.foo;` },
    // Read whole — OK
    { code: `const x = shallowRef({foo: 1}); const y = x.value;` },
    // ref (not shallowRef) — inner mutation OK
    { code: `const a = ref({foo: 1}); a.value.foo = 2;` },
    // reactive (no .value) — OK
    { code: `const b = reactive({foo: 1}); b.foo = 2;` },
    // shallowRef in inner scope (shadowed) — OK
    {
      code: `
        const x = shallowRef({foo: 1});
        function inner() {
          const x = ref({foo: 1});
          x.value.foo = 2; // OK, x is ref here
        }
      `,
    },
    // Computed read — OK
    { code: `const x = shallowRef({foo: 1}); const y = x.value['foo'];` },
    // Mixed chain read — OK
    { code: `const x = shallowRef({foo: [1, 2]}); const y = x.value.foo[0];` },
  ],

  invalid: [
    // Inner property mutation
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    // Nested mutation
    {
      code: `const x = shallowRef({foo: {bar: 1}}); x.value.foo.bar = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    // Multiple violations in same file
    {
      code: `
        const x = shallowRef({foo: 1, baz: 2});
        x.value.foo = 1;
        x.value.baz = 2;
      `,
      errors: [
        { messageId: 'mutateShallowRef' },
        { messageId: 'mutateShallowRef' },
      ],
    },
    // Computed property mutation
    {
      code: `const x = shallowRef({foo: 1}); x.value['foo'] = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
    // Mixed computed/non-computed chain mutation
    {
      code: `const x = shallowRef({foo: {bar: 1}}); x.value.foo['bar'] = 2;`,
      errors: [{ messageId: 'mutateShallowRef' }],
    },
  ],
})
