import { ref } from 'vue'

export function useTypewriterMode() {
  const enabled = ref(false)

  function toggle() { enabled.value = !enabled.value }

  function computeOffset(scrollTarget, viewportHeight = window.innerHeight) {
    if (!enabled.value) return 0
    return Math.max(0, scrollTarget - viewportHeight / 3)
  }

  return { enabled, toggle, computeOffset }
}
