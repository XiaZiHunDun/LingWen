import assert from 'node:assert/strict';
import { test } from 'node:test';

import { buildChapterExport } from '../src/lib/chapter-export.js';

/** 典型章节：seq / title / content 齐全。 */
const chapter = { seq: 3, title: '风起', content: '正文第一段。\n正文第二段。' };

test('md：首行 `# 第 N 章 标题`，空行后接正文，contentType 为 text/markdown', () => {
  const out = buildChapterExport(chapter, 'md');

  assert.equal(out.contentType, 'text/markdown; charset=utf-8');
  const lines = out.body.split('\n');
  assert.equal(lines[0], '# 第 3 章 风起', 'md 首行应为一级标题');
  assert.equal(lines[1], '', '标题行后应有一个空行');
  assert.equal(lines[2], '正文第一段。', '空行后紧接正文');
  assert.ok(out.body.includes('正文第二段。'));
});

test('txt：首行 `第 N 章 标题`，空行后接正文，contentType 为 text/plain', () => {
  const out = buildChapterExport(chapter, 'txt');

  assert.equal(out.contentType, 'text/plain; charset=utf-8');
  const lines = out.body.split('\n');
  assert.equal(lines[0], '第 3 章 风起', 'txt 首行不带 #');
  assert.equal(lines[1], '');
  assert.equal(lines[2], '正文第一段。');
});

test('format 非法（含 undefined/null/大写/未知值）一律按 md 处理', () => {
  const expected = buildChapterExport(chapter, 'md');

  for (const bad of [undefined, null, '', 'MD', 'TXT', 'html', 'markdown', 1, true]) {
    const out = buildChapterExport(chapter, bad);
    assert.deepEqual(out, expected, `${JSON.stringify(bad)} 应按 md 处理，与整书导出同口径`);
  }
});

test('空标题用「未命名」兜底，正文为空时只有标题行', () => {
  const mdOut = buildChapterExport({ seq: 1, title: '   ', content: '' }, 'md');
  assert.equal(mdOut.body, '# 第 1 章 未命名\n', '空标题 + 空正文只输出标题行');
  assert.equal(mdOut.body.split('\n')[0], '# 第 1 章 未命名');

  const txtOut = buildChapterExport({ seq: 2, content: '' }, 'txt');
  assert.equal(txtOut.body, '第 2 章 未命名\n', '缺 title 字段同样兜底为「未命名」');

  // 有标题但正文为空：仍然只有一行标题，没有多余空行。
  const emptyContent = buildChapterExport({ seq: 3, title: '风起', content: '' }, 'md');
  assert.equal(emptyContent.body, '# 第 3 章 风起\n');
});

test('seq 非法（缺失/NaN/Infinity/非数字）时序号退回 1', () => {
  for (const bad of [undefined, null, NaN, Infinity, '7', {}]) {
    const out = buildChapterExport({ seq: bad, title: '无名章', content: '' }, 'md');
    assert.equal(out.body.split('\n')[0], '# 第 1 章 无名章', `seq=${String(bad)} 应按 1 处理`);
  }

  // seq 合法时原样使用。
  assert.equal(
    buildChapterExport({ seq: 12, title: '终章', content: '' }, 'txt').body.split('\n')[0],
    '第 12 章 终章',
  );
});

test('filename 经过 encodeURIComponent，形如「第 1 章 标题.md」', () => {
  const mdOut = buildChapterExport({ seq: 1, title: '标题', content: '正文' }, 'md');
  assert.equal(mdOut.filename, encodeURIComponent('第 1 章 标题.md'));
  assert.equal(decodeURIComponent(mdOut.filename), '第 1 章 标题.md');
  assert.ok(!/\s/.test(mdOut.filename), 'filename 中不应出现未编码的空格');

  const txtOut = buildChapterExport({ seq: 1, title: '标题', content: '' }, 'txt');
  assert.equal(decodeURIComponent(txtOut.filename), '第 1 章 标题.txt');

  // 未传 format（按 md）时扩展名同样是 .md。
  assert.equal(decodeURIComponent(buildChapterExport({ seq: 1, title: '标题' }).filename), '第 1 章 标题.md');
});
