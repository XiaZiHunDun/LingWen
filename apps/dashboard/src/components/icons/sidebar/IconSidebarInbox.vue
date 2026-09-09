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
    <path d="M224 152 168 96H88L32 152H80l16 24h64l16-24Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M224 152v56a8 8 0 0 1-8 8H40a8 8 0 0 1-8-8v-56" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
