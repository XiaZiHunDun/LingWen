/** 设定集筛选纯函数的类型声明（实现见 bible-filter.js）。 */

export interface BibleFilterItem {
  title?: string | null;
  content?: string | null;
  category?: string | null;
}

export interface BibleFilterOptions {
  query?: string | null;
  category?: string | null;
}

export declare function filterBibleItems<T extends BibleFilterItem>(
  items: readonly T[] | null | undefined,
  options?: BibleFilterOptions,
): T[];

export declare function collectBibleCategories(
  items: readonly BibleFilterItem[] | null | undefined,
): string[];
