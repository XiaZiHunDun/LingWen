import { test, expect } from '@playwright/test';
import { skipUnlessLiveLlm } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  openCompanionProject,
  restoreCreatorProject,
  selectChapter,
} from './helpers/companion-project.js';

test.describe('Agent plan LLM track (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('@live-llm companion_director_path_uses_llm_stream_when_configured', async ({ page, request }) => {
    skipUnlessLiveLlm(test);
    test.setTimeout(120_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);

    await expect(page.getByTestId('write-director-paths-panel-main')).toBeVisible({ timeout: 15_000 });

    const streamDone = page.waitForResponse(
      (resp) => resp.url().includes('/api/creator/agent/plan/stream') && resp.ok(),
      { timeout: 90_000 },
    );
    await page.getByTestId('director-path-run-faster').click();
    const streamResp = await streamDone;
    const body = await streamResp.text();

    const hasLlmChunk = /"source"\s*:\s*"llm"/.test(body);
    const hasLlmProvider = /"provider"\s*:\s*"llm"/.test(body);
    expect(hasLlmChunk || hasLlmProvider).toBe(true);

    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('write-candidate-steady').or(page.getByTestId('write-candidate-c1'))).toBeVisible({
      timeout: 15_000,
    });
  });
});
