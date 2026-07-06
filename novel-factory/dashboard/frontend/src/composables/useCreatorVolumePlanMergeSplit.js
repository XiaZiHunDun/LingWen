/**
 * useCreatorVolumePlanMergeSplit — 卷纲合并/拆分逻辑（从 useCreatorVolumePlan 抽出）
 */
import { ref } from 'vue';
import {
  mergeCreatorVolumePlan,
  splitCreatorVolumePlan,
} from '../api/index.js';
import { formatDisplayLabel, normalizeVolumePlanVolumes } from '../utils/displayProjectName.js';

/**
 * @param {
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   editableVolumes: import('vue').Ref<object[]>,
 *   handleSaveError: (err: unknown) => void,
 * } deps
 */
export function useCreatorVolumePlanMergeSplit(deps) {
  const { error, saveMessage, editableVolumes, handleSaveError } = deps;

  const mergeStartIdx = ref(0);

  const mergeEndIdx = ref(1);

  const mergeLabel = ref('');

  const mergePreview = ref(null);

  const mergeApplying = ref(false);

  const splitVolumeIdx = ref(0);

  const splitAtChapter = ref(2);

  const splitPreview = ref(null);

  const splitApplying = ref(false);

  function syncSplitChapterFromVolume() {
    const vol = editableVolumes.value[splitVolumeIdx.value];
    if (!vol) return;
    const mid = vol.start_chapter + Math.floor((vol.end_chapter - vol.start_chapter) / 2);
    splitAtChapter.value = Math.min(vol.end_chapter, Math.max(vol.start_chapter + 1, mid));
  }

  function resetMergeSplitIndices(volumeCount) {
    mergeStartIdx.value = 0;
    mergeEndIdx.value = Math.min(1, Math.max(0, volumeCount - 1));
    splitVolumeIdx.value = 0;
  }

  function clearMergeSplitPreviews() {
    mergePreview.value = null;
    splitPreview.value = null;
  }

  function resetAfterLoad(volumeCount) {
    resetMergeSplitIndices(volumeCount);
    clearMergeSplitPreviews();
    syncSplitChapterFromVolume();
  }

  async function applyVolumeSplit() {
    splitApplying.value = true;
    error.value = null;
    try {
      const result = await splitCreatorVolumePlan({
        volumes: editableVolumes.value,
        volume_index: splitVolumeIdx.value,
        split_at_chapter: splitAtChapter.value,
      });
      editableVolumes.value = normalizeVolumePlanVolumes(result.volumes);
      splitPreview.value = {
        first_label: formatDisplayLabel(result.first_label),
        second_label: formatDisplayLabel(result.second_label),
        first_range: result.first_range,
        second_range: result.second_range,
      };
      mergePreview.value = null;
      saveMessage.value = `已拆为「${formatDisplayLabel(result.first_label)}」与「${formatDisplayLabel(result.second_label)}」，请保存卷纲`;
      syncSplitChapterFromVolume();
    } catch (e) {
      handleSaveError(e);
    } finally {
      splitApplying.value = false;
    }
  }

  async function applyVolumeMerge() {
    if (mergeStartIdx.value > mergeEndIdx.value) return;
    mergeApplying.value = true;
    error.value = null;
    try {
      const result = await mergeCreatorVolumePlan({
        volumes: editableVolumes.value,
        start_index: mergeStartIdx.value,
        end_index: mergeEndIdx.value,
        label: mergeLabel.value.trim() || undefined,
      });
      editableVolumes.value = normalizeVolumePlanVolumes(result.volumes);
      mergePreview.value = {
        merged_label: formatDisplayLabel(result.merged_label),
        merged_range: result.merged_range,
      };
      mergeStartIdx.value = 0;
      mergeEndIdx.value = Math.min(1, Math.max(0, editableVolumes.value.length - 1));
      mergeLabel.value = '';
      saveMessage.value = `已合并为「${formatDisplayLabel(result.merged_label)}」，请保存卷纲`;
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergeApplying.value = false;
    }
  }

  return {
    mergeStartIdx,
    mergeEndIdx,
    mergeLabel,
    mergePreview,
    mergeApplying,
    splitVolumeIdx,
    splitAtChapter,
    splitPreview,
    splitApplying,
    syncSplitChapterFromVolume,
    resetAfterLoad,
    clearMergeSplitPreviews,
    applyVolumeSplit,
    applyVolumeMerge,
  };
}
