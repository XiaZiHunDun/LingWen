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
    <path d="M211.31 92.69 163.31 44.69l-104 104v48h48ZM136 70l50 50" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="m186 60 10 10-22 22-10-10ZM64 192l80-80 32 32-80 80Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
