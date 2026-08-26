import { Node } from '@tiptap/core'

export const SceneBreak = Node.create({
  name: 'sceneBreak',
  group: 'block',
  atom: true,
  inline: false,
  selectable: true,
  parseHTML() {
    return [{ tag: 'div[data-scene-break]' }]
  },
  renderHTML() {
    return ['div', { 'data-scene-break': 'true' }]
  },
})
