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
    <path d="M40 200V40h16v160Zm32 0V72h16v128Zm32 0v-96h16v96Zm32 0v-72h16v72Zm32 0V88h16v112Zm32 0v-72h16v72Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M48 56h160v128H48Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" opacity="0.3" />
  </svg>
</template>
