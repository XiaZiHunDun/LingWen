import test from 'node:test';
import assert from 'node:assert/strict';

import {
  BIBLE_SNIPPET_CHARS,
  EXISTING_TAIL_CHARS,
  FALLBACK_OPENING_CHARS,
  MAX_BIBLE_ITEMS,
  MAX_EARLIER_CHAPTERS,
  OUTLINE_SUMMARY_CHARS,
  PREV_TAIL_CHARS,
  SUMMARY_CHARS,
  clipText,
  selectChapterContext,
  takeHead,
  takeTail,
} from '../src/lib/chapter-context.js';

const book = {
  id: 1,
  title: '长夜书',
  genre: '玄幻',
  style: '冷峻克制',
  summary: '一个少年寻找失落记忆的故事。',
};

/** 造一行章节（repo 返回的 camelCase 形状）。 */
function chapter(seq, title, content, extra = {}) {
  return {
    id: extra.id ?? seq,
    seq,
    title,
    content,
    summary: extra.summary ?? null,
    outlineId: extra.outlineId ?? null,
  };
}

// 3000 字长正文：开头有独特标记，结尾也有独特标记，用于断言「取的是尾部」。
const HEAD_MARK = '开头标记开头标记';
const TAIL_MARK = '结尾标记结尾标记';
const LONG_BODY_1 = `${HEAD_MARK}${'中'.repeat(3000)}${TAIL_MARK}`;

test('两章的书：生成第二章时前情块含第一章正文结尾，而不是只给摘要', () => {
  const first = chapter(1, '初雪', LONG_BODY_1, { summary: '第一章的简短摘要' });
  const second = chapter(2, '夜行', '');
  const ctx = selectChapterContext({
    book,
    bible: [],
    outlines: [],
    chapters: [second, first], // 故意乱序，验证内部按 seq 排序
    currentChapter: second,
  });

  const previous = ctx.blocks.find((block) => block.key === 'previous');
  assert.ok(previous, '应当产出 previous 前情提要块');
  assert.match(previous.content, /第 1 章 初雪 · 正文结尾/);
  // 正文结尾进了上下文（不是只有摘要）
  assert.ok(previous.content.includes(TAIL_MARK), '前情块应包含上一章正文结尾');
  assert.ok(!previous.content.includes(HEAD_MARK), '前情块不应包含上一章正文开头');
  assert.ok(ctx.promptText.includes(TAIL_MARK));

  const tailSegment = takeTail(LONG_BODY_1, PREV_TAIL_CHARS);
  assert.equal(tailSegment.length, PREV_TAIL_CHARS);
  assert.ok(tailSegment.endsWith('…'));
  assert.ok(tailSegment.includes(TAIL_MARK));
  assert.ok(previous.content.includes(tailSegment));

  assert.equal(ctx.stats.hasPreviousTail, true);
  assert.equal(ctx.stats.previousChapterTitle, '第 1 章 初雪');
  assert.equal(ctx.stats.earlierCount, 0);
  assert.deepEqual(ctx.stats.chaptersWithoutSummary, []);
});

