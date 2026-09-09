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
    <!-- base: airplane body + wings (closed filled silhouette) -->
    <path
      d="M240 128 152 96 86.51 30.51a8 8 0 0 0-11.31 0L66.34 39.4a8 8 0 0 0-1.05 10l29.59 50.06L40 110.34a8 8 0 0 0-9.66 9.66l20.83 50.84L16 240l69.16-35.17 50.84 20.83a8 8 0 0 0 9.66-9.66l-20.84-54.88 50.06-29.59a8 8 0 0 0 1.05-10L167 99.31a8 8 0 0 0-11.31 0L128 128Z"
      fill="currentColor"
    />
    <!-- accent: cockpit window highlight (closed filled dot) -->
    <path
      d="M128 128a8 8 0 0 1-8 8 8 8 0 0 1-8-8 8 8 0 0 1 8-8 8 8 0 0 1 8 8Z"
      fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))"
    />
  </svg>
</template>
