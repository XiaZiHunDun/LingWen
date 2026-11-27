/**
 * selectChapterContext 的「可手动排除块」行为 + normalizeExcludeKeys 归一化。
 * 只覆盖纯函数，不碰数据库 / 网络。
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  EXCLUDABLE_BLOCK_KEYS,
  normalizeExcludeKeys,
  selectChapterContext,
} from '../src/lib/chapter-context.js';

/** 构造一份含全部块（含可排除 5 块）的上下文入参。 */
function fixture() {
  const chapters = [
    { id: 1, seq: 1, title: '第一章', content: '更早章节正文', summary: '更早章节摘要' },
    { id: 2, seq: 2, title: '第二章', content: '上一章正文内容', summary: '上一章摘要' },
    { id: 3, seq: 3, title: '第三章', outlineId: 9, content: '本章已有正文' },
  ];
  return {
    book: { title: '测试书', genre: '玄幻' },
    bible: [{ category: '人物', title: '林一', content: '主角' }],
    outlines: [{ id: 9, title: '大纲标题', summary: '大纲摘要' }],
    chapters,
    currentChapter: chapters[2],
    existingContent: '本章已有正文',
    targetWords: 1200,
    mode: 'append',
    instruction: '写得克制一些',
  };
}

const ALL_KEYS = ['book', 'bible', 'previous', 'outline', 'title', 'existing', 'target', 'task', 'instruction'];

test('normalizeExcludeKeys：固定可排除 key 集合为 5 项', () => {
  assert.deepEqual([...EXCLUDABLE_BLOCK_KEYS], ['book', 'bible', 'previous', 'outline', 'existing']);
});

test('normalizeExcludeKeys：数组去重并保留首见顺序', () => {
  assert.deepEqual(normalizeExcludeKeys(['bible', 'book', 'bible']), ['bible', 'book']);
});

test('normalizeExcludeKeys：逗号分隔字符串', () => {
  assert.deepEqual(normalizeExcludeKeys('book, outline ,previous'), ['book', 'outline', 'previous']);
});

test('normalizeExcludeKeys：重复 query 参数（数组元素内含逗号）也能归一', () => {
  assert.deepEqual(normalizeExcludeKeys(['book,bible', 'bible', 'outline']), [
    'book',
    'bible',
    'outline',
  ]);
});

test('normalizeExcludeKeys：title/task/target/instruction 传了也忽略', () => {
  assert.deepEqual(normalizeExcludeKeys(['title', 'task', 'target', 'instruction']), []);
  assert.deepEqual(normalizeExcludeKeys('title,task,book'), ['book']);
});

test('normalizeExcludeKeys：非法输入静默返回 []', () => {
  assert.deepEqual(normalizeExcludeKeys(undefined), []);
  assert.deepEqual(normalizeExcludeKeys(null), []);
  assert.deepEqual(normalizeExcludeKeys(123), []);
  assert.deepEqual(normalizeExcludeKeys({ book: true }), []);
  assert.deepEqual(normalizeExcludeKeys('unknown,nope'), []);
  assert.deepEqual(normalizeExcludeKeys(['book', 42, null, { key: 'bible' }, 'bible']), [
    'book',
    'bible',
  ]);
});

test('selectChapterContext：默认输出全部块，顺序稳定', () => {
  const context = selectChapterContext(fixture());
  assert.deepEqual(
    context.blocks.map((block) => block.key),
    ALL_KEYS,
  );
  assert.equal(context.promptText, context.blocks.map((block) => block.content).join('\n\n'));
  assert.equal(context.totalChars, context.promptText.length);
});

test('selectChapterContext：excludeKeys 只剔除对应块，promptText / totalChars 同步变化', () => {
  const input = fixture();
  const full = selectChapterContext(input);
  const partial = selectChapterContext({ ...input, excludeKeys: ['book', 'bible', 'previous'] });

  assert.deepEqual(
    partial.blocks.map((block) => block.key),
    ['outline', 'title', 'existing', 'target', 'task', 'instruction'],
  );
  assert.equal(partial.promptText.includes('【书籍信息】'), false);
  assert.equal(partial.promptText.includes('【设定集/人物】'), false);
  assert.equal(partial.promptText.includes('【前情提要】'), false);
  assert.equal(partial.promptText.includes('【本章大纲】'), true);
  assert.equal(partial.totalChars, partial.promptText.length);
  assert.ok(partial.totalChars < full.totalChars);
});

test('selectChapterContext：排除不影响 stats 口径', () => {
  const input = fixture();
  const full = selectChapterContext(input);
  const partial = selectChapterContext({
    ...input,
    excludeKeys: ['previous', 'outline', 'existing'],
  });
  assert.deepEqual(partial.stats, full.stats);
  assert.equal(partial.stats.previousChapterTitle, '第 2 章 第二章');
  assert.equal(partial.stats.earlierCount, 1);
});

test('selectChapterContext：title/task 永远不可排除，非法 key 与错类型入参静默忽略', () => {
  const input = fixture();
  const full = selectChapterContext(input);

  const ignoringProtected = selectChapterContext({
    ...input,
    excludeKeys: ['title', 'task', 'target', 'instruction', 'unknown'],
  });
  assert.deepEqual(
    ignoringProtected.blocks.map((block) => block.key),
    ALL_KEYS,
  );
  assert.equal(ignoringProtected.promptText, full.promptText);

  const wrongTypes = selectChapterContext({ ...input, excludeKeys: 'not-an-array-but-a-key' });
  assert.deepEqual(wrongTypes.blocks.map((block) => block.key), ALL_KEYS);

  const notArray = selectChapterContext({ ...input, excludeKeys: 42 });
  assert.deepEqual(notArray.blocks.map((block) => block.key), ALL_KEYS);
});

test('selectChapterContext：字符串形式的 excludeKeys 与数组等价（逗号分隔）', () => {
  const input = fixture();
  const byArray = selectChapterContext({ ...input, excludeKeys: ['book', 'existing'] });
  const byString = selectChapterContext({ ...input, excludeKeys: 'book, existing, book' });
  assert.deepEqual(
    byString.blocks.map((block) => block.key),
    byArray.blocks.map((block) => block.key),
  );
  assert.equal(byString.promptText, byArray.promptText);
});
