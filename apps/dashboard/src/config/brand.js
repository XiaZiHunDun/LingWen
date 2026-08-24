/**
 * 墨灵 Studio · 品牌字符串真相之源
 * 用户面向字符串一律指向这里。
 *
 * - product* : 用户可见的产品品牌（墨灵 Studio）
 * - framework*: 内部框架名（灵文引擎），仅控制台 / about 页可见
 *
 * 命名空间历史说明：
 *   - 产品 = 墨灵 Studio（"墨灵"），UI 标题、侧栏副标题、对外文档均使用产品品牌。
 *   - 框架 = 灵文引擎（"灵文"），控制台 log、关于页、内部技术文档使用框架品牌。
 *   - 工程命名空间（包名 / import path / Python module）沿用历史 `lingwen`，
 *     不要改成 `moling` —— 改名会破坏外部引用与历史 commit blame。
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
  productNameZh: '墨灵 Studio',
  productNameEn: 'MoLing Studio',
  productShortZh: '墨灵',
  productShortEn: 'MoLing',
  productTagline: 'AI 驱动的小说创作助手',

  // 框架名（用户不可见，仅控制台 / about 页）
  frameworkNameZh: '灵文引擎',
  frameworkNameEn: 'LingWen Engine',
  frameworkShortZh: '灵文',
  frameworkShortEn: 'LingWen',

  // 内部工程命名空间（沿用历史，不要改成 "moling"）
  engineeringNamespace: 'lingwen',
});
