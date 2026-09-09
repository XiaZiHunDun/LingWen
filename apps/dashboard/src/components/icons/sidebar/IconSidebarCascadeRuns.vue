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
    <!-- base: root node + 2 child nodes + connecting lines (branching tree) -->
    <path
      d="M128 32a24 24 0 0 0-24 24 24 24 0 0 0 24 24 24 24 0 0 0 24-24 24 24 0 0 0-24-24ZM56 176a24 24 0 0 0-24 24 24 24 0 0 0 24 24 24 24 0 0 0 24-24 24 24 0 0 0-24-24ZM200 176a24 24 0 0 0-24 24 24 24 0 0 0 24 24 24 24 0 0 0 24-24 24 24 0 0 0-24-24ZM112 80v32h32V80M128 112 56 200M128 112l72 88"
      fill="currentColor"
    />
    <!-- accent: highlight on root node (filled center dot) -->
    <path
      d="M128 56a8 8 0 0 0-8 8 8 8 0 0 0 8 8 8 8 0 0 0 8-8 8 8 0 0 0-8-8Z"
      fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))"
    />
  </svg>
</template>
