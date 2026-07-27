import { computed, unref } from 'vue';
import { useStudioProject } from './useStudioProject.js';
import { resolveEffectiveCreationMode } from '../utils/effectiveCreationMode.js';

/**
 * @param {import('vue').MaybeRefOrGetter<string | null | undefined>} rawModeSource
 * @param {import('vue').MaybeRefOrGetter<{ slug?: string, name?: string } | null | undefined>} [projectSource]
 */
export function useEffectiveCreationMode(rawModeSource, projectSource) {
  const studio = useStudioProject();

  const activeProject = computed(() => {
    const injected = unref(projectSource);
    if (injected) return injected;

    const slug = studio.activeSlug;
    const projects = studio.projects ?? [];
    const fromList = projects.find((p) => p.slug === slug);
    if (fromList) return fromList;
    if (slug) {
      return { slug, name: studio.summary?.name };
    }
    return null;
  });

  return computed(() => resolveEffectiveCreationMode(
    unref(rawModeSource),
    activeProject.value,
  ));
}
