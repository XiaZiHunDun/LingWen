import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { mockDelayedAgentPlanStream } from './helpers/mock-agent-stream.js';
import {
  COMPANION_SLUG,
  clearBodySelection,
  getBodyDraft,
  openCompanionProject,
  restoreCreatorProject,
  selectBodyRange,
  selectChapter,
  setBodyDraft,
} from './helpers/companion-project.js';

const BODY = '开头段落。\n\n中间待改。\n\n结尾。';
const SELECTED = '中间待改';
const REPLACED = '中间已润色';
const REPLACED_C2 = '中间更大胆';
const EXPECTED = '开头段落。\n\n中间已润色。\n\n结尾。';
const EXPECTED_C2 = '开头段落。\n\n中间更大胆。\n\n结尾。';
const INSERTED = 'E2E插入的新段落。';
const INSERT_EXPECTED = `${EXPECTED}\n\n${INSERTED}`;

function mockAgentPlanStream(page, { selectionText = REPLACED, chapterText = INSERTED } = {}) {
  return page.route('**/api/creator/agent/plan/stream', async (route) => {
    const payload = route.request().postDataJSON?.() ?? {};
    const isSelection = payload.scope?.type === 'selection';
    const text = isSelection ? selectionText : chapterText;
    const sse = [
      'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + text + '"}],"provider":"mock","annotations":[],"scope":{"type":"' + (isSelection ? 'selection' : 'chapter') + '","chapter":1}}}\n\n',
    ].join('');
    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: sse,
    });
  });
}

