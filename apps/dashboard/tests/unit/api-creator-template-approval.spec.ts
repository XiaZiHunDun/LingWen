/**
 * api/templateApproval 独立测试（Phase 62.6）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorTemplateApprovals,
  submitCreatorTemplateVersionApproval,
  approveCreatorTemplateApproval,
  rejectCreatorTemplateApproval,
  fetchCreatorTemplateApprovalChainConfig,
  saveCreatorTemplateApprovalChainConfig,
  fetchCreatorTemplateApprovalHistory,
  fetchCreatorTemplateApprovalSlaConfig,
  saveCreatorTemplateApprovalSlaConfig,
  fetchCreatorTemplateApprovalOverdue,
  transferCreatorTemplateApproval,
  fetchCreatorTemplateApprovalSnapshotDiff,
  fetchCreatorTemplateApprovalSnapshotDrift,
  batchApproveCreatorTemplateApprovals,
  batchRejectCreatorTemplateApprovals,
} from '../../src/api/templateApproval.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/templateApproval', () => {
  it('fetchCreatorTemplateApprovals GETs without params', async () => {
    mocks.request.mockResolvedValueOnce({ approvals: [] });
    await fetchCreatorTemplateApprovals();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals',
    );
  });

  it('fetchCreatorTemplateApprovals serializes status and template_id params', async () => {
    mocks.request.mockResolvedValueOnce({ approvals: [] });
    await fetchCreatorTemplateApprovals({ status: 'pending', template_id: 't1' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals?status=pending&template_id=t1',
    );
  });

  it('fetchCreatorTemplateApprovals ignores unknown params', async () => {
    mocks.request.mockResolvedValueOnce({ approvals: [] });
    await fetchCreatorTemplateApprovals({ status: 'pending', foo: 'bar' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals?status=pending',
    );
  });

  it('submitCreatorTemplateVersionApproval POSTs encoded templateId', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await submitCreatorTemplateVersionApproval('t/1', { version: 1 });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/t%2F1/version-approval',
      { method: 'POST', body: { version: 1 } },
    );
  });

  it('approveCreatorTemplateApproval POSTs encoded approvalId', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await approveCreatorTemplateApproval('a/1', { comment: 'ok' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/a%2F1/approve',
      { method: 'POST', body: { comment: 'ok' } },
    );
  });

  it('approveCreatorTemplateApproval defaults body to empty object', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await approveCreatorTemplateApproval('a1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/a1/approve',
      { method: 'POST', body: {} },
    );
  });

  it('rejectCreatorTemplateApproval POSTs encoded approvalId with body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await rejectCreatorTemplateApproval('a 1', { reason: 'no' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/a%201/reject',
      { method: 'POST', body: { reason: 'no' } },
    );
  });

  it('fetchCreatorTemplateApprovalChainConfig GETs chain-config', async () => {
    mocks.request.mockResolvedValueOnce({ chain: [] });
    await fetchCreatorTemplateApprovalChainConfig();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/chain-config',
    );
  });

  it('saveCreatorTemplateApprovalChainConfig PUTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorTemplateApprovalChainConfig({ chain: ['user1'] });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/chain-config',
      { method: 'PUT', body: { chain: ['user1'] } },
    );
  });

  it('fetchCreatorTemplateApprovalHistory GETs with default limit', async () => {
    mocks.request.mockResolvedValueOnce({ history: [] });
    await fetchCreatorTemplateApprovalHistory();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/history?limit=20',
    );
  });

  it('fetchCreatorTemplateApprovalHistory GETs with custom limit', async () => {
    mocks.request.mockResolvedValueOnce({ history: [] });
    await fetchCreatorTemplateApprovalHistory(50);
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/history?limit=50',
    );
  });

  it('fetchCreatorTemplateApprovalSlaConfig GETs sla-config', async () => {
    mocks.request.mockResolvedValueOnce({ config: {} });
    await fetchCreatorTemplateApprovalSlaConfig();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/sla-config',
    );
  });

  it('saveCreatorTemplateApprovalSlaConfig PUTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorTemplateApprovalSlaConfig({ maxDays: 7 });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/sla-config',
      { method: 'PUT', body: { maxDays: 7 } },
    );
  });

  it('fetchCreatorTemplateApprovalOverdue GETs overdue', async () => {
    mocks.request.mockResolvedValueOnce({ overdue: [] });
    await fetchCreatorTemplateApprovalOverdue();
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/overdue',
    );
  });

  it('transferCreatorTemplateApproval POSTs encoded approvalId', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await transferCreatorTemplateApproval('a/1', { to: 'user2' });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/a%2F1/transfer',
      { method: 'POST', body: { to: 'user2' } },
    );
  });

  it('fetchCreatorTemplateApprovalSnapshotDiff GETs encoded approvalId', async () => {
    mocks.request.mockResolvedValueOnce({ diff: {} });
    await fetchCreatorTemplateApprovalSnapshotDiff('a/1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/a%2F1/snapshot-diff',
    );
  });

  it('fetchCreatorTemplateApprovalSnapshotDrift GETs encoded approvalId', async () => {
    mocks.request.mockResolvedValueOnce({ drift: {} });
    await fetchCreatorTemplateApprovalSnapshotDrift('a/1');
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/a%2F1/snapshot-drift',
    );
  });

  it('batchApproveCreatorTemplateApprovals POSTs body to batch-approve', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await batchApproveCreatorTemplateApprovals({ ids: ['a1', 'a2'] });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/batch-approve',
      { method: 'POST', body: { ids: ['a1', 'a2'] } },
    );
  });

  it('batchRejectCreatorTemplateApprovals POSTs body to batch-reject', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await batchRejectCreatorTemplateApprovals({ ids: ['a1'] });
    expect(mocks.request).toHaveBeenCalledWith(
      '/creator/volume-plan/templates/approvals/batch-reject',
      { method: 'POST', body: { ids: ['a1'] } },
    );
  });
});
