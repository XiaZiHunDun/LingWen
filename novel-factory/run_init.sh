#!/bin/bash
#===============================================================================
# 灵文 · 新项目初始化脚本
# 用法: ./run_init.sh <项目名> <章节数> [卷数]
# 示例: ./run_init.sh 星陨纪元 360 3
#       ./run_init.sh 新书名 100 2
#
# v1.4 增加：方法论文档验证 + 模板库初始化 + methodology_markers
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
WORKFLOW_FILE="$PROJECT_ROOT/workflow_state.json"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

#-------------------------------------------------------------------------------
# 帮助信息
#-------------------------------------------------------------------------------
show_help() {
    cat << EOF
${GREEN}灵文 · 新项目初始化脚本${NC}

${YELLOW}用法:${NC}
    ./run_init.sh <项目名> <章节数> [卷数]

${YELLOW}参数:${NC}
    项目名     - 小说名称（如：星陨纪元）
    章节数     - 总章节数（如：360）
    卷数       - 卷数，默认为3（如：3）

${YELLOW}示例:${NC}
    ./run_init.sh 星陨纪元 360 3
    ./run_init.sh 新书名 100 2

${YELLOW}功能:${NC}
    1. 验证方法论文档（11_方法论/）
    2. 验证模板库（01_灵感库/模板库/）
    3. 创建项目文件夹结构
    4. 初始化 workflow_state.json（含methodology_markers）
    5. 生成各层 index.json
    6. 生成项目立项模板文件
    7. 更新主控记忆

EOF
}

