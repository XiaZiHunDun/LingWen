import { Mark } from '@tiptap/core'

export const SceneBreak = Mark.create({
  name: 'sceneBreak',
  inclusive: false,
  parseHTML() {
    return [{ tag: 'span[data-scene-break]' }]
  },
  renderHTML() {
    return ['span', { 'data-scene-break': 'true' }, 0]
  },
})
