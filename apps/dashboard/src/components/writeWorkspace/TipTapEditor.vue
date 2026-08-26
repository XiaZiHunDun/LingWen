<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import { SceneBreak } from './sceneBreakMark.js'
import { onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [StarterKit, SceneBreak],
  editable: props.editable,
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

defineExpose({
  handleUpdate(html) { emit('update:modelValue', html) },
  insertSceneBreak() {
    editor.value?.chain().focus().insertContent({ type: 'sceneBreak' }).run()
  },
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<template>
  <div class="tiptap-editor" data-testid="tiptap-editor">
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.tiptap-editor :deep(.ProseMirror) {
  outline: none;
  min-height: 60vh;
  font-family: 'Noto Serif SC', 'PingFang SC', serif;
  font-size: 18px;
  line-height: 1.8;
}
.tiptap-editor :deep([data-scene-break]) {
  display: block;
  text-align: center;
  color: #888;
  margin: 1em 0;
}
.tiptap-editor :deep([data-scene-break])::before {
  content: '* * *';
}
</style>
