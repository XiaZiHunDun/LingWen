import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  FALLBACK_BOOK_TITLE,
  FALLBACK_CHAPTER_TITLE,
  parseMarkdownBook,
  unescapeMarkdownBody,
} from '../src/lib/book-import.js';
import { buildBookExport, escapeMarkdownBody } from '../src/lib/book-export.js';
import { countWords } from '../src/lib/wordcount.js';

/** 拼 Markdown 片段，避免模板字符串里的缩进污染正文。 */
function md(...lines) {
  return lines.join('\n');
}

test('正常多章：章数 / 顺序 / 标题 / 字数正确', () => {
  const source = md(
    '# 长夜行',
    '',
    '> 类型：玄幻',
    '> 简介：一个关于夜行的故事。',
    '',
    '## 开端',
    '',
    '第一段正文。',
    '',
    '### 三级标题保留',
    '',
    '第二段正文。',
    '',
    '## 转折',
    '',
    '转折正文。',
  );

  const { book, chapters } = parseMarkdownBook(source, { filename: '忽略.md' });

  assert.equal(book.title, '长夜行');
  assert.equal(book.genre, '玄幻');
  assert.equal(book.summary, '一个关于夜行的故事。');
  assert.equal(chapters.length, 2);

  assert.equal(chapters[0].title, '开端');
  assert.equal(chapters[1].title, '转折');
  assert.equal(chapters[0].content, '第一段正文。\n\n### 三级标题保留\n\n第二段正文。');
  assert.equal(chapters[1].content, '转折正文。');
  assert.equal(chapters[0].wordCount, countWords(chapters[0].content));
  assert.equal(chapters[1].wordCount, countWords('转折正文。'));
});

test('无二级标题：只有一章，章标题用书名', () => {
  const { book, chapters } = parseMarkdownBook(md('# 独章书', '', '全文就是一段正文。'));

  assert.equal(book.title, '独章书');
  assert.equal(chapters.length, 1);
  assert.equal(chapters[0].title, '独章书');
  assert.equal(chapters[0].content, '全文就是一段正文。');
  assert.equal(chapters[0].wordCount, countWords('全文就是一段正文。'));
});

test('两级标题都为空：书名与章标题都走兜底文案', () => {
  const { book, chapters } = parseMarkdownBook(md('#   ', '', '##   ', '', '正文内容。'), {
    filename: '空标题.md',
  });

  assert.equal(book.title, '空标题');
  assert.equal(chapters.length, 1);
  assert.equal(chapters[0].title, FALLBACK_CHAPTER_TITLE);
  assert.equal(chapters[0].content, '正文内容。');
});

test('无一级标题：书名取文件名（去掉 .md / .MD），没有文件名用兜底', () => {
  const withName = parseMarkdownBook(md('## 第一章', '', '正文。'), { filename: '我的书.md' });
  assert.equal(withName.book.title, '我的书');

  const upper = parseMarkdownBook(md('## 第一章', '', '正文。'), { filename: '大写的书.MD' });
  assert.equal(upper.book.title, '大写的书');

  const none = parseMarkdownBook(md('## 第一章', '', '正文。'));
  assert.equal(none.book.title, FALLBACK_BOOK_TITLE);
});

test('空文件 / 只有标题没正文：不抛错，返回 0 章空结构', () => {
  const empty = parseMarkdownBook('');
  assert.equal(empty.book.title, FALLBACK_BOOK_TITLE);
  assert.deepEqual(empty.chapters, []);

  const blank = parseMarkdownBook('   \n\n\t\n');
  assert.deepEqual(blank.chapters, []);

  const titleOnly = parseMarkdownBook(md('# 只有标题', '', '   '));
  assert.equal(titleOnly.book.title, '只有标题');
  assert.deepEqual(titleOnly.chapters, []);

  const emptyHeading = parseMarkdownBook(md('# 只有标题', '', '## 空章', ''));
  assert.equal(emptyHeading.chapters.length, 1);
  assert.equal(emptyHeading.chapters[0].content, '');
  assert.equal(emptyHeading.chapters[0].wordCount, 0);
});

test('超长正文（10 万字以上 / 几千行）不截断', () => {
  const lines = [];
  for (let i = 0; i < 4000; i += 1) {
    lines.push(`第 ${i} 行正文，这里是一段足够长的中文内容用来堆字数。`);
  }
  const body = lines.join('\n');
  assert.ok(body.length > 100000);

  const { chapters } = parseMarkdownBook(md('# 长书', '', '## 长章', '', body));
  assert.equal(chapters.length, 1);
  assert.equal(chapters[0].content, body);
  assert.equal(chapters[0].wordCount, countWords(body));
});

test('unescapeMarkdownBody 是 escapeMarkdownBody 的逆函数', () => {
  const samples = [
    '',
    '普通正文。',
    '# 看起来像标题',
    '> 引用行\n> 第二行引用',
    '- 列表项\n+ 另一种列表\n* 星号列表',
    '1. 有序列表\n2. 第二项',
    '---',
    '===',
    '***',
    '___',
    '- - -',
    '```js\nconst a = 1;\n```',
    '~~~\n波浪号围栏\n~~~',
    '已经转义过的 \\# 与 \\> 与 \\-\\-\\-',
    '单个反斜杠 \\ 与双反斜杠 \\\\ 与结尾反斜杠 \\',
    '| 表格 | 列 |\n| --- | --- |',
    '\n\n前后空行\n\n',
  ];

  for (const sample of samples) {
    assert.equal(unescapeMarkdownBody(escapeMarkdownBody(sample)), sample);
  }
});

test('导出 → 导入往返：章数 / 顺序 / 每章正文与字数一致', () => {
  const book = { title: '往返之书', genre: '悬疑', summary: '简介里也可能有 # 号。' };
  const chapters = [
    {
      seq: 1,
      title: '第一章的标题',
      content: md(
        '# 这行本来像一级标题',
        '',
        '> 这行本来像引用',
        '',
        '- 列表项一',
        '1. 有序列表项',
        '',
        '---',
        '',
        '```js',
        'const a = 1;',
        '```',
        '',
        '## 这行本来像二级标题',
        '',
        '正文结束。',
      ),
    },
    { seq: 2, title: '第二 章', content: '只有一行正文。' },
    { seq: 3, title: '空章', content: '' },
    {
      seq: 4,
      title: '反斜杠章',
      content: '转义过的 \\# 与 \\> 以及结尾反斜杠 \\',
    },
  ];

  const exported = buildBookExport({ book, chapters }, 'md');
  const parsed = parseMarkdownBook(exported.body, { filename: '往返之书.md' });

  assert.equal(parsed.book.title, '往返之书');
  assert.equal(parsed.book.genre, '悬疑');
  assert.equal(parsed.book.summary, '简介里也可能有 # 号。');
  assert.equal(parsed.chapters.length, chapters.length);

  chapters.forEach((original, index) => {
    const imported = parsed.chapters[index];
    assert.equal(imported.title, original.title);
    assert.equal(imported.content, original.content);
    assert.equal(imported.wordCount, countWords(original.content));
    assert.equal(imported.wordCount, countWords(imported.content));
  });

  // 统计段不该变成最后一章正文。
  assert.ok(!parsed.chapters.some((chapter) => chapter.content.includes('总字数')));
  assert.equal(
    parsed.chapters.reduce((sum, chapter) => sum + chapter.wordCount, 0),
    exported.wordCount,
  );
});

test('导出 → 导入往返：0 章的书不产生章节', () => {
  const exported = buildBookExport({ book: { title: '空书' }, chapters: [] }, 'md');
  const parsed = parseMarkdownBook(exported.body, { filename: '空书.md' });
  assert.equal(parsed.book.title, '空书');
  assert.deepEqual(parsed.chapters, []);
});
