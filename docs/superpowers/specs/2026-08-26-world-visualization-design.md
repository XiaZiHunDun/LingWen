# World Visualization v1 — Design

> **Phase**: Task F (carryover from handoff §2 Priority 3)
> **Date**: 2026-08-26
> **Status**: Design approved (brainstorm complete)
> **Next**: → writing-plans skill for implementation plan

## 0. TL;DR

Build a top-level `/world` page in the dashboard that visualizes and edits
the novel's characters, factions, lore, and timeline. Source data lives
in a SQLite store (`infra/world_db/`) with markdown round-trip
import/export. All edits (human and agent) go through a review queue
(proposal table). Vis-network renders the faction/character relationship
graph.

## 1. Goals & non-goals

**Goals**:
- Browse/edit character cards, factions, lore entries, timeline events
- Visualize faction/character relationships as a graph
- Markdown round-trip (existing `docs/character-bible/*.md` stays authoritative for export)
- Human + agent edit proposals reviewed in queue before apply
- All sub-features in v1 (no v2 split)

**Non-goals** (deferred to v2+):
- Visual graph diff for relationship changes
- Multi-user real-time collaboration
- Lore cross-reference graph view
- Timeline swimlane view
- Markdown export with embedded diff history

## 2. Architecture

```
┌─────────────────────────────────────────────────┐
│ /world (top-level page, IA section)            │
│ ┌─────────────────────────────────────────────┐ │
│ │ Tabs: 人物卡 | 势力图 | 时间线 | 世界书   │ │
│ │ (active tab content)                       │ │
│ │ [proposal inbox badge]   [import/export]  │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
        ↓                          ↓
   Vue 3 components          FastAPI routes
        ↓                          ↓
   Pinia store            SQLite (.state/world.db)
        ↓                          ↓
   vis-network (graph)    markdown import/export
```

Three layers:
1. **Routes/components**: `/world` page with 4 tabs
2. **Composable layer**: `useWorldDb`, `useWorldReview`, `useWorldAgent`
3. **Backend**: FastAPI routes mounted on `studio_api`, SQLite store

**Architecture invariants respected**:
- `infra/` owns persistence (per AGENTS.md)
- `apps/dashboard/` no direct SQLite access (via FastAPI only)
- New module `infra/world_db/` (mirrors `infra/persistence/` pattern)
- No new dependencies on rejected stack (cytoscape-fcose per Phase 114)

## 3. Data model

```sql
CREATE TABLE character (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  canon_level TEXT NOT NULL,         -- 'Established' | 'Provisional' | 'Draft'
  status TEXT,                       -- 'alive' | 'dead' | 'sleeping' | 'unknown'
  first_chapter INTEGER,
  last_seen_chapter INTEGER,
  attributes JSON,                   -- {appearance, personality, motivation, arc, ...}
  aliases JSON,                      -- for search
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE faction (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  attributes JSON,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE relationship (
  id INTEGER PRIMARY KEY,
  source_kind TEXT NOT NULL,         -- 'character' | 'faction'
  source_id INTEGER NOT NULL,
  target_kind TEXT NOT NULL,
  target_id INTEGER NOT NULL,
  kind TEXT NOT NULL,                -- 'ally' | 'enemy' | 'family' | 'mentor' | 'member_of' | 'romantic'
  strength REAL,
  chapter INTEGER,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(source_kind, source_id, target_kind, target_id, kind)
);

CREATE TABLE lore_entry (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  category TEXT NOT NULL,            -- 'magic_system' | 'geography' | 'history' | 'creature' | 'technology'
  summary TEXT NOT NULL,
  body TEXT NOT NULL,
  tags JSON,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE timeline_event (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  story_year INTEGER,                -- T-37 etc.
  story_label TEXT,
  chapter INTEGER,
  description TEXT,
  category TEXT,                     -- 'history' | 'character' | 'plot'
  related_characters JSON,
  related_factions JSON,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE proposal (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,                -- 'character.create' | 'character.update' | etc.
  target_kind TEXT,
  target_id INTEGER,
  payload JSON NOT NULL,
  source TEXT NOT NULL,              -- 'human' | 'agent'
  source_context TEXT,
  status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'accepted' | 'rejected' | 'edited'
  reviewer TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL
);
```

