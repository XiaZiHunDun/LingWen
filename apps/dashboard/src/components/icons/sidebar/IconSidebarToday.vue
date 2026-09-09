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
    <path d="M240 152H32V56a8 8 0 0 1 8-8h176a8 8 0 0 1 8 8v96Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M16 168v32a8 8 0 0 0 8 8h32Zm208 0v40h32a8 8 0 0 0 8-8v-32Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
