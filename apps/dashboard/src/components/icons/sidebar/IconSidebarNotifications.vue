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
    <!-- Phosphor-duotone base layer: bell body + clapper -->
    <path
      d="M221.8 175.94c-5.55-9.56-13.8-36.61-13.8-71.94a80 80 0 0 0-160 0c0 35.34-8.26 62.38-13.81 71.94A16 16 0 0 0 48 200h40.81a40 40 0 0 0 78.38 0H208a16 16 0 0 0 13.8-24.06ZM128 216a24 24 0 0 1-22.62-16h45.24A24 24 0 0 1 128 216Z"
      fill="currentColor"
    />
    <!-- Phosphor-duotone accent layer: dome highlight -->
    <path
      d="M128 40a64 64 0 0 1 64 64c0 30.71 6.31 58.69 14.46 80H49.54C57.69 162.69 64 134.71 64 104a64 64 0 0 1 64-64Z"
      fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))"
    />
  </svg>
</template>
