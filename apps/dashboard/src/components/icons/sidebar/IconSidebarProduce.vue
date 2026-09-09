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
    <path d="M160 32 96 144h48l-32 80 96-128h-48Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="m152 56-48 88h36l-32 56 88-104h-44Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
