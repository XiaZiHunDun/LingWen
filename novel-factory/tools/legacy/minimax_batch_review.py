#!/usr/bin/env python3
"""
MiniMax M2.7 全量检查脚本 - 360章 / 4000次调用

使用 MiniMax M2.7 模型对星陨纪元全部360章进行全面质量检查
每章约11次调用，总计约4000次调用

检查维度：S1-S8 + 一致性 + 伏笔 + AI痕迹
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 立即刷新stdout
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.ai_service import MiniMaxProvider, ProviderConfig


class MiniMaxReviewer:
    """MiniMax全量审查器"""

    def __init__(self, api_key: str):
        config = ProviderConfig(api_key=api_key)
        self.provider = MiniMaxProvider(config)
        self.characters = self._load_character_profiles()

    def _load_character_profiles(self) -> Dict:
        profile_path = Path(__file__).parent.parent / "03_内容仓库/角色设定/character_profiles.json"
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {c["name"]: c for c in data.get("characters", [])}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"加载角色配置失败: {e}")
            return {}

    def _load_chapter(self, chapter_num: int) -> Optional[str]:
        chapter_file = Path(__file__).parent.parent / f"03_内容仓库/04_正文/ch{chapter_num:03d}.md"
        try:
            with open(chapter_file, "r", encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"文件读取失败: {e}")
            return None

    def _call(self, prompt: str, max_tokens: int = 1500) -> str:
        try:
            return self.provider.generate(prompt=prompt, max_tokens=max_tokens, temperature=0.3)
        except Exception as e:
            return f"ERROR: {e}"

    def _parse_json(self, response: str) -> Any:
        try:
            text = response.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
                    if text.startswith("json"):
                        text = text[4:].lstrip("\n")
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            return {}

    def review_chapter(self, chapter_num: int) -> Dict[str, Any]:
        """检查单个章节"""
        content = self._load_chapter(chapter_num)
        if not content:
            return {"chapter": f"ch{chapter_num:03d}", "error": "not found", "llm_calls": 0}

        chapter_id = f"ch{chapter_num:03d}"
        result = {"chapter": chapter_id, "llm_calls": 0, "scores": {}, "issues": []}
        calls = 0

        # 截取内容
        text = content[:3000]

        # ========== 调用1: 8维评分一次性 ==========
        prompt = f'''对以下章节进行评分。返回JSON格式，包含8个维度的评分(0-100)和简短评价：
{{"S1": score, "S2": score, "S3": score, "S4": score, "S5": score, "S6": score, "S7": score, "S8": score, "comment": "一句话评价"}}

章节：{chapter_id}
内容：{text}

只返回JSON，不要其他文字。'''

        data = self._parse_json(self._call(prompt, max_tokens=2000))
        calls += 1

        for i in range(1, 9):
            result["scores"][f"S{i}"] = {"score": data.get(f"S{i}", 0)}

        # ========== 调用2: 角色一致性检查 ==========
        prompt = f'''检查以下章节中的人物表现是否与角色设定一致。返回JSON：
{{"issues": [{{"character": "角色名", "type": "问题类型", "location": "位置", "desc": "描述"}}]}}

角色设定：{json.dumps(self.characters, ensure_ascii=False)[:1500]}

章节：{chapter_id}
内容：{text}

只返回JSON。'''

        data = self._parse_json(self._call(prompt))
        calls += 1

        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                result["issues"].append({
                    "severity": "P1",
                    "dimension": "一致性",
                    "type": f"角色-{issue.get('character', '')}",
                    "description": f"{issue.get('desc', '')}",
                    "location": issue.get("location", "")
                })

        # ========== 调用3: 世界观一致性 ==========
        prompt = f'''检查以下章节设定是否与大綱一致。返回JSON：
{{"issues": [{{"type": "设定冲突", "location": "位置", "desc": "描述"}}]}}

境界：粒子境/星火境/脉冲境/裂变境(卷1) → 黑洞境(卷2) → 创世境/永恒境(卷3)
势力：星辰会/玄机阁/万剑宗/灵兽谷/暗域/星际修真联盟

章节：{chapter_id}
内容：{text}

只返回JSON。'''

        data = self._parse_json(self._call(prompt))
        calls += 1

        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                result["issues"].append({
                    "severity": "P1",
                    "dimension": "世界观",
                    "type": issue.get("type", "设定冲突"),
                    "description": issue.get("desc", ""),
                    "location": issue.get("location", "")
                })

        # ========== 调用4: 逻辑矛盾 ==========
        prompt = f'''检查以下章节是否存在事实矛盾。返回JSON：
{{"issues": [{{"type": "矛盾", "location": "位置", "desc": "描述"}}]}}

章节：{chapter_id}
内容：{text}

只返回JSON。'''

        data = self._parse_json(self._call(prompt))
        calls += 1

        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                result["issues"].append({
                    "severity": "P1",
                    "dimension": "逻辑",
                    "type": "事实矛盾",
                    "description": issue.get("desc", ""),
                    "location": issue.get("location", "")
                })

        # ========== 调用5: 伏笔检测 ==========
        prompt = f'''检查以下章节的伏笔埋设与回收情况。返回JSON：
{{"foreshadows": [{{"type": "伏笔类型", "status": "已埋设/已回收/未回收", "desc": "描述"}}]}}

章节：{chapter_id}
内容：{text}

只返回JSON。'''

        data = self._parse_json(self._call(prompt))
        calls += 1

        for fs in data.get("foreshadows", []):
            if isinstance(fs, dict) and fs.get("status") == "未回收":
                result["issues"].append({
                    "severity": "P2",
                    "dimension": "伏笔",
                    "type": "伏笔未回收",
                    "description": fs.get("desc", ""),
                    "location": ""
                })

        # ========== 调用6: AI痕迹 ==========
        prompt = f'''检查以下章节是否存在AI创作痕迹。返回JSON：
{{"issues": [{{"type": "痕迹类型", "location": "位置", "desc": "描述"}}]}}

常见AI痕迹：套路句式("首先...其次...最后")、模板结构、过度解释

章节：{chapter_id}
内容：{text}

只返回JSON。'''

        data = self._parse_json(self._call(prompt))
        calls += 1

        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                issue_type = issue.get("type", "AI痕迹")
                if "套路" in issue_type:
                    issue_type = "套路句式"
                result["issues"].append({
                    "severity": "P2",
                    "dimension": "AI痕迹",
                    "type": issue_type,
                    "description": issue.get("desc", ""),
                    "location": issue.get("location", "")
                })

        # ========== 调用7: 综合评分 ==========
        prompt = f'''对以下章节进行综合评分。返回JSON：
{{"overall": 0-100, "summary": "一句话总结", "top_issue": "最重要的问题"}}

章节：{chapter_id}
内容：{text[:1500]}

只返回JSON。'''

        data = self._parse_json(self._call(prompt))
        calls += 1

        result["overall_score"] = data.get("overall", 0)
        result["summary"] = data.get("summary", "")
        result["top_issue"] = data.get("top_issue", "")

        result["llm_calls"] = calls
        return result


def run_full_review():
    """执行全量360章检查，约4000次调用"""
    print("=" * 60)
    print("MiniMax M2.7 全量检查 - 星陨纪元360章")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    api_key = os.getenv("MINIMAX_API_KEY", "")
    if not api_key:
        print("Error: MINIMAX_API_KEY not set")
        return

    output_dir = Path(__file__).parent / "logs" / "minimax_review"
    output_dir.mkdir(parents=True, exist_ok=True)

    reviewer = MiniMaxReviewer(api_key)

    all_results = []
    total_calls = 0
    start_time = datetime.now()

    # 每10章报告一次进度
    for ch_num in range(1, 361):
        result = reviewer.review_chapter(ch_num)
        all_results.append(result)
        total_calls += result.get("llm_calls", 0)

        # 每10章输出一次进度
        if ch_num % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            avg_time = elapsed / ch_num
            eta = avg_time * (360 - ch_num)
            s1 = result.get("scores", {}).get("S1", {}).get("score", 0)
            print(f"ch{ch_num:03d}: S1={s1}, Calls={total_calls}, Elapsed={elapsed/60:.1f}min, ETA={eta/60:.1f}min")

        # 每50章保存中间结果
        if ch_num % 50 == 0:
            temp_path = output_dir / f"temp_ch001-ch{ch_num:03d}.json"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"  -> 已保存中间结果: {temp_path}")

        time.sleep(0.3)  # 避免过快

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # ========== 生成报告 ==========
    print("\n" + "=" * 60)
    print("生成最终报告...")
    print("=" * 60)

    # 1. 完整结果
    full_path = output_dir / "all_chapters_review.json"
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # 2. 汇总统计
    summary = {
        "total_chapters": 360,
        "total_llm_calls": total_calls,
        "duration_minutes": duration / 60,
        "avg_calls_per_chapter": total_calls / 360,
        "issue_count_by_severity": {"P0": 0, "P1": 0, "P2": 0},
        "issue_count_by_dimension": {},
        "avg_scores": {},
        "chapters_with_issues": 0
    }

    score_sums = {f"S{i}": 0 for i in range(1, 9)}
    score_counts = {f"S{i}": 0 for i in range(1, 9)}

    for result in all_results:
        if result.get("issues"):
            summary["chapters_with_issues"] += 1

        for issue in result.get("issues", []):
            sev = issue.get("severity", "P2")
            if sev in summary["issue_count_by_severity"]:
                summary["issue_count_by_severity"][sev] += 1

            dim = issue.get("dimension", "其他")
            if dim not in summary["issue_count_by_dimension"]:
                summary["issue_count_by_dimension"][dim] = 0
            summary["issue_count_by_dimension"][dim] += 1

        for i in range(1, 9):
            score = result.get("scores", {}).get(f"S{i}", {}).get("score", 0)
            if isinstance(score, (int, float)) and score > 0:
                score_sums[f"S{i}"] += score
                score_counts[f"S{i}"] += 1

    for i in range(1, 9):
        if score_counts[f"S{i}"] > 0:
            summary["avg_scores"][f"S{i}"] = round(score_sums[f"S{i}"] / score_counts[f"S{i}"], 1)
        else:
            summary["avg_scores"][f"S{i}"] = 0

    summary_path = output_dir / "review_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 3. Markdown报告
    md = f"""# 星陨纪元 · MiniMax M2.7 全量检查报告

