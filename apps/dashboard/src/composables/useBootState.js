/**
 * useBootState — 首次启动侦测
 *
 * 判断当前是否「没有任何已配置项目」，用于决定是否展示无项目首次引导。
 *
 * 判定规则：
 *  - `GET /studio/projects` 返回空列表 → 无项目
 *  - 返回 404（后端 `no studio projects configured`）→ 无项目
 *  - 其它错误（如后端未就绪/离线）→ 记为 error，由界面给出「重试」而非直接判定无项目
 *
 * @returns {{
 *   booting: import('vue').Ref<boolean>,
 *   noProject: import('vue').Ref<boolean>,
 *   error: import('vue').Ref<string|null>,
 *   check: () => Promise<void>,
 *   refresh: () => Promise<void>,
 * }}
 */
import { ref } from 'vue';
import { fetchStudioProjects } from '@/api/studio';

export function useBootState() {
  const booting = ref(true);
  const noProject = ref(false);
  const error = ref(null);

  async function check() {
    booting.value = true;
    error.value = null;
    noProject.value = false;
    try {
      const data = await fetchStudioProjects();
      noProject.value = (data?.projects ?? []).length === 0;
    } catch (err) {
      // 404「no studio projects configured」→ 确无项目；其余错误仅上报，不误判无项目。
      const status = err && typeof err === 'object' ? err.status : undefined;
      if (status === 404) {
        noProject.value = true;
      } else {
        error.value = err && typeof err === 'object' && err.message ? err.message : String(err);
      }
    } finally {
      booting.value = false;
    }
  }

  function refresh() {
    return check();
  }

  return { booting, noProject, error, check, refresh };
}