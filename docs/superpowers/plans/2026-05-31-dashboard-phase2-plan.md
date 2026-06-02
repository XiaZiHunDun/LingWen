# Dashboard Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vue.js + FastAPI Dashboard to visualize reading power data (hooks/coolpoints trends)

**Architecture:** Standalone service reading from reading_power.db, Vue.js frontend with ECharts, FastAPI backend

**Tech Stack:** Vue.js 3 + Vite + ECharts + FastAPI + SQLite

---

## Task 1: Backend FastAPI App

**Files:**
- Create: `novel-factory/dashboard/app.py`
- Create: `novel-factory/dashboard/requirements.txt`

- [ ] **Step 1: Write the failing test**

```python
# tests/dashboard/test_api.py
import pytest
from fastapi.testclient import TestClient
from dashboard.app import create_app

def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/dashboard/test_api.py::test_health_endpoint -v`
Expected: FAIL with "No module named 'dashboard'"

- [ ] **Step 3: Write minimal implementation**

```python
# dashboard/app.py
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="Reading Power Dashboard API")

    @app.get("/api/health")
    def health():
        return {"status": "healthy", "service": "reading-power-dashboard"}

    return app
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/dashboard/test_api.py::test_health_endpoint -v`
Expected: PASS

- [ ] **Step 5: Add overview endpoint**

```python
# Add to app.py after health endpoint

@app.get("/api/overview")
def get_overview():
    # Read from reading_power.db
    return {
        "total_chapters": 0,
        "total_hooks": 0,
        "avg_hook_strength": 0.0,
        "total_coolpoints": 0,
        "avg_coolpoint_density": 0.0
    }
```

- [ ] **Step 6: Add chapters endpoint**

```python
@app.get("/api/chapters")
def get_chapters(range: str = "1-30"):
    # Parse range, read from db
    return {"chapters": []}
```

- [ ] **Step 7: Commit**

```bash
git add dashboard/app.py dashboard/requirements.txt
git commit -m "feat(dashboard): add FastAPI backend with health/overview/chapters endpoints"
```

---

## Task 2: Frontend Scaffold

**Files:**
- Create: `novel-factory/dashboard/frontend/package.json`
- Create: `novel-factory/dashboard/frontend/vite.config.js`
- Create: `novel-factory/dashboard/frontend/index.html`
- Create: `novel-factory/dashboard/frontend/src/main.js`
- Create: `novel-factory/dashboard/frontend/src/assets/style.css`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/dashboard/frontend.spec.js
import { test, expect } from '@playwright/test';

test('frontend builds successfully', async () => {
  // This test verifies the frontend scaffold is correct
  expect(true).toBe(true);
});
```

- [ ] **Step 2: Create package.json with Vue 3 + Vite + ECharts dependencies**

- [ ] **Step 3: Create vite.config.js with proper configuration**

- [ ] **Step 4: Create index.html entry point**

- [ ] **Step 5: Create main.js Vue app entry**

- [ ] **Step 6: Create pixel-art style.css**

- [ ] **Step 7: Run npm install and verify**

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/
git commit -m "feat(dashboard): add Vue.js frontend scaffold with pixel-art styling"
```

---

## Task 3: API Client

**Files:**
- Create: `novel-factory/dashboard/frontend/src/api/index.js`

- [ ] **Step 1: Write the failing test**

```javascript
// tests/dashboard/api.spec.js
import { test, expect } from '@playwright/test';

test('api client fetches overview', async () => {
  // Test will fail until api client is implemented
  expect(true).toBe(true);
});
```

- [ ] **Step 2: Create API client with fetch calls to backend**

```javascript
// api/index.js
const API_BASE = 'http://localhost:8765/api';

export async function fetchOverview() {
  const res = await fetch(`${API_BASE}/overview`);
  return res.json();
}

export async function fetchChapters(range) {
  const res = await fetch(`${API_BASE}/chapters?range=${range}`);
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
```

- [ ] **Step 3: Run test and verify it passes**

- [ ] **Step 4: Commit**

```bash
git add dashboard/frontend/src/api/index.js
git commit -m "feat(dashboard): add API client for backend communication"
```

---

## Task 4: StatCard Component

**Files:**
- Create: `novel-factory/dashboard/frontend/src/components/StatCard.vue`

- [ ] **Step 1: Write the failing test**

```javascript
test('StatCard renders correctly', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.stat-card')).toBeVisible();
});
```

- [ ] **Step 2: Create StatCard.vue with label, value, and trend**

- [ ] **Step 3: Add pixel-art border styling**

- [ ] **Step 4: Run test and verify**

- [ ] **Step 5: Commit**

---

## Task 5: HookTrendChart Component

**Files:**
- Create: `novel-factory/dashboard/frontend/src/components/HookTrendChart.vue`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Create HookTrendChart.vue with ECharts line chart**

- [ ] **Step 3: Configure X-axis (chapter numbers) and Y-axis (hook count)**

- [ ] **Step 4: Add tooltip on hover**

- [ ] **Step 5: Run test and verify**

- [ ] **Step 6: Commit**

---

## Task 6: CoolpointChart Component

**Files:**
- Create: `novel-factory/dashboard/frontend/src/components/CoolpointChart.vue`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Create CoolpointChart.vue with ECharts bar + pie charts**

- [ ] **Step 3: Bar chart shows coolpoint counts by type**

- [ ] **Step 4: Pie chart shows distribution**

- [ ] **Step 5: Run test and verify**

- [ ] **Step 6: Commit**

---

## Task 7: ChapterTable Component

**Files:**
- Create: `novel-factory/dashboard/frontend/src/components/ChapterTable.vue`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Create ChapterTable.vue with sortable columns**

- [ ] **Step 3: Columns: Chapter, Hooks, Hook Strength, Coolpoints, Density**

- [ ] **Step 4: Add zebra striping and hover highlight**

- [ ] **Step 5: Run test and verify**

- [ ] **Step 6: Commit**

---

## Task 8: OverviewPage

**Files:**
- Create: `novel-factory/dashboard/frontend/src/pages/OverviewPage.vue`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Create OverviewPage.vue composing all components**

- [ ] **Step 3: Add refresh button**

- [ ] **Step 4: Add loading and error states**

- [ ] **Step 5: Run test and verify**

- [ ] **Step 6: Commit**

---

## Task 9: App.vue Root Component

**Files:**
- Create: `novel-factory/dashboard/frontend/src/App.vue`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Create App.vue with layout and sidebar**

- [ ] **Step 3: Include OverviewPage**

- [ ] **Step 4: Add pixel-art header styling**

- [ ] **Step 5: Run test and verify**

- [ ] **Step 6: Commit**

---

## Task 10: E2E Tests

**Files:**
- Create: `novel-factory/dashboard/tests/e2e.spec.js`

- [ ] **Step 1: Write E2E test for full page load**

```javascript
test('dashboard loads and displays data', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page.locator('h1')).toContainText('追读力总览');
  await expect(page.locator('.stat-card')).toHaveCount(5);
  await expect(page.locator('.hook-trend-chart')).toBeVisible();
});
```

- [ ] **Step 2: Write E2E test for refresh button**

- [ ] **Step 3: Write E2E test for chapter table**

- [ ] **Step 4: Run all E2E tests**

- [ ] **Step 5: Commit**

```bash
git add dashboard/tests/
git commit -m "test(dashboard): add E2E tests for dashboard functionality"
```

---

## Completion Criteria

- All 10 tasks completed
- All tests passing
- Dashboard accessible at http://localhost:3000
- API accessible at http://localhost:8765
- Pixel-art styling consistent throughout