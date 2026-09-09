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
    <path d="M224 200v16H32V40h16v160Zm-144-32V72H64v96Zm32 0V72h16v96Z" fill="currentColor" />
    <!-- Phosphor-duotone accent layer -->
    <path d="M96 88h16v80H96Zm32 0h16v80h-16Z" fill="var(--lingwen-icon-accent, oklch(70% 0.18 280))" />
  </svg>
</template>
