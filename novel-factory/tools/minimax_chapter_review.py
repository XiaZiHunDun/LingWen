#!/usr/bin/env python3
"""
MiniMax M2.7 章节检查脚本 - 试点30章

使用 MiniMax M2.7 模型对星陨纪元前30章进行全面质量检查
每章约17次调用，总计约500次调用

检查维度：S1-S8 + 一致性 + 伏笔 + AI痕迹
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.ai_service import MiniMaxProvider, ProviderConfig


class ChapterReviewer:
    """章节审查器 - 使用MiniMax M2.7进行检查"""

    def __init__(self, api_key: str, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        config = ProviderConfig(api_key=api_key)
        self.provider = MiniMaxProvider(config)

        # 角色档案
        self.characters = self._load_character_profiles()
        self.outline = self._load_outline()

    def _load_character_profiles(self) -> Dict:
        """加载角色档案"""
        profile_path = Path(__file__).parent.parent / "03_内容仓库/角色设定/character_profiles.json"
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                characters = {c["name"]: c for c in data.get("characters", [])}
                return characters
        except Exception as e:
            print(f"Warning: Cannot load character profiles: {e}")
            return {}

    def _load_outline(self) -> str:
        """加载全局大纲"""
        outline_path = Path(__file__).parent.parent / "03_内容仓库/01_全文总体大纲/全局大纲.md"
        try:
            with open(outline_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Cannot load outline: {e}")
            return ""

    def _load_chapter(self, chapter_num: int) -> Optional[str]:
        """加载章节内容"""
        chapter_file = Path(__file__).parent.parent / f"03_内容仓库/04_正文/ch{chapter_num:03d}.md"
        try:
            with open(chapter_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error: Cannot load chapter {chapter_num}: {e}")
            return None

    def _call_llm(self, prompt: str, system: Optional[str] = None, max_tokens: int = 2048) -> str:
        """调用MiniMax LLM"""
        try:
            response = self.provider.generate(
                prompt=prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response
        except Exception as e:
            print(f"LLM call error: {e}")
            return f"ERROR: {str(e)}"

    def _safe_json(self, response: str, default: Any = None) -> Any:
        """安全解析JSON"""
        try:
            # 尝试清理响应
            text = response.strip()
            # 移除可能的markdown代码块 ```json ... ```
            if text.startswith("```"):
                # 格式: ```json\n{...}\n```
                # parts[0]='', parts[1]='json\n{...}\n', parts[2]=''
                parts = text.split("```")
                if len(parts) >= 2:
                    # parts[1]包含"json\n"前缀和JSON内容
                    text = parts[1]
                    # 移除开头的 "json\n" 或 "json" 部分
                    if text.startswith("json"):
                        text = text[4:].lstrip("\n")
                text = text.strip()
            return json.loads(text)
        except Exception:
            return default if default is not None else {}

    def check_chapter(self, chapter_num: int) -> Dict[str, Any]:
        """检查单个章节，返回问题和评分"""
        chapter_content = self._load_chapter(chapter_num)
        if not chapter_content:
            return {"chapter": f"ch{chapter_num:03d}", "error": "Cannot load chapter", "llm_calls": 0}

        chapter_id = f"ch{chapter_num:03d}"
        result = {
            "chapter": chapter_id,
            "llm_calls": 0,
            "scores": {},
            "issues": []
        }

        call_count = 0

        # ========== S1-S8 基础评分 ==========

        # S1 剧情完整性
        s1_prompt = f"""你是小说质量审核官。请对以下章节进行S1剧情完整性评分。

评分标准：
- S1剧情完整性：故事是否有开头、过程、结尾？情节是否连贯？是否有逻辑断裂？

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和comment字段。"""

        response = self._call_llm(s1_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S1"] = {"score": data.get("score", 0), "comment": data.get("comment", "")}

        # S2 逻辑自洽
        s2_prompt = f"""你是小说质量审核官。请对以下章节进行S2逻辑自洽检查。

检查要点：
- 事实是否一致？（如：前一秒说"A在左边"，后一秒说"A在右边"）
- 角色行为是否合理？
- 是否有明显矛盾？