**Key design choices**:
- `revision` per row: optimistic concurrency (409 on conflict, mirrors creator volume-plan pattern)
- `slug` for URL-safe identifiers (composite unique with project_id for multi-project support)
- `JSON` columns for flexible nested data (appearance, personality, etc.)
- `proposal` table decoupled from main tables: human/agent changes go through review queue

## 4. Component hierarchy

```
src/
├── pages/WorldPage.vue              ← top-level IA section, /world route
├── components/world/
│   ├── WorldTabs.vue                ← 人物卡 | 势力图 | 时间线 | 世界书
│   ├── WorldProposalInbox.vue       ← badge + dropdown of pending proposals
│   ├── WorldImportExport.vue        ← markdown in/out controls
│   ├── characters/
│   │   ├── CharacterList.vue
│   │   ├── CharacterCard.vue
│   │   ├── CharacterDetail.vue
│   │   ├── CharacterEditor.vue
│   │   └── CharacterRelationships.vue
│   ├── factions/
│   │   ├── FactionList.vue
│   │   ├── FactionGraph.vue         ← vis-network
│   │   └── FactionDetail.vue
│   ├── timeline/
│   │   ├── TimelineView.vue         ← horizontal scrolling timeline
│   │   ├── TimelineEventDetail.vue
│   │   └── TimelineEditor.vue
│   └── lore/
│       ├── LoreList.vue
│       ├── LoreDetail.vue
│       └── LoreEditor.vue
├── composables/world/
│   ├── useWorldDb.js
│   ├── useWorldReview.js
│   ├── useWorldAgent.js
│   └── useWorldImportExport.js
└── stores/useWorldStore.js          ← Pinia: active tab, filters, drafts

infra/
└── world_db/
    ├── __init__.py
    ├── schema.py
    ├── queries/
    │   ├── characters.py
    │   ├── factions.py
    │   ├── relationships.py
    │   ├── lore.py
    │   ├── timeline.py
    │   └── proposals.py
    ├── markdown_roundtrip.py
    └── agent_extractors.py

apps/studio_api/routes/world.py      ← FastAPI router
```

**Routes**:
- `GET /api/world/characters`, `GET /api/world/characters/{slug}`
- `POST /api/world/proposals`, `POST /api/world/proposals/{id}/accept|reject`
- `POST /api/world/import`, `GET /api/world/export`

## 5. Markdown round-trip format

