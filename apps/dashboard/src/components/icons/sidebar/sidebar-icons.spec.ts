import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import type { Component } from 'vue'
import {
  SIDEBAR_ICONS,
  IconSidebarAsk,
  IconSidebarWrite,
  IconSidebarCreator,
  IconSidebarLibrary,
  IconSidebarMore,
  IconSidebarToday,
  IconSidebarProduce,
  IconSidebarInbox,
  IconSidebarInsight,
  IconSidebarCascadeRuns,
  IconSidebarSettings,
} from './index'

// Single source of truth: id → component tuple.
// Adding a 12th icon = 1 import + 1 tuple entry; no parallel arrays to drift.
const ICON_CASES: ReadonlyArray<readonly [string, Component]> = [
  ['ask', IconSidebarAsk],
  ['write', IconSidebarWrite],
  ['creator', IconSidebarCreator],
  ['library', IconSidebarLibrary],
  ['more', IconSidebarMore],
  ['today', IconSidebarToday],
  ['produce', IconSidebarProduce],
  ['inbox', IconSidebarInbox],
  ['insight', IconSidebarInsight],
  ['cascade-runs', IconSidebarCascadeRuns],
  ['settings', IconSidebarSettings],
] as const

const EXPECTED_IDS = ICON_CASES.map(([id]) => id)

describe('sidebar icons: SIDEBAR_ICONS registry', () => {
  it('exports a dict with all 11 expected ids', () => {
    for (const id of EXPECTED_IDS) {
      expect(SIDEBAR_ICONS).toHaveProperty(id)
    }
  })

  it('keys match the recognized module ids exactly (no extras)', () => {
    expect(Object.keys(SIDEBAR_ICONS).sort()).toEqual([...EXPECTED_IDS].sort())
  })
})

describe('sidebar icons: per-SFC rendering', () => {
  for (const [id, Component] of ICON_CASES) {
    it(`${id} renders svg with base+accent dual-path Phosphor-duotone structure`, () => {
      const wrapper = mount(Component)
      try {
        const svg = wrapper.find('svg')
        expect(svg.exists()).toBe(true)
        expect(svg.attributes('viewBox')).toBe('0 0 256 256')

        const paths = wrapper.findAll('path')
        expect(paths).toHaveLength(2)

        // base path (first child) uses currentColor
        expect(paths[0].attributes('fill')).toBe('currentColor')

        // accent path (second child) uses themed CSS var
        // (Insight is the lone exception: stroked trending arrow, so check stroke too)
        const accentFill = paths[1].attributes('fill') ?? ''
        const accentStroke = paths[1].attributes('stroke') ?? ''
        const usesAccent = accentFill.includes('--lingwen-icon-accent') || accentStroke.includes('--lingwen-icon-accent')
        expect(usesAccent).toBe(true)
      } finally {
        wrapper.unmount()
      }
    })
  }
})
