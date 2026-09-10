// tests/unit/sidebar-nav-micro-interaction.spec.ts — Phase 41++
//
// Static regression guard for the 6 micro-interaction polish items added to
// .nav-item / .nav-icon in App.vue. Reads the source file directly and asserts
// each marker is present at least once. This is faster + more deterministic
// than mounting App.vue (which would require Pinia + vue-router + store wiring)
// and survives CSS refactors that keep the same semantics.
//
// Phase 41++ lesson: when behavior is "CSS class lives in this file", assert
// the source — don't try to mount the whole App.

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
// __dirname = apps/dashboard/tests/unit → up 3 to apps/dashboard, then src/App.vue
const APP_VUE_PATH = resolve(__dirname, '..', '..', 'src', 'App.vue')

function readAppVue(): string {
  return readFileSync(APP_VUE_PATH, 'utf-8')
}

describe('sidebar nav micro-interaction polish (Phase 41++)', () => {
  const src = readAppVue()

  it('App.vue source is readable (sanity)', () => {
    expect(src.length).toBeGreaterThan(1000)
  })

  it('(1) .nav-item uses explicit transition-property, not `transition: all`', () => {
    // Scope to the .nav-item rule (do not let comments inside the rule block
    // match the negative assertion — strip /* ... */ blocks first).
    const stripComments = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, '')
    const navItemRule = src.match(/\.nav-item\s*\{[\s\S]*?\n\}/)
    expect(navItemRule).not.toBeNull()
    const cleaned = stripComments(navItemRule![0])
    expect(cleaned).toMatch(/transition-property:\s*background-color,\s*color,\s*transform,\s*box-shadow/)
    // Confirm `transition: all` is NOT a real declaration in the .nav-item rule.
    expect(cleaned).not.toMatch(/transition:\s*all/)
  })

  it('(2) .nav-item:hover .nav-icon has scale(1.08) lift', () => {
    expect(src).toMatch(/\.nav-item:hover\s+\.nav-icon\s*\{[\s\S]*?transform:\s*scale\(1\.08\)/)
  })

  it('(3) .nav-item:active has press feedback (translateX + scale)', () => {
    const activeRule = src.match(/\.nav-item:active\s*\{[\s\S]*?\n\}/)
    expect(activeRule).not.toBeNull()
    expect(activeRule![0]).toMatch(/transform:\s*translateX\(2px\)\s*scale\(0\.98\)/)
  })

  it('(4) .nav-item:focus-visible declares a keyboard focus ring', () => {
    expect(src).toMatch(/\.nav-item:focus-visible\s*\{[\s\S]*?outline:\s*2px solid var\(--color-accent\)/)
    // Companion reset so :focus (mouse click) does not leak an outline.
    expect(src).toMatch(/\.nav-item:focus\s*\{[\s\S]*?outline:\s*none/)
  })

  it('(5) svg.nav-icon path has a fill transition (duotone accent smoothing)', () => {
    expect(src).toMatch(/svg\.nav-icon\s+path\s*\{[\s\S]*?transition:\s*fill\s+var\(--transition-normal\)/)
  })

  it('(6) @media (prefers-reduced-motion: reduce) strips nav transitions/transforms', () => {
    const reducedBlock = src.match(
      /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[\s\S]*?nav-item[\s\S]*?nav-icon[\s\S]*?\}\s*\}/
    )
    expect(reducedBlock).not.toBeNull()
    // Strip transitions
    expect(reducedBlock![0]).toMatch(/transition:\s*none/)
    // Strip transforms
    expect(reducedBlock![0]).toMatch(/transform:\s*none/)
  })
})
