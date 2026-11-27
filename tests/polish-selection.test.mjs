import test from 'node:test';
import assert from 'node:assert/strict';

import {
  MAX_CONTEXT_CHARS,
  MAX_SELECTION_CHARS,
  buildPolishPrompt,
  normalizePolishSelection,
} from '../src/lib/polish-prompt.js';

const base = {
  mode: 'polish',
  chapterTitle: '第七章 夜行',
  bookSettings: '书名：长夜\n风格：冷峻',
  outline: '标题：夜行\n摘要：主角夜闯码头。',
  content: '整章正文第一段。\n\n整章正文第二段。',
  selection: '他停在码头尽头，风把衣角掀起来。',
  before: '船灯在水面上晃。',
  after: '他听见有人叫他的名字。',
};

test('片段模式 prompt 同时包含【上文】【选中片段】【下文】三块', () => {
  const prompt = buildPolishPrompt(base);
  assert.equal(prompt.fragment, true);
  assert.ok(prompt.user.includes('【上文】'), '缺少【上文】');
  assert.ok(prompt.user.includes('【选中片段】'), '缺少【选中片段】');
  assert.ok(prompt.user.includes('【下文】'), '缺少【下文】');
  assert.ok(prompt.user.includes(base.selection));
  assert.ok(prompt.user.includes(base.before));
  assert.ok(prompt.user.includes(base.after));
  // 片段模式要求：保持人称语气、自然衔接、不新增人物情节、走向不变
  assert.ok(prompt.user.includes('保持叙事人称'));
  assert.ok(prompt.user.includes('自然衔接'));
  assert.ok(prompt.user.includes('不新增未出现的人物'));
  assert.ok(prompt.user.includes('情节走向与事件顺序不变'));
  // 只输出片段本身
  assert.ok(prompt.user.includes('只输出改写后的【选中片段】本身'));
});

test('无 before/after 时省略对应上下文块', () => {
  const prompt = buildPolishPrompt({ ...base, before: '', after: '   ' });
  assert.equal(prompt.fragment, true);
  assert.ok(prompt.user.includes('【选中片段】'));
  assert.ok(!prompt.user.includes('【上文】'), '空 before 不应出现【上文】');
  assert.ok(!prompt.user.includes('【下文】'), '空白 after 不应出现【下文】');
});

test('【原文正文】只出现在整章模式', () => {
  const whole = buildPolishPrompt({ ...base, selection: '', before: '', after: '' });
  assert.equal(whole.fragment, false);
  assert.ok(whole.user.includes('【原文正文】'));
  assert.ok(whole.user.includes(base.content));
  assert.ok(whole.user.includes('请直接输出修改后的完整正文。'));

  const fragment = buildPolishPrompt(base);
  assert.ok(!fragment.user.includes('【原文正文】'), '片段模式不应出现【原文正文】');
  assert.ok(!fragment.user.includes(base.content), '片段模式不应把整章正文塞进 prompt');
  assert.ok(
    !fragment.user.includes('请直接输出修改后的完整正文。'),
    '片段模式不应包含整章模式专属收尾句',
  );
  // 纯空白 selection 也走整章模式
  const blank = buildPolishPrompt({ ...base, selection: '   \n\t ' });
  assert.equal(blank.fragment, false);
  assert.ok(blank.user.includes('【原文正文】'));
});

test('选中内容超过 4000 字时校验失败', () => {
  assert.equal(typeof MAX_SELECTION_CHARS, 'number');
  const ok = buildPolishPrompt({ ...base, selection: '甲'.repeat(MAX_SELECTION_CHARS) });
  assert.equal(ok.fragment, true);

  const tooLong = '甲'.repeat(MAX_SELECTION_CHARS + 1);
  assert.throws(
    () => buildPolishPrompt({ ...base, selection: tooLong }),
    (err) => {
      assert.equal(err.name, 'PolishSelectionError');
      assert.equal(err.status, 400);
      assert.equal(err.message, '选中内容过长（最多 4000 字），请缩小范围');
      return true;
    },
  );
  assert.throws(() => normalizePolishSelection({ selection: '乙'.repeat(5000) }), /4000/);
});

test('before/after 截断到 500 字', () => {
  const long = '前'.repeat(900);
  const longAfter = '后'.repeat(1200);
  const normalized = normalizePolishSelection({
    selection: '片段',
    before: long,
    after: longAfter,
  });
  assert.equal(MAX_CONTEXT_CHARS, 500);
  assert.equal(normalized.before.length, 500);
  assert.equal(normalized.after.length, 500);
  assert.equal(normalized.before, long.slice(0, 500));
  assert.equal(normalized.after, longAfter.slice(0, 500));

  const prompt = buildPolishPrompt({ ...base, before: long, after: longAfter });
  assert.ok(prompt.user.includes(`【上文】\n${long.slice(0, 500)}`));
  assert.ok(prompt.user.includes(`【下文】\n${longAfter.slice(0, 500)}`));
  assert.ok(!prompt.user.includes(long.slice(0, 501)));
});
