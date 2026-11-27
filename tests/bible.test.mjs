import test from 'node:test';
import assert from 'node:assert/strict';

import { normalizeBiblePatch, BIBLE_LIMITS } from '../src/lib/bible.js';

test('normalizeBiblePatch：只传 title 时只更新 title（部分字段更新）', () => {
  const { values, error } = normalizeBiblePatch({ title: '林昭' });
  assert.equal(error, null);
  assert.deepEqual(values, { title: '林昭' });
});

test('normalizeBiblePatch：只传 content 时只更新 content', () => {
  const { values, error } = normalizeBiblePatch({ content: '少年剑客' });
  assert.equal(error, null);
  assert.deepEqual(values, { content: '少年剑客' });
});

test('normalizeBiblePatch：category 与 title 会 trim，content 原样保留', () => {
  const { values, error } = normalizeBiblePatch({
    category: '  人物  ',
    title: '  林昭  ',
    content: ' 少年剑客 ',
  });
  assert.equal(error, null);
  assert.deepEqual(values, { category: '人物', title: '林昭', content: ' 少年剑客 ' });
});

test('normalizeBiblePatch：空分类 / 空内容存成空字符串', () => {
  const { values, error } = normalizeBiblePatch({ category: '   ', content: '' });
  assert.equal(error, null);
  assert.deepEqual(values, { category: '', content: '' });
});

test('normalizeBiblePatch：title 超长报错', () => {
  const { values, error } = normalizeBiblePatch({ title: 'a'.repeat(BIBLE_LIMITS.title + 1) });
  assert.equal(values.category, undefined);
  assert.deepEqual(values, {});
  assert.equal(typeof error, 'string');
  assert.match(error, /标题/);
});

test('normalizeBiblePatch：category 超长报错', () => {
  const { error } = normalizeBiblePatch({ category: '一'.repeat(BIBLE_LIMITS.category + 1) });
  assert.equal(typeof error, 'string');
  assert.match(error, /分类/);
});

test('normalizeBiblePatch：content 超长报错', () => {
  const { error } = normalizeBiblePatch({ content: '字'.repeat(BIBLE_LIMITS.content + 1) });
  assert.equal(typeof error, 'string');
  assert.match(error, /内容/);
});

test('normalizeBiblePatch：title 只有空白视为空 title 并报错', () => {
  const { values, error } = normalizeBiblePatch({ title: '    ' });
  assert.deepEqual(values, {});
  assert.equal(typeof error, 'string');
  assert.match(error, /标题/);
});

test('normalizeBiblePatch：title 为空字符串报错', () => {
  const { error } = normalizeBiblePatch({ title: '' });
  assert.equal(typeof error, 'string');
  assert.match(error, /标题/);
});

test('normalizeBiblePatch：全部是非法 key 时报错', () => {
  const { values, error } = normalizeBiblePatch({ foo: 'bar', nope: 1 });
  assert.deepEqual(values, {});
  assert.equal(typeof error, 'string');
});

test('normalizeBiblePatch：空 body 报错', () => {
  const { error } = normalizeBiblePatch({});
  assert.equal(typeof error, 'string');
});

test('normalizeBiblePatch：未知 key 被忽略，合法字段照常生效', () => {
  const { values, error } = normalizeBiblePatch({ title: '新标题', foo: 'bar', bookId: 99 });
  assert.equal(error, null);
  assert.deepEqual(values, { title: '新标题' });
});

test('normalizeBiblePatch：非字符串字段报错', () => {
  const { error } = normalizeBiblePatch({ title: 123 });
  assert.equal(typeof error, 'string');
  assert.match(error, /标题/);
});

test('BIBLE_LIMITS：限制与需求一致', () => {
  assert.equal(BIBLE_LIMITS.title, 40);
  assert.equal(BIBLE_LIMITS.category, 20);
  assert.equal(BIBLE_LIMITS.content, 500);
});
