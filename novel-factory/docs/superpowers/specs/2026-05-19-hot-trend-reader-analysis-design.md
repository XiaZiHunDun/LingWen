# 热梗素材抓取 + 读者评论分析设计文档

> 日期：2026-05-19
> 方案：方向11（热梗素材抓取 + 读者评论分析）
> 状态：已批准，等待实施

---

## 一、背景与目标

### 1.1 现状问题

当前小说工厂在"市场洞察"方面的处理方式：
- 有 `05_模拟读者池/读者{N}/` 模拟读者
- 有 `06_意见仓库/` 存储审核/评论记录
- **缺失**：没有系统化的热梗素材抓取机制
- **缺失**：没有读者评论的深度分析来指导创作方向

### 1.2 优化目标

构建一个市场洞察系统：
- **热梗素材抓取**：从网络平台抓取当前热门梗/题材/元素
- **读者评论分析**：分析读者评论，提取情感倾向和创作建议
- **趋势预测**：基于热梗和评论分析，预测未来创作方向
- **写作辅助**：将热梗元素融入创作建议

---

## 二、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 热梗抓取 | 网络爬虫 + 规则过滤 | 从公开平台抓取热门内容 |
| 评论分析 | LLM 调用（情感分析） | 分析读者情感倾向 |
| 趋势预测 | 规则引擎 + 统计 | 基于历史数据预测 |
| 部署环境 | Python + Docker | 与现有环境一致 |

---

## 三、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    市场洞察引擎                                  │
│                                                              │
│  输入：                                                        │
│    1. 网络热梗/热门题材（外部数据）                            │
│    2. 读者评论数据（内部数据）                                │
│       ↓                                                        │
│  分析维度：                                                    │
│    1. 热梗抓取（网络热门梗/题材/元素）                        │
│    2. 评论分析（读者情感/偏好/建议）                          │
│    3. 趋势预测（基于热梗+评论预测方向）                      │
│    4. 写作辅助（提供可融入的热梗元素建议）                    │
│       ↓                                                        │
│  输出：                                                        │
│    1. 热门题材清单及热度评分                                   │
│    2. 读者偏好分析报告                                         │
│    3. 创作建议（可融入的热梗元素）                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、热梗素材抓取

### 4.1 抓取来源

```yaml
trend_sources:
  - platform: "微博热搜"
    type: "social_trending"
    update_frequency: "daily"

  - platform: "抖音热点"
    type: "video_trending"
    update_frequency: "daily"

  - platform: "起点读书排行榜"
    type: "novel_platform"
    update_frequency: "weekly"

  - platform: "晋江文学城排行榜"
    type: "novel_platform"
    update_frequency: "weekly"

  - platform: "知乎小说话题"
    type: "qa_platform"
    update_frequency: "weekly"

  - platform: "小红书小说推荐"
    type: "social_media"
    update_frequency: "daily"
```

### 4.2 抓取内容

```yaml
captured_content:
  hot_memes:
    - name: "题材名称"
      heat_score: 85  # 0-100
      source: "抖音热点"
      example_works: ["作品A", "作品B"]
      extraction_date: "2026-05-19"

  hot_themes:
    - name: "主题名称"
      heat_score: 72
      source: "微博热搜"
      description: "主题描述"
      target_audience: "18-25岁"

  hot_elements:
    - name: "元素名称"
      type: "character_archetype"  # character_archetype / plot_device / world_building / writing_style
      heat_score: 68
      source: "起点排行榜"
      usage_examples: ["作品A第30章", "作品B第50章"]
```

### 4.3 热度评分算法

```yaml
heat_score_algorithm:
  factors:
    - name: "平台热度"
      weight: 0.4
      calculation: "normalize_to_100"

    - name: "讨论量增长"
      weight: 0.3
      calculation: "growth_rate_7d"

    - name: "持续时间"
      weight: 0.2
      calculation: "days_in_top_10"

    - name: "相关性"
      weight: 0.1
      calculation: "keyword_match_with_genre"

  final_score: "weighted_sum"
```

---

## 五、读者评论分析

### 5.1 分析维度

```yaml
comment_analysis:
  input: "读者评论文本"

  output:
    # 1. 情感分析
    sentiment_analysis:
      overall_sentiment: "positive"  # positive / neutral / negative
      sentiment_score: 0.75  # 0-1
      key_emotions: ["excited", "engaged", "curious"]

    # 2. 偏好提取
    preference_extraction:
      liked_elements: ["角色性格", "剧情反转", "感情线"]
      disliked_elements: ["节奏太慢", "女主太弱"]
      suggested_improvements: ["希望男二有更多戏份"]

    # 3. 主题分析
    theme_analysis:
      recurring_themes: ["成长", "救赎", "并肩作战"]
      emerging_themes: ["星际", "穿越"]
      fading_themes: ["传统玄幻"]

    # 4. 受众画像
    audience_profile:
      age_range: "18-25"
      primary_gender: "female"
      engagement_level: "high"
      retention_probability: 0.82
```

### 5.2 分析流程

