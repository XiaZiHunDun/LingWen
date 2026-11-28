import test from 'node:test';
import assert from 'node:assert/strict';

import { summarizeBibleCoverage } from '../src/lib/bible-coverage.js';

test('正文多处命中：occurrences 累加、chapterCount 去重计数', () => {
  const result = summarizeBibleCoverage({
    bible: [{ id: 1, title: '苏晚', category: '人物' }],
    chapters: [
      { content: '苏晚走进雨里。苏晚抬头。', title: '第一章' },
      { content: '与苏晚无关。', title: '第二章' },
      { content: '没有她。', title: '第三章' },
    ],
    outlines: [],
  });

  assert.equal(result.total, 1);
  assert.equal(result.usedCount, 1);
  assert.equal(result.unusedCount, 0);
  assert.deepEqual(result.items[0], {
    id: 1,
    title: '苏晚',
    category: '人物',
    occurrences: 3,
    chapterCount: 2,
    outlineCount: 0,
  });
});

test('仅大纲摘要命中一次', () => {
  const result = summarizeBibleCoverage({
    bible: [{ id: 7, title: '钥匙', category: '道具' }],
    chapters: [{ content: '门锁着。', title: '第一章' }],
    outlines: [
      { title: '卷一', summary: '她摸到粗粝的钥匙。' },
      { title: '卷二', summary: '空的。' },
    ],
  });

  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].occurrences, 1);
  assert.equal(result.items[0].chapterCount, 0);
  assert.equal(result.items[0].outlineCount, 1);
  assert.equal(result.usedCount, 1);
});

test('大纲摘要 + 大纲标题命中：occurrences 累加、outlineCount 按条去重', () => {
  const result = summarizeBibleCoverage({
    bible: [{ id: 8, title: '钥匙', category: '道具' }],
    chapters: [],
    outlines: [
      { title: '卷一', summary: '钥匙，还是钥匙。' },
      { title: '钥匙卷', summary: '与其它无关。' },
      { title: '卷三', summary: '无关。' },
    ],
  });

  assert.equal(result.items[0].occurrences, 3);
  assert.equal(result.items[0].outlineCount, 2);
  assert.equal(result.usedCount, 1);
  assert.equal(result.unusedCount, 0);
});

test('从未命中：occurrences 全 0 且计入 unusedCount', () => {
  const result = summarizeBibleCoverage({
    bible: [{ id: 2, title: '灰塔', category: '地点' }],
    chapters: [{ content: '这里只有雨。', title: '第一章' }],
    outlines: [{ title: '卷一', summary: '风很大。' }],
  });

  assert.equal(result.total, 1);
  assert.equal(result.usedCount, 0);
  assert.equal(result.unusedCount, 1);
  assert.deepEqual(result.items[0], {
    id: 2,
    title: '灰塔',
    category: '地点',
    occurrences: 0,
    chapterCount: 0,
    outlineCount: 0,
  });
});

test('空标题 / 非字符串标题跳过，且不计入 total', () => {
  const result = summarizeBibleCoverage({
    bible: [
      { id: 1, title: '   ', category: '人物' },
      { id: 2, title: '', category: '人物' },
      { id: 3, title: 42, category: '人物' },
      { id: 4, category: '人物' },
      { id: 5, title: '陆迟', category: '人物' },
    ],
    chapters: [{ content: '陆迟来了。', title: '第一章' }],
    outlines: [],
  });

  assert.equal(result.total, 1);
  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].title, '陆迟');
  assert.equal(result.usedCount, 1);
});

test('区分大小写：Abc 不命中 abc', () => {
  const lower = summarizeBibleCoverage({
    bible: [{ id: 1, title: 'Abc', category: '术语' }],
    chapters: [{ content: 'abc abc', title: '第一章' }],
    outlines: [],
  });
  assert.equal(lower.items[0].occurrences, 0);
  assert.equal(lower.unusedCount, 1);

  const exact = summarizeBibleCoverage({
    bible: [{ id: 1, title: 'Abc', category: '术语' }],
    chapters: [{ content: 'Abc abc', title: '第一章' }],
    outlines: [],
  });
  assert.equal(exact.items[0].occurrences, 1);
  assert.equal(exact.usedCount, 1);
});

test('排序：未使用在前，同分按 title 升序', () => {
  const result = summarizeBibleCoverage({
    bible: [
      { id: 1, title: '乙物', category: '道具' },
      { id: 2, title: '丙物', category: '道具' },
      { id: 3, title: '甲物', category: '道具' },
      { id: 4, title: '丁物', category: '道具' },
    ],
    chapters: [{ content: '甲物 甲物 乙物 丙物', title: '第一章' }],
    outlines: [],
  });

  // 丁物 0 命中排最前；丙物 1 / 乙物 1 同分按标题升序（丙 < 乙）；甲物 2 最后。
  assert.deepEqual(
    result.items.map((item) => [item.title, item.occurrences]),
    [
      ['丁物', 0],
      ['丙物', 1],
      ['乙物', 1],
      ['甲物', 2],
    ],
  );
  assert.equal(result.usedCount, 3);
  assert.equal(result.unusedCount, 1);
});

test('空输入返回全 0 与空数组', () => {
  const empty = summarizeBibleCoverage({ bible: [], chapters: [], outlines: [] });
  assert.deepEqual(empty, { items: [], total: 0, usedCount: 0, unusedCount: 0 });

  assert.deepEqual(summarizeBibleCoverage(), {
    items: [],
    total: 0,
    usedCount: 0,
    unusedCount: 0,
  });
});
