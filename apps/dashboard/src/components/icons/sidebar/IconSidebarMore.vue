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
    <path d="M64 56h32v32H64Zm48 0h32v32h-32Zm48 0h32v32h-32ZM64 104h32v32H64Zm48 0h32v32h-32Zm48 0h32v32h-32ZM64 152h32v32H64Zm48 0h32v32h-32Zm48 0h32v32h-32Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M88 80h128v32H88Zm0 48h128v32H88Zm0 48h128v32H88Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
