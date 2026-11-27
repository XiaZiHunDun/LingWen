import assert from 'node:assert/strict';
import { test } from 'node:test';

import { initDb, closeDb } from '../src/lib/db.js';
import {
  createBook,
  createChapter,
  getChapter,
  listChapterRevisions,
  listChapters,
} from '../src/lib/repo.js';
import { countOccurrences, previewBookReplace, replaceBookText } from '../src/lib/find-replace.js';
import { countWords } from '../src/lib/wordcount.js';

/**
 * 建一个 :memory: 临时库 + 一本临时书，测试结束自动关连接。
 * 绝不触碰 data/ 下的真实书籍数据。
 * @param {import('node:test').TestContext} t
 * @returns {number} 临时书 id
 */
function setup(t) {
  initDb(':memory:');
  t.after(() => closeDb());
  const book = createBook({ title: '临时测试书（find-replace）' });
  return Number(book.id);
}

test('预览：统计每章命中次数与上下文片段，且不写库', (t) => {
  const bookId = setup(t);
  const first = createChapter({
    bookId,
    seq: 1,
    title: '第一章',
    content: '剑光如虹。剑光再起。无关内容。',
    status: 'final',
  });
  const second = createChapter({ bookId, seq: 2, title: '第二章', content: '没有那个词。' });
  const third = createChapter({
    bookId,
    seq: 3,
    title: '第三章',
    content: '剑光一闪，剑光又闪，剑光第三次。',
  });

  const preview = previewBookReplace(bookId, '剑光');
  assert.equal(preview.totalMatches, 5, '两章合计 5 处命中');
  assert.equal(preview.chapterCount, 2, '只有两章命中');
  assert.deepEqual(
    preview.chapters.map((chapter) => chapter.chapterId),
    [Number(first.id), Number(third.id)],
    '按章节顺序返回命中的章节',
  );
  assert.equal(preview.chapters[0].matches, 2);
  assert.equal(preview.chapters[1].matches, 3);
  assert.ok(preview.chapters[0].snippets.length >= 1, '应带上下文片段');
  assert.equal(preview.chapters[0].snippets[0].match, '剑光');
  assert.ok(preview.chapters[0].snippets[0].after.includes('如虹'), '片段应包含命中词后文');

  // 预览是只读操作：正文、字数、历史版本都不应变化。
  const unchanged = getChapter(first.id);
  assert.equal(String(unchanged.content), '剑光如虹。剑光再起。无关内容。');
  assert.equal(Number(unchanged.wordCount), 0, '预览不应回写 word_count');
  assert.equal(listChapterRevisions(first.id).length, 0, '预览不应产生历史快照');
  assert.equal(String(getChapter(second.id).content), '没有那个词。');

  // 空查找词：0 命中，绝不「匹配每处」。
  assert.equal(countOccurrences('aaaa', ''), 0);
  assert.equal(previewBookReplace(bookId, '').totalMatches, 0);
});

test('替换：正文与 word_count 一起更新，并给出「共替换 N 处，涉及 M 章」', (t) => {
  const bookId = setup(t);
  const first = createChapter({
    bookId,
    seq: 1,
    title: '第一章',
    content: '剑光如虹。剑光再起。无关内容。',
  });
  const second = createChapter({ bookId, seq: 2, title: '第二章', content: '没有那个词。' });

  const result = replaceBookText(bookId, { query: '剑光', replacement: '刀芒' });
  assert.equal(result.totalMatches, 2);
  assert.equal(result.chapterCount, 1);
  assert.equal(result.message, '共替换 2 处，涉及 1 章');

  const expectedContent = '刀芒如虹。刀芒再起。无关内容。';
  const updated = getChapter(first.id);
  assert.equal(String(updated.content), expectedContent, '正文应全部替换');
  assert.equal(Number(updated.wordCount), countWords(expectedContent), 'word_count 应重算');
  assert.ok(Number.isInteger(Number(updated.wordCount)));

  // 未命中的章节保持原样。
  assert.equal(String(getChapter(second.id).content), '没有那个词。');

  // 替换后旧词不再命中；重复替换同样的词返回 0 处且不报错。
  assert.equal(previewBookReplace(bookId, '剑光').totalMatches, 0);
  const again = replaceBookText(bookId, { query: '剑光', replacement: '刀芒' });
  assert.equal(again.totalMatches, 0);
  assert.equal(again.chapterCount, 0);

  // 支持替换成空串（删除该词）。
  replaceBookText(bookId, { query: '无关内容', replacement: '' });
  // 删除词后原句两个句号相邻，属预期。
  assert.equal(String(getChapter(first.id).content), '刀芒如虹。刀芒再起。。');
});

