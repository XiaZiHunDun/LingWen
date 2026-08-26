<template>
  <div class="write-workspace-page" data-testid="write-workspace-page">
    <h1>Write Workspace (placeholder)</h1>
    <p>Chapter ID: {{ chapterId }}</p>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const chapterId = computed(() => Number(route.params.chapterId))
</script>
