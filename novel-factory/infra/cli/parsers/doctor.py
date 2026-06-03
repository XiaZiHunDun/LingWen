"""doctor subparser — system diagnostics (env/db/chapters/fixes)."""
import argparse


def add_doctor_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'doctor' 子命令的参数解析器(无参数)。

    用法:
        lingwen.py doctor
    """
    return subparsers.add_parser(
        "doctor",
        help="系统诊断",
        description="检查环境、数据库、章节文件等系统状态",
    )
