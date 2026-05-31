# 阶段2：Dashboard可视化系统设计

> 日期：2026-05-31
> 状态：草稿
> 版本：v1.0

---

## 1. 背景与目标

### 1.1 背景

阶段1已实现追读力系统（钩子检测+爽点标记），数据已存储到 `reading_power.db`。但目前缺乏可视化界面，无法直观查看追读力趋势和章节状态。

### 1.2 目标

阶段2实现追读力Dashboard可视化，提供：
- 追读力总览统计
- 章节钩子/爽点趋势图
- 章节数据表格

### 1.3 约束

| 约束 | 说明 |
|------|------|
| 技术栈 | Vue.js 3 + Vite + ECharts + FastAPI |
| 样式 | 像素风（与webnovel-writer一致） |
| 部署 | 独立服务（端口8765 API + 3000 前端） |
| 功能范围 | 最小可用版（总览+趋势图+数据表） |
| 刷新方式 | 手动刷新按钮 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard 独立服务                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Vue.js + ECharts)     │  Backend (FastAPI)         │
│  ┌─────────────────────────┐      │  ┌───────────────────┐   │
│  │  OverviewPage           │      │  │ GET /api/overview │   │
│  │  - 追读力趋势图         │      │  │ GET /api/chapters │   │
│  │  - 钩子/爽点统计卡片    │      │  │ GET /api/health   │   │
│  └─────────────────────────┘      │  └───────────────────┘   │
│  Port: 3000 (Vite)              │  Port: 8765               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  reading_power.db    │
              │  (.state/)           │
              └──────────────────────┘
```

### 2.2 组件职责

| 组件 | 位置 | 职责 |
|------|------|------|
| `app.py` | `dashboard/app.py` | FastAPI应用，API端点 |
| `OverviewPage.vue` | `dashboard/frontend/src/pages/` | 追读力总览页面 |
| `StatCard.vue` | `dashboard/frontend/src/components/` | 统计卡片组件 |
| `HookTrendChart.vue` | `dashboard/frontend/src/components/` | 钩子趋势图 |
| `CoolpointChart.vue` | `dashboard/frontend/src/components/` | 爽点分布图 |
| `ChapterTable.vue` | `dashboard/frontend/src/components/` | 章节数据表 |

---

## 3. API设计

### 3.1 端点定义

| 端点 | 方法 | 返回数据 |
|------|------|----------|
| `/api/overview` | GET | 总览统计（总章节数、总钩子、总爽点、平均分数） |
| `/api/chapters` | GET | 章节数据列表，支持 `?range=1-30` 参数 |
| `/api/health` | GET | 服务健康状态 |

### 3.2 数据模型

**GET /api/overview 返回**
```json
{
  "total_chapters": 360,
  "total_hooks": 1234,
  "avg_hook_strength": 0.72,
  "total_coolpoints": 567,
  "avg_coolpoint_density": 0.68
}
```

**GET /api/chapters?range=1-30 返回**
```json
{
  "chapters": [
    {
      "chapter": 1,
      "hook_count": 3,
      "hook_strength_avg": 0.75,
      "coolpoint_count": 2,
      "coolpoint_density": 0.85
    }
  ]
}
```

---

## 4. 前端设计

### 4.1 页面结构

```
frontend/src/
├── App.vue                 # 根组件（布局+侧边栏）
├── pages/
│   └── OverviewPage.vue   # 总览页（唯一页面）
├── components/
│   ├── StatCard.vue       # 统计卡片
│   ├── HookTrendChart.vue # 钩子趋势折线图
│   ├── CoolpointChart.vue # 爽点分布柱状图+饼图
│   └── ChapterTable.vue   # 章节数据表格
├── api/
│   └── index.js          # API调用封装
└── assets/
    └── style.css         # 像素风样式
