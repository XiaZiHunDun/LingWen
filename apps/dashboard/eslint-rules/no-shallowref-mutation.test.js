'use strict'

// eslint-rules/no-shallowref-mutation.test.js
// RuleTester unit test for custom/no-shallowref-mutation.

const { RuleTester } = require('eslint')
const rule = require('./no-shallowref-mutation.js')

const ruleTester = new RuleTester({
  languageOptions: {
    ecmaVersion: 2024,
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
    // optional chain read (Phase 88 NEW) — OK
    { code: `const x = shallowRef({foo: 1}); x.value?.foo;` },
    // delete non-shallowRef (Phase 88 NEW) — OK
    { code: `const obj = {foo: 1}; delete obj.foo;` },

    // Phase 98 NEW: wholesale update on whole .value is OK
    // (postfix / prefix, increment / decrement)
    { code: `const x = shallowRef({foo: 1}); x.value++;` },
    { code: `const x = shallowRef({foo: 1}); ++x.value;` },
    { code: `const x = shallowRef({foo: 1}); x.value--;` },
    { code: `const x = shallowRef({foo: 1}); --x.value;` },
  ],

  invalid: [
    // Inner property mutation
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo = 2;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    // Nested mutation
    {
      code: `const x = shallowRef({foo: {bar: 1}}); x.value.foo.bar = 2;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'bar' } }],
    },
    // Multiple violations in same file
    {
      code: `
        const x = shallowRef({foo: 1, baz: 2});
        x.value.foo = 1;
        x.value.baz = 2;
      `,
      errors: [
        { messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } },
        { messageId: 'mutateShallowRef', data: { name: 'x', prop: 'baz' } },
      ],
    },
    // Computed property mutation
    {
      code: `const x = shallowRef({foo: 1}); x.value['foo'] = 2;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    // Mixed computed/non-computed chain mutation
    {
      code: `const x = shallowRef({foo: {bar: 1}}); x.value.foo['bar'] = 2;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'bar' } }],
    },
    // delete shallowRef inner property (Phase 88 NEW)
    {
      code: `const x = shallowRef({foo: 1}); delete x.value.foo;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    // NOTE: `x.value?.foo = 2` cannot be tested directly because optional
    // chaining on assignment LHS is not yet standardized in espree
    // (any ecmaVersion fails to parse). The rule's AssignmentExpression
    // chain walk handles it by descending through optional segments
    // without filtering on `optional`.
    // optional chain nested + delete (Phase 88 NEW)
    {
      code: `const x = shallowRef({foo: {bar: 1}}); delete x.value?.foo.bar;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'bar' } }],
    },

    // Phase 98 NEW: UpdateExpression on inner property
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo++;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: 1}); ++x.value.foo;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo--;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: 1}); --x.value.foo;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value['foo']++;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: {bar: 1}}); x.value.foo.bar++;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'bar' } }],
    },
    // NOTE: `x.value?.foo++` cannot be tested directly because optional
    // chaining on UpdateExpression argument is not parseable in espree
    // (any ecmaVersion fails: "Optional chaining cannot appear in
    // left-hand side"). The handler's chain walk descends through
    // segments without filtering on `optional`, mirroring the
    // AssignmentExpression note above.

    // Phase 98 NEW: CompoundAssignment lock-in (already implicitly covered
    // by AssignmentExpression handler; explicit tests document contract)
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo += 1;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo -= 1;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value['foo'] *= 2;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
    {
      code: `const x = shallowRef({foo: 1}); x.value.foo ??= 2;`,
      errors: [{ messageId: 'mutateShallowRef', data: { name: 'x', prop: 'foo' } }],
    },
  ],
})