```yaml
analysis_flow:
  1. "收集评论"
     - source: "模拟读者反馈"
     - source: "审核员意见"
     - source: "主公反馈"

  2. "预处理"
     - remove_duplicates: true
     - filter_low_quality: true
     - normalize_text: true

  3. "情感分析"
     - llm_analyze: "判断情感倾向"
     - extract_emotions: "高兴/愤怒/好奇/失望"

  4. "偏好提取"
     - liked_elements: "LLM提取读者喜欢的内容"
     - disliked_elements: "LLM提取读者不喜欢的内容"

  5. "生成报告"
     - summary: "汇总分析"
     - suggestions: "创作建议"
```

---

## 六、趋势预测

### 6.1 预测维度

```yaml
trend_prediction:
  # 1. 短期趋势（1-3个月）
  short_term:
    - trend: "题材热度上升/下降"
      confidence: 0.85
      prediction_period: "1-3个月"

  # 2. 中期趋势（3-6个月）
  medium_term:
    - trend: "新题材崛起"
      confidence: 0.70
      prediction_period: "3-6个月"

  # 3. 长期趋势（6-12个月）
  long_term:
    - trend: "市场走向"
      confidence: 0.60
      prediction_period: "6-12个月"
```

### 6.2 预测输入

```yaml
prediction_inputs:
  - "热梗抓取数据（过去30天）"
  - "读者评论分析结果"
  - "平台排行榜历史数据"
  - "行业报告"
```

---

## 七、写作辅助

### 7.1 热梗融入建议

```yaml
meme_integration:
  input:
    - "当前章节的大纲"
    - "当前读者偏好分析"

  output:
    - "可融入的热梗元素"
    - "融入方式建议"
    - "预期效果"

  example:
    current_chapter: "林夜与苏琳首次相遇"
    hot_meme: "欢喜冤家"
    integration_suggestion: "让苏琳对林夜表现出傲娇反应，增加互动趣味性"
    expected_effect: "提升读者好感度"
```

### 7.2 读者反馈驱动创作

```yaml
feedback_driven_creation:
  input:
    - "读者偏好报告"
    - "当前创作方向"

  output:
    - "调整建议"
    - "新增元素建议"
    - "删除元素建议"

  example:
    reader_feedback: "希望看到更多主角展现能力的场景"
    current_direction: "主角目前以隐忍为主"
    adjustment_suggestion: "在ch030让主角展示一次实力，提升读者爽感"
```

---

## 八、存储结构

```
novel-factory/
├── market_insight/
│   ├── __init__.py
│   ├── hot_meme_crawler/
│   │   ├── __init__.py
│   │   ├── crawler.py              # 爬虫核心
│   │   ├── platforms/
│   │   │   ├── __init__.py
│   │   │   ├── weibo.py
│   │   │   ├── douyin.py
│   │   │   ├── qidian.py
│   │   │   └── ...
│   │   └── filters/
│   │       └── meme_filter.py      # 梗过滤
│   ├── comment_analyzer/
│   │   ├── __init__.py
│   │   ├── sentiment.py             # 情感分析
│   │   ├── preference.py            # 偏好提取
│   │   └── report_generator.py     # 报告生成
│   ├── trend_predictor/
│   │   ├── __init__.py
│   │   ├── short_term.py           # 短期预测
│   │   ├── medium_term.py          # 中期预测
│   │   └── long_term.py            # 长期预测
│   ├── writing_assistant/
│   │   ├── __init__.py
│   │   ├── meme_integrator.py      # 热梗融入
│   │   └── feedback_driver.py      # 反馈驱动
│   └── config/
│       ├── sources.yaml            # 数据源配置
│       ├── thresholds.yaml         # 阈值配置
│       └── meme_categories.yaml    # 梗分类
└── ...
```

---

## 九、实施步骤

### 阶段1（2-3周）：热梗抓取

1. 实现基础爬虫框架
2. 实现微博热搜爬虫
3. 实现抖音热点爬虫
4. 实现起点排行榜爬虫
5. 实现热度评分算法
6. 验证：能正确抓取并评分

### 阶段2（2-3周）：读者评论分析

7. 实现评论收集机制
8. 实现情感分析（LLM）
9. 实现偏好提取
10. 实现报告生成
11. 验证：分析结果准确率高

### 阶段3（2-3周）：趋势预测 + 写作辅助

12. 实现短期趋势预测
13. 实现中期趋势预测
14. 实现热梗融入建议
15. 实现反馈驱动创作
16. 与灵感部门集成
17. 验证：完整流程测试

---

## 十、验收标准

| 阶段 | 验收条件 |
|------|---------|
| 阶段1 | 能正确抓取3个以上平台的热梗数据，输出热度评分 |
| 阶段2 | 评论分析准确率≥80%，能提取有价值的读者偏好 |
| 阶段3 | 趋势预测置信度≥70%，热梗融入建议相关度高 |

---

## 十一、关键设计决策

| 决策 | 说明 |
|------|------|
| 多平台抓取 | 从多个公开平台抓取热梗，覆盖面广 |
| LLM 情感分析 | 用 LLM 分析读者评论中的情感和偏好 |
| 分层预测 | 短期/中期/长期分别预测，满足不同需求 |
| 写作辅助 | 直接提供可融入的热梗元素，而非仅做分析 |
| 隐私合规 | 仅使用公开数据，不涉及用户隐私 |