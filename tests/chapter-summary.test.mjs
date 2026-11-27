import test from 'node:test';
import assert from 'node:assert/strict';

import {
  SUMMARY_MAX_CHARS,
  buildChapterSummaryPrompt,
  clipSummary,
} from '../src/lib/chapter-summary.js';

test('clipSummary：去掉 Markdown / 包裹引号 / 多余空白，压成单段且 ≤200 字', () => {
  const raw = [
    '## 第 3 章 概述',
    '',
    '**林昭**  在  雪夜   追查`密信`，',
    '- 列表项一',
    '- 列表项二',
    '> 引用一句话',
    '[链接文字](https://example.com)',
    '```',
    'code 片段',
    '```',
  ].join('\n');

  const cleaned = clipSummary(raw);
  assert.ok(cleaned.length <= SUMMARY_MAX_CHARS);
  assert.ok(!cleaned.includes('#'));
  assert.ok(!cleaned.includes('**'));
  assert.ok(!cleaned.includes('`'));
  assert.ok(!cleaned.includes('- '));
  assert.ok(!cleaned.includes('>'));
  assert.ok(!cleaned.includes('](http'));
  assert.ok(!cleaned.includes('```'));
  assert.ok(!cleaned.includes('\n'));
  assert.ok(!/\s{2,}/.test(cleaned), '连续空白应被压成单个空格');
  assert.ok(cleaned.includes('林昭'));
  assert.ok(cleaned.includes('链接文字'));

  assert.equal(clipSummary('「这是一段带引号的摘要」'), '这是一段带引号的摘要');
  assert.equal(clipSummary('“双层引号内容”'), '双层引号内容');

  const long = '字'.repeat(500);
  const clipped = clipSummary(long);
  assert.equal(clipped.length, SUMMARY_MAX_CHARS);
  assert.ok(clipped.endsWith('…'));

  assert.equal(clipSummary(null), '');
  assert.equal(clipSummary(undefined), '');
  assert.equal(clipSummary(123), '');
  assert.ok(clipSummary('自定义上限', 3).length <= 3);
});

test('buildChapterSummaryPrompt：system 说明摘要规则，user 含标题与正文', () => {
  const title = '第 7 章 雪夜追凶';
  const content = '林昭踏进雪地，借着月光辨认脚印，一路追到废弃的钟楼。'.repeat(10);
  const { system, user } = buildChapterSummaryPrompt({ title, content });

  assert.equal(typeof system, 'string');
  assert.equal(typeof user, 'string');
  assert.ok(system.includes('摘要'));
  assert.ok(system.includes(String(SUMMARY_MAX_CHARS)));
  assert.ok(system.includes('只输出'));
  assert.ok(/不分点|不要分点/.test(system));
  assert.ok(!system.includes(title), 'system 不应夹带本章标题');

  assert.ok(user.includes(title));
  assert.ok(user.includes('林昭踏进雪地'));
  assert.ok(user.includes('【章节标题】'));
  assert.ok(user.includes('【章节正文】'));
  assert.ok(user.includes(String(SUMMARY_MAX_CHARS)));
  assert.ok(!user.includes('正文已截断'));
});

test('buildChapterSummaryPrompt：超长正文默认截到 6000 字并标注截断', () => {
  const content = `${'前'.repeat(8000)}结尾独特标记`;
  const { user } = buildChapterSummaryPrompt({ title: '长章', content });

  assert.ok(user.includes('正文已截断'));
  assert.ok(user.includes('6000'));
  assert.ok(!user.includes('结尾独特标记'), '截断后不应包含正文末尾');
  assert.ok(user.length < content.length);

  // 自定义 maxChars 透传到 prompt
  const custom = buildChapterSummaryPrompt({ title: '短章', content: '正文', maxChars: 80 });
  assert.ok(custom.system.includes('80'));
  assert.ok(custom.user.includes('80'));
});

test('buildChapterSummaryPrompt：入参缺失时不抛错，标题有兜底', () => {
  const empty = buildChapterSummaryPrompt();
  assert.ok(empty.system.length > 0);
  assert.ok(empty.user.includes('（未命名章节）'));
  assert.ok(empty.user.includes('（正文为空）'));

  const noTitle = buildChapterSummaryPrompt({ content: '只有正文' });
  assert.ok(noTitle.user.includes('（未命名章节）'));
  assert.ok(noTitle.user.includes('只有正文'));
});