角色设定：
{json.dumps(self.characters, ensure_ascii=False)[:2000]}

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和issues数组。issues中每项包含type、location、desc。"""

        response = self._call_llm(s2_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S2"] = {"score": data.get("score", 0)}
        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                result["issues"].append({
                    "severity": "P1",
                    "dimension": "S2",
                    "type": issue.get("type", "逻辑矛盾"),
                    "description": issue.get("desc", ""),
                    "location": issue.get("location", "")
                })

        # S3 文笔风格
        s3_prompt = f"""你是小说质量审核官。请对以下章节进行S3文笔风格检查。

检查要点：
- 句式是否多样化？（避免"首先...其次...最后"等套路）
- 用词是否精准？
- 描写是否生动？

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和issues数组。"""

        response = self._call_llm(s3_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S3"] = {"score": data.get("score", 0)}
        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                result["issues"].append({
                    "severity": "P2",
                    "dimension": "S3",
                    "type": issue.get("type", "句式问题"),
                    "description": issue.get("desc", ""),
                    "location": issue.get("location", "")
                })

        # S4 情感共鸣
        s4_prompt = f"""你是小说质量审核官。请对以下章节进行S4情感共鸣检查。

检查要点：
- 情感表达是否真挚？
- 能否引起读者共鸣？
- 人物情感是否真实可信？

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和comment字段。"""

        response = self._call_llm(s4_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S4"] = {"score": data.get("score", 0), "comment": data.get("comment", "")}

        # S5 节奏控制
        s5_prompt = f"""你是小说质量审核官。请对以下章节进行S5节奏控制检查。

检查要点：
- 是否有高潮/低谷分布？
- 节奏是否张弛有度？
- 是否存在拖沓或仓促？

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和comment字段。"""

        response = self._call_llm(s5_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S5"] = {"score": data.get("score", 0), "comment": data.get("comment", "")}

        # S6 可读性
        s6_prompt = f"""你是小说质量审核官。请对以下章节进行S6可读性评估。

检查要点：
- 语言是否流畅？
- 是否有阅读障碍？
- 段落结构是否合理？

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和comment字段。"""

        response = self._call_llm(s6_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S6"] = {"score": data.get("score", 0), "comment": data.get("comment", "")}

        # S7 主角魅力
        s7_prompt = f"""你是小说质量审核官。请对以下章节进行S7主角魅力检查。

主角信息：
- 林夜：废土少年，冷静坚强，热血果断
- 苏琳：林夜青梅竹马，温柔智慧，有预言能力

检查要点：
- 主角表现是否有魅力？
- 主角决策是否令人信服？
- 主角是否有成长展现？

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和comment字段。"""

        response = self._call_llm(s7_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S7"] = {"score": data.get("score", 0), "comment": data.get("comment", "")}

        # S8 人物弧光
        s8_prompt = f"""你是小说质量审核官。请对以下章节进行S8人物弧光检查。

检查要点：
- 人物是否有成长/变化？
- 人物决策是否有内在驱动力？
- 人物弧光是否合理？

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含score和comment字段。"""

        response = self._call_llm(s8_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["scores"]["S8"] = {"score": data.get("score", 0), "comment": data.get("comment", "")}

        # ========== 角色一致性检查 ==========
        char_check_prompt = f"""你是角色一致性审查官。请检查以下章节中的人物表现是否与角色设定一致。

角色设定：
{json.dumps(self.characters, ensure_ascii=False)[:3000]}

章节：{chapter_id}
内容：
{chapter_content[:4000]}

请返回JSON格式，包含issues数组，每项包含character、type、location、desc。"""

        response = self._call_llm(char_check_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                result["issues"].append({
                    "severity": "P1",
                    "dimension": "一致性",
                    "type": f"角色不一致-{issue.get('character', '')}",
                    "description": f"{issue.get('character', '')}: {issue.get('desc', '')}",
                    "location": issue.get("location", "")
                })

        # ========== 世界观一致性 ==========
        world_check_prompt = f"""你是世界观一致性审查官。请检查以下章节中的设定是否与大綱一致。

大綱设定（境界体系）：
- 粒子境、星火境、脉冲境、裂变境（第一卷）
- 黑洞境（第二卷）
- 创世境、永恒境（第三卷）

