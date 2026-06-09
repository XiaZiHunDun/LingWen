// eslint-rules/testid-class-sync.js — Phase 8.36
// 规则: .vue 元素加 data-testid="x" 必加 class 含 "x" (kebab-case 镜像).
//       加 class="...x..." 必加 data-testid="x" 仅 when:
//         (a) element 是 interactive (button/a/@click/role=), AND
//         (b) class token 跟同 SFC 其他 testid 同名 (drift 检测).
// 形态: 镜像 Phase 8.33 no-class-selector-in-test.js pattern (本地 ESLint rule).
// 范围: VAttribute.parent = VStartTag, VStartTag.parent = VElement.
// 限定: 纯视觉 class 0 强 (例 .pixel-card 仅 styling). 同 SFC 内命名差异 token 0 强.
// 实现: Program:enter 0 0 0 document 0 0 0 0 0 0 0 0 fileTestids,
//       0 0 0 template body visitor (0 0 0 0 0 0 0 0 0 0 0 0 0) 0 0 fileClasses
//       Program:exit 0 0 0 0 0 0 0 0 0 0 0 0 0.

'use strict'

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description:
        '强制 .vue 元素加 data-testid="x" 必加 class 含 "x", 反之亦然 (drift 限定)',
    },
    schema: [],
  },
  create(context) {
    const fileTestids = new Set()
    const fileClassRefs = []  // [{node, token}]

    // Collect testids from entire SFC document (walks children of VDocumentFragment).
    function collectTestidsFromDocument() {
      const services = context.parserServices || (context.sourceCode && context.sourceCode.parserServices)
      if (!services || typeof services.getDocumentFragment !== 'function') return
      const doc = services.getDocumentFragment()
      if (!doc || !Array.isArray(doc.children)) return
      for (const root of doc.children) {
        walk(root)
      }
    }
    function walk(node) {
      if (!node) return
      if (node.type === 'VStartTag' && Array.isArray(node.attributes)) {
        for (const a of node.attributes) {
          if (
            !a.directive &&
            a.key &&
            a.key.name === 'data-testid' &&
            a.value &&
            a.value.value
          ) {
            fileTestids.add(a.value.value)
          }
        }
      }
      for (const k of Object.keys(node)) {
        if (k === 'parent') continue
        const v = node[k]
        if (Array.isArray(v)) {
          for (const c of v) if (c && typeof c === 'object' && c.type) walk(c)
        } else if (v && typeof v === 'object' && v.type) {
          walk(v)
        }
      }
    }

    // Build template body visitors. Returns scriptVisitor with Program:exit
    // that triggers the template body walk using our visitors.
    // Phase 8.43.6: ESLint 10 + flat config 走 context.sourceCode.parserServices
    // (context.parserServices 在 10 的 flat config 下 undefined, vue-eslint-parser 10
    // 跟 ESLint 10 集成要求 sourceCode 路径). 跟 line 30 fallback 一致.
    const parserServices = context.parserServices || (context.sourceCode && context.sourceCode.parserServices)
    if (!parserServices || typeof parserServices.defineTemplateBodyVisitor !== 'function') {
      return {}  // parser not vue-eslint-parser (e.g., .ts path), rule N/A
    }
    const templateScriptVisitor = parserServices.defineTemplateBodyVisitor({
      "VAttribute[directive=false][key.name='data-testid']"(node) {
        const testid = node.value && node.value.value
        if (!testid) return
        const startTag = node.parent
        const classAttr = (startTag.attributes || []).find(
          (a) => a.key && a.key.name === 'class',
        )
        if (!classAttr || !classAttr.value || !classAttr.value.value) {
          context.report({
            node,
            message: `data-testid="${testid}" 必须加 class 镜像`,
          })
          return
        }
        if (!classAttr.value.value.split(/\s+/).includes(testid)) {
          context.report({
            node,
            message: `class 必须包含 "${testid}" (kebab-case 镜像 testid)`,
          })
        }
      },
      "VAttribute[directive=false][key.name='class']"(node) {
        const cls = node.value && node.value.value
        if (!cls) return
        const startTag = node.parent
        const element = startTag && startTag.parent
        if (!element) return
        const hasTestid = (startTag.attributes || []).some(
          (a) => a.key && a.key.name === 'data-testid',
        )
        if (hasTestid) return
        const isInteractive = (startTag.attributes || []).some(
          (a) =>
            (a.directive && a.key && a.key.name && a.key.name.name === 'on') ||
            (!a.directive && a.key && a.key.name === 'role') ||
            (element.name === 'button' || element.name === 'a'),
        )
        if (!isInteractive) return
        const tokens = cls.split(/\s+/).filter(Boolean)
        for (const t of tokens) {
          if (/^[a-z][a-z0-9-]*$/.test(t) && t.length > 2) {
            fileClassRefs.push({ node, token: t })
          }
        }
      },
    })

    // Chain: Program:enter collects testids, Program:exit (from templateScriptVisitor)
    // walks template, then our Program:exit runs the drift check.
    const templateProgramExit = templateScriptVisitor['Program:exit']

    return {
      // 0 0 Program 0 0 0 0 0 0 0 0 0 0 0 0 0 — 0 0 0 0 fileTestids 0
      Program() {
        collectTestidsFromDocument()
      },
      // Wrap Program:exit to: (1) trigger template walk, (2) run drift check
      'Program:exit': function (node) {
        if (typeof templateProgramExit === 'function') {
          templateProgramExit(node)
        }
        for (const { node: clsNode, token } of fileClassRefs) {
          if (fileTestids.has(token)) {
            context.report({
              node: clsNode,
              message: `class="${token}" 必加 data-testid="${token}" (drift: 同 SFC 内已有 testid="${token}")`,
            })
          }
        }
      },
    }
  },
}
