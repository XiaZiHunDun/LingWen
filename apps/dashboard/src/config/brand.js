/**
 * 灵文工作室 · 品牌字符串真相之源
 * 用户面向字符串一律指向这里。
 *
 * - product* : 用户可见的产品品牌（灵文工作室）
 * - framework*: 内部框架名（灵文引擎），仅控制台 / about 页可见
 *
 * 命名空间历史说明：
 *   - 产品 = 灵文工作室（"灵文"），UI 标题、侧栏副标题、对外文档均使用产品品牌。
 *   - 框架 = 灵文引擎（"灵文"），控制台 log、关于页、内部技术文档使用框架品牌。
 *   - 工程命名空间（包名 / import path / Python module）沿用历史 `lingwen`，
 *     不要改成 `moling` —— 改名会破坏外部引用与历史 commit blame。
 *   - 2026-09-10 v40.0 闭环：productNameZh '墨灵 Studio' → '灵文工作室'，同步所有用户可见
 *     字符串消费方（App.vue / NoProjectOnboarding / TodayPage / e2e smoke）。
 *   - 2026-09-10 Phase 41+ mini：asset 文件名 `moling-logo.jpg` → `lingwen-logo.jpg`
 *     （`apps/dashboard/public/assets/brand/`），2 个 runtime 引用迁移完毕。
 *     `concepts/moling-ui-concept.jpg` 为美术资产（非品牌字串），留 known legacy。
 *
 * @typedef {{
 *   productNameZh: string,
 *   productNameEn: string,
 *   productShortZh: string,
 *   productShortEn: string,
 *   productTagline: string,
 *   frameworkNameZh: string,
 *   frameworkNameEn: string,
 *   frameworkShortZh: string,
 *   frameworkShortEn: string,
 *   engineeringNamespace: string,
 * }} Brand
 */

/** @type {Readonly<Brand>} */
export const BRAND = Object.freeze({
  // 产品名（用户可见）
  productNameZh: '灵文工作室',
  productNameEn: 'LingWen Studio',
  productShortZh: '灵文',
  productShortEn: 'LingWen',
  productTagline: 'AI 驱动的小说创作助手',

  // 框架名（用户不可见，仅控制台 / about 页）
  frameworkNameZh: '灵文引擎',
  frameworkNameEn: 'LingWen Engine',
  frameworkShortZh: '灵文',
  frameworkShortEn: 'LingWen',

  // 内部工程命名空间（沿用历史，不要改成 "moling"）
  engineeringNamespace: 'lingwen',
});