test('替换：为每章保存「替换前」历史版本快照，字数按旧正文计算', (t) => {
  const bookId = setup(t);
  const oldContent = '剑光如虹。剑光再起。';
  const chapter = createChapter({ bookId, seq: 1, title: '第一章', content: oldContent });

  replaceBookText(bookId, { query: '剑光', replacement: '刀芒' });

  const revisions = listChapterRevisions(chapter.id);
  assert.equal(revisions.length, 1, '每章一条历史快照');
  assert.equal(revisions[0].source, 'manual', '换词归类为手动编辑');
  assert.equal(revisions[0].wordCount, countWords(oldContent), '快照字数按旧正文计算');
  assert.ok(revisions[0].preview.includes('剑光'), '快照内容应是替换前的正文');
  assert.equal(String(getChapter(chapter.id).content), '刀芒如虹。刀芒再起。');
});

test('失败回滚：中途抛异常时正文、字数、历史快照全部不落库', (t) => {
  const bookId = setup(t);
  const first = createChapter({ bookId, seq: 1, title: '第一章', content: '剑光如虹。' });
  const second = createChapter({ bookId, seq: 2, title: '第二章', content: '剑光再起。' });

  const snapshot = () =>
    listChapters(bookId).map((row) => ({
      id: row.id,
      content: row.content,
      wordCount: row.wordCount,
      status: row.status,
    }));
  const before = snapshot();

  let calls = 0;
  assert.throws(
    () =>
      replaceBookText(bookId, {
        query: '剑光',
        replacement: '刀芒',
        onChapterUpdated: () => {
          calls += 1;
          if (calls === 1) throw new Error('模拟中途异常');
        },
      }),
    /模拟中途异常/,
    '异常应向上抛出',
  );

  assert.deepEqual(snapshot(), before, '章节正文 / 字数 / 状态应保持替换前状态');
  assert.equal(listChapterRevisions(first.id).length, 0, '第一处快照必须随事务回滚');
  assert.equal(listChapterRevisions(second.id).length, 0, '第二处快照也必须回滚');
  assert.equal(previewBookReplace(bookId, '剑光').totalMatches, 2, '旧词应仍然存在');

  // 回滚后重试应能成功，说明连接 / 事务状态正常。
  const retry = replaceBookText(bookId, { query: '剑光', replacement: '刀芒' });
  assert.equal(retry.totalMatches, 2);
  assert.equal(String(getChapter(first.id).content), '刀芒如虹。');
});

test('非法参数：空查找词、与原词相同都抛 RangeError（不写库）', (t) => {
  const bookId = setup(t);
  const chapter = createChapter({ bookId, seq: 1, title: '第一章', content: '剑光如虹。' });

  assert.throws(() => replaceBookText(bookId, { query: '', replacement: '刀芒' }), RangeError);
  assert.throws(
    () => replaceBookText(bookId, { query: '剑光', replacement: '剑光' }),
    RangeError,
  );
  assert.equal(String(getChapter(chapter.id).content), '剑光如虹。');
  assert.equal(listChapterRevisions(chapter.id).length, 0);
});