test.describe('Companion selection agent (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('companion_selection_rewrite_and_insert', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await mockAgentPlanStream(page);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await expect(page.getByTestId('write-scope-bar')).toContainText('选中', { timeout: 10_000 });
    await page.getByTestId('write-agent-input').fill('润色选中段落');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(EXPECTED);

    await clearBodySelection(page);

    await page.getByTestId('write-agent-input').fill('在章末插入一段');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(INSERT_EXPECTED);
  });

  test('companion_selection_preset_confirm_undo', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    let capturedPayload = null;
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      capturedPayload = route.request().postDataJSON?.() ?? {};
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"稳健","text":"' + REPLACED + '"},{"id":"c2","label":"大胆","text":"中间更大胆"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await expect(page.getByTestId('write-scope-bar')).toContainText('选中', { timeout: 10_000 });
    await expect(page.getByTestId('write-selection-tools')).toBeVisible({ timeout: 10_000 });
    await page.getByTestId('rewrite-preset-concrete').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    expect(capturedPayload?.action).toBe('rewrite:concrete');
    expect(capturedPayload?.scope?.type).toBe('selection');

    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(EXPECTED);

    await expect(page.getByTestId('write-undo-bar-main')).toBeVisible({ timeout: 10_000 });
    await page.locator('[data-testid^="checkpoint-diff-"]').first().click();
    await expect(page.getByTestId('write-checkpoint-diff')).toBeVisible({ timeout: 10_000 });
    await page.getByTestId('write-undo-last-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(BODY);
  });

  test('companion_selection_preset_blocked_when_locked', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    let streamCalls = 0;
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      streamCalls += 1;
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: 'data: {"type":"done","plan":{"advice_only":false,"candidates":[],"provider":"mock"}}\n\n',
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('selection-lock-toggle').click();
    await expect(page.getByTestId('rewrite-preset-concrete')).toBeDisabled();
    await expect(page.getByTestId('write-agent-status-main')).toContainText('锁定', { timeout: 10_000 });
    expect(streamCalls).toBe(0);
  });

  test('companion_selection_director_path_confirm_apply', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    const PATH_REPLACED = '加快节奏后的段落';
    const PATH_EXPECTED = `开头段落。\n\n${PATH_REPLACED}。\n\n结尾。`;
    let capturedPayload = null;

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      capturedPayload = route.request().postDataJSON?.() ?? {};
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + PATH_REPLACED + '"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await expect(page.getByTestId('write-scope-bar')).toContainText('选中', { timeout: 10_000 });
    await page.getByTestId('director-path-run-faster').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    expect(capturedPayload?.action).toBe('path:faster');
    expect(capturedPayload?.scope?.type).toBe('selection');

    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(PATH_EXPECTED);
  });

  test('companion_selection_preset_pick_c2_confirms_body', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"稳健","text":"' + REPLACED + '"},{"id":"c2","label":"大胆","text":"' + REPLACED_C2 + '"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('rewrite-preset-dramatic').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c2').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(EXPECTED_C2);
  });

  test('companion_style_strength_main_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await expect(page.getByTestId('write-style-bar-main')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('style-strength-slider')).toBeVisible();
    await expect(page.getByTestId('style-strength-label')).toBeVisible();
  });

  test('companion_goal_tags_main_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await expect(page.getByTestId('write-goal-tags-main')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('goal-tag-suspense')).toBeVisible();
  });

  test('companion_goal_suspense_rewrites_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const fasterCard = page.getByTestId('director-path-faster');
    await expect(fasterCard).toBeVisible({ timeout: 10_000 });
    await expect(fasterCard).toContainText('信息披露前移');

    await page.getByTestId('goal-tag-suspense').click();
    await expect(fasterCard).toContainText('悬疑感可能减弱', { timeout: 10_000 });
  });

  test('companion_goal_restraint_rewrites_conflict_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const conflictCard = page.getByTestId('director-path-conflict');
    await expect(conflictCard).toBeVisible({ timeout: 10_000 });
    await expect(conflictCard).toContainText('对立加深');

    await page.getByTestId('goal-tag-restraint').click();
    await expect(conflictCard).toContainText('与「克制」目标冲突', { timeout: 10_000 });
  });

  test('companion_agent_annotations_main_after_editor_lens_plan', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + REPLACED + '"}],"provider":"mock","annotations":[{"id":"e1","level":"warn","text":"铺垫略长，进入「更具体」前可删 1 句","paragraph":1}],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('agent-lens-editor').click();
    await page.getByTestId('rewrite-preset-concrete').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('write-agent-annotations-main')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('agent-annotation-e1')).toContainText('铺垫略长');
  });

  test('companion_agent_lens_main_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await expect(page.getByTestId('write-agent-lens-main')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('agent-lens-author')).toBeVisible();
    await expect(page.getByTestId('agent-lens-editor')).toBeVisible();
  });

  test('companion_agent_lens_main_sends_lens_in_plan', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    const planLenses = [];
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const body = route.request().postDataJSON?.() ?? {};
      planLenses.push(body.lens);
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + REPLACED + '"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('agent-lens-editor').click();
    await page.getByTestId('rewrite-preset-concrete').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    expect(planLenses.length).toBeGreaterThan(0);
    expect(planLenses.at(-1)).toBe('editor');
  });

  test('companion_worldbuilding_toggle_main_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await expect(page.getByTestId('write-worldbuilding-toggle-main')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('allow-worldbuilding-toggle')).toBeVisible();
  });

  test('companion_worldbuilding_main_sends_fill_in_plan', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    const fillFlags = [];
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const body = route.request().postDataJSON?.() ?? {};
      fillFlags.push(body.allow_worldbuilding_fill);
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + REPLACED + '"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('allow-worldbuilding-toggle').click();
    await page.getByTestId('rewrite-preset-concrete').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    expect(fillFlags.length).toBeGreaterThan(0);
    expect(fillFlags.at(-1)).toBe(true);
  });

  test('companion_goal_pace_rewrites_restrained_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const restrainedCard = page.getByTestId('director-path-restrained');
    await expect(restrainedCard).toBeVisible({ timeout: 10_000 });
    await expect(restrainedCard).toContainText('情绪降温');

    await page.getByTestId('goal-tag-pace').click();
    await expect(restrainedCard).toContainText('节奏目标下留白增多', { timeout: 10_000 });
  });

  test('companion_goal_conflict_rewrites_faster_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const fasterCard = page.getByTestId('director-path-faster');
    await expect(fasterCard).toBeVisible({ timeout: 10_000 });
    await expect(fasterCard).toContainText('信息披露前移');

    await page.getByTestId('goal-tag-conflict').click();
    await expect(fasterCard).toContainText('冲突目标下加快披露', { timeout: 10_000 });
  });

  test('companion_agent_stream_preview_main_visible_during_sse', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await mockDelayedAgentPlanStream(page, { chunkText: '主区流式预览', chunkDelayMs: 1500 });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const preview = page.getByTestId('write-agent-stream-preview-main');
    await Promise.all([
      expect(preview).toBeVisible({ timeout: 15_000 }),
      page.getByTestId('rewrite-preset-concrete').click(),
    ]);
    await expect(preview).toContainText(/主区流式预览|候选预览/);
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
  });

  test('companion_agent_prompt_main_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await expect(page.getByTestId('write-agent-prompt-main')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('write-agent-input')).toBeVisible();
    await expect(page.getByTestId('write-agent-send-btn')).toBeVisible();
  });

  test('companion_agent_prompt_main_submits_plan', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    const planBodies = [];
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const body = route.request().postDataJSON?.() ?? {};
      planBodies.push(body);
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + REPLACED + '"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('write-agent-input').fill('主区补充指令');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    expect(planBodies.length).toBeGreaterThan(0);
    expect(planBodies.at(-1)?.action).toBe('prompt');
    expect(planBodies.at(-1)?.action_label).toBe('主区补充指令');
  });

  test('companion_goal_conflict_rewrites_restrained_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const restrainedCard = page.getByTestId('director-path-restrained');
    await expect(restrainedCard).toBeVisible({ timeout: 10_000 });
    await expect(restrainedCard).toContainText('情绪降温');

    await page.getByTestId('goal-tag-conflict').click();
    await expect(restrainedCard).toContainText('冲突目标下情绪降温', { timeout: 10_000 });
  });

  test('companion_generate_toolbar_main_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await expect(page.getByTestId('write-generate-toolbar-main')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('write-generate-btn')).toBeVisible();
    await expect(page.getByTestId('write-stop-btn')).toBeVisible();
    await expect(page.getByTestId('write-agent-mode-toggle')).toBeVisible();
  });

  test('companion_goal_suspense_rewrites_restrained_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const restrainedCard = page.getByTestId('director-path-restrained');
    await expect(restrainedCard).toBeVisible({ timeout: 10_000 });
    await expect(restrainedCard).toContainText('情绪降温');

    await page.getByTestId('goal-tag-suspense').click();
    await expect(restrainedCard).toContainText('悬疑目标下留白增加', { timeout: 10_000 });
  });

  test('companion_candidate_dock_main_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"稳健","text":"' + REPLACED + '"},{"id":"c2","label":"大胆","text":"' + REPLACED_C2 + '"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);
    await page.getByTestId('rewrite-preset-concrete').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    const dock = page.getByTestId('write-candidate-dock-main');
    await expect(dock).toBeVisible({ timeout: 10_000 });
    await expect(dock).toContainText('候选预览（2）');
    await expect(page.getByTestId('write-candidate-c1')).toBeVisible();
    await expect(page.getByTestId('write-candidate-c2')).toBeVisible();
  });

  test('companion_goal_suspense_rewrites_conflict_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const conflictCard = page.getByTestId('director-path-conflict');
    await expect(conflictCard).toBeVisible({ timeout: 10_000 });
    await expect(conflictCard).toContainText('对立加深');

    await page.getByTestId('goal-tag-suspense').click();
    await expect(conflictCard).toContainText('悬疑目标下冲突升级', { timeout: 10_000 });
  });

  test('companion_goal_pace_rewrites_faster_director_path_copy', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    const fasterCard = page.getByTestId('director-path-faster');
    await expect(fasterCard).toBeVisible({ timeout: 10_000 });
    await expect(fasterCard).toContainText('信息披露前移');

    await page.getByTestId('goal-tag-pace').click();
    await expect(fasterCard).toContainText('节奏目标下推进加速', { timeout: 10_000 });
  });

  test('companion_selection_director_path_blocked_when_locked', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    let streamCalls = 0;
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      streamCalls += 1;
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: 'data: {"type":"done","plan":{"advice_only":false,"candidates":[],"provider":"mock"}}\n\n',
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('selection-lock-toggle').click();
    await page.getByTestId('director-path-run-faster').click();

    await expect(page.getByTestId('write-director-plan-card')).toBeHidden();
    await expect(page.getByTestId('write-agent-status-main')).toContainText('锁定', { timeout: 10_000 });
    expect(streamCalls).toBe(0);
  });
});
