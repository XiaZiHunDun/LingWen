import test from 'node:test';
import assert from 'node:assert/strict';

import { MAX_BIBLE_ITEMS, selectChapterContext } from '../src/lib/chapter-context.js';

const book = { id: 1, title: '长夜书', genre: '玄幻', style: '冷峻克制', summary: '一个少年寻找失落记忆的故事。' };

/** 本章大纲：摘要里出现「沈九斤」，用于验证设定相关性命中。 */
const outline = { id: 7, bookId: 1, order: 2, title: '转折', summary: '沈九斤在雨夜登场，与主角对峙。' };

const chapters = [
  { id: 1, seq: 1, title: '初雪', content: '第一章正文内容。', summary: '第一章摘要：主角离开山村。' },
  { id: 2, seq: 2, title: '夜行', content: '', summary: null, outlineId: 7 },
];
const current = chapters[1];

/** 造 30 条设定，默认标题「人物1」…「人物30」；overrides 可指定某条的标题。 */
function bibleList(overrides = {}) {
  const list = [];
  for (let i = 1; i <= 30; i += 1) {
    list.push({
      id: i,
      bookId: 1,
      category: '人物',
      title: overrides[i] ?? `人物${i}`,
      content: `第 ${i} 条设定：只在这条里出现的描述。`,
    });
  }
  return list;
}

/** 取设定块的正文行（去掉块头）。 */
function bibleLines(ctx) {
  const block = ctx.blocks.find((item) => item.key === 'bible');
  assert.ok(block, '应当产出 bible 设定块');
  return block.content.split('\n').slice(1);
}

test('30 条设定中第 25 条命中本章大纲 → 前移进前 20 条，stats 口径正确', () => {
  const ctx = selectChapterContext({
    book,
    bible: bibleList({ 25: '沈九斤' }),
    outlines: [outline],
    chapters,
    currentChapter: current,
  });

  const lines = bibleLines(ctx);
  assert.equal(lines.length, MAX_BIBLE_ITEMS, '设定块最多保留 20 条');
  assert.match(lines[0], /沈九斤/, '命中的设定应排到第一行');
  assert.ok(ctx.promptText.includes('沈九斤'), 'promptText 设定块里应出现命中的名字');
  // 其余未命中项保持原有顺序（人物1…人物24 依次补齐到第 20 条）。
  for (let index = 1; index < MAX_BIBLE_ITEMS; index += 1) {
    assert.match(lines[index], new RegExp(`人物${index}：`));
  }

  assert.equal(ctx.stats.bibleTotal, 30);
  assert.equal(ctx.stats.bibleIncluded, MAX_BIBLE_ITEMS);
  assert.ok(ctx.stats.bibleMentioned >= 1, '至少 1 条被判定为与本章相关');
  assert.equal(ctx.stats.bibleOmitted, 10);
});

test('全部未命中时设定顺序与改动前完全一致', () => {
  const ctx = selectChapterContext({
    book,
    bible: bibleList(),
    outlines: [outline],
    chapters,
    currentChapter: current,
  });

  const lines = bibleLines(ctx);
  assert.equal(lines.length, MAX_BIBLE_ITEMS);
  for (let index = 0; index < MAX_BIBLE_ITEMS; index += 1) {
    assert.match(lines[index], new RegExp(`人物${index + 1}：`), '未命中时保持原有数组顺序');
  }
  assert.equal(ctx.stats.bibleTotal, 30);
  assert.equal(ctx.stats.bibleIncluded, MAX_BIBLE_ITEMS);
  assert.equal(ctx.stats.bibleMentioned, 0);
  assert.equal(ctx.stats.bibleOmitted, 10);
});

test('不传 bible 时 stats 全 0 且不报错、不产出设定块', () => {
  const ctx = selectChapterContext({ book, outlines: [outline], chapters, currentChapter: current });

  assert.equal(ctx.blocks.some((block) => block.key === 'bible'), false);
  assert.equal(ctx.stats.bibleTotal, 0);
  assert.equal(ctx.stats.bibleIncluded, 0);
  assert.equal(ctx.stats.bibleMentioned, 0);
  assert.equal(ctx.stats.bibleOmitted, 0);
});

test('bible 被 exclude 时 bibleIncluded / bibleMentioned 为 0，总数与省略数仍按全量', () => {
  const ctx = selectChapterContext({
    book,
    bible: bibleList({ 25: '沈九斤' }),
    outlines: [outline],
    chapters,
    currentChapter: current,
    excludeKeys: ['bible'],
  });

  assert.equal(ctx.blocks.some((block) => block.key === 'bible'), false);
  // 注意：本章大纲摘要里本来就有「沈九斤」，所以只校验设定块自身的内容没有进 prompt。
  assert.ok(!ctx.promptText.includes('【设定集/人物】'), '被排除后不应出现设定块头');
  assert.ok(!ctx.promptText.includes('第 25 条设定'), '被排除后设定正文不应进入 prompt');
  assert.equal(ctx.stats.bibleTotal, 30);
  assert.equal(ctx.stats.bibleIncluded, 0);
  assert.equal(ctx.stats.bibleMentioned, 0);
  assert.equal(ctx.stats.bibleOmitted, 30);
});

test('标题不足 2 字不参与评分；上一章标题与额外要求里的名字也能提升命中', () => {
  const bible = [
    { id: 1, category: '人物', title: '甲', content: '单字标题，不参与评分。' },
    { id: 2, category: '人物', title: '雪', content: '单字标题命中上一章标题也不计入。' },
    { id: 3, category: '物品', title: '路人甲', content: '普通设定一。' },
    { id: 4, category: '物品', title: '路人乙', content: '普通设定二。' },
    { id: 5, category: '人物', title: '初雪', content: '与上一章标题同名的人物。' },
    { id: 6, category: '地点', title: '渡口', content: '额外要求里点名的地点。' },
  ];

  const ctx = selectChapterContext({
    book,
    bible,
    outlines: [outline],
    chapters,
    currentChapter: current,
    instruction: '这一章的落点在渡口。',
  });

  const lines = bibleLines(ctx);
  assert.equal(lines.length, bible.length);
  assert.match(lines[0], /初雪/, '上一章标题命中的设定应前置');
  assert.match(lines[1], /渡口/, '额外要求命中的设定应前置');
  assert.equal(ctx.stats.bibleTotal, 6);
  assert.equal(ctx.stats.bibleIncluded, 6);
  assert.equal(ctx.stats.bibleMentioned, 2);
  assert.equal(ctx.stats.bibleOmitted, 0);
  // 单字标题不参与评分，未命中项保持原顺序（甲、雪、路人甲、路人乙）。
  assert.match(lines[2], /甲/);
  assert.match(lines[3], /雪/);
  assert.match(lines[4], /路人甲/);
  assert.match(lines[5], /路人乙/);
});
