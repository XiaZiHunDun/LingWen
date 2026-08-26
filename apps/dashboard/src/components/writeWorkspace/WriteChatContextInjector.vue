<template>
  <div class="ws-context-injector" data-testid="context-injector">
    <div class="ws-context-injector__chip">
      章节: <strong>{{ context.current_chapter_heading }}</strong>
    </div>
    <div class="ws-context-injector__chip">
      场景: <strong>{{ context.current_scene }}</strong>
    </div>
    <div v-if="context.characters_in_scene?.length" class="ws-context-injector__chip">
      人物: <strong>{{ context.characters_in_scene.join('、') }}</strong>
    </div>
    <div v-if="context.prev_chapter_tail" class="ws-context-injector__chip">
      上章末: <em>{{ context.prev_chapter_tail }}</em>
    </div>
  </div>
</template>

<script setup>
defineProps({
  context: { type: Object, required: true },
})
</script>

<style scoped>
.ws-context-injector {
  background: var(--n-fill-color-hover);
  border-radius: 6px;
  padding: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}
.ws-context-injector__chip {
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--n-border-color);
}
.ws-context-injector__chip:last-child { border-bottom: none; }
</style>