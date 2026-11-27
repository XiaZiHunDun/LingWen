import assert from 'node:assert/strict';
import { test } from 'node:test';

import { buildBookExport, escapeMarkdownBody } from '../src/lib/book-export.js';
import { countWords } from '../src/lib/wordcount.js';

/** 典型书籍：含书名 / 类型 / 简介。 */
const book = { id: 1, title: '风起长林', genre: '仙侠', summary: '少年上山学剑。' };

/** 典型章节：顺序即输出顺序；第二章正文故意带 Markdown 活性字符与反斜杠。 */
const chapters = [
  { id: 11, seq: 1, title: '初入山门', content: '第一段。\n第二段。' },
  { id: 12, seq: 2, title: '试剑', content: '# 这不是标题\n路径 C:\\temp 结尾反斜杠 \\' },
];

test('章节顺序与输入一致，标题层级为 #（书名）/ ##（章节）', () => {
  const out = buildBookExport({ book, chapters }, 'md');
  const lines = out.body.split('\n');

  assert.equal(lines[0], '# 风起长林', '首行必须是书名一级标题');
  assert.equal(out.contentType, 'text/markdown; charset=utf-8');

  const first = out.body.indexOf('## 第 1 章 初入山门');
  const second = out.body.indexOf('## 第 2 章 试剑');
  assert.ok(first > 0 && second > 0, '两章都应输出二级标题');
  assert.ok(first < second, '章节顺序必须与输入（seq ASC）一致');

  // 除首行书名外，不应再有其它一级标题。
  const h1 = lines.filter((line) => /^#\s/u.test(line));
  assert.deepEqual(h1, ['# 风起长林']);
});

test('正文以 # 开头、含反斜杠的文本被正确转义，不会被渲染成标题', () => {
  const out = buildBookExport({ book, chapters }, 'md');

  assert.ok(out.body.includes('\\# 这不是标题'), '行首 # 应转义为 \\#');
  assert.ok(!/^# 这不是标题$/mu.test(out.body), '正文不应出现未转义的一级标题行');
  assert.ok(out.body.includes('C:\\\\temp'), '反斜杠应转义为 \\\\');
  assert.ok(out.body.includes('结尾反斜杠 \\\\'), '行尾反斜杠同样转义');

  // 行首其它活性字符：列表、有序列表、引用、表格。
  assert.equal(escapeMarkdownBody('- 一项'), '\\- 一项');
  assert.equal(escapeMarkdownBody('+ 一项'), '\\+ 一项');
  assert.equal(escapeMarkdownBody('* 一项'), '\\* 一项');
  assert.equal(escapeMarkdownBody('1. 一项'), '1\\. 一项');
  assert.equal(escapeMarkdownBody('> 引用'), '\\> 引用');
  assert.equal(escapeMarkdownBody('| a | b |'), '\\| a | b |');
  // 先转义反斜杠再处理行首，避免把新增的反斜杠二次转义。
  assert.equal(escapeMarkdownBody('# 反斜杠 \\ 混合'), '\\# 反斜杠 \\\\ 混合');
  // 非字符串 / 空串安全。
  assert.equal(escapeMarkdownBody(''), '');
  assert.equal(escapeMarkdownBody(undefined), '');
});

test('format 非法（含 undefined/null/大写/未知值）一律按 md 处理', () => {
  const expected = buildBookExport({ book, chapters }, 'md');

  for (const bad of [undefined, null, '', 'MD', 'TXT', 'html', 'markdown', 0, false]) {
    const out = buildBookExport({ book, chapters }, bad);
    assert.deepEqual(out, expected, `${JSON.stringify(bad)} 应按 md 处理`);
  }

  // txt 不转义：正文原样保留。
  const txtOut = buildBookExport({ book, chapters }, 'txt');
  assert.equal(txtOut.contentType, 'text/plain; charset=utf-8');
  assert.ok(txtOut.body.includes('# 这不是标题'), 'txt 应保持纯文本，不转义');
  assert.ok(txtOut.body.includes('C:\\temp'), 'txt 不应转义反斜杠');
  assert.ok(!txtOut.body.includes('\\#'), 'txt 不应出现转义字符');
});

test('末尾统计段的章数与总字数正确（口径同 countWords）', () => {
  const expectedWords =
    countWords(chapters[0].content) + countWords(chapters[1].content);

  const mdOut = buildBookExport({ book, chapters }, 'md');
  assert.ok(mdOut.body.includes('---'), 'md 统计段前应有 --- 分隔');
  assert.ok(
    mdOut.body.trimEnd().endsWith(`共 2 章，总字数 ${expectedWords} 字。`),
    '统计段应为最后一行',
  );
  assert.equal(mdOut.chapterCount, 2);
  assert.equal(mdOut.wordCount, expectedWords);

  const txtOut = buildBookExport({ book, chapters }, 'txt');
  assert.ok(txtOut.body.trimEnd().endsWith(`共 2 章，总字数 ${expectedWords} 字。`));

  // 空书：0 章 0 字，且只有书名 + 统计段。
  const empty = buildBookExport({ book: { title: '空的' }, chapters: [] }, 'md');
  assert.ok(empty.body.includes('# 空的'));
  assert.ok(empty.body.trimEnd().endsWith('共 0 章，总字数 0 字。'));

  // 空正文只输出标题。
  const headingOnly = buildBookExport(
    { book: { title: '书' }, chapters: [{ seq: 7, title: '空章', content: '' }] },
    'md',
  );
  assert.ok(headingOnly.body.includes('## 第 7 章 空章\n\n---'), '空正文章节只输出标题行');
});

test('seq 非法时按数组下标 + 1 兜底；空标题用「未命名」', () => {
  const out = buildBookExport(
    {
      book: { title: '书' },
      chapters: [
        { title: '第一章', content: 'a' },
        { seq: '2', title: '第二章', content: 'b' },
        { seq: NaN, content: '' },
      ],
    },
    'md',
  );

  assert.ok(out.body.includes('## 第 1 章 第一章'));
  assert.ok(out.body.includes('## 第 2 章 第二章'), '非数字 seq 按下标 + 1');
  assert.ok(out.body.includes('## 第 3 章 未命名'));
});

test('filename 含书名且已 encodeURIComponent', () => {
  const mdOut = buildBookExport({ book, chapters }, 'md');
  assert.equal(mdOut.filename, encodeURIComponent('风起长林.md'));
  assert.equal(decodeURIComponent(mdOut.filename), '风起长林.md');
  assert.ok(mdOut.filename.includes(encodeURIComponent('风起长林')), 'filename 必须含书名');
  assert.ok(!/\s/u.test(mdOut.filename), 'filename 不应出现未编码字符');

  const txtOut = buildBookExport({ book, chapters }, 'txt');
  assert.equal(decodeURIComponent(txtOut.filename), '风起长林.txt');

  // 缺书名兜底「未命名」。
  assert.equal(decodeURIComponent(buildBookExport({ chapters: [] }).filename), '未命名.md');
});
