"""Phase 109 regression guards — frontend-static source scans.

Mirrors Phase 107 `test_phase107_bulk_delete.py` pattern. Verifies the
Phase 109 orthogonal UX wiring is intact without coupling to backend test
infrastructure (backend is untouched — Phase 106 contract preserved).

Guards:
  G1 — `NotificationListItem.vue` imports NPopconfirm from naive-ui
  G2 — `useNotificationStore.js` exports `deleteAssetFromNotification`
  G3 — `NotificationListItem.vue` source contains the 4-condition `canDelete`
  G4 — `_deleted` field mention exists in `useNotificationStore.js`
  G5 — `useDeleteFromNotificationToast.ts` exports default factory
  G6 — backend `routes/illustrations.py` `delete_asset` route signature
        unchanged from Phase 106 contract (regression: Phase 106 deleted_asset
        still routes through `_delete_asset_inner(mode="single")`)
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_g1_notification_list_item_imports_npopconfirm():
    """G1: NPopconfirm wrapper present in NotificationListItem.vue."""
    text = _read("apps/dashboard/src/components/notifications/NotificationListItem.vue")
    assert "NPopconfirm" in text
    assert "from 'naive-ui'" in text


def test_g2_store_exports_delete_asset_from_notification():
    """G2: useNotificationStore exposes the action."""
    text = _read("apps/dashboard/src/stores/useNotificationStore.js")
    assert "deleteAssetFromNotification" in text
    # Must be in the returned object too (exported from store)
    assert "deleteAssetFromNotification," in text


def test_g3_can_delete_predicate_contains_four_conditions():
    """G3: canDelete computed has the eligibility guard."""
    text = _read("apps/dashboard/src/components/notifications/NotificationListItem.vue")
    # The 4 conditions: _deleted check, eventType check, assetId check, projectSlug check
    assert "item._deleted" in text
    assert "props.item.eventType !== 'generation' && props.item.eventType !== 'regeneration'" in text
    assert "props.item.assetId" in text
    assert "props.item.projectSlug" in text


def test_g4_deleted_field_in_store_source():
    """G4: _deleted field mutation exists in store action."""
    text = _read("apps/dashboard/src/stores/useNotificationStore.js")
    assert "_deleted" in text
    assert "_deleted: true" in text


def test_g5_toast_composable_exists_and_exports():
    """G5: useDeleteFromNotificationToast composable exists + exports."""
    path = REPO_ROOT / "apps/dashboard/src/composables/useDeleteFromNotificationToast.ts"
    assert path.exists(), f"missing composable: {path}"
    text = path.read_text(encoding="utf-8")
    assert "export function useDeleteFromNotificationToast" in text
    assert "showResult" in text


def test_g6_phase106_delete_asset_route_signature_unchanged():
    """G6: Phase 106 delete_asset contract preserved (regression guard).

    The Phase 109 frontend routes through the Phase 106 endpoint. If anyone
    refactors `delete_asset` and changes its signature, this guard catches it.
    """
    text = _read("apps/studio_api/routes/illustrations.py")
    # Route declaration must still be @app.delete on /api/illustrations/{asset_id}
    assert '@app.delete("/api/illustrations/{asset_id}")' in text
    # Helper delegation must still use mode="single"
    assert 'mode="single"' in text
    # The 5-path state machine in _delete_asset_inner must still call record_failure
    assert "notifications.record_failure" in text
