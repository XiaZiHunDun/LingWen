import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Phase 110 G2: composables/index.ts must export all Phase 107-109
 * composables introduced after the last index update.
 */

const NEW_COMPOSABLES = [
  'useBulkDeleteToast',
  'useBulkRegenerateToast',
  'useDeleteFromNotificationToast',
  'useNotificationStream',
];

describe('Phase 110 G2: Phase 107-109 composables registered', () => {
  const indexPath = path.resolve(__dirname, '../../../src/composables/index.ts');
  const content = fs.readFileSync(indexPath, 'utf-8');

  for (const name of NEW_COMPOSABLES) {
    it(`${name} is exported from index.ts`, () => {
      expect(content).toContain(name);
    });
  }

  it('docstring mentions Phase 107-109', () => {
    expect(content).toMatch(/Phase 107.*?10[789]/);
  });
});