势力：星辰会、玄机阁、万剑宗、灵兽谷、暗域、星际修真联盟

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含issues数组，每项包含type、location、desc。"""

        response = self._call_llm(world_check_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                result["issues"].append({
                    "severity": "P1",
                    "dimension": "世界观",
                    "type": issue.get("type", "设定冲突"),
                    "description": issue.get("desc", ""),
                    "location": issue.get("location", "")
                })

        # ========== 伏笔回收检查 ==========
        foreshadow_prompt = f"""你是伏笔审查官。请检查以下章节中的伏笔是否有效回收。

已知伏笔：
- ch001: 林夜父母被杀害（可能在结局回收）
- ch024: 父亲临终前注入能量（需在后续回收）

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含foreshadows数组，每项包含type、status、desc。status为"已回收"、"未回收"或"新伏笔"。"""

        response = self._call_llm(foreshadow_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        for fs in data.get("foreshadows", []):
            if isinstance(fs, dict) and fs.get("status") == "未回收":
                result["issues"].append({
                    "severity": "P2",
                    "dimension": "伏笔",
                    "type": f"伏笔未回收-{fs.get('type', '')}",
                    "description": fs.get("desc", ""),
                    "location": ""
                })

        # ========== AI痕迹检测 ==========
        ai_prompt = f"""你是AI痕迹检测专家。请检查以下章节是否存在AI创作痕迹。

常见AI痕迹：
1. 套路句式："首先...其次...最后"、"值得注意的是"、"毫无疑问"
2. 模板结构：每个段落都以相似结构开头
3. 过度解释：事无巨细地解释每一个动作
4. 缺乏质感：描写过于完美/机械

章节：{chapter_id}
内容：
{chapter_content[:3000]}

请返回JSON格式，包含issues数组，每项包含type、location、desc。"""

        response = self._call_llm(ai_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        for issue in data.get("issues", []):
            if isinstance(issue, dict):
                issue_type = issue.get("type", "")
                if "套路" in issue_type:
                    issue_type = "套路句式"
                result["issues"].append({
                    "severity": "P2",
                    "dimension": "AI痕迹",
                    "type": issue_type,
                    "description": issue.get("desc", ""),
                    "location": issue.get("location", "")
                })

        # ========== 综合评分 ==========
        overall_prompt = f"""请对以下章节进行综合评分和总结。

章节：{chapter_id}
内容：
{chapter_content[:2000]}

