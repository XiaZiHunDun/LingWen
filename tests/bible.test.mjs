import test from 'node:test';
import assert from 'node:assert/strict';

import {
  normalizeBiblePatch,
  BIBLE_LIMITS,
  replaceAllCount,
  collectRenameChanges,
} from '../src/lib/bible.js';

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

// ---------------------------------------------------------------------------
// 「设定改名同步改全书」的纯函数：replaceAllCount / collectRenameChanges
// ---------------------------------------------------------------------------

test('replaceAllCount：单字段多处命中（非重叠、区分大小写、字面量）', () => {
  assert.deepEqual(replaceAllCount('林昭见林昭，又见林昭', '林昭', '苏昭'), {
    value: '苏昭见苏昭，又见苏昭',
    count: 3,
  });
  // 区分大小写：小写不命中
  assert.deepEqual(replaceAllCount('Abc abc', 'Abc', 'X'), { value: 'X abc', count: 1 });
  // 非重叠：'aa' 在 'aaaa' 中命中 2 次
  assert.deepEqual(replaceAllCount('aaaa', 'aa', 'b'), { value: 'bb', count: 2 });
});

test('replaceAllCount：from 为空 / 非字符串 / 新旧相同 → 0 处且原样返回', () => {
  assert.deepEqual(replaceAllCount('林昭', '', '苏昭'), { value: '林昭', count: 0 });
  assert.deepEqual(replaceAllCount('林昭', 123, '苏昭'), { value: '林昭', count: 0 });
  assert.deepEqual(replaceAllCount('林昭', '林昭', '林昭'), { value: '林昭', count: 0 });
  assert.deepEqual(replaceAllCount(undefined, '林昭', '苏昭'), { value: '', count: 0 });
});

test('collectRenameChanges：跨章 / 跨大纲合计命中次数与改动条数', () => {
  const plan = collectRenameChanges(
    {
      chapters: [
        { id: 1, seq: 1, title: '林昭来访', content: '林昭握剑，林昭笑了。' },
        { id: 2, seq: 2, title: '无事', content: '这一章没有旧名字。' },
      ],
      outlines: [
        { id: 11, seq: 1, title: '林昭入门', summary: '林昭拜师。' },
        { id: 12, seq: 2, title: '旁枝', summary: '与主线无关。' },
      ],
    },
    '林昭',
    '苏昭',
  );

  assert.equal(plan.from, '林昭');
  assert.equal(plan.to, '苏昭');
  // 章节 1：标题 1 处 + 正文 2 处；章节 2 不命中
  assert.equal(plan.chapterCount, 1);
  assert.equal(plan.chapters[0].id, 1);
  assert.equal(plan.chapters[0].titleOccurrences, 1);
  assert.equal(plan.chapters[0].contentOccurrences, 2);
  assert.equal(plan.chapters[0].titleAfter, '苏昭来访');
  assert.equal(plan.chapters[0].contentAfter, '苏昭握剑，苏昭笑了。');
  // 大纲 11：标题 1 处 + 摘要 1 处；大纲 12 不命中
  assert.equal(plan.outlineCount, 1);
  assert.equal(plan.outlines[0].summaryAfter, '苏昭拜师。');
  // 合计 1+2+1+1 = 5
  assert.equal(plan.occurrences, 5);
});

test('collectRenameChanges：from 为空 / from === to 时 0 处且不产生变更', () => {
  const input = {
    chapters: [{ id: 1, title: '林昭', content: '林昭' }],
    outlines: [{ id: 2, title: '林昭', summary: '林昭' }],
  };
  for (const [from, to] of [
    ['', '苏昭'],
    ['   ', '苏昭'],
    ['林昭', '林昭'],
  ]) {
    const plan = collectRenameChanges(input, from, to);
    assert.equal(plan.occurrences, 0);
    assert.equal(plan.chapterCount, 0);
    assert.equal(plan.outlineCount, 0);
    assert.deepEqual(plan.chapters, []);
    assert.deepEqual(plan.outlines, []);
  }
});

test('collectRenameChanges：只有大纲命中时章节数为 0', () => {
  const plan = collectRenameChanges(
    {
      chapters: [{ id: 3, title: '第一章', content: '正文里没有那个人。' }],
      outlines: [{ id: 31, seq: 1, title: '旧名登场', summary: '旧名与旧名对峙。' }],
    },
    '旧名',
    '新名',
  );
  assert.equal(plan.chapterCount, 0);
  assert.equal(plan.outlineCount, 1);
  assert.equal(plan.occurrences, 3);
  assert.equal(plan.outlines[0].titleAfter, '新名登场');
  assert.equal(plan.outlines[0].summaryAfter, '新名与新名对峙。');
});

test('collectRenameChanges：完全无命中时三个计数都为 0', () => {
  const plan = collectRenameChanges(
    {
      chapters: [{ id: 1, title: '甲', content: '乙' }],
      outlines: [{ id: 2, title: '丙', summary: '丁' }],
    },
    '不存在',
    '替换',
  );
  assert.equal(plan.chapterCount, 0);
  assert.equal(plan.outlineCount, 0);
  assert.equal(plan.occurrences, 0);
});

test('collectRenameChanges：入参缺省时安全返回空计划', () => {
  const plan = collectRenameChanges(undefined, '林昭', '苏昭');
  assert.equal(plan.occurrences, 0);
  assert.deepEqual(plan.chapters, []);
  assert.deepEqual(plan.outlines, []);
});