test('更早章节：有摘要用摘要（≤200 字），无摘要用正文开头 200 字并标注「无摘要」', () => {
  const longSummary = `第一章摘要 ${'铺'.repeat(600)}`;
  const c1 = chapter(1, '甲', '正文甲'.repeat(200), { summary: longSummary });
  const c2 = chapter(2, '乙', '乙章节正文开头在这里'.repeat(100));
  const c3 = chapter(3, '丙', '丙章节正文'.repeat(50), { summary: '丙摘要' });
  const c4 = chapter(4, '丁', '');

  const ctx = selectChapterContext({
    book,
    bible: [],
    outlines: [],
    chapters: [c1, c2, c3, c4],
    currentChapter: c4,
  });

  const previous = ctx.blocks.find((block) => block.key === 'previous');
  assert.ok(previous);

  // 更早章节 = 1、2、3 章；上一章 = 第 3 章
  assert.equal(ctx.stats.earlierCount, 2);
  assert.equal(ctx.stats.previousChapterTitle, '第 3 章 丙');
  assert.deepEqual(ctx.stats.chaptersWithoutSummary, [2]);

  const clippedSummary = clipText(longSummary, SUMMARY_CHARS);
  assert.equal(clippedSummary.length, SUMMARY_CHARS);
  assert.ok(previous.content.includes(clippedSummary), '有摘要的章节应注入摘要（已压到 200 字）');
  assert.ok(!previous.content.includes(longSummary), '不应注入未截断的长摘要');

  assert.ok(previous.content.includes('（无摘要，取正文开头）'));
  const head = takeHead(c2.content, FALLBACK_OPENING_CHARS);
  assert.equal(head.length, FALLBACK_OPENING_CHARS);
  assert.ok(previous.content.includes(head), '无摘要的章节应注入正文开头 200 字');
});

test('上一章正文为空 / 不存在 / 没有任何入参时拼装不报错', () => {
  const first = chapter(1, '空章', '');
  const second = chapter(2, '本章', '');
  const ctx = selectChapterContext({
    book,
    chapters: [first, second],
    currentChapter: second,
  });
  assert.equal(ctx.stats.hasPreviousTail, false);
  assert.match(ctx.promptText, /上一章正文为空/);
  assert.ok(ctx.promptText.length > 0);

  const noPrev = selectChapterContext({
    book,
    chapters: [],
    currentChapter: { id: 9, seq: 9, title: '孤章' },
  });
  assert.equal(noPrev.stats.hasPreviousTail, false);
  assert.equal(noPrev.stats.previousChapterTitle, null);
  assert.equal(noPrev.stats.earlierCount, 0);
  assert.ok(noPrev.blocks.every((block) => block.key !== 'previous'));
  assert.ok(noPrev.blocks.some((block) => block.key === 'title'));

  const blank = selectChapterContext();
  assert.ok(Array.isArray(blank.blocks));
  assert.equal(blank.promptText, blank.blocks.map((block) => block.content).join('\n\n'));
  assert.equal(blank.totalChars, blank.promptText.length);
});

test('clipText / takeHead / takeTail 边界：非字符串归一为空串、超长以「…」收尾且不超上限', () => {
  assert.equal(clipText(null), '');
  assert.equal(clipText(undefined), '');
  assert.equal(clipText(42), '');
  assert.equal(clipText(''), '');
  assert.equal(takeHead(null), '');
  assert.equal(takeTail({}), '');

  assert.equal(clipText('短文本', 10), '短文本');
  assert.equal(clipText('正好十个字啊哈哈', 8).length, 8);
  assert.equal(clipText('abcdefghij', 5), 'abcd…');

  const long = `${'前'.repeat(300)}${'后'.repeat(300)}`;
  assert.equal(takeHead(long, 100).length, 100);
  assert.ok(takeHead(long, 100).startsWith('前'));
  assert.ok(takeHead(long, 100).endsWith('…'));
  assert.ok(!takeHead(long, 100).includes('后'));

  assert.equal(takeTail(long, 100).length, 100);
  assert.ok(takeTail(long, 100).includes('后'));
  assert.ok(takeTail(long, 100).endsWith('…'));
  assert.ok(!takeTail(long, 100).includes('前'));
});

