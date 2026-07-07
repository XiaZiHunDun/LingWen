/** Product copy for creation_mode — used on Today hub and header hint. */

const MODE_META = {
  companion: {
    label: '陪伴模式',
    tagline: '人主笔 · P0 守门 · 章内编辑',
    audience: '适合日常手改连载',
  },
  advance: {
    label: '推进模式',
    tagline: '脉络预警 · Batch 产章 · 卷纲 diff',
    audience: '适合批量推进与调度',
  },
  studio: {
    label: '工作室模式',
    tagline: '工厂流水线 · 质检 · Golden Set',
    audience: '适合运维与工业化产线',
  },
};

export function creationModeMeta(mode) {
  return MODE_META[mode] || {
    label: mode || '未知模式',
    tagline: '',
    audience: '',
  };
}

/**
 * Pick the single primary CTA for the Today hub.
 * @param {object} ctx
 */
export function resolveTodayPrimaryAction(ctx) {
  const {
    creationMode = 'companion',
    pendingDecisions = 0,
    pendingRipples = 0,
    batchActive = false,
    wizardProgressPct = 100,
    chaptersWritten = 0,
    coveragePct = 0,
    alertCount = 0,
    isReviewer = false,
    microTask = null,
    activeChapter = null,
  } = ctx;

  if (isReviewer) {
    if (pendingDecisions > 0) {
      return {
        id: 'decisions',
        label: `查看 ${pendingDecisions} 条待决策`,
        nav: 'inbox',
        tab: 'decisions',
        reason: '审阅模式：确认工作流待办',
      };
    }
    if (pendingRipples > 0) {
      return {
        id: 'ripples',
        label: `查看 ${pendingRipples} 条一致性变更`,
        nav: 'inbox',
        tab: 'ripples',
        reason: '审阅模式：只读审阅跨卷变更',
      };
    }
    return {
      id: 'insight',
      label: '查看追读力洞察',
      nav: 'insight',
      tab: 'overview',
      reason: '审阅模式：只读查看本书诊断数据',
    };
  }

  if (pendingDecisions > 0) {
    return {
      id: 'decisions',
      label: `处理 ${pendingDecisions} 条待决策`,
      nav: 'inbox',
      tab: 'decisions',
      reason: '工作流在等待你的确认',
    };
  }
  if (pendingRipples > 0) {
    return {
      id: 'ripples',
      label: `审阅 ${pendingRipples} 条一致性变更`,
      nav: 'inbox',
      tab: 'ripples',
      reason: '跨卷变更需要人工确认',
    };
  }
  if (batchActive) {
    return {
      id: 'batch',
      label: '查看 Batch 生产进度',
      nav: 'produce',
      tab: 'studio',
      reason: '后台 Batch 正在运行',
    };
  }
  if (wizardProgressPct < 100) {
    return {
      id: 'wizard',
      label: '继续入门向导',
      nav: 'creator',
      wizard: true,
      reason: `新书设置未完成（${wizardProgressPct}%）`,
    };
  }
  if (creationMode === 'companion') {
    if (chaptersWritten === 0) {
      return {
        id: 'write-first',
        label: '去写作页写 ch001',
        nav: 'creator',
        chapter: 1,
        reason: '从第一章开始人主笔创作',
      };
    }
    if (microTask?.remaining > 0 && activeChapter) {
      const chLabel = `ch${String(activeChapter).padStart(3, '0')}`;
      return {
        id: 'write-micro',
        label: `再写 ${microTask.remaining} 字`,
        nav: 'creator',
        chapter: activeChapter,
        reason: `${chLabel} 还差 ${microTask.remaining} 字达标（${microTask.current}/${microTask.goal}）`,
      };
    }
    return {
      id: 'write',
      label: '继续创作',
      nav: 'creator',
      reason: alertCount > 0 ? `有 ${alertCount} 条脉络预警待查看` : '回到三栏写作工作台',
    };
  }
  if (creationMode === 'advance') {
    if (coveragePct < 100) {
      return {
        id: 'produce',
        label: '去生产跑 Preflight / Batch',
        nav: 'produce',
        tab: 'studio',
        reason: `正文进度 ${coveragePct}%`,
      };
    }
    return {
      id: 'pulse',
      label: '查看脉络与偏离',
      nav: 'creator',
      reason: '推进模式：检查卷纲与偏离',
    };
  }
  if (coveragePct < 100) {
    return {
      id: 'studio-produce',
      label: '打开生产控制台',
      nav: 'produce',
      tab: 'studio',
      reason: `正文进度 ${coveragePct}%`,
    };
  }
  return {
    id: 'studio-quality',
    label: '查看质量仪表盘',
    nav: 'produce',
    tab: 'studio',
    reason: '工作室模式：质检与产线状态',
  };
}
