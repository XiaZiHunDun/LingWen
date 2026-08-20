/**
 * VolumeTemplate API
 *
 * Phase 62.5: 从 api/creator.js 拆出。
 *
 * 包含: VolumeTemplate CRUD + Factory + Sync + Publish + Changelog + Version (15 funcs)
 */

import { request } from './core.js';

export async function fetchCreatorVolumeTemplates() {
  return request('/creator/volume-plan/templates');
}

export async function saveCreatorVolumeTemplate(body) {
  return request('/creator/volume-plan/templates/save', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorVolumeTemplate(templateId) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
}

export async function renameCreatorVolumeTemplate(templateId, body) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'PATCH',
    body,
  });
}

export async function setCreatorVolumeTemplateVersion(templateId, body) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version`, {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorVolumeTemplateChangelog(templateId) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-changelog`,
  );
}

export async function rollbackCreatorVolumeTemplate(templateId, body) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-rollback`,
    { method: 'POST', body },
  );
}

export async function importCreatorVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/import', {
    method: 'POST',
    body,
  });
}

export async function exportCreatorVolumeTemplates() {
  return request('/creator/volume-plan/templates/export');
}

export async function fetchCreatorVolumeTemplateSyncSources() {
  return request('/creator/volume-plan/templates/sync-sources');
}

export async function syncCreatorVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/sync', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorFactoryVolumeTemplates() {
  return request('/creator/volume-plan/templates/factory');
}

export async function publishCreatorVolumeTemplateToFactory(body) {
  return request('/creator/volume-plan/templates/factory/publish', {
    method: 'POST',
    body,
  });
}

export async function pullCreatorFactoryVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/factory/pull', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorFactoryVolumeTemplate(templateId) {
  return request(`/creator/volume-plan/templates/factory/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
}
