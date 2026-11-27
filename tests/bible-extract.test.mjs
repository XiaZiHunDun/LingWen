import assert from 'node:assert/strict';
import test from 'node:test';

import {
  BIBLE_CATEGORIES,
  MAX_CANDIDATES,
  MAX_CONTENT_CHARS,
  MAX_TITLE_CHARS,
  buildBibleExtractPrompt,
  parseBibleCandidates,
} from '../src/lib/bible-extract.js';

test('buildBibleExtractPrompt 带上正文、已有标题与输出格式要求', () => {
  const { system, user } = buildBibleExtractPrompt({
    chapterTitle: '第一章 夜奔',
    content: '林昭推开镖局的门，风雪扑面。',
    existingTitles: ['林昭', ' ', '城南镖局'],
  });

  assert.match(system, /JSON 数组/);
  assert.match(system, /人物 \/ 地点 \/ 物品 \/ 组织 \/ 设定/);
  assert.match(user, /第一章 夜奔/);
  assert.match(user, /林昭、城南镖局/);
  assert.match(user, /林昭推开镖局的门/);
});

test('buildBibleExtractPrompt 缺省参数也能生成稳定文本', () => {
  const { system, user } = buildBibleExtractPrompt();

  assert.equal(typeof system, 'string');
  assert.match(user, /（未命名章节）/);
  assert.match(user, /（暂无）/);
  assert.match(user, /（正文为空）/);
});

test('parseBibleCandidates 解析纯 JSON 数组', () => {
  const raw = JSON.stringify([
    { category: '人物', title: '林昭', content: '城南镖局的少年镖师' },
    { category: '地点', title: '城南镖局', content: '林昭栖身的地方' },
  ]);

  const { candidates, skippedDuplicates } = parseBibleCandidates(raw);
  assert.equal(skippedDuplicates, 0);
  assert.deepEqual(candidates, [
    { category: '人物', title: '林昭', content: '城南镖局的少年镖师' },
    { category: '地点', title: '城南镖局', content: '林昭栖身的地方' },
  ]);
});

test('parseBibleCandidates 容忍 ```json 围栏与前后多余文字', () => {
  const raw = [
    '好的，以下是抽取结果：',
    '```json',
    JSON.stringify([{ category: '物品', title: '断雪刀', content: '林昭的佩刀' }]),
    '```',
    '以上共 1 条。',
  ].join('\n');

  const { candidates } = parseBibleCandidates(raw);
  assert.deepEqual(candidates, [{ category: '物品', title: '断雪刀', content: '林昭的佩刀' }]);
});

test('parseBibleCandidates 兼容 { candidates: [...] } 包装', () => {
  const raw = JSON.stringify({ candidates: [{ category: '组织', title: '城南镖局', content: '镖局' }] });
  const { candidates } = parseBibleCandidates(raw);
  assert.equal(candidates.length, 1);
  assert.equal(candidates[0].category, '组织');
});

test('parseBibleCandidates 非法 JSON 抛含「模型输出不是合法 JSON」的错误', () => {
  assert.throws(() => parseBibleCandidates('这不是 JSON'), /模型输出不是合法 JSON/);
  assert.throws(() => parseBibleCandidates('[{"category":"人物",'), /模型输出不是合法 JSON/);
});

test('parseBibleCandidates 非法分类归「设定」，并清洗空白', () => {
  const raw = JSON.stringify([
    { category: '灵兽', title: '  雪 鹰 ', content: '  通体雪白\n的鹰  ' },
    { category: '道具', title: '断雪刀', content: '佩刀' },
  ]);

  const { candidates } = parseBibleCandidates(raw);
  assert.equal(candidates[0].category, '设定');
  assert.equal(candidates[0].title, '雪 鹰');
  assert.equal(candidates[0].content, '通体雪白 的鹰');
  assert.equal(candidates[1].category, '物品');
  assert.ok(BIBLE_CATEGORIES.includes(candidates[0].category));
});

test('parseBibleCandidates 按 title 去重（忽略空白与大小写）并统计 skippedDuplicates', () => {
  const raw = JSON.stringify([
    { category: '人物', title: 'Lin Zhao', content: 'a' },
    { category: '人物', title: 'linzhao', content: 'b' },
    { category: '人物', title: '林 昭', content: 'c' },
    { category: '人物', title: '林昭', content: 'd' },
  ]);

  const { candidates, skippedDuplicates } = parseBibleCandidates(raw);
  assert.equal(candidates.length, 2);
  assert.equal(skippedDuplicates, 2);
  assert.deepEqual(
    candidates.map((item) => item.title),
    ['Lin Zhao', '林 昭'],
  );
});

test('parseBibleCandidates 过滤掉与已有设定重复的标题', () => {
  const raw = JSON.stringify([
    { category: '人物', title: ' 林昭 ', content: '重复' },
    { category: '地点', title: '城南镖局', content: '新增' },
  ]);

  const { candidates, skippedDuplicates } = parseBibleCandidates(raw, [' 林昭 ', '旧镖局']);
  assert.deepEqual(candidates, [{ category: '地点', title: '城南镖局', content: '新增' }]);
  assert.equal(skippedDuplicates, 1);
});

test('parseBibleCandidates 截断超长 title / content 并最多返回 MAX_CANDIDATES 条', () => {
  const longTitle = '标'.repeat(40);
  const longContent = '文'.repeat(200);
  const raw = JSON.stringify(
    Array.from({ length: MAX_CANDIDATES + 4 }, (_, index) => ({
      category: '设定',
      title: `${longTitle}${index}`,
      content: longContent,
    })),
  );

  const { candidates } = parseBibleCandidates(raw);
  assert.equal(candidates.length, MAX_CANDIDATES);

  const shorterTitle = JSON.stringify([{ category: '设定', title: longTitle, content: longContent }]);
  const single = parseBibleCandidates(shorterTitle).candidates[0];
  assert.ok(single.title.length <= MAX_TITLE_CHARS);
  assert.ok(single.content.length <= MAX_CONTENT_CHARS);
  assert.ok(single.content.endsWith('…'));
});

test('parseBibleCandidates 丢弃空标题条目', () => {
  const raw = JSON.stringify([
    { category: '人物', title: '   ', content: '无标题' },
    { category: '人物', title: '林昭', content: '' },
  ]);

  const { candidates } = parseBibleCandidates(raw);
  assert.deepEqual(candidates, [{ category: '人物', title: '林昭', content: '' }]);
});