#-------------------------------------------------------------------------------
# 检查参数
#-------------------------------------------------------------------------------
check_args() {
    if [ $# -lt 2 ]; then
        echo -e "${RED}错误: 参数不足${NC}"
        echo "用法: ./run_init.sh <项目名> <章节数> [卷数]"
        echo "示例: ./run_init.sh 星陨纪元 360 3"
        exit 1
    fi

    PROJECT_NAME="$1"
    CHAPTER_COUNT="$2"
    VOLUME_COUNT="${3:-3}"

    # 验证章节数为数字
    if ! [[ "$CHAPTER_COUNT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 章节数必须是数字${NC}"
        exit 1
    fi

    # 验证卷数为数字
    if ! [[ "$VOLUME_COUNT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: 卷数必须是数字${NC}"
        exit 1
    fi

    echo -e "${BLUE}项目信息:${NC}"
    echo "  项目名称: $PROJECT_NAME"
    echo "  章节数: $CHAPTER_COUNT"
    echo "  卷数: $VOLUME_COUNT"
    echo ""
}

#-------------------------------------------------------------------------------
# 验证方法论文档（新增 v1.4）
#-------------------------------------------------------------------------------
verify_methodology() {
    echo -e "${YELLOW}[1/7] 验证方法论文档...${NC}"

    local required_docs=(
        "11_方法论/PART0_总纲/00_总纲.md"
        "11_方法论/PART1_创作方法论/01_灵感捕捉与筛选.md"
        "11_方法论/PART1_创作方法论/02_核心三要素.md"
        "11_方法论/PART1_创作方法论/03_世界观与设定.md"
        "11_方法论/PART1_创作方法论/04_人物塑造体系.md"
        "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
        "11_方法论/PART1_创作方法论/06_初稿写作.md"
        "11_方法论/PART1_创作方法论/07_修改打磨.md"
        "11_方法论/PART1_创作方法论/08_定稿发布.md"
        "11_方法论/PART0_总纲/xx_术语表.md"
    )

    local missing_docs=()
    for doc in "${required_docs[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$doc" ]; then
            missing_docs+=("$doc")
        fi
    done

    if [ ${#missing_docs[@]} -gt 0 ]; then
        echo -e "${RED}  错误: 缺少方法论文档:${NC}"
        for doc in "${missing_docs[@]}"; do
            echo "    - $doc"
        done
        echo ""
        echo -e "${YELLOW}  请检查方法论文档是否在 11_方法论/ 目录${NC}"
        exit 1
    fi

    echo -e "${GREEN}  ✓ 方法论文档验证通过（${#required_docs[@]}份）${NC}"
}

#-------------------------------------------------------------------------------
# 验证模板库（新增 v1.4）
#-------------------------------------------------------------------------------
verify_template_library() {
    echo -e "${YELLOW}[2/7] 验证模板库...${NC}"

    local required_templates=(
        "01_灵感库/模板库/灵感筛选流程.md"
        "01_灵感库/模板库/核心三要素.yaml"
        "01_灵感库/模板库/世界观设定.yaml"
        "01_灵感库/模板库/人物弧光设计.yaml"
        "01_灵感库/模板库/基础层.yaml"
    )

    local missing_templates=()
    for tmpl in "${required_templates[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$tmpl" ]; then
            missing_templates+=("$tmpl")
        fi
    done

    if [ ${#missing_templates[@]} -gt 0 ]; then
        echo -e "${RED}  错误: 缺少模板文件:${NC}"
        for tmpl in "${missing_templates[@]}"; do
            echo "    - $tmpl"
        done
        exit 1
    fi

    echo -e "${GREEN}  ✓ 模板库验证通过（${#required_templates[@]}份）${NC}"
}

#-------------------------------------------------------------------------------
# 创建目录结构
#-------------------------------------------------------------------------------
create_dirs() {
    echo -e "${YELLOW}[3/7] 创建目录结构...${NC}"

    # 项目文件夹
    mkdir -p "$PROJECT_ROOT/01_灵感库/$PROJECT_NAME"
    mkdir -p "$PROJECT_ROOT/01_灵感库/$PROJECT_NAME/立项"
    mkdir -p "$PROJECT_ROOT/01_灵感库/$PROJECT_NAME/人物弧光"

    # 各卷文件夹
    for i in $(seq 1 $VOLUME_COUNT); do
        mkdir -p "$PROJECT_ROOT/03_内容仓库/02_卷大纲/卷$i"
        mkdir -p "$PROJECT_ROOT/03_内容仓库/03_阶段大纲/卷$i"
        mkdir -p "$PROJECT_ROOT/03_内容仓库/04_正文/卷$i"
    done

    mkdir -p "$PROJECT_ROOT/06_意见仓库/01_全文大纲_审核"
    mkdir -p "$PROJECT_ROOT/06_意见仓库/02_卷大纲_审核"
    mkdir -p "$PROJECT_ROOT/06_意见仓库/03_阶段大纲_审核"
    mkdir -p "$PROJECT_ROOT/06_意见仓库/04_正文_审核"
    mkdir -p "$PROJECT_ROOT/06_意见仓库/04_作家修改"
    mkdir -p "$PROJECT_ROOT/06_意见仓库/05_读者评论"
    mkdir -p "$PROJECT_ROOT/06_意见仓库/06_汇总_审核"
    mkdir -p "$PROJECT_ROOT/06_意见仓库/情感审核"

    mkdir -p "$PROJECT_ROOT/07_汇总仓库/汇总主笔"
    mkdir -p "$PROJECT_ROOT/07_汇总仓库/汇总编辑"
    mkdir -p "$PROJECT_ROOT/07_汇总仓库/汇总校验"

    mkdir -p "$PROJECT_ROOT/08_已发布"

    echo -e "${GREEN}  目录结构创建完成${NC}"
}

#-------------------------------------------------------------------------------
# 初始化 workflow_state.json（含 methodology_markers v1.4）
#-------------------------------------------------------------------------------
init_workflow_state() {
    echo -e "${YELLOW}[4/7] 初始化 workflow_state.json...${NC}"

    if [ -f "$WORKFLOW_FILE" ]; then
        echo -e "${YELLOW}  备份现有 workflow_state.json → workflow_state.json.bak${NC}"
        cp "$WORKFLOW_FILE" "$WORKFLOW_FILE.bak"
    fi

    # 生成 chapters 数组
    chapters_json=""
    for i in $(seq 1 $CHAPTER_COUNT); do
        ch_num=$(printf "%03d" $i)
        chapters_json="$chapters_json\"ch$ch_num\", "
    done
    chapters_json="${chapters_json%, }"

    cat > "$WORKFLOW_FILE" << EOF
{
    "version": "v1.4",
    "project_info": {
        "project_name": "$PROJECT_NAME",
        "total_chapters": $CHAPTER_COUNT,
        "volume_count": $VOLUME_COUNT,
        "chapters_per_volume": $(($CHAPTER_COUNT / $VOLUME_COUNT)),
        "created_at": "$(date +%Y-%m-%d)",
        "framework_version": "v1.4"
    },
    "current_phase": "PHASE_1_LAUNCH",
    "current_step": "STEP_01",
    "methodology_version": "1.0",
    "phases": {
        "PHASE_0_SETUP": {
            "status": "completed",
            "steps": {
                "SETUP_00": {
                    "status": "completed",
                    "name": "初始化",
                    "methodology_markers": {
                        "stage": "阶段0: 灵感捕捉与筛选",
                        "doc": "11_方法论/PART1_创作方法论/01_灵感捕捉与筛选.md"
                    }
                }
            }
        },
        "PHASE_1_LAUNCH": {
            "status": "pending",
            "steps": {
                "STEP_01": {
                    "status": "pending",
                    "name": "灵感生成",
                    "methodology_markers": {
                        "stage": "阶段0: 灵感捕捉与筛选",
                        "doc": "11_方法论/PART1_创作方法论/01_灵感捕捉与筛选.md",
                        "output_template": "01_灵感库/模板库/基础层.yaml",
                        "screening_required": true
                    }
                },
                "STEP_02": {
                    "status": "pending",
                    "name": "全文大纲初稿",
                    "methodology_markers": {
                        "stage": "阶段1-3: 核心三要素/世界观/大纲结构",
                        "doc": "11_方法论/PART1_创作方法论/02_核心三要素.md, 03_世界观与设定.md, 05_大纲结构设计.md",
                        "output_template": "01_灵感库/{项目}/立项/00_核心三要素.yaml"
                    }
                }
            }
        },
        "PHASE_2_OUTLINE": {
            "status": "pending",
            "steps": {
                "STEP_03": {
                    "status": "pending",
                    "name": "全文大纲审核",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md",
                        "review_checklist": "三幕式8节点结构检查"
                    }
                },
                "STEP_04": {
                    "status": "pending",
                    "name": "全文大纲修改",
                    "methodology_markers": {
                        "stage": "阶段5: 修改打磨 - 第一轮宏观",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_05": {
                    "status": "pending",
                    "name": "全文大纲终审",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
                    }
                }
            }
        },
        "PHASE_3_VOLUME": {
            "status": "pending",
            "steps": {
                "STEP_06": {
                    "status": "pending",
                    "name": "卷大纲生成",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计 - 章纲",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md",
                        "structure_template": "8节点大纲"
                    }
                },
                "STEP_07": {
                    "status": "pending",
                    "name": "卷大纲审核",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
                    }
                },
                "STEP_08": {
                    "status": "pending",
                    "name": "卷大纲修改",
                    "methodology_markers": {
                        "stage": "阶段5: 修改打磨 - 第一轮宏观",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_09": {
                    "status": "pending",
                    "name": "卷大纲终审",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
                    }
                }
            }
        },
        "PHASE_4_STAGE": {
            "status": "pending",
            "steps": {
                "STEP_10": {
                    "status": "pending",
                    "name": "阶段大纲生成",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计 - 章纲写法",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md",
                        "chapter_outline_format": "本章目标+出场人物+剧情走向+情绪落点+留钩子"
                    }
                },
                "STEP_11": {
                    "status": "pending",
                    "name": "阶段大纲审核",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
                    }
                },
                "STEP_12": {
                    "status": "pending",
                    "name": "阶段大纲修改",
                    "methodology_markers": {
                        "stage": "阶段5: 修改打磨 - 第一轮宏观",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_13": {
                    "status": "pending",
                    "name": "阶段大纲终审",
                    "methodology_markers": {
                        "stage": "阶段3: 大纲结构设计",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
                    }
                }
            }
        },
        "PHASE_5_BODY": {
            "status": "pending",
            "steps": {
                "STEP_14": {
                    "status": "pending",
                    "name": "正文创作",
                    "methodology_markers": {
                        "stage": "阶段4: 初稿写作",
                        "doc": "11_方法论/PART1_创作方法论/06_初稿写作.md",
                        "writing_rules": "先完成再完美/不回读修改/卡住跳过"
                    }
                },
                "STEP_15": {
                    "status": "pending",
                    "name": "读者评论",
                    "methodology_markers": {
                        "stage": "阶段4: 初稿写作 - 读者视角",
                        "doc": "11_方法论/PART1_创作方法论/06_初稿写作.md"
                    }
                },
                "STEP_16": {
                    "status": "pending",
                    "name": "正文审核",
                    "methodology_markers": {
                        "stage": "阶段5: 修改打磨 - 三轮修改",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md",
                        "review_order": "宏观→中观→微观"
                    }
                },
                "STEP_17": {
                    "status": "pending",
                    "name": "正文修改",
                    "methodology_markers": {
                        "stage": "阶段5: 修改打磨 - 对应轮次",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_18": {
                    "status": "pending",
                    "name": "正文定稿",
                    "methodology_markers": {
                        "stage": "阶段5-6: 修改打磨+定稿发布",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md, 08_定稿发布.md"
                    }
                }
            }
        },
        "PHASE_6_SUMMARY": {
            "status": "pending",
            "steps": {
                "STEP_19": {
                    "status": "pending",
                    "name": "阶段汇总",
                    "methodology_markers": {
                        "stage": "阶段3-5: 伏笔回收+弧光完整性",
                        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md, 04_人物塑造体系.md"
                    }
                },
                "STEP_20": {
                    "status": "pending",
                    "name": "阶段汇总审核",
                    "methodology_markers": {
                        "stage": "阶段5: 修改打磨",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_21": {
                    "status": "pending",
                    "name": "阶段汇总微调",
                    "methodology_markers": {
                        "stage": "阶段5: 修改打磨",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_22": {
                    "status": "pending",
                    "name": "卷汇总",
                    "methodology_markers": {
                        "stage": "阶段5-6: 全局一致性",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_23": {
                    "status": "pending",
                    "name": "全文汇总",
                    "methodology_markers": {
                        "stage": "阶段5-6: 全局一致性",
                        "doc": "11_方法论/PART1_创作方法论/07_修改打磨.md"
                    }
                },
                "STEP_24": {
                    "status": "pending",
                    "name": "终审与发布",
                    "methodology_markers": {
                        "stage": "阶段6: 定稿发布",
                        "doc": "11_方法论/PART1_创作方法论/08_定稿发布.md"
                    }
                }
            }
        },
        "PHASE_7_CLOSE": {
            "status": "pending",
            "steps": {
                "STEP_25": {
                    "status": "pending",
                    "name": "归档与发布",
                    "methodology_markers": {
                        "stage": "阶段6: 定稿发布 - 最终校对",
                        "doc": "11_方法论/PART1_创作方法论/08_定稿发布.md",
                        "final_checklist": "错别字/标点/格式/人名统一/章节完整"
                    }
                }
            }
        }
    },
    "chapters": [$chapters_json],
    "agent_tasks": {},
    "issues_found": {},
    "issues_resolution_log": [],
    "next_actions": "准备启动 PHASE_1_LAUNCH → STEP_01 灵感生成",
    "methodology_notes": {
        "description": "每个步骤的methodology_markers字段指向对应的方法论文档",
        "screening_required_steps": ["STEP_01"],
        "three_act_structure_steps": ["STEP_03", "STEP_05", "STEP_07", "STEP_09", "STEP_11", "STEP_13"],
        "three_round_revision_steps": ["STEP_16", "STEP_17"]
    }
}
EOF

    echo -e "${GREEN}  workflow_state.json 初始化完成（v1.4 含methodology_markers）${NC}"
}

#-------------------------------------------------------------------------------
# 生成各层 index.json（v1.4 增加 methodology_markers）
#-------------------------------------------------------------------------------
generate_indexes() {
    echo -e "${YELLOW}[5/7] 生成各层 index.json...${NC}"

    # 全文总体大纲 index（含 methodology_markers）
    cat > "$PROJECT_ROOT/03_内容仓库/01_全文总体大纲/index.json" << EOF
{
    "layer": "全文总体大纲",
    "project": "$PROJECT_NAME",
    "created_at": "$(date +%Y-%m-%d)",
    "methodology_markers": {
        "stage": "阶段3: 大纲结构设计",
        "structure": "三幕式",
        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
    },
    "entries": []
}
EOF

    # 卷大纲 index
    for i in $(seq 1 $VOLUME_COUNT); do
        cat > "$PROJECT_ROOT/03_内容仓库/02_卷大纲/卷$i/index.json" << EOF
{
    "layer": "卷大纲",
    "project": "$PROJECT_NAME",
    "volume": $i,
    "created_at": "$(date +%Y-%m-%d)",
    "methodology_markers": {
        "stage": "阶段3: 大纲结构设计 - 8节点",
        "structure": "8节点大纲",
        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
    },
    "entries": []
}
EOF
    done

    # 阶段大纲 index（按卷）
    for i in $(seq 1 $VOLUME_COUNT); do
        cat > "$PROJECT_ROOT/03_内容仓库/03_阶段大纲/卷$i/index.json" << EOF
{
    "layer": "阶段大纲",
    "project": "$PROJECT_NAME",
    "volume": $i,
    "created_at": "$(date +%Y-%m-%d)",
    "methodology_markers": {
        "stage": "阶段3: 大纲结构设计 - 章纲",
        "chapter_format": "本章目标+出场人物+剧情走向+情绪落点+留钩子",
        "doc": "11_方法论/PART1_创作方法论/05_大纲结构设计.md"
    },
    "entries": []
}
EOF
    done

    # 正文 index（按卷）
    chapters_per_vol=$(($CHAPTER_COUNT / $VOLUME_COUNT))
    for i in $(seq 1 $VOLUME_COUNT); do
        # 生成该卷的章节列表
        entries_json=""
        for j in $(seq 1 $chapters_per_vol); do
            global_ch=$(($(($i - 1)) * $chapters_per_vol + $j))
            ch_num=$(printf "%03d" $global_ch)
            entries_json="$entries_json\"ch$ch_num\", "
        done
        entries_json="${entries_json%, }"

        cat > "$PROJECT_ROOT/03_内容仓库/04_正文/卷$i/index.json" << EOF
{
    "layer": "正文",
    "project": "$PROJECT_NAME",
    "volume": $i,
    "chapters_per_volume": $chapters_per_vol,
    "created_at": "$(date +%Y-%m-%d)",
    "methodology_markers": {
        "stage": "阶段4: 初稿写作",
        "doc": "11_方法论/PART1_创作方法论/06_初稿写作.md",
        "writing_rules": ["先完成再完美", "不回读修改", "卡住跳过用//TODO:"]
    },
    "entries": [$entries_json]
}
EOF
    done

    echo -e "${GREEN}  各层 index.json 生成完成（含methodology_markers）${NC}"
}

#-------------------------------------------------------------------------------
# 生成项目立项模板文件（新增 v1.4）
#-------------------------------------------------------------------------------
generate_project_templates() {
    echo -e "${YELLOW}[6/7] 生成项目立项模板文件...${NC}"

    local proj_insp="$PROJECT_ROOT/01_灵感库/$PROJECT_NAME"
    local proj_dir="$proj_insp/立项"

    # 核心三要素模板
    cat > "$proj_dir/00_核心三要素.yaml" << 'TEMPLATE'
# 核心三要素 - {PROJECT_NAME}
# 参照: 11_方法论/PART1_创作方法论/02_核心三要素.md
# 生成时间: {DATE}

protagonist:
  一句话: "身份 + 性格 + 执念/短板"
  身份: ""
  性格: ""
  执念/短板: ""

primary_goal:
  一句话描述: ""
  具体化: ""
  贯穿全书: false

obstacle:
  主要阻碍:
    类型: "外在反派 / 自身缺陷 / 社会环境"
    描述: ""
  层层阻碍:
    - ""

stakes:
  如果失败: ""
  代价级别: "致命 / 严重 / 中等"

desire_fear_conflict:
  欲望: ""
  恐惧: ""
  冲突说明: ""

methodology_check:
  三要素完整: false
  一句话故事清晰: false
  筛选标准通过: false
TEMPLATE

    # 替换占位符
    sed -i "s/{PROJECT_NAME}/$PROJECT_NAME/g" "$proj_dir/00_核心三要素.yaml"
    sed -i "s/{DATE}/$(date +%Y-%m-%d)/g" "$proj_dir/00_核心三要素.yaml"

    # 世界观设定模板
    cat > "$proj_dir/01_世界观设定.yaml" << 'TEMPLATE'
# 世界观设定 - {PROJECT_NAME}
# 参照: 11_方法论/PART1_创作方法论/03_世界观与设定.md

时代: ""
时间跨度: ""
主要场景: []

core_rules: []

power_system:
  source: ""
  cost: ""
  constraints: ""
  social_attitude: ""

methodology_check:
  核心规则一句话说清: false
  力量体系有代价: false
  主要场景不超过3个: false
  无堆砌设定: false
TEMPLATE

    sed -i "s/{PROJECT_NAME}/$PROJECT_NAME/g" "$proj_dir/01_世界观设定.yaml"

    # 灵感基础层（从模板库复制并定制）
    cat > "$proj_insp/基础层.yaml" << EOF
# 灵感基础层 - $PROJECT_NAME
# 参照: 11_方法论/PART1_创作方法论/01_灵感捕捉与筛选.md
# 生成时间: $(date +%Y-%m-%d)

type: ""
theme: ""
core_conflict: ""
selling_points: []
audience: ""

# === 方法论新增字段 ===

inspiration_check:
  has_conflict: false
  has_contrast: false
  has_emotion: false
  filter_passed: false

one_sentence_story: ""

core_three_elements:
  protagonist: ""
  goal: ""
  obstacle: ""

genre_markers:
  核心契约: ""

emotion_anchor:
  primary: ""
  secondary: ""
  target_readers_feel: ""
EOF

    # 方法论快速入口（供作家参考）
    cat > "$proj_insp/方法论速查.md" << EOF
# $PROJECT_NAME 方法论速查

## 项目信息
- 总章节数：$CHAPTER_COUNT
- 卷数：$VOLUME_COUNT
- 创建时间：$(date +%Y-%m-%d)

## 各阶段方法论文档

| 阶段 | 方法论文档 |
|------|-----------|
| 灵感捕捉 | 11_方法论/PART1_创作方法论/01_灵感捕捉与筛选.md |
| 核心三要素 | 11_方法论/PART1_创作方法论/02_核心三要素.md |
| 世界观设定 | 11_方法论/PART1_创作方法论/03_世界观与设定.md |
| 人物塑造 | 11_方法论/PART1_创作方法论/04_人物塑造体系.md |
| 大纲结构 | 11_方法论/PART1_创作方法论/05_大纲结构设计.md |
| 初稿写作 | 11_方法论/PART1_创作方法论/06_初稿写作.md |
| 修改打磨 | 11_方法论/PART1_创作方法论/07_修改打磨.md |
| 定稿发布 | 11_方法论/PART1_创作方法论/08_定稿发布.md |

## 立项文件清单

- [ ] 00_核心三要素.yaml - 主角/目标/阻碍
- [ ] 01_世界观设定.yaml - 世界设定
- [ ] 基础层.yaml - 灵感输出（含筛选记录）
- [ ] 人物弧光/ - 角色弧光设计文件夹

## 快速参考

### 三幕式结构
- 第一幕(1-20%)：日常打破，第一扇门
- 第二幕(20%-70%)：尝试失败→中点→低谷→反击
- 第三幕(70%-100%)：终极对决→结局收尾

### 8节点大纲
1. 主角日常
2. 突发意外
3. 第一次尝试失败
4. 遇帮手，反派加压
5. 跌入最低谷
6. 醒悟，决心反击
7. 终极对决
8. 结局收尾

### 开篇三原则
1. 快速出场主角
2. 立刻抛出困境/危机
3. 直接给希望/转机

### 修改三轮
1. 宏观结构（动大手术）
2. 中观节奏（章/翻页钩子）
3. 微观语言（文笔/对话）
EOF

    echo -e "${GREEN}  项目立项模板文件生成完成${NC}"
}

#-------------------------------------------------------------------------------
# 更新主控记忆
#-------------------------------------------------------------------------------
update_memory() {
    echo -e "${YELLOW}[7/7] 更新主控记忆...${NC}"

    cat > "$PROJECT_ROOT/memory/MEMORY.md" << EOF
# 灵文 · 主控 Agent 记忆

## 项目状态
- 当前项目：$PROJECT_NAME（🆕 新项目 v1.4）
- 阶段：PHASE_1_LAUNCH（STEP_01 待启动）
- 总章节数：$CHAPTER_COUNT 章
- 卷数：$VOLUME_COUNT 卷
- 版本：v1.0（初始化，含方法论嵌入）

## 关键文件
- 主控人设：\`CLAUDE.md\`
- 工作流状态：\`workflow_state.json\`（v1.4 含methodology_markers）
- 方法论文档：\`11_方法论/\`
- 模板库：\`01_灵感库/模板库/\`

## 方法论嵌入说明
- 每个步骤的 methodologymarkers 字段指向对应方法论文档
- 灵感生成(STEP_01)必须经过筛选流程
- 大纲审核对应三幕式8节点结构检查
- 正文审核对应三轮修改（宏观→中观→微观）

## 调度命令
- 启动Agent：\`./run_workflow.sh launch <task> <agent> <desc>\`
- 查看任务：\`./run_workflow.sh tasks\`
- 查看状态：\`./run_workflow.sh status\`

## 部门结构
- 灵感部门(3) + 作家部门(10) + 审核部门(10) + 读者部门(20) + 汇总部门(3) = 46 Agent
- 状态机驱动 + 人工重大决策

## 新项目启动流程
1. 灵感生成（必须筛选）→ 01_灵感库/模板库/灵感筛选流程.md
2. 核心三要素提取 → 01_灵感库/{项目}/立项/00_核心三要素.yaml
3. 大纲起草（对照方法论）→ 11_方法论/PART1_创作方法论/05_大纲结构设计.md
4. 正文创作（先完成再完美）→ 11_方法论/PART1_创作方法论/06_初稿写作.md
5. 审核修改（先大后小）→ 11_方法论/PART1_创作方法论/07_修改打磨.md

## 下一步操作
- 启动灵感生成：\`./run_workflow.sh launch\`
- 或手动进入 STEP_01：\`./run_workflow.sh advance STEP_01\`
EOF

    echo -e "${GREEN}  主控记忆更新完成${NC}"
}

#-------------------------------------------------------------------------------
# 完成
#-------------------------------------------------------------------------------
show_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  灵文 · 项目初始化完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}项目信息:${NC}"
    echo "  项目名称: $PROJECT_NAME"
    echo "  章节数: $CHAPTER_COUNT"
    echo "  卷数: $VOLUME_COUNT"
    echo "  版本: v1.4（含方法论嵌入）"
    echo ""
    echo -e "${YELLOW}方法论验证:${NC}"
    echo "  ✓ 11_方法论/ 文档完整"
    echo "  ✓ 01_灵感库/模板库/ 模板完整"
    echo "  ✓ workflow_state.json 含 methodology_markers"
    echo ""
    echo -e "${YELLOW}立项文件:${NC}"
    echo "  01_灵感库/$PROJECT_NAME/立项/00_核心三要素.yaml"
    echo "  01_灵感库/$PROJECT_NAME/立项/01_世界观设定.yaml"
    echo "  01_灵感库/$PROJECT_NAME/基础层.yaml"
    echo "  01_灵感库/$PROJECT_NAME/方法论速查.md"
    echo ""
    echo -e "${YELLOW}下一步操作:${NC}"
    echo "  1. 进入项目目录: cd $PROJECT_ROOT"
    echo "  2. 启动灵感生成: ./run_workflow.sh launch"
    echo "  3. 查看状态: ./run_workflow.sh status"
    echo ""
    echo -e "${YELLOW}目录结构:${NC}"
    echo "  01_灵感库/$PROJECT_NAME/    - 项目灵感文件"
    echo "  01_灵感库/模板库/           - 方法论模板库"
    echo "  11_方法论/                  - 方法论文档"
    echo "  03_内容仓库/               - 四层结构（大纲+正文）"
    echo "  06_意见仓库/               - 审核/评论记录"
    echo "  07_汇总仓库/               - 汇总文件"
    echo "  08_已发布/                 - 最终成品"
    echo ""
}

#-------------------------------------------------------------------------------
# 主流程
#-------------------------------------------------------------------------------
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi

    check_args "$@"
    verify_methodology      # 新增 v1.4
    verify_template_library  # 新增 v1.4
    create_dirs
    init_workflow_state     # 更新 v1.4（methodology_markers）
    generate_indexes        # 更新 v1.4（methodology_markers）
    generate_project_templates  # 新增 v1.4
    update_memory
    show_summary
}

main "$@"