```

### 4.2 统计卡片（StatCard）

| 指标 | 说明 |
|------|------|
| 总章节数 | 已分析的章节总数 |
| 总钩子数 | 所有章节的钩子总数 |
| 平均钩子强度 | 0.0-1.0 |
| 总爽点数 | 所有章节的爽点总数 |
| 平均爽点密度 | 0.0-1.0 |

### 4.3 钩子趋势图（HookTrendChart）

- **类型**：折线图
- **X轴**：章节号
- **Y轴**：钩子数量
- **交互**：鼠标悬停显示详情

### 4.4 爽点分布图（CoolpointChart）

- **类型**：柱状图 + 饼图
- **柱状图**：各爽点类型数量
- **饼图**：爽点类型占比

### 4.5 章节数据表（ChapterTable）

| 列 | 说明 |
|----|------|
| 章节 | 章节号 |
| 钩子数 | 本章钩子数量 |
| 钩子强度 | 平均强度 |
| 爽点数 | 本章爽点数量 |
| 爽点密度 | 密度评分 |

---

## 5. 样式设计

### 5.1 像素风主题

```css
:root {
  --bg-primary: #fff7e8;      /* 暖色调背景 */
  --bg-secondary: #f5efe6;      /* 次级背景 */
  --color-accent: #26a8ff;      /* 强调蓝 */
  --color-warning: #f5a524;      /* 警告橙 */
  --color-danger: #d7263e;      /* 危险红 */
  --color-success: #2ec27e;     /* 成功绿 */
  --color-text: #2a220f;        /* 主文字 */
  --border-color: #2a220f;     /* 边框色 */
}

.pixel-border {
  border: 4px solid var(--border-color);
  box-shadow: 6px 6px 0 var(--border-color);
}

.pixel-font {
  font-family: 'Press Start 2P', monospace;
}
```

### 5.2 组件样式

- 卡片：像素边框 + 阴影
- 按钮：hover状态颜色变化
- 表格：斑马纹 + hover高亮

---

## 6. 目录结构

```
novel-factory/
├── dashboard/                    # 新增Dashboard模块
│   ├── app.py                    # FastAPI应用
│   ├── frontend/                 # Vue.js前端
│   │   ├── src/
│   │   │   ├── App.vue
│   │   │   ├── pages/
│   │   │   │   └── OverviewPage.vue
│   │   │   ├── components/
│   │   │   │   ├── StatCard.vue
│   │   │   │   ├── HookTrendChart.vue
│   │   │   │   ├── CoolpointChart.vue
│   │   │   │   └── ChapterTable.vue
│   │   │   ├── api/
│   │   │   │   └── index.js
│   │   │   └── assets/
│   │   │       └── style.css
│   │   ├── index.html
│   │   ├── package.json
│   │   └── vite.config.js
│   └── requirements.txt          # Python依赖
└── rules/                        # 现有规则库（不变）
```

---

## 7. 启动方式

```bash
# 方式1：分别启动
# 终端1: 启动API服务
cd novel-factory/dashboard
python -m uvicorn app:create_app --reload --port 8765

# 终端2: 启动前端
cd novel-factory/dashboard/frontend
npm install
npm run dev

# 方式2：访问 http://localhost:3000
```

---

## 8. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 数据库不存在 | 返回空数据，提示"请先运行 lingwen.py reading-power 分析" |
| API请求超时 | 显示错误提示，提供重试按钮 |
| 前端构建失败 | 提供详细错误日志 |

---

## 9. 测试策略

| 测试类型 | 覆盖内容 |
|----------|----------|
| API单元测试 | 各端点返回数据验证 |
| 前端组件测试 | StatCard、ChapterTable渲染 |
| E2E测试 | 完整页面加载和数据展示 |

---

## 10. 阶段3预告

Dashboard完成后，后续可扩展：

| 功能 | 说明 |
|------|------|
| SSE实时推送 | 文件变化时自动刷新 |
| 质量分数集成 | 叠加S1-S11质量数据 |
| 角色关系图 | 基于角色数据的关系可视化 |

---

## 11. 附录：参考文件

| 文件 | 说明 |
|------|------|
| `reference/webnovel-writer/.../dashboard/` | webnovel-writer完整Dashboard参考 |
| `novel-factory/infra/reading_power/` | 阶段1追读力系统 |

---

## 12. 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-31 | v1.0 | 初稿 |