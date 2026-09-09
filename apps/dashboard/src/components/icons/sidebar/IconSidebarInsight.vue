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
    <!-- base: vertical bars at increasing heights (chart frame) -->
    <path
      d="M40 200V40h16v160Zm32 0V72h16v128Zm32 0v-96h16v96Zm32 0v-72h16v72Zm32 0V88h16v112Zm32 0v-72h16v72Z"
      fill="currentColor"
    />
    <!-- accent: trending arrow line on top of bars (highlight detail) -->
    <path
      d="M48 168l48-48 32 16 48-56 32 24"
      stroke="var(--lingwen-icon-accent, oklch(70% 0.18 280))"
      stroke-width="12"
      stroke-linecap="round"
      stroke-linejoin="round"
      fill="none"
    />
  </svg>
</template>