**Existing character-bible/*.md structure** (already in repo):
- `# 角色圣经 · {name}` → `character.name`
- `> Canon 等级：{level}` → `character.canon_level`
- `## 快速参考` → `character.attributes.quick_ref` (parsed list)
- `## 外貌/个性/弧光/关系/Lore 连接` → `character.attributes.{section}` (parsed)
- `## 关系` → also parsed into `relationship` table rows
- `## Lore 连接` → also parsed into `relationship` rows (character ↔ faction/lore)

**Faction / lore / timeline**:
- Faction: `# 阵营 · {name}` + `## {section}` blocks
- Lore: `# 世界观条目 · {title}` + category header
- Timeline: not currently in markdown; export as separate `timeline.md` file

**Backwards compat**:
- Re-import same project after edits: should round-trip without data loss (round-trip property test)

## 6. Review flow

```
┌──────────────────────────────────────────────────────────┐
│  Human edits in CharacterEditor                          │
│    OR                                                    │
│  Agent extracts from chapter text / manual prompt        │
│        ↓                                                 │
│  POST /api/world/proposals (kind, payload, source)       │
│        ↓                                                 │
│  proposal row inserted with status='pending'             │
│        ↓                                                 │
│  WorldProposalInbox badge shows count                    │
│        ↓                                                 │
│  Human opens inbox, sees diff preview                    │
│    - accept → apply payload to main table, revision++     │
│    - reject → mark rejected (preserve payload for audit)  │
│    - edit   → human modifies payload, then accept/reject  │
│        ↓                                                 │
│  Main table updated atomically (transaction)              │
└──────────────────────────────────────────────────────────┘
```

**Diff preview UX**:
- character.create: proposed character as markdown side-by-side with empty
- character.update: old version vs new version (reuses `creator_volume_diff` pattern)
- relationship.create: graph highlight of new edge before/after
- Accept/reject buttons in inbox; edit opens editor with pre-filled payload

**Audit trail**:
- All proposals retained in `proposal` table (even rejected) — audit/replay possible
- `reviewer` field tracks who approved/rejected
- `reviewed_at` timestamp

**Conflict handling**:
- If main table's `revision` has changed since proposal was created (409): force human to re-edit proposal against new baseline

## 7. Agent proposal flow

**Two trigger paths**:

**Path A — Auto-extract from chapter text**:
1. User opens CharacterEditor for character X
2. Clicks "从最近章节提取"
3. Frontend sends: `POST /api/world/agent/extract { character_slug, chapter_range }`
4. Backend reads chapter text → LLM call with structured prompt → validates against schema → creates proposal row
5. Frontend shows preview with original text highlighted + proposed changes + Accept/Reject/Edit

**Path B — Manual text prompt**:
1. User opens CharacterEditor for character X
2. Types freeform text in "提示" textarea → clicks "提取设定"
3. Same backend endpoint, but with prompt='manual'
4. Same LLM extraction + proposal creation

**LLM constraints**:
- Output must conform to proposal payload schema (Pydantic validation)
- LLM only proposes; never directly writes to main tables
- Confidence score in payload; inbox sorts by score desc
- Per existing `infra/llm_quality_deep_check.py` patterns

**Cost guardrails**:
- Default `chapter_range` = last 10 chapters
- Token budget cap (~4000 tokens per call)
- Rate limit: max 5 extractions per session (per handoff §5)

## 8. Testing strategy

| Layer | What | How |
|-------|------|-----|
| Unit (backend) | `infra/world_db/queries/*` CRUD + revision concurrency | pytest, isolated SQLite fixtures |
| Unit (backend) | `markdown_roundtrip.py` round-trip property test | pytest with existing `.md` as fixtures |
| Unit (backend) | `agent_extractors.py` prompt → proposal payload | pytest with stubbed LLM client |
| Unit (frontend) | composables with mocked fetch | vitest |
| Component | `CharacterEditor`, `FactionGraph`, `TimelineView` | vitest + @vue/test-utils |
| Page | `WorldPage.vue` with stubbed children | vitest (mirrors WriteWorkspacePage pattern) |
| E2E | import → edit proposal → accept → export round-trip | Playwright (Phase 114 dev baseline) |

## 9. Risks + mitigations

| Risk | Mitigation |
|------|------------|
| vis-network bundle size | Lazy-load only when /world graph tab is active; ~150kb gzipped |
| Cytoscape regression repeat (Phase 114) | vis-network is vanilla JS, no rollup commonjs conflict; verified via `pnpm build` before commit |
| Markdown round-trip data loss | Round-trip property test (parse → serialize → parse → diff assert) |
| LLM agent cost | Rate limit + token cap per session (per handoff §5 限成本) |
| SQLite schema migration | Use versioned CREATE TABLE + migration script (mirrors `infra/persistence/migrations/`) |
| Long content editor | Use existing TextEditor component for lore body; TipTap reserved for Write Workspace |
| Cross-project collision | World DB scoped per-project; slug + project_id composite uniqueness |

## 10. Acceptance criteria

- All 4 tabs render with real data (loaded from DB)
- Round-trip import/export produces equivalent markdown (round-trip test passes for all sample character-bible files)
- Agent extraction produces valid proposal payload (Pydantic schema validation)
- E2E: import existing character-bible → see in UI → edit proposal → accept → export → exported file matches input modulo formatting whitespace
- vue-tsc: 0 errors; ESLint: 0 warnings; ruff: clean; pnpm build: OK
- Tests: ≥80% coverage on new files

## 11. Open questions / known deferred items

- v2 candidate: visual graph diff for relationship changes (currently text diff only)
- v2 candidate: multi-user real-time collaboration
- v2 candidate: lore cross-reference graph view
- v2 candidate: timeline swimlane view
- v2 candidate: markdown export with embedded diff history
- v2 candidate: agent proposal diff explanation (why this change)
