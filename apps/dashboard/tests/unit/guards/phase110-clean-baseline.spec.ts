import { describe, it, expect } from 'vitest';
import { execSync } from 'node:child_process';
import * as path from 'node:path';

/**
 * Phase 110 G3 / G4 / G5 — final baseline guards.
 *
 * G3: `pnpm tsc --noEmit` exits 0 (zero tsc errors)
 * G4: `pnpm vitest run` reports zero failed tests
 * G5: 6 previously-erroring spec files remain tsc-clean (defense in depth)
 *
 * These are "outer guard" tests — they invoke external CLIs and verify
 * exit codes / output. If they ever start failing, the baseline has slipped.
 */

const repoRoot = path.resolve(__dirname, '../../../');

describe('Phase 110 G3: tsc baseline clean', () => {
  it('pnpm tsc --noEmit exits 0 with zero errors', { timeout: 180_000 }, () => {
    let stderr = '';
    try {
      execSync('pnpm tsc --noEmit', { cwd: repoRoot, stdio: 'pipe' });
    } catch (e) {
      stderr = (e as { stderr?: { toString(): string } }).stderr?.toString() ?? '';
      throw new Error(`tsc reported errors:\n${stderr}`);
    }
    expect(true).toBe(true);
  });
}, 180_000);

describe('Phase 110 G4: vitest baseline clean', () => {
  it('pnpm vitest run reports 0 failed', { timeout: 240_000 }, () => {
    let stdout = '';
    try {
      stdout = execSync('pnpm vitest run --reporter=basic', {
        cwd: repoRoot,
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });
    } catch (e) {
      // vitest exits non-zero on failures; capture stdout
      stdout = (e as { stdout?: string }).stdout ?? '';
    }
    // The summary line looks like:
    //   Tests  2172 passed | 1 skipped (2173)
    // Match either the absence of "X failed" or "0 failed".
    const failedMatch = stdout.match(/Tests\s+(\d+)\s+failed/);
    const failedCount = failedMatch ? Number(failedMatch[1]) : 0;
    expect(failedCount).toBe(0);
  });
}, 240_000);

const SPEC_FILES_WITH_TSC_ERRORS = [
  'tests/unit/components/creator/CreatorDeviationFinalize.spec.ts',
  'tests/unit/components/creator/CreatorBatchRhythm.spec.ts',
  'tests/unit/components/world/factions/FactionGraphCanvas.spec.ts',
  'tests/unit/components/world/factions/FactionGraph.spec.ts',
  'tests/unit/components/world/characters/CharacterRelationships.spec.ts',
  'tests/unit/components/world/WorldTabs.spec.ts',
];

describe('Phase 110 G5: fixed spec files remain tsc-clean', () => {
  it('tsc reports 0 errors mentioning these 6 paths', { timeout: 180_000 }, () => {
    let stdout = '';
    try {
      stdout = execSync('pnpm tsc --noEmit', { cwd: repoRoot, encoding: 'utf-8' });
      expect(true).toBe(true);
    } catch (e) {
      stdout = (e as { stdout?: string }).stdout ?? '';
    }
    for (const specFile of SPEC_FILES_WITH_TSC_ERRORS) {
      expect(stdout).not.toContain(specFile);
    }
  });
}, 180_000);