请返回JSON格式，包含overall_score（0-10）、summary（一段话总结）、top_issues（最重要的问题数组，最多2个）。"""

        response = self._call_llm(overall_prompt)
        call_count += 1
        data = self._safe_json(response, {})
        result["overall_score"] = data.get("overall_score", 0)
        result["summary"] = data.get("summary", "")
        result["top_issues"] = data.get("top_issues", [])

        result["llm_calls"] = call_count

        return result


def main():
    """主函数 - 执行30章试点检查"""
    print("=" * 60)
    print("MiniMax M2.7 章节检查 - 试点30章")
    print("=" * 60)

    # API Key
    api_key = os.getenv("MINIMAX_API_KEY", "")
    if not api_key:
        print("Error: MINIMAX_API_KEY not set")
        print("请设置环境变量: export MINIMAX_API_KEY=your_key")
        return

    output_dir = Path(__file__).parent
    reviewer = ChapterReviewer(api_key, str(output_dir))

    # 检查章范围
    start_ch = 1
    end_ch = 30

    all_results = []
    total_calls = 0
    start_time = datetime.now()

    print(f"\n开始检查 ch{start_ch:03d} - ch{end_ch:03d}")
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    for ch_num in range(start_ch, end_ch + 1):
        print(f"\n检查 ch{ch_num:03d}...", end=" ", flush=True)
        result = reviewer.check_chapter(ch_num)
        all_results.append(result)
        total_calls += result.get("llm_calls", 0)

        # 打印简要结果
        issues_count = len(result.get("issues", []))
        score_s1 = result.get("scores", {}).get("S1", {}).get("score", "N/A")
        print(f"S1={score_s1}, Issues={issues_count}, Calls={result.get('llm_calls', 0)}")

        # 避免过于频繁
        time.sleep(0.5)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # ========== 生成报告 ==========
    print("\n" + "=" * 60)
    print("生成报告...")
    print("=" * 60)

    # 1. 详细问题报告
    report_path = output_dir / "ch001-ch030_问题报告.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"问题报告: {report_path}")

    # 2. 汇总统计
    summary = {
        "total_chapters": end_ch - start_ch + 1,
        "total_llm_calls": total_calls,
        "duration_seconds": duration,
        "avg_calls_per_chapter": total_calls / (end_ch - start_ch + 1),
        "issue_count_by_severity": {"P0": 0, "P1": 0, "P2": 0},
        "issue_count_by_dimension": {},
        "avg_scores": {}
    }

    for result in all_results:
        for issue in result.get("issues", []):
            sev = issue.get("severity", "P2")
            if sev in summary["issue_count_by_severity"]:
                summary["issue_count_by_severity"][sev] += 1

            dim = issue.get("dimension", "其他")
            if dim not in summary["issue_count_by_dimension"]:
                summary["issue_count_by_dimension"][dim] = 0
            summary["issue_count_by_dimension"][dim] += 1

        for dim, score_data in result.get("scores", {}).items():
            if dim not in summary["avg_scores"]:
                summary["avg_scores"][dim] = {"total": 0, "count": 0}
            s = score_data.get("score", 0)
            if isinstance(s, (int, float)):
                summary["avg_scores"][dim]["total"] += s
                summary["avg_scores"][dim]["count"] += 1

    # 计算平均分
    for dim in summary["avg_scores"]:
        data = summary["avg_scores"][dim]
        if data["count"] > 0:
            summary["avg_scores"][dim] = round(data["total"] / data["count"], 2)
        else:
            summary["avg_scores"][dim] = 0

    summary_path = output_dir / "ch001-ch030_评分汇总.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"评分汇总: {summary_path}")

    # 3. Markdown报告
    md_content = f"""# 星陨纪元 · MiniMax M2.7 检查报告（试点30章）

## 检查概览

| 项目 | 数据 |
|------|------|
| 检查章节 | ch001 - ch030 |
| 总调用次数 | {total_calls} |
| 耗时 | {duration/60:.1f} 分钟 |
| 平均每章调用 | {total_calls/30:.1f} 次 |

## 评分汇总

| 维度 | 平均分 | 说明 |
|------|--------|------|
"""

    for dim in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]:
        score = summary["avg_scores"].get(dim, 0)
        desc = {
            "S1": "剧情完整性", "S2": "逻辑自洽", "S3": "文笔风格",
            "S4": "情感共鸣", "S5": "节奏控制", "S6": "可读性",
            "S7": "主角魅力", "S8": "人物弧光"
        }.get(dim, dim)
        md_content += f"| {dim} | {score:.1f} | {desc} |\n"

    md_content += f"""
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
        md_content += f"- {dim}: {count}个问题\n"

    md_content += f"""
## 详细问题

"""
    for result in all_results:
        ch = result.get("chapter", "")
        issues = result.get("issues", [])
        if issues:
            md_content += f"\n### {ch}\n\n"
            for issue in issues[:5]:  # 每章最多5个问题
                md_content += f"- **[{issue.get('severity', 'P2')}][{issue.get('dimension', '其他')}]** {issue.get('type', '问题')}: {issue.get('description', '')[:100]}\n"

    md_report_path = output_dir / "ch001-ch030_汇总报告.md"
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"汇总报告: {md_report_path}")

    # 4. 调用统计
    stats = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration,
        "total_calls": total_calls,
        "chapters_processed": end_ch - start_ch + 1
    }
    stats_path = output_dir / "调用统计.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"调用统计: {stats_path}")

    print("\n" + "=" * 60)
    print("试点完成！")
    print("=" * 60)
    print(f"总调用: {total_calls}次 / 500次预算")
    print(f"输出文件:")
    print(f"  - {report_path}")
    print(f"  - {summary_path}")
    print(f"  - {md_report_path}")


if __name__ == "__main__":
    main()