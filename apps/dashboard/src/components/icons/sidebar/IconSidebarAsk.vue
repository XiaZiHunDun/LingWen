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
    <!-- Phosphor-duotone base layer -->
    <path d="M80.59 154.51a72 72 0 1 1 89.21-89.21 72 72 0 0 1-89.21 89.21Zm-14.92 10.81-26.83 19.21a8 8 0 0 1-12.52-8.62l5.51-26.92a87.93 87.93 0 1 1 105.32 30.59Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M166.18 109.41a56 56 0 0 1-69.31 69.31 56 56 0 0 0 69.31-69.31Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
