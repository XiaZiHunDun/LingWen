import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Phase 110 G1: production code MUST NOT reference `$fetch` global.
 * `$fetch` is a Nuxt auto-import not provided by Vite. Phase 96-109 wrappers
 * used it but silently depended on test stubs. Phase 110 closes the gap.
 */

const productionFiles = [
  'src/api/illustrations.ts',
];

describe('Phase 110 G1: no $fetch in production code', () => {
  for (const relPath of productionFiles) {
    it(`${relPath} contains zero $fetch references`, () => {
      const fullPath = path.resolve(__dirname, '../../../', relPath);
      const content = fs.readFileSync(fullPath, 'utf-8');
      // Match $fetch as a function call (not in a string literal / comment)
      const matches = content.match(/\$fetch(?:\s*\()/g) ?? [];
      expect(matches).toEqual([]);
    });
  }
});