<template>
  <section class="ws-editor-pane" data-testid="editor-pane">
    <TipTapEditor
      :model-value="content"
      :editable="editable"
      @update:model-value="handleEditorUpdate"
    />
  </section>
</template>

<script setup>
import TipTapEditor from './TipTapEditor.vue'

const props = defineProps({
  content: { type: String, required: true },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:content'])

function handleEditorUpdate(html) {
  emit('update:content', html)
}
</script>

<style scoped>
.ws-editor-pane {
  flex: 1;
  padding: 2rem 3rem;
  overflow-y: auto;
}
</style>