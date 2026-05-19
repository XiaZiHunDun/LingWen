#!/usr/bin/env python3
"""
模板版本管理 CLI

Usage:
    python -m prompt_templates version save <template_path> <comment>
    python -m prompt_templates version list <template_path>
    python -m prompt_templates version rollback <template_path> <version_id>
    python -m prompt_templates version diff <version_a> <version_b>
"""
import argparse
import sys
from pathlib import Path

try:
    from .version_manager import VersionManager
except ImportError:
    # Fallback when run directly as __main__.py
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "version_manager",
        Path(__file__).parent / "version_manager.py"
    )
    vm_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm_module)
    VersionManager = vm_module.VersionManager


def get_module_dir() -> Path:
    """Get the directory of this module."""
    return Path(__file__).parent


def cmd_save(args, vm: VersionManager):
    """Save a version snapshot."""
    module_dir = get_module_dir()
    template_path = module_dir / args.template_path  # Resolve relative to module
    template_id = template_path.stem  # Use filename without extension as ID

    try:
        version = vm.create_version(
            template_id=template_id,
            changelog=args.comment,
            template_dir=template_path
        )
        print(f"Version saved successfully: {version.version}")
        print(f"  Template: {template_id}")
        print(f"  Created: {version.created_at}")
        print(f"  Comment: {args.comment}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error saving version: {e}", file=sys.stderr)
        return 1


def cmd_list(args, vm: VersionManager):
    """List all versions for a template."""
    module_dir = get_module_dir()
    template_path = module_dir / args.template_path  # Resolve relative to module
    template_id = template_path.stem

    history = vm.get_history(template_id)

    if not history:
        print(f"No version history found for: {template_id}")
        return 0

    print(f"\nVersion history for: {template_id}\n")
    print(f"{'Version':<12} {'Created':<20} {'Status':<10} {'Comment'}")
    print("-" * 70)

    for v in history:
        comment = v.changelog[:40] + "..." if len(v.changelog) > 40 else v.changelog
        print(f"{v.version:<12} {v.created_at:<20} {v.status:<10} {comment}")

    print(f"\nTotal: {len(history)} version(s)")
    return 0


def cmd_rollback(args, vm: VersionManager):
    """Rollback to a specific version."""
    module_dir = get_module_dir()
    template_path = module_dir / args.template_path  # Resolve relative to module
    template_id = template_path.stem
    target_version = args.version_id

    # First check if version exists
    history = vm.get_history(template_id)
    version_exists = any(v.version == target_version for v in history)

    if not version_exists:
        print(f"Error: Version '{target_version}' not found for template '{template_id}'", file=sys.stderr)
        return 1

    try:
        success = vm.rollback(template_id, target_version)
        if success:
            print(f"Successfully rolled back to version: {target_version}")
            print(f"Template: {template_id}")
            # Note: A backup of current version was created automatically
            print("(Current version has been backed up)")
            return 0
        else:
            print(f"Error: Rollback failed", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error during rollback: {e}", file=sys.stderr)
        return 1


def cmd_diff(args, vm: VersionManager):
    """Compare two versions."""
    version_a = args.version_a
    version_b = args.version_b

    # Parse version identifiers (format: template_id@version or just version_id)
    # If just version IDs are provided, we need to find the template first
    parts_a = version_a.split("@") if "@" in version_a else [None, version_a]
    parts_b = version_b.split("@") if "@" in version_b else [None, version_b]

    # Get all templates with history to find matching versions
    all_history = vm.get_all_templates_with_history()

    if not all_history:
        print("No version history found.", file=sys.stderr)
        return 1

    # Find the template and versions
    found = False
    for template_id, versions in all_history.items():
        version_ids = [v.version for v in versions]
        if version_a in version_ids and version_b in version_ids:
            found = True
            break

    if not found:
        print(f"Error: Could not find versions '{version_a}' and '{version_b}' in the same template", file=sys.stderr)
        return 1

    try:
        diff = vm.compare_versions(template_id, version_a, version_b)

        print(f"\nComparing versions: {version_a} -> {version_b}")
        print(f"Template: {template_id}\n")

        if diff.changed_fields:
            print(f"Changed fields: {', '.join(diff.changed_fields)}")
        else:
            print("No changes detected between versions.")

        if diff.diff_content:
            print("\n" + "=" * 40)
            print("DIFF:")
            print("=" * 40)
            print(diff.diff_content)

        return 0
    except Exception as e:
        print(f"Error comparing versions: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Template Version Management CLI",
        prog="python -m prompt_templates"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Version subcommand
    version_parser = subparsers.add_parser("version", help="Version management commands")
    version_subparsers = version_parser.add_subparsers(dest="subcommand", help="Version subcommands")

    # save subcommand
    save_parser = version_subparsers.add_parser("save", help="Save a version snapshot")
    save_parser.add_argument("template_path", help="Path to the template file")
    save_parser.add_argument("comment", help="Comment describing this version")
    save_parser.set_defaults(func=cmd_save)

    # list subcommand
    list_parser = version_subparsers.add_parser("list", help="List all versions")
    list_parser.add_argument("template_path", help="Path to the template file")
    list_parser.set_defaults(func=cmd_list)

    # rollback subcommand
    rollback_parser = version_subparsers.add_parser("rollback", help="Rollback to a version")
    rollback_parser.add_argument("template_path", help="Path to the template file")
    rollback_parser.add_argument("version_id", help="Version ID to rollback to")
    rollback_parser.set_defaults(func=cmd_rollback)

    # diff subcommand
    diff_parser = version_subparsers.add_parser("diff", help="Compare two versions")
    diff_parser.add_argument("version_a", help="First version ID (or template_id@version)")
    diff_parser.add_argument("version_b", help="Second version ID (or template_id@version)")
    diff_parser.set_defaults(func=cmd_diff)

    args = parser.parse_args()

    if args.command != "version":
        parser.print_help()
        return 1

    if not hasattr(args, "subcommand") or args.subcommand is None:
        version_parser.print_help()
        return 1

    # Initialize VersionManager with module's root directory
    # (where templates and config/prompts both live)
    module_dir = get_module_dir()
    config_dir = module_dir  # Templates are alongside config/prompts in module root
    vm = VersionManager(str(config_dir))

    return args.func(args, vm)


if __name__ == "__main__":
    sys.exit(main() or 0)