# 灵文工作室 · 30 分钟 Demo 录屏分镜稿

> **版本**：recording-v3 · 2026-06-20（八书 · 静海主打样章）  
> **对应脚本**：[`studio-demo.md`](studio-demo.md) 路线 B  
> **目标时长**：28–32 分钟（含 1 分钟片头片尾）  
> **录制建议**：1920×1080 · 终端字体 14pt+ · 浏览器 125% 缩放

---

## 录屏前 10 分钟（镜头外完成）

```bash
cd novel-factory
unset LINGWEN_PROJECT_ROOT          # doctor 用星陨 root
python lingwen.py doctor            # 应全部 ✓

# 单端口 Dashboard（API + 静态 UI，推荐 Cursor SSH）
bash scripts/run-dashboard-single-port.sh
```

**Cursor SSH 访问 Studio（Windows）**

1. Cursor **Ports** 面板确认 **8765** 已转发
2. 在 Cursor 内先点链接 **`http://127.0.0.1:8765/?nav=studio`**（激活转发）
3. 再开浏览器访问同一地址（勿用 `localhost`，若开 mihomo 需直连 127.0.0.1）
4. 备用：`bash scripts/expose-dashboard-tunnel.sh` 公网 HTTPS（Demo 临时用）

**浏览器预开标签**

| Tab | 地址 / 文件 |
|-----|-------------|
| A | `http://127.0.0.1:8765/?nav=studio` |
| B | `docs/trial-read-index.md`（IDE 预览） |
| C | `projects/jinghai-rizhi/docs/trial-read-ch001-003.md`（**主打样章**） |

| 检查 | 动作 |
|------|------|
| 工程 smoke | `bash scripts/verify-studio-release.sh`（或 blind 子集） |
| 顶栏项目列表 | Studio 页可见八项目 + 星陨 |
| 麦克风 | 试录 10 秒，确认无系统通知音 |

**片头字幕（可选，5 秒）**：灵文工作室 · 八书闭环 · 静海样章

---

## 分镜表（按时间轴）

| 时间 | 镜头 | 画面操作 | 旁白 / 话术要点 |
|------|------|----------|-----------------|
| **0:00–2:00** | 定位 | IDE 打开 `HANDOFF.md` §0 TL;DR，滚动 30 秒 | 「灵文不是无止尽写星陨——星陨是 testbed。产品是**工作室**：八项目验证同一 pipeline，**静海日志**是对外主打样章。」 |
| **2:00–7:00** | 试读 | Tab B：`trial-read-index.md`，先点 **静海** | 「对外优先发试读 3 章；八书 P0=0，Golden Set 进 CI。」 |
| **7:00–9:00** | 钩子 1 | Tab C：静海 ch001 频道十七 | 「主打样章——沿海悬疑。」 |
| **9:00–10:30** | 钩子 2–3 | 灰域「你看到了。」→ 暗夜信标 | 「同 pipeline，不同 pillars。」 |
| **10:30–12:00** | 工程 | 终端：`bash scripts/verify-studio-release.sh`（可预录） | 「doctor + onboarding + golden-set 八 slug，发布前一命令。」 |
| **12:00–15:00** | Dashboard 入场 | Tab A：Studio 页，展示顶栏 **ProjectSwitcher** | 「Dashboard 是多项目控制台，不是单书编辑器。」 |
| **15:00–18:00** | 切换 ×3 | 依次选：**灰域档案** → **暗夜信标** → **静海日志** | 每次切换停顿 3 秒：「slug 变，大纲门 / 角色表 / 报告路径全部跟项目走。」 |
| **18:00–22:00** | 质量面板 | 选 **静海日志**（或雪线），展开 **Full-check 报告** | 「P0–P3 按章折叠；P0=0 是发布候选硬指标。报告由 `generate-full-check-report.sh` 写入 `docs/`。」 |
| **22:00–25:00** | Golden Set | 终端：`bash scripts/verify-golden-set.sh jinghai-rizhi` | 「三章 frozen sample；CI matrix **八 slug**。」 |
| **25:00–28:00** | 生产控制台 | Studio 页：**Preflight 1–3**，展示通过项；复制 **Batch 命令**（不真跑） | 「生产前有硬门：REAL_LLM、大纲、canon max_chapter。Batch 预算带 15% 余量。」 |
| **28:00–30:00** | 收尾 Q&A | 回到 `trial-read-index.md` 或 HANDOFF「下一期推荐」 | 三句收束见下方「标准收尾词」 |

---

## 标准收尾词（28–30 分钟）

1. **差异**：「和通用 AI 写作工具的差别是硬门 + 质检 + Golden Set，不是无限续写。」
2. **指标**：「成功看闭环——10 章 + 试读包 + P0=0，不看章数 KPI。」
3. **下一步**：「新书 = `init-project` + 改 pillars/大纲 + 同样 batch；星陨继续作压测 testbed。」

---

## 镜头切换技巧

| 场景 | 建议 |
|------|------|
| 终端命令 | 全屏终端，命令先粘贴再回车；输出保留 2 秒再切 |
| 长命令 blind test | 可剪 6 秒预录 PASS 片段，旁白说「刚才已跑过，结果 PASS」 |
| Dashboard | 鼠标移动慢；折叠面板一次只展开一章 |
| 试读 Markdown | 用 IDE 预览或 Glass，字号调大 |

---

## 可选加分镜头（超时则删）

| 加镜 | 时长 | 内容 |
|------|------|------|
| A | +3 min | 切换 **雪线档案**，展示第五本 Golden Set |
| B | +5 min | `export LINGWEN_ONBOARDING_PILOT=1` 跑 1 章 pilot（耗 API，建议另录） |
| C | +2 min | GitHub Actions `golden-set` job 截图 |

---

## 录屏后检查

- [ ] 音画同步，无卡帧 > 2 秒
- [ ] 未泄露 `.env` / API Key（终端 `echo $MINIMAX` 勿入镜）
- [ ] 五书名、P0=0、五书 Golden Set 均已口播或字幕
- [ ] 导出 1080p MP4；文件名建议 `lingwen-studio-demo-2026-06-18.mp4`
- [ ] 更新 [`demo-checklist-report.md`](demo-checklist-report.md) 录屏项为 `[x]`

---

## 故障备用话术

| 情况 | 说法 |
|------|------|
| Dashboard 502 | 「本地未起服务，我们切文件演示——试读索引同样代表交付物。」 |
| Full-check 面板空 | 「报告在 `projects/<slug>/docs/full-check-report.md`，CLI 与 Studio 同源。」 |
| 项目列表缺书 | 「检查 `projects/<slug>/config/project.yaml` 是否存在。」 |

---

## 相关文档

- [`studio-demo.md`](studio-demo.md) — 路线 A/B 提纲
- [`demo-checklist-report.md`](demo-checklist-report.md) — 自动化验收记录
- [`trial-read-index.md`](trial-read-index.md) — 五书试读链接
- [`studio-onboarding.md`](studio-onboarding.md) — 30 分钟第一本实操
