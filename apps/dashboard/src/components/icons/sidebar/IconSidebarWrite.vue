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
    <path d="M224 200v16a8 8 0 0 1-8 8H40a8 8 0 0 1-8-8V40a8 8 0 0 1 8-8h96v16H48v160h160v-40h16Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M224 32 160 96l24 24 64-64Zm-80 72-12 36 36-12Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
