import test from 'node:test';
import assert from 'node:assert/strict';

import { filterBibleItems, collectBibleCategories } from '../src/lib/bible-filter.js';

const items = [
  { id: 1, category: '人物', title: '林青', content: '剑宗大弟子，性格沉稳。' },
  { id: 2, category: '地点', title: '青云山', content: '剑宗山门所在，终年云雾。' },
  { id: 3, category: '法宝', title: '断水剑', content: '林青的佩剑，可斩断水流。' },
  { id: 4, category: '人物', title: '苏白', content: '魔宗长老，擅长幻术。' },
];

const ids = (list) => list.map((item) => item.id);

test('按标题命中', () => {
  assert.deepEqual(ids(filterBibleItems(items, { query: '林青' })), [1, 3]);
});

test('按内容命中', () => {
  assert.deepEqual(ids(filterBibleItems(items, { query: '幻术' })), [4]);
});

test('按分类命中', () => {
  assert.deepEqual(ids(filterBibleItems(items, { query: '地点' })), [2]);
});

test('大小写不敏感', () => {
  const mixed = [{ id: 9, category: 'Faction', title: 'Sky Sect', content: 'Ancient Sword Gate' }];
  assert.deepEqual(ids(filterBibleItems(mixed, { query: 'sky' })), [9]);
  assert.deepEqual(ids(filterBibleItems(mixed, { query: 'SWORD' })), [9]);
  assert.deepEqual(ids(filterBibleItems(mixed, { query: 'faction' })), [9]);
});

test('搜索 + 分类叠加', () => {
  assert.deepEqual(ids(filterBibleItems(items, { query: '剑', category: '法宝' })), [3]);
  assert.deepEqual(ids(filterBibleItems(items, { query: '剑', category: '人物' })), [1]);
});

test('空 query 不过滤关键词', () => {
  assert.deepEqual(ids(filterBibleItems(items, { query: '' })), [1, 2, 3, 4]);
  assert.deepEqual(ids(filterBibleItems(items, { query: '   ' })), [1, 2, 3, 4]);
  assert.deepEqual(ids(filterBibleItems(items, {})), [1, 2, 3, 4]);
  assert.deepEqual(ids(filterBibleItems(items)), [1, 2, 3, 4]);
  assert.deepEqual(ids(filterBibleItems(items, { query: '' , category: '  ' })), [1, 2, 3, 4]);
});

test('不存在的分类返回空数组', () => {
  assert.deepEqual(filterBibleItems(items, { category: '功法' }), []);
  assert.deepEqual(filterBibleItems(items, { query: '林青', category: '功法' }), []);
});

test('分类 trim 后完全匹配', () => {
  assert.deepEqual(ids(filterBibleItems(items, { category: ' 人物 ' })), [1, 4]);
});

test('空数组返回空数组', () => {
  assert.deepEqual(filterBibleItems([], { query: '林青' }), []);
  assert.deepEqual(collectBibleCategories([]), []);
});

test('非数组入参与脏元素不炸', () => {
  assert.deepEqual(filterBibleItems(null, { query: 'x' }), []);
  assert.deepEqual(filterBibleItems(undefined), []);
  assert.deepEqual(collectBibleCategories(null), []);
  assert.deepEqual(
    ids(filterBibleItems([...items, null, 'bad', 42], { query: '林青' })),
    [1, 3],
  );
});

test('保持原顺序且返回原对象引用', () => {
  const result = filterBibleItems(items, { query: '宗' });
  assert.deepEqual(ids(result), [1, 2, 4]);
  assert.equal(result[0], items[0]);
});

test('分类去重并按中文排序', () => {
  const list = [
    { category: '地点' },
    { category: '人物' },
    { category: '法宝' },
    { category: '人物' },
    { category: '' },
    { category: '   ' },
    { title: '无分类' },
    { category: null },
  ];
  assert.deepEqual(collectBibleCategories(list), ['地点', '法宝', '人物']);
  assert.deepEqual(collectBibleCategories(items), ['地点', '法宝', '人物']);
});
