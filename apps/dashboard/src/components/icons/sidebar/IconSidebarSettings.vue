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
    :aria-label="($attrs['aria-label'] as string | undefined)"
  >
    <!-- Phosphor-duotone base layer -->
    <path d="m128 24 8 24 24-8 8 24-16 16 8 24-24 8-16-16-24 8-8-24 16-16-8-24 24-8Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M128 96a32 32 0 1 0 32 32 32 32 0 0 0-32-32Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