test('上限都生效：更早章节超过 20 章只留最近若干章，设定集最多 20 条、每条 300 字', () => {
  const chapters = [];
  for (let seq = 1; seq <= 25; seq += 1) {
    chapters.push(chapter(seq, `第${seq}节`, `正文${seq}`, { summary: `摘要${seq}` }));
  }
  const current = chapter(26, '终章', '');
  chapters.push(current);

  const bible = [];
  for (let index = 0; index < 30; index += 1) {
    bible.push({ id: index + 1, category: '人物', title: `角色${index}`, content: '设'.repeat(1000) });
  }
  const outlines = [{ id: 7, title: '大纲标题', summary: '大纲摘要'.repeat(200) }];
  const currentWithOutline = { ...current, outlineId: 7 };

  const ctx = selectChapterContext({
    book,
    bible,
    outlines,
    chapters,
    currentChapter: currentWithOutline,
    existingContent: `${'旧'.repeat(2000)}已有正文结尾`,
    targetWords: 1500,
    mode: 'replace',
    instruction: '保持第一人称'.repeat(200),
  });

  assert.equal(MAX_EARLIER_CHAPTERS, 20);
  assert.equal(ctx.stats.earlierCount, MAX_EARLIER_CHAPTERS);
  // 保留最近若干章：第 25 章是上一章，更早的 1~5 章被丢弃
  const previous = ctx.blocks.find((block) => block.key === 'previous');
  assert.ok(previous.content.includes('摘要6'));
  assert.ok(!previous.content.includes('摘要1：'));

  const bibleBlock = ctx.blocks.find((block) => block.key === 'bible');
  const bibleLines = bibleBlock.content.split('\n').slice(1);
  assert.equal(bibleLines.length, MAX_BIBLE_ITEMS);
  for (const line of bibleLines) {
    assert.ok(line.length <= BIBLE_SNIPPET_CHARS + 20, `单条设定超长：${line.length}`);
  }

  const outlineBlock = ctx.blocks.find((block) => block.key === 'outline');
  assert.ok(outlineBlock.content.includes('标题：大纲标题'));
  const outlineSummaryLine = outlineBlock.content
    .split('\n')
    .find((line) => line.startsWith('摘要：'));
  assert.equal(outlineSummaryLine.length, '摘要：'.length + OUTLINE_SUMMARY_CHARS);

  const existing = ctx.blocks.find((block) => block.key === 'existing');
  assert.ok(existing.content.includes('已有正文结尾'));
  assert.ok(existing.content.includes('不要照抄'));
  assert.equal(takeTail(`${'旧'.repeat(2000)}已有正文结尾`, EXISTING_TAIL_CHARS).length, EXISTING_TAIL_CHARS);

  const target = ctx.blocks.find((block) => block.key === 'target');
  assert.match(target.content, /约 1500 字/);

  const task = ctx.blocks.find((block) => block.key === 'task');
  assert.match(task.content, /重写本章正文/);

  const instruction = ctx.blocks.find((block) => block.key === 'instruction');
  assert.ok(instruction.content.length <= '【额外要求】\n'.length + 800);

  // block 形状与拼接规则
  for (const block of ctx.blocks) {
    assert.equal(block.chars, block.content.length);
    assert.equal(typeof block.key, 'string');
    assert.equal(typeof block.label, 'string');
  }
  assert.equal(ctx.totalChars, ctx.promptText.length);
});

test('纯函数：不修改入参、结果可重复、空块不出现', () => {
  const chapters = [chapter(1, '一', '正文一', { summary: '摘要一' }), chapter(2, '二', '')];
  const input = {
    book,
    bible: [{ id: 1, category: '', title: '剑', content: '' }],
    outlines: [],
    chapters,
    currentChapter: chapters[1],
  };
  const snapshot = JSON.stringify(input);

  const first = selectChapterContext(input);
  const second = selectChapterContext(input);

  assert.equal(JSON.stringify(input), snapshot, '入参不应被修改');
  assert.equal(first.promptText, second.promptText);
  assert.ok(first.blocks.every((block) => block.content.trim() !== ''));
  // 没有 outline / instruction / targetWords 时不产出对应块
  for (const key of ['outline', 'instruction', 'target']) {
    assert.ok(first.blocks.every((block) => block.key !== key));
  }

  const keys = first.blocks.map((block) => block.key);
  assert.deepEqual(keys.slice(0, 3), ['book', 'bible', 'previous']);
  assert.ok(keys.includes('title'));
  assert.equal(keys[keys.length - 1], 'task');
  assert.match(first.promptText, /^【书籍信息】/);
});
