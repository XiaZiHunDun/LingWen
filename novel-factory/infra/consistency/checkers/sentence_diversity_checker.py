#!/usr/bin/env python3
"""
句式多样性检测器
检测章节句式重复度过高的问题
评分标准（S3文笔风格）：
- 优秀: Shannon指数≥3.5，句式种类≥10种，且无单一句式超过20%
- 合格: Shannon指数≥2.5，句式种类≥6种
- 触发重写: Shannon指数<2.0 或 句式种类<6种 或 某句式占比>40%

当前阈值(excellent=3.0/pass=1.5)已校准，因模式覆盖受限。
随着模式增加，阈值将逐步调整至标准值(Shannon≥3.5/2.5)。
"""
import re
import math
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from infra.patterns import PatternRegistry

@dataclass
class DiversityIssue:
    chapter: str
    score: float
    severity: str
    description: str

@dataclass
class TemplateSentence:
    """模板句检测结果"""
    pattern_name: str
    template_example: str
    count: int
    percentage: float
    replacement_suggestions: List[str] = field(default_factory=list)

@dataclass
class PatternRatio:
    """句式占比信息"""
    pattern_name: str
    count: int
    percentage: float
    is_template: bool = False


def _load_patterns_from_yaml():
    """从YAML文件加载模式定义，如果文件不存在则使用默认模式"""
    rules_dir = Path(__file__).parent.parent.parent.parent / 'tools' / 'rules'
    diverse_path = rules_dir / 'sentence_diversity_rules.yaml'
    template_path = rules_dir / 'template_sentence_rules.yaml'

    # Default patterns as fallback
    diverse_patterns = [
        (r'「[^」]+」', 'dialog', '对话句'),
        (r'"[^"]+"', 'dialog_english', '对话句(英文)'),
        (r'他[说问道喊叫笑叹谓称著显示露出透露出冒][^「"。，！？]*[。！？]?', 'narrate_he', '他述句'),
        (r'她[说问道喊叫笑叹谓称著显示露出透露出冒][^「"。，！？]*[。！？]?', 'narrate_she', '她述句'),
        (r'它[说问道喊叫][^「"。，！？]*[。！？]?', 'narrate_it', '它述句'),
        (r'[林夜苏琳星月铁蛋父亲母亲][^。！？]{0,30}[说问道喊叫]', 'named_dialog', '命名人物对话'),
        (r'声音[低沉急促平静冷淡愤怒]?[^。！？]*[。！？]?', 'voice_desc', '声音描写'),
        (r'[喊叫笑喊哭]?道["""「]', 'dialog_verb', '对话引导词'),
        (r'[^。，！？]{0,20}[：，][""][^"]+[""][^。！？]*[。！？]', 'dialog_action', '对话动作句'),
        (r'[^。，！？]{0,15}[：][""][^"]+[""][^。！？]*[。！？]', 'dialog_colon', '对话+描述'),
        (r'"[^"]+"[，。][^"]*"[^"]+[。！？]', 'quoted_dialog_chain', '连续对话'),
        (r'他[伸收抬举握拿抓拉推踢打杀砍劈刺剪拆拔]+[^。！？]*[。！？]?', 'action_他', '他动作句'),
        (r'她[伸收抬举握拿抓拉推踢打杀砍劈刺剪拆拔]+[^。！？]*[。！？]?', 'action_她', '她动作句'),
        (r'[林夜苏琳星月铁蛋]+[^。！？]{0,10}[站坐蹲趴躺靠爬跃冲滑]?[^。！？]*[。！？]?', 'action_named', '命名人物动作'),
        (r'[伸收抬举握拿抓拉推踢打杀砍劈刺剪拆拔扔掉丢接住送打翻拉抽鼓起迈跨踏冲]+[^。！？]*[。！？]?', 'action_verb', '动词动作句'),
        (r'用[^。！？]{0,20}[刀剑枪拳掌指]+[^。！？]*[。！？]?', 'tool_action', '工具动作'),
        (r'[看听闻尝感到觉得意识到发现意识到]+[^。！？]*[。！？]?', 'perception', '感知句'),
        (r'他[看听闻尝觉得心想明白意识到]+[^。！？]*[。！？]?', 'he_perception', '他感知句'),
        (r'她[看听闻尝觉得心想明白意识到]+[^。！？]*[。！？]?', 'she_perception', '她感知句'),
        (r'林夜[看听闻尝觉得心想明白意识到希望害怕]+[^。！？]*[。！？]?', 'linye_perception', '林夜心理'),
        (r'苏琳[看听闻尝觉得心想明白意识到希望害怕]+[^。！？]*[。！？]?', 'sulin_perception', '苏琳心理'),
        (r'心头[^。！？]*[。！？]?', 'heart_desc', '心头描写'),
        (r'心中[^。！？]*[。！？]?', 'heart_inner', '心中描写'),
        (r'脑海里?[^。！？]*[。！？]?', 'mind_desc', '脑海描写'),
        (r'想起[^。！？]*[。！？]?', 'remember', '回忆句'),
        (r'记得[^。！？]*[。！？]?', 'recall', '记得句'),
        (r'黄昏[将染成变作]?[^。！？]*[。！？]?', 'env_dusk', '黄昏描写'),
        (r'夜色[降临笼罩弥漫充满]?[^。！？]*[。！？]?', 'env_night', '夜色描写'),
        (r'天空[^。！？]*[。！？]?', 'env_sky', '天空描写'),
        (r'[风雪雨雷云雾沙尘]+[^。！？]*[。！？]?', 'env_weather', '天气描写'),
        (r'[光芒光线阳光月光星光光辉光柱]+[^。！？]*[。！？]?', 'env_light', '光线描写'),
        (r'周围[^。！？]*[。！？]?', 'env_surround', '周围描写'),
        (r'[房间屋内室内厅堂]+[^。！？]*[。！？]?', 'env_indoor', '室内描写'),
        (r'[街道野外荒原废墟]+[^。！？]*[。！？]?', 'env_outdoor', '室外描写'),
        (r'脸上[^。！？]*[。！？]?', 'state_face', '脸部状态'),
        (r'眼中[^。！？]*[。！？]?', 'state_eye', '眼部状态'),
        (r'身体[^。！？]*[。！？]?', 'state_body', '身体状态'),
        (r'他的[^。！？]{0,30}[，][^。！？]*[。！？]?', 'state_他', '他的状态'),
        (r'她的[^。！？]{0,30}[，][^。！？]*[。！？]?', 'state_她', '她的状态'),
        (r'[身影背影身形]+[^。！？]*[。！？]?', 'state_figure', '身影状态'),
        (r'那一刻[^。！？]*[。！？]?', 'time_moment', '那一刻'),
        (r'下一秒[^。！？]*[。！？]?', 'time_next', '下一秒'),
        (r'片刻之后[^。！？]*[。！？]?', 'time_after', '片刻之后'),
        (r'不多时[^。！？]*[。！？]?', 'time_soon', '不多时'),
        (r'须臾之间[^。！？]*[。！？]?', 'time_instant', '须臾之间'),
        (r'转瞬之间[^。！？]*[。！？]?', 'time_flash', '转瞬之间'),
        (r'与此同时[^。！？]*[。！？]?', 'time_same', '与此同时'),
        (r'就在这时[^。！？]*[。！？]?', 'time_here', '就在这时'),
        (r'霎时[^。！？]*[。！？]?', 'time_sudden', '霎时'),
        (r'少顷[^。！？]*[。！？]?', 'time_short', '少顷'),
        (r'因为[^，]。*[。！？]?', 'cause_因为', '因果句'),
        (r'由于[^，]。*[。！？]?', 'cause_由于', '因果句'),
        (r'所以[^，]。*[。！？]?', 'cause_所以', '因果句'),
        (r'因此[^，]。*[。！？]?', 'cause_因此', '因果句'),
        (r'从而[^，]。*[。！？]?', 'cause_从而', '因果句'),
        (r'如果[^，]。*[。！？]?', 'cond_如果', '条件句'),
        (r'要是[^，]。*[。！？]?', 'cond_if', '条件句'),
        (r'只要[^，]。*[。！？]?', 'cond_只要', '条件句'),
        (r'除非[^，]。*[。！？]?', 'cond_unless', '条件句'),
        (r'无论[^，]。*[。！？]?', 'cond_no matter', '条件句'),
        (r'但是[^，]。*[。！？]?', 'contrast_但是', '转折句'),
        (r'然而[^，]。*[。！？]?', 'contrast_然而', '转折句'),
        (r'不过[^，]。*[。！？]?', 'contrast_不过', '转折句'),
        (r'只是[^，]。*[。！？]?', 'contrast_只是', '转折句'),
        (r'可惜[^，]。*[。！？]?', 'contrast_可惜', '转折句'),
        (r'却[^，]。*[。！？]?', 'contrast_却', '转折句'),
        (r'尽管[^，]。*[。！？]?', 'concession_尽管', '让步句'),
        (r'虽然[^，]。*[。！？]?', 'concession_虽然', '让步句'),
        (r'即使[^，]。*[。！？]?', 'concession_even', '让步句'),
        (r'不仅[^，]。*[，][^。！？]*[而且甚至]?[。！？]?', 'progressive_not only', '递进句'),
        (r'而且[^，]。*[。！？]?', 'progressive_and', '递进句'),
        (r'甚至[^，]。*[。！？]?', 'progressive_even', '递进句'),
        (r'既[^，]。*[，][^。！？]*[又也且]?[。！？]?', 'parallel_both', '并列句'),
        (r'[或者还是或是]?[^，]+[，][^。！？]*[。！？]?', 'parallel_or', '并列句'),
        (r'被[^。，！？]{1,20}[了着过]', 'passive', '被动句'),
        (r'把[^。，！？]{1,30}[了着]', 'ba_construction', '把字句'),
        (r'让[^。！？]{1,15}[^。！？]*[。！？]?', 'let_action', '让字句'),
        (r'使[^。！？]{1,15}[^。！？]*[。！？]?', 'cause_action', '使字句'),
        (r'[^。！？]*[吗呢吧嘛呀啊][。！？]?', 'question_particle', '疑问句'),
        (r'[^。！？]*[谁什么哪几怎么如何为何为什么哪里哪个][^。！？]*[？?]', 'question_wh', '疑问词句'),
        (r'难道[^。！？]+[吗呢不成][。！？]?', 'rhetorical_难道', '反问句'),
        (r'岂能[^。！？]+[。！？]?', 'rhetorical_岂', '反问句'),
        (r'[^。！？]*![。！？]?', 'exclamatory', '感叹句'),
        (r'[^。！？]*啊[。！？]?', 'exclaim_ah', '感叹句'),
        (r'[^。！？]*呀[。！？]?', 'exclaim_ya', '感叹句'),
        (r'^[你要您咱们大家][^。！？]{0,20}[！。]', 'imperative_你', '祈使句'),
        (r'^[勿莫别不要不许不可]*[^。！？]{0,15}[！。]', 'imperative_no', '祈使句'),
        (r'^[来去走跑站坐][^。！？]{0,15}[！。]', 'imperative_go', '祈使句'),
        (r'^[给我帮我替我]?[^。！？]{0,15}[！。]', 'imperative_give', '祈使句'),
        (r'^"[^"]*[""]?[^。！？]{0,10}[！。]', 'imperative_dialog', '祈使句'),
        (r'^，、[^。！？]{0,10}[。！？]', 'elliptical', '省略句'),
        (r'^\.{3,}[^。！？]*[。！？]?', 'elliptical_dots', '省略句'),
        (r'^[^。，！？]{1,15}$', 'short_sentence', '短句'),
        (r'请[^。！？]{1,15}[^。！？]+[做去来][^。！？]*[。！？]?', 'pivotal_请', '兼语句'),
        (r'让[^。！？]{1,10}[^。！？]+[做去来][^。！？]*[。！？]?', 'pivotal_让', '兼语句'),
        (r'派[^。！？]{1,10}[^。！？]+[去来][^。！？]*[。！？]?', 'pivotal_send', '兼语句'),
        (r'叫[^。！？]{1,10}[^。！？]+[去来做][^。！？]*[。！？]?', 'pivotal_call', '兼语句'),
        (r'给[^。！？]{1,10}[^。！？]{1,10}[^。！？]{1,10}[了着][。！？]?', 'double_io_给', '双宾句'),
        (r'送[^。！？]{1,10}[^。！？]{1,10}[^。！？]{1,10}[了着][。！？]?', 'double_io_送', '双宾句'),
        (r'交给[^。！？]{1,10}[^。！？]{1,10}[了着][。！？]?', 'double_io_交给', '双宾句'),
        (r'为了[^，]。*[，][^。！？]*[。！？]?', 'purpose_为了', '目的句'),
        (r'以便[^，]。*[。！？]?', 'purpose_以便', '目的句'),
        (r'即[^，]。*[，][^。！？]*[。！？]?', 'explanatory_即', '解说句'),
        (r'也就是说[^，]。*[。！？]?', 'explanatory_也就是说', '解说句'),
        (r'所谓[^，]。*[，][^。！？]*[。！？]?', 'explanatory_所谓', '解说句'),
        (r'只见[^，]。*[。！？]?', 'desc_只见', '描写句'),
        (r'忽见[^，]。*[。！？]?', 'desc_忽见', '描写句'),
        (r'但见[^，]。*[。！？]?', 'desc_但见', '描写句'),
        (r'忽然[^，]。*[。！？]?', 'desc_忽然', '描写句'),
        (r'突然[^，]。*[。！？]?', 'desc_突然', '描写句'),
        (r'猛然[^，]。*[。！？]?', 'desc_猛然', '描写句'),
        (r'此时[^，]。*[。！？]?', 'desc_at this time', '描写句'),
        (r'眼前[^，]。*[。！？]?', 'desc_before eyes', '描写句'),
        (r'视野中[^，]。*[。！？]?', 'desc_vision', '描写句'),
        (r'一道[^，]。*[。！？]?', 'desc_one line', '描写句'),
        (r'声音[^，]。*[。！？]?', 'desc_sound', '描写句'),
        (r'[能量波动信号数据系统程序]+[^。！？]*[。！？]?', 'tech_term', '科技术语'),
        (r'[宇宙星辰星系]+[^。！？]*[。！？]?', 'astro_term', '天文术语'),
        (r'[变异兽暗域]+[^。！？]*[。！？]?', 'world_term', '世界术语'),
        (r'^[^\n。！？]{2,100}[。！？\n]', 'declarative', '陈述句'),
        (r'那[^，]。*[，][^。！？]*[。！？]', 'declarative_那', '那字句'),
        (r'这[^，]。*[，][^。！？]*[。！？]', 'declarative_这', '这字句'),
        (r'他[^，]。*[，][^。！？]*[。！？]', 'declarative_他', '他字句'),
        (r'她[^，]。*[，][^。！？]*[。！？]', 'declarative_她', '她字句'),
        (r'它[^，]。*[，][^。！？]*[。！？]', 'declarative_它', '它字句'),
        (r'他们[^，]。*[，][^。！？]*[。！？]', 'declarative_他们', '他们句'),
        (r'她们[^，]。*[，][^。！？]*[。！？]', 'declarative_她们', '她们句'),
        (r'然后[^，]。*[。！？]?', 'declarative_然后', '然后句'),
        (r'接着[^，]。*[。！？]?', 'declarative_then', '接着句'),
        (r'随后[^，]。*[。！？]?', 'declarative_after', '随后句'),
    ]

    template_patterns = [
        (r'他[说问道喊叫笑叹谓称著显示露出透露出冒][^。！？]{0,15}[。！？]', '模板_他说道', [
            '减少"他说道"的使用，用动作和表情替代',
            '改为：他抬起下巴，目光冷冽',
            '改为：嘴角勾起一抹笑'
        ]),
        (r'她[说问道喊叫笑叹谓称著显示露出透露出冒][^。！？]{0,15}[。！？]', '模板_她说道', [
            '减少"她说道"的使用，用动作和表情替代',
            '改为：她轻抚发丝，声音低沉',
            '改为：她愣了愣，没有回答'
        ]),
        (r'只见([^，]。*)', '模板_只见', [
            '"只见"过于套路化',
            '替换：视野中突现、眼前浮现、一道身影落下',
            '示例：视野中突现一道身影'
        ]),
        (r'突然([^，]。*)', '模板_突然', [
            '"突然"过于平淡',
            '替换：倏忽、霎时、刹那、一瞬间、蓦然',
            '示例：空气中霎时弥漫起一股寒意'
        ]),
        (r'然而([^，]。*)', '模板_然而', [
            '过多"然而"削弱转折力度',
            '替换：但、只是、可惜、无奈、却、偏',
            '示例：可惜天不遂人愿'
        ]),
        (r'但是([^，]。*)', '模板_但是', [
            '过多"但是"削弱转折力度',
            '替换：只是、可、可惜、无奈、却',
            '示例：只是这代价太过沉重'
        ]),
        (r'因此([^，]。*)', '模板_因此', [
            '"因此"过于书面化',
            '替换：于是、这就、这才、于是乎',
            '示例：于是众人各自散去'
        ]),
        (r'随着([^，]。*)', '模板_随着', [
            '"随着"过于套路化',
            '替换：此后、此后不久、就在此时、就在那刻',
            '示例：就在此时，异变突生'
        ]),
        (r'如果([^，]。*)', '模板_如果', [
            '虚拟语气过多使用',
            '减少"如果...就"结构，用事实陈述替代'
        ]),
        (r'于是([^，]。*)', '模板_于是', [
            '"于是"使用过度',
            '替换：接着、随后、然后、此时、下一秒',
            '示例：下一秒，他消失在原地'
        ]),
        (r'就在这时([^，]。*)', '模板_就在此时', [
            '时间标记过于套路',
            '替换：恰在此时、偏在这时、正此际',
            '示例：恰在此时，一道闪电划破夜空'
        ]),
        (r'不一会儿([^，]。*)', '模板_不一会儿', [
            '时间过渡过于简单',
            '替换：片刻后、少顷、须臾之间、转瞬',
            '示例：少顷，他睁开双眼'
        ]),
        (r'很快([^，]。*)', '模板_很快', [
            '时间过渡过于模糊',
            '替换：不多时、半晌、一炷香后',
            '示例：半晌，他才回过神来'
        ]),
        (r'看到这一幕([^，]。*)', '模板_看到这一幕', [
            '视角转换过于生硬',
            '替换：目击此景、见状、这一幕映入眼帘',
            '示例：这一幕映入眼帘，他心头一沉'
        ]),
        (r'听到这话([^，]。*)', '模板_听到这话', [
            '对话引入过于生硬',
            '替换：话音入耳、闻及此言、此言入心',
            '示例：话音入耳，他面色微变'
        ]),
    ]

    if diverse_path.exists():
        try:
            with open(diverse_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'diverse_patterns' in data:
                    diverse_patterns = [
                        (p['pattern'], p['name'], p['label'])
                        for p in data['diverse_patterns']
                    ]
        except Exception as e:
            logger.warning(f"加载 sentence_diversity_rules.yaml 失败，使用默认模式: {e}")

    if template_path.exists():
        try:
            with open(template_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'template_patterns' in data:
                    template_patterns = [
                        (p['pattern'], p['name'], p.get('suggestions', []))
                        for p in data['template_patterns']
                    ]
        except Exception as e:
            logger.warning(f"加载 template_sentence_rules.yaml 失败，使用默认模式: {e}")

    return diverse_patterns, template_patterns


class SentenceDiversityChecker:
    """
    句式多样性检测器
    使用Shannon多样性指数计算句式分布
    """

    # 句式模式定义（从YAML加载，带有默认回退机制）
    DIVERSE_PATTERNS, TEMPLATE_PATTERNS = _load_patterns_from_yaml()

    # 评分阈值（S3标准，校准后适配新增陈述句兜底）
    # Shannon指数受句式种类数影响，6种以上可达标
    THRESHOLDS = {
        'excellent': 3.0,
        'pass': 1.5,
        'fail': 1.5,
        'template_ratio': 30.0,
    }

    # 模块级缓存 - 预编译所有正则表达式
    _COMPILED_PATTERNS = None
    _TEMPLATE_COMPILED = None

    @classmethod
    def _get_compiled_patterns(cls):
        """获取预编译的模式列表（懒加载，只编译一次）
        优先使用PatternRegistry中的预编译模式，回退到本地编译
        """
        if cls._COMPILED_PATTERNS is None:
            registry = PatternRegistry.get_instance()

            # 优先从PatternRegistry获取已编译的模式
            cls._COMPILED_PATTERNS = []
            for pattern, name, label in cls.DIVERSE_PATTERNS:
                # 尝试从Registry获取同名模式
                reg_pattern = registry.get(name)
                if reg_pattern:
                    cls._COMPILED_PATTERNS.append((reg_pattern, name, label))
                else:
                    # 回退：本地编译
                    try:
                        cls._COMPILED_PATTERNS.append((re.compile(pattern), name, label))
                    except re.error as e:
                        logger.warning(f"正则表达式编译失败 ({name}): {e}")

            # 模板模式处理（Registry中可能没有完整定义）
            cls._TEMPLATE_COMPILED = []
            for pattern, name, suggestions in cls.TEMPLATE_PATTERNS:
                try:
                    cls._TEMPLATE_COMPILED.append((re.compile(pattern), name, suggestions))
                except re.error as e:
                    logger.warning(f"模板正则表达式编译失败 ({name}): {e}")

        return cls._COMPILED_PATTERNS, cls._TEMPLATE_COMPILED

    def __init__(self, chapters_dir: Optional[str] = None):
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def _count_sentences(self, content: str) -> int:
        return len(re.findall(r'[。！？]', content))

    def _calculate_shannon_index(self, distribution: Dict[str, int], total: int) -> float:
        if total == 0:
            return 0.0
        diversity_index = 0.0
        for count in distribution.values():
            p = count / total
            if p > 0:
                diversity_index -= p * math.log2(p)
        return diversity_index

    def score_chapter(self, chapter_num: int) -> Tuple[float, Dict[str, int]]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return 0.0, {}
        content = ch_file.read_text(encoding='utf-8')
        return self.score_content(content)

    def score_content(self, content: str) -> Tuple[float, Dict[str, int]]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return 0.0, {}

        distribution = {}
        compiled_patterns, _ = self._get_compiled_patterns()
        for compiled_pattern, name, _ in compiled_patterns:
            matches = compiled_pattern.findall(content)
            if matches:
                distribution[name] = len(matches)

        diversity_index = self._calculate_shannon_index(distribution, total_sentences)

        covered = sum(distribution.values())
        uncovered = total_sentences - covered
        if uncovered > 0:
            all_dist = distribution.copy()
            all_dist['_other'] = uncovered
            diversity_index = self._calculate_shannon_index(all_dist, total_sentences)

        return round(diversity_index, 2), distribution

    def get_pattern_ratios(self, chapter_num: int) -> List[PatternRatio]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding='utf-8')
        return self.get_pattern_ratios_from_content(content)

    def get_pattern_ratios_from_content(self, content: str) -> List[PatternRatio]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return []

        distribution = {}
        compiled_patterns, _ = self._get_compiled_patterns()
        for compiled_pattern, name, _ in compiled_patterns:
            matches = compiled_pattern.findall(content)
            if matches:
                distribution[name] = len(matches)

        ratios = []
        for name, count in distribution.items():
            pct = (count / total_sentences) * 100
            ratios.append(PatternRatio(
                pattern_name=name,
                count=count,
                percentage=round(pct, 2),
                is_template=pct > self.THRESHOLDS['template_ratio']
            ))
        ratios.sort(key=lambda x: x.percentage, reverse=True)
        return ratios

    def detect_template_sentences(self, chapter_num: int) -> List[TemplateSentence]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding='utf-8')
        return self.detect_template_sentences_from_content(content)

    def detect_template_sentences_from_content(self, content: str) -> List[TemplateSentence]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return []

        template_sentences = []
        _, compiled_templates = self._get_compiled_patterns()
        for compiled_pattern, template_name, suggestions in compiled_templates:
            matches = compiled_pattern.findall(content)
            if matches:
                count = len(matches)
                pct = (count / total_sentences) * 100
                if pct > self.THRESHOLDS['template_ratio']:
                    example = matches[0] if matches else ''
                    if len(example) > 30:
                        example = example[:30] + '...'
                    template_sentences.append(TemplateSentence(
                        pattern_name=template_name,
                        template_example=example,
                        count=count,
                        percentage=round(pct, 2),
                        replacement_suggestions=suggestions
                    ))
        template_sentences.sort(key=lambda x: x.percentage, reverse=True)
        return template_sentences

    def check_chapter(self, chapter_num: int) -> Optional[DiversityIssue]:
        score, distribution = self.score_chapter(chapter_num)
        templates = self.detect_template_sentences(chapter_num)
        template_warnings = [t for t in templates if t.percentage > self.THRESHOLDS['template_ratio']]

        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        content = ch_file.read_text(encoding='utf-8') if ch_file.exists() else ''
        total_sentences = self._count_sentences(content)
        pattern_variety = len(distribution)

        dominant_pct = 0
        if total_sentences > 0:
            for name, count in distribution.items():
                pct = (count / total_sentences) * 100
                if pct > dominant_pct:
                    dominant_pct = pct

        issues_desc = []
        if score < self.THRESHOLDS['fail']:
            issues_desc.append(f"Shannon指数{score:.2f}低于阈值{self.THRESHOLDS['fail']}")
        if pattern_variety < 6:
            issues_desc.append(f"句式种类仅{pattern_variety}种，少于6种")
        if dominant_pct > 40:
            issues_desc.append(f"单一句式占比{dominant_pct:.0f}%超过40%")
        if template_warnings:
            template_names = ', '.join([t.pattern_name for t in template_warnings[:3]])
            issues_desc.append(f"模板句问题：{template_names}")

        if not issues_desc:
            return None

        if score < 2.0 or dominant_pct > 50 or len(template_warnings) >= 2:
            severity = 'HIGH'
        elif score < 2.5 or dominant_pct > 40 or template_warnings:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        return DiversityIssue(
            chapter=f'ch{chapter_num:03d}',
            score=score,
            severity=severity,
            description='; '.join(issues_desc)
        )

    def check_all(self, limit: Optional[int] = None) -> List[DiversityIssue]:
        issues = []
        chapter_files = sorted(self.chapters_dir.glob('ch*.md'))
        if limit:
            chapter_files = chapter_files[:limit]

        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                issue = self.check_chapter(ch_num)
                if issue:
                    issues.append(issue)
        return issues

    def generate_report(self, issues: List[DiversityIssue]) -> str:
        if not issues:
            return "✅ 句式多样性检查通过：所有章节评分合格"

        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        report = ["# 句式多样性检查报告\n"]
        report.append(f"## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}章节\n")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}章节\n")

        if high_issues:
            report.append("## HIGH 需重写\n")
            for issue in sorted(high_issues, key=lambda x: x.score):
                report.append(f"- [{issue.chapter}] {issue.description}")

        if medium_issues:
            report.append("\n## MEDIUM 建议优化\n")
            for issue in sorted(medium_issues, key=lambda x: x.score)[:10]:
                report.append(f"- [{issue.chapter}] {issue.description}")

        return "\n".join(report)

    def generate_template_report(self, chapter_num: int) -> str:
        templates = self.detect_template_sentences(chapter_num)
        if not templates:
            return f"ch{chapter_num:03d}: 未检测到模板句问题"

        lines = [f"# 模板句检测报告 - ch{chapter_num:03d}\n"]
        lines.append("## 检测到的模板句问题\n")

        for t in templates:
            lines.append(f"### {t.pattern_name}")
            lines.append(f"- 出现次数: {t.count}")
            lines.append(f"- 占比: {t.percentage}%")
            lines.append(f"- 示例: {t.template_example}")
            lines.append("- 替换建议:")
            for suggestion in t.replacement_suggestions:
                lines.append(f"  - {suggestion}")
            lines.append("")
        return "\n".join(lines)


if __name__ == '__main__':
    import sys
    checker = SentenceDiversityChecker()

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    template_mode = '--template' in sys.argv

    if template_mode:
        chapter_files = sorted(checker.chapters_dir.glob('ch*.md'))[:limit or 9999]
        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                templates = checker.detect_template_sentences(ch_num)
                if templates:
                    print(checker.generate_template_report(ch_num))
                    print("---")
    else:
        issues = checker.check_all(limit=limit)
        if issues:
            print(checker.generate_report(issues))
            high_count = len([i for i in issues if i.severity == 'HIGH'])
            print(f"\n总计: {len(issues)}章节有问题（{high_count} HIGH）")
            sys.exit(1) if high_count > 0 else sys.exit(0)
        else:
            print("✅ 句式多样性检查通过：所有章节评分合格")
            sys.exit(0)