<script setup lang="ts">
defineProps<{ size?: number | string }>()
</script>

<template>
  <svg
    :width="size ?? '1em'"
    :height="size ?? '1em'"
    viewBox="0 0 256 256"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    :aria-label="$attrs['aria-label']"
  >
    <!-- base: pen nib outline (closed shape, no dead subpaths) -->
    <path
      d="M216 32 96 152v56h56L216 144Zm-96 176h-32v-32"
      fill="currentColor"
    />
    <!-- accent: nib slit + ink drop detail -->
    <path
      d="M168 56l32 32-72 72h-32v-32ZM128 144l16 16M120 168l-8 8 16 16 8-8Z"
      fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))"
    />
  </svg>
</template>