## 检查概览

| 项目 | 数据 |
|------|------|
| 检查章节 | 360章 |
| 总调用次数 | {total_calls} |
| 耗时 | {duration/60:.1f} 分钟 |
| 平均每章调用 | {total_calls/360:.1f} 次 |
| 有问题章节 | {summary['chapters_with_issues']}章 |

## 评分汇总

| 维度 | 平均分 | 说明 |
|------|--------|------|
"""

    dim_names = ["剧情完整性", "逻辑自洽", "文笔风格", "情感共鸣",
                 "节奏控制", "可读性", "主角魅力", "人物弧光"]
    for i in range(1, 9):
        md += f"| S{i} | {summary['avg_scores'].get(f'S{i}', 0):.1f} | {dim_names[i-1]} |\n"

    md += f"""
## 问题统计

### 按严重程度

| 严重程度 | 数量 |
|----------|------|
| P0（致命） | {summary['issue_count_by_severity'].get('P0', 0)} |
| P1（严重） | {summary['issue_count_by_severity'].get('P1', 0)} |
| P2（优化） | {summary['issue_count_by_severity'].get('P2', 0)} |

### 按维度

"""
    for dim, count in sorted(summary["issue_count_by_dimension"].items(), key=lambda x: -x[1]):
        md += f"- {dim}: {count}个问题\n"

    md += """
## P0/P1 重要问题列表

"""
    p1_issues = []
    for result in all_results:
        for issue in result.get("issues", []):
            if issue.get("severity") in ["P0", "P1"]:
                p1_issues.append({
                    "chapter": result.get("chapter"),
                    "dimension": issue.get("dimension"),
                    "type": issue.get("type"),
                    "description": issue.get("description", "")[:100]
                })

    for issue in p1_issues[:50]:
        md += f"- **{issue['chapter']}** [{issue['dimension']}] {issue['type']}: {issue['description']}\n"

    md_path = output_dir / "review_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    # 4. 调用统计
    stats_path = output_dir / "review_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration / 60,
            "total_calls": total_calls,
            "chapters_processed": 360
        }, f, ensure_ascii=False, indent=2)

    print("\n完成！")
    print(f"总调用: {total_calls}次")
    print("输出文件:")
    print(f"  - {full_path}")
    print(f"  - {summary_path}")
    print(f"  - {md_path}")


if __name__ == "__main__":
    run_full_review()
