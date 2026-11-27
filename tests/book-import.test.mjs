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

// ---- 可选拆章标题级别（headingLevel）+ 导入预览纯函数 ----
// import 声明在模块顶层会被提升，这里单独追加一条以保持既有断言块不动。
import { previewMarkdownImport } from '../src/lib/book-import.js';

test('headingLevel=3：三级标题拆章，`## ` 行保留在正文里', () => {
  const source = md(
    '# 三级书',
    '',
    '> 类型：玄幻',
    '',
    '## 卷一 卷首说明',
    '',
    '卷首说明正文。',
    '',
    '### 第 1 章 开端',
    '',
    '第一章正文。',
    '',
    '## 卷中过渡',
    '',
    '### 第 2 章 转折',
    '',
    '第二章正文。',
  );

  const { book, chapters } = parseMarkdownBook(source, { headingLevel: 3 });

  assert.equal(book.title, '三级书');
  assert.equal(book.genre, '玄幻');
  assert.equal(chapters.length, 2);
  assert.equal(chapters[0].title, '开端');
  assert.equal(chapters[1].title, '转折');
  // 首个 `### ` 之前的 `## ` 行与正文作为首章前置内容保留。
  assert.equal(
    chapters[0].content,
    '## 卷一 卷首说明\n\n卷首说明正文。\n\n第一章正文。\n\n## 卷中过渡',
  );
  // 第二章之前没有 `## ` 行，正文只有它自己。
  assert.equal(chapters[1].content, '第二章正文。');
  assert.equal(chapters[0].wordCount, countWords(chapters[0].content));
  assert.equal(chapters[1].wordCount, countWords(chapters[1].content));
});

test('headingLevel=3 且整篇没有三级标题：退回一章，章名用书名', () => {
  const source = md(
    '# 无三级',
    '',
    '## 看起来像章',
    '',
    '正文一。',
    '',
    '## 又一个',
    '',
    '正文二。',
  );

  const { book, chapters } = parseMarkdownBook(source, { headingLevel: 3 });
  assert.equal(book.title, '无三级');
  assert.equal(chapters.length, 1);
  assert.equal(chapters[0].title, '无三级');
  assert.equal(chapters[0].content, '## 看起来像章\n\n正文一。\n\n## 又一个\n\n正文二。');
  assert.equal(chapters[0].wordCount, countWords(chapters[0].content));

  // 空结构约定与 2 级一致：只有标题没正文 → 0 章。
  const titleOnly = parseMarkdownBook(md('# 只有标题', '', '   '), { headingLevel: 3 });
  assert.deepEqual(titleOnly.chapters, []);
});

test('headingLevel 只接受 2 / 3：缺省与显式 2 等价，其它值抛 TypeError', () => {
  const source = md('# 书', '', '## 章', '', '正文。', '', '### 三级', '', '更多正文。');

  assert.deepEqual(parseMarkdownBook(source), parseMarkdownBook(source, { headingLevel: 2 }));
  assert.deepEqual(
    parseMarkdownBook(source, { headingLevel: undefined }),
    parseMarkdownBook(source),
  );

  assert.throws(() => parseMarkdownBook(source, { headingLevel: 1 }), TypeError);
  assert.throws(() => parseMarkdownBook(source, { headingLevel: 4 }), TypeError);
  assert.throws(() => parseMarkdownBook(source, { headingLevel: '3' }), TypeError);
});

test('默认（2 级）导入结果不受新参数影响：导出产物仍能往返', () => {
  const book = { title: '默认二级', genre: null, summary: null };
  const chapters = [
    { seq: 1, title: '一', content: '正文一。' },
    { seq: 2, title: '二', content: '### 三级标题留在正文\n\n正文二。' },
  ];

  const exported = buildBookExport({ book, chapters }, 'md');
  const byDefault = parseMarkdownBook(exported.body, { filename: '默认二级.md' });
  const byTwo = parseMarkdownBook(exported.body, { filename: '默认二级.md', headingLevel: 2 });

  assert.deepEqual(byDefault, byTwo);
  assert.equal(byDefault.book.title, '默认二级');
  assert.equal(byDefault.chapters.length, 2);
  assert.deepEqual(
    byDefault.chapters.map((chapter) => chapter.title),
    ['一', '二'],
  );
  assert.equal(byDefault.chapters[1].content, '### 三级标题留在正文\n\n正文二。');
  assert.deepEqual(
    byDefault.chapters.map((chapter) => chapter.wordCount),
    chapters.map((chapter) => countWords(chapter.content)),
  );
});

test('previewMarkdownImport：书名 / 章节数 / 前 3 章标题正确且无副作用', () => {
  const source = md(
    '# 预览之书',
    '',
    '> 类型：奇幻',
    '> 简介：一段简介。',
    '',
    '## 第 1 章 开端',
    '',
    '正文一。',
    '',
    '## 第 2 章 发展',
    '',
    '正文二。',
    '',
    '## 第 3 章 高潮',
    '',
    '正文三。',
    '',
    '## 第 4 章 结局',
    '',
    '正文四。',
  );

  const before = JSON.stringify(source);
  const preview = previewMarkdownImport(source, { filename: '预览之书.md' });

  assert.deepEqual(preview, {
    book: { title: '预览之书', genre: '奇幻', summary: '一段简介。' },
    chapterCount: 4,
    chapterTitles: ['开端', '发展', '高潮'],
  });

  // 不修改入参、不落库：原文不变，重复调用结果一致。
  assert.equal(JSON.stringify(source), before);
  assert.deepEqual(preview, previewMarkdownImport(source, { filename: '预览之书.md' }));

  // 换 3 级：没有 `### ` → 退回一章（章名用书名），仍走同一份解析。
  const three = previewMarkdownImport(source, { filename: '预览之书.md', headingLevel: 3 });
  assert.equal(three.book.title, '预览之书');
  assert.equal(three.chapterCount, 1);
  assert.deepEqual(three.chapterTitles, ['预览之书']);

  // 0 章的空结构也能预览。
  const empty = previewMarkdownImport('', { filename: '空.md' });
  assert.equal(empty.chapterCount, 0);
  assert.deepEqual(empty.chapterTitles, []);
});
