#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0",
# ]
# requires-python = ">=3.9"
# ///

"""
export_skills.py
Universal export and packaging utility for ChatGPT and Google Gemini custom skills.
Packages ai-agent-toolkit context modules into upload-ready zip archives.
Emits structured JSON report to stdout and diagnostic progress to stderr.
"""

import argparse
from contextlib import contextmanager
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
TOOL_ROOT = SCRIPT_DIR.parent
DEFAULT_ICON_PATH = TOOL_ROOT / "assets" / "default_icon.svg"


def checked_skill_name(name: str) -> str:
    if not isinstance(name, str) or len(name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("Expected a lowercase, hyphen-separated skill name of at most 64 characters")
    return name


def checked_bundle_path(bundle: Path, path: Path) -> Path:
    root = bundle.absolute()
    path = path.absolute()
    if not path.is_relative_to(root) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Bundle input escapes its source directory: {path}")
    if any(part.is_symlink() for part in (path, *path.parents) if part.is_relative_to(root)):
        raise ValueError(f"Symlink bundle input is not supported: {path}")
    return path


@contextmanager
def output_file(directory: Path, name: str):
    if name in (".", "..") or Path(name).name != name or "\\" in name:
        raise ValueError("Invalid export filename")
    directory = directory.resolve()
    destination = directory / name
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ValueError(f"Invalid export destination: {destination}")
    fd, temporary = tempfile.mkstemp(prefix=".toolkit-export-", dir=directory)
    os.close(fd)
    try:
        yield Path(temporary)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def reference_files(bundle: Path):
    directory = checked_bundle_path(bundle, bundle / "skills" / "references")
    if not directory.is_dir():
        directory = checked_bundle_path(bundle, bundle / "references")
    if directory.is_dir():
        for path in sorted(directory.rglob("*")):
            checked_bundle_path(bundle, path)
            if path.is_file():
                relative_path = path.relative_to(directory).as_posix()
                if "\\" in relative_path:
                    raise ValueError(f"Invalid reference filename: {path.name}")
                yield path, relative_path


def find_toolkit_root(start_dir: Path) -> Path:
    """Finds the root of the ai-agent-toolkit repository."""
    current = start_dir
    while current != current.parent:
        if (current / "bin" / "context.sh").is_file():
            return current
        current = current.parent
    return start_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package toolkit contexts into ChatGPT and Google Gemini skills (zip archives and raw copy-pasteable system prompts).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 export_skills.py shared/thanglish-mentor-persona\n"
            "  python3 export_skills.py shared/* --tool chatgpt --mode prompt\n"
            "  python3 export_skills.py shared/thanglish-mentor-persona --mode prompt --copy\n"
            "  python3 export_skills.py frameworks/angular --tool both --mode both\n"
        ),
    )
    parser.add_argument(
        "selectors",
        nargs="+",
        help="Toolkit module paths, shorthands, or globs (e.g. shared/thanglish-mentor-persona, shared/*)",
    )
    parser.add_argument(
        "--tool",
        "-T",
        choices=["chatgpt", "gemini", "both", "all"],
        default="both",
        help="Target platform format: chatgpt, gemini, or both/all (default: both)",
    )
    parser.add_argument(
        "--mode",
        choices=["zip", "prompt", "both"],
        default="both",
        help="Export mode: zip archives, raw system prompts, or both (default: both)",
    )
    parser.add_argument(
        "--out",
        "-o",
        default="dist/skills",
        help="Destination directory for generated zip archives (default: dist/skills)",
    )
    parser.add_argument(
        "--prompt-out",
        default="dist/prompts",
        help="Destination directory for generated prompt markdown files (default: dist/prompts)",
    )
    parser.add_argument(
        "--copy",
        "-c",
        action="store_true",
        help="Copy generated prompt directly to system clipboard (wl-copy, xclip, pbcopy, clip.exe)",
    )
    parser.add_argument(
        "--strict-budget",
        action="store_true",
        help="Fail with error if prompt exceeds ChatGPT 8,000 character instructions limit",
    )
    parser.add_argument(
        "--with-rules",
        dest="with_rules",
        action="store_true",
        default=True,
        help="Synthesize rules into SKILL.md under constraints section (default: True)",
    )
    parser.add_argument(
        "--no-rules",
        dest="with_rules",
        action="store_false",
        help="Do not synthesize rules; keep SKILL.md as authored",
    )
    parser.add_argument(
        "--icon",
        help="Path to custom SVG icon to use for ChatGPT skill packaging",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON summary to stdout (default: human-friendly console output)",
    )
    return parser.parse_args()


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Splits markdown content into YAML frontmatter and body."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        sys.stderr.write(f"Warning: Failed to parse YAML frontmatter: {exc}\n")
        return {}, content
    if not isinstance(data, dict):
        raise ValueError("Expected a mapping in skill frontmatter")
    return data, match.group(2)


def format_display_name(raw_name: str, body: str) -> str:
    """Derives a human-friendly display name for OpenAI metadata."""
    # Look for top-level H1 header
    h1_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()
        title = re.sub(r"\s*\(.*?\)\s*", " ", title)
        title = re.sub(r"\s*Skill\s*$", "", title, flags=re.IGNORECASE).strip()
        if title:
            return title

    # Fallback to kebab-case conversion
    parts = raw_name.replace("_", "-").split("-")
    return " ".join(part.capitalize() for part in parts if part)


def extract_rule_constraints(rule_path: Path) -> Optional[str]:
    """Extracts constraints section or key rules from a rule file."""
    try:
        content = rule_path.read_text(encoding="utf-8")
        _, body = extract_frontmatter(content)

        # Try to find '## Constraints' section
        constraints_match = re.search(r"(##\s+Constraints.*)", body, re.DOTALL)
        if constraints_match:
            return constraints_match.group(1).strip()

        # Fallback to returning body
        return body.strip()
    except Exception as exc:
        sys.stderr.write(f"Warning: Failed to read rule {rule_path}: {exc}\n")
        return None


def synthesize_skill_content(skill_path: Path, bundle_dir: Path, with_rules: bool) -> Tuple[Dict[str, Any], str]:
    """Reads SKILL.md and optionally appends rules constraints."""
    raw_content = checked_bundle_path(bundle_dir, skill_path).read_text(encoding="utf-8")
    frontmatter, body = extract_frontmatter(raw_content)

    if not with_rules:
        return frontmatter, raw_content

    rules_dir = checked_bundle_path(bundle_dir, bundle_dir / "rules")
    if not rules_dir.is_dir():
        return frontmatter, raw_content

    rule_files = sorted(rules_dir.glob("*.md"))
    if not rule_files:
        return frontmatter, raw_content

    collected_constraints: List[str] = []
    for r_file in rule_files:
        constraints = extract_rule_constraints(checked_bundle_path(bundle_dir, r_file))
        if constraints:
            rule_title = r_file.stem.replace("-", " ").title()
            collected_constraints.append(f"### {rule_title}\n\n{constraints}")

    if not collected_constraints:
        return frontmatter, raw_content

    # Synthesize rules into the body
    synthesized_rules = "\n\n---\n\n## Mandatory Architectural & Implementation Constraints\n\n" + "\n\n".join(collected_constraints)

    # Reconstruct sanitized frontmatter
    sanitized_frontmatter = {
        "name": frontmatter.get("name", bundle_dir.name),
        "description": frontmatter.get("description", f"Expert skills for {bundle_dir.name}"),
    }
    dumped_fm = yaml.safe_dump(sanitized_frontmatter, sort_keys=False).strip()
    synthesized_content = f"---\n{dumped_fm}\n---\n\n{body.strip()}\n{synthesized_rules}\n"
    return sanitized_frontmatter, synthesized_content


def resolve_bundle_dirs(toolkit_root: Path, selector: str) -> List[Path]:
    """Resolves a selector or path into list of bundle directories containing SKILL.md."""
    resolved: List[Path] = []
    
    # 1. Direct path check
    direct = Path(selector)
    if not direct.is_absolute():
        direct = (Path.cwd() / selector).absolute()
        if not direct.exists():
            direct = (toolkit_root / selector).absolute()

    def check_and_add(candidate: Path):
        if not candidate.is_dir():
            return
        # Resolve only after rejecting links in discovered bundle roots.
        if Path(os.path.abspath(candidate)) != candidate.resolve():
            if (candidate / "SKILL.md").is_file() or (candidate / "skills" / "SKILL.md").is_file():
                raise ValueError(f"Symlink bundle directory is not supported: {candidate}")
            return
        candidate = candidate.resolve()
        if (candidate / "skills" / "SKILL.md").is_file():
            resolved.append(candidate)
        elif (candidate / "SKILL.md").is_file():
            # If candidate is a 'skills' directory itself, return its parent bundle
            if candidate.name == "skills":
                resolved.append(candidate.parent)
            else:
                resolved.append(candidate)

    if "*" in selector or "?" in selector:
        # Glob pattern relative to cwd or toolkit_root
        patterns = [
            str(Path.cwd() / selector),
            str(toolkit_root / selector),
        ]
        for root in ["shared", "frameworks", "infra", "domains", "tools"]:
            patterns.append(str(toolkit_root / root / selector))

        matched_dirs = set()
        for pat in patterns:
            for match in glob.glob(pat):
                matched_dirs.add(Path(match).absolute())

        for m_dir in sorted(matched_dirs):
            check_and_add(m_dir)
            # Search subdirectories if it's a category container (e.g. shared/)
            if m_dir.is_dir():
                for sub in sorted(m_dir.iterdir()):
                    check_and_add(sub)
    else:
        if direct.exists() and direct.is_dir():
            check_and_add(direct)
            # If directory contains sub-bundles (e.g. shared)
            for sub in sorted(direct.iterdir()):
                check_and_add(sub)
        else:
            # Try searching under known toolkit roots
            for root in ["shared", "frameworks", "infra", "domains", "tools"]:
                candidate = (toolkit_root / root / selector).absolute()
                if candidate.exists() and candidate.is_dir():
                    check_and_add(candidate)
                    for sub in sorted(candidate.iterdir()):
                        check_and_add(sub)

    # Deduplicate while preserving order
    seen = set()
    unique_bundles = []
    for b in resolved:
        if b not in seen:
            seen.add(b)
            unique_bundles.append(b)
    return unique_bundles


def package_chatgpt_skill(
    bundle_dir: Path,
    skill_content: str,
    frontmatter: Dict[str, Any],
    out_dir: Path,
    icon_source: Optional[Path],
) -> Path:
    """Builds ChatGPT format zip archive: <skill-name>/SKILL.md, agents/openai.yaml, assets/icon.svg."""
    skill_name = checked_skill_name(frontmatter.get("name", bundle_dir.name))
    display_name = format_display_name(skill_name, skill_content)
    description = frontmatter.get("description", f"Expert skill for {skill_name}")

    openai_yaml_data = {
        "interface": {
            "display_name": display_name,
            "short_description": description,
            "icon_small": "assets/icon.svg",
            "icon_large": "assets/icon.svg",
        },
        "policy": {
            "products": ["chatgpt", "codex", "api", "atlas"],
            "allow_implicit_invocation": True,
        },
    }
    openai_yaml_str = yaml.safe_dump(openai_yaml_data, sort_keys=False)

    # Determine icon
    icon_data: bytes
    if icon_source and icon_source.is_file():
        icon_data = icon_source.read_bytes()
    elif checked_bundle_path(bundle_dir, bundle_dir / "skills" / "assets" / "icon.svg").is_file():
        icon_data = (bundle_dir / "skills" / "assets" / "icon.svg").read_bytes()
    elif checked_bundle_path(bundle_dir, bundle_dir / "assets" / "icon.svg").is_file():
        icon_data = (bundle_dir / "assets" / "icon.svg").read_bytes()
    elif DEFAULT_ICON_PATH.is_file():
        icon_data = DEFAULT_ICON_PATH.read_bytes()
    else:
        icon_data = b'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" fill="#00B194"/></svg>'

    zip_filename = f"chatgpt-{skill_name}.zip"
    zip_path = out_dir / zip_filename

    with output_file(out_dir, zip_filename) as temporary, zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED
    ) as zf:
        # 1. SKILL.md
        zf.writestr(f"{skill_name}/SKILL.md", skill_content)
        # 2. agents/openai.yaml
        zf.writestr(f"{skill_name}/agents/openai.yaml", openai_yaml_str)
        # 3. assets/icon.svg
        zf.writestr(f"{skill_name}/assets/icon.svg", icon_data)

        # 4. references/ (if present in skills/references)
        for ref_file, relative in reference_files(bundle_dir):
            zf.write(ref_file, arcname=f"{skill_name}/references/{relative}")

    return zip_path


def package_gemini_skill(
    bundle_dir: Path,
    skill_content: str,
    frontmatter: Dict[str, Any],
    out_dir: Path,
) -> Path:
    """Builds Gemini format zip archive: SKILL.md at root."""
    skill_name = checked_skill_name(frontmatter.get("name", bundle_dir.name))
    zip_filename = f"gemini-{skill_name}.zip"
    zip_path = out_dir / zip_filename

    with output_file(out_dir, zip_filename) as temporary, zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED
    ) as zf:
        # 1. SKILL.md at root
        zf.writestr("SKILL.md", skill_content)

        # 2. references/ (if present)
        for ref_file, relative in reference_files(bundle_dir):
            zf.write(ref_file, arcname=f"references/{relative}")

    return zip_path


def copy_to_clipboard(text: str) -> Tuple[bool, str]:
    """Attempts to copy text to system clipboard via available CLI utilities."""
    commands = [
        ("wl-copy", ["wl-copy"]),
        ("xclip", ["xclip", "-selection", "clipboard"]),
        ("xsel", ["xsel", "--clipboard", "--input"]),
        ("pbcopy", ["pbcopy"]),
        ("clip.exe", ["clip.exe"]),
    ]

    for name, cmd in commands:
        if shutil.which(name):
            try:
                subprocess.run(
                    cmd,
                    input=text.encode("utf-8"),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                )
                return True, f"Copied to clipboard via {name}"
            except Exception as exc:
                sys.stderr.write(f"Warning: {name} failed: {exc}\n")

    return False, "No working clipboard utility found (wl-copy, xclip, xsel, pbcopy, clip.exe)"


def generate_references_overview(bundle_dir: Path) -> str:
    """Scans references directory and creates a structured knowledge index."""
    ref_lines: List[str] = []
    for rf, rel in reference_files(bundle_dir):
        if rf.suffix != ".md":
            continue
        summary = "Architectural reference guide"
        try:
            for line in rf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#"):
                    summary = re.sub(r"^#+\s*", "", line).strip()
                    break
        except (OSError, UnicodeError):
            pass
        ref_lines.append(f"- `{rel}`: {summary}")

    if not ref_lines:
        return ""

    return (
        "<knowledge_references>\n"
        "The following specialized references are bundled in this capability module:\n"
        + "\n".join(ref_lines)
        + "\n</knowledge_references>\n"
    )


def synthesize_structured_prompt(
    bundle_dir: Path,
    skill_content: str,
    frontmatter: Dict[str, Any],
    platform: str,
    with_rules: bool = True,
) -> Tuple[str, Dict[str, Any]]:
    """Synthesizes high-adherence structured XML/Markdown prompt with character budget guard."""
    skill_name = checked_skill_name(frontmatter.get("name", bundle_dir.name))
    display_name = format_display_name(skill_name, skill_content)
    description = frontmatter.get("description", f"Expert skill for {skill_name}")

    # Extract base SKILL.md body
    skill_path = bundle_dir / "skills" / "SKILL.md"
    if not skill_path.is_file():
        skill_path = bundle_dir / "SKILL.md"
    skill_path = checked_bundle_path(bundle_dir, skill_path)
    raw_content = skill_path.read_text(encoding="utf-8") if skill_path.is_file() else skill_content
    _, raw_body = extract_frontmatter(raw_content)

    # Collect rule constraints
    constraints_text = ""
    if with_rules:
        rules_dir = checked_bundle_path(bundle_dir, bundle_dir / "rules")
        if rules_dir.is_dir():
            rule_files = sorted(rules_dir.glob("*.md"))
            constraints_list: List[str] = []
            for r_file in rule_files:
                c = extract_rule_constraints(checked_bundle_path(bundle_dir, r_file))
                if c:
                    r_title = r_file.stem.replace("-", " ").title()
                    constraints_list.append(f"#### {r_title}\n{c}")
            if constraints_list:
                constraints_text = "\n\n".join(constraints_list)

    # References summary
    references_overview = generate_references_overview(bundle_dir)

    prompt_blocks = [
        f"<!-- System Instructions for {display_name} ({platform.upper()}) -->\n",
        f"<role>\nYou are an expert assistant acting as {display_name}.\n{description}\n</role>\n",
        f"<instructions>\n{raw_body.strip()}\n</instructions>\n",
    ]

    if constraints_text:
        prompt_blocks.append(f"<constraints>\n{constraints_text.strip()}\n</constraints>\n")

    if references_overview:
        prompt_blocks.append(references_overview.strip() + "\n")

    prompt_str = "\n".join(prompt_blocks).strip() + "\n"
    char_count = len(prompt_str)
    tokens_est = max(1, char_count // 4)
    chatgpt_limit = 8000
    within_chatgpt_limit = char_count <= chatgpt_limit

    metrics = {
        "platform": platform,
        "character_count": char_count,
        "estimated_tokens": tokens_est,
        "chatgpt_limit": chatgpt_limit,
        "within_chatgpt_limit": within_chatgpt_limit,
    }

    return prompt_str, metrics


def write_prompt_file(
    prompt_out_dir: Path,
    platform: str,
    skill_name: str,
    prompt_text: str,
) -> Path:
    """Writes synthesized prompt to markdown file in prompt_out_dir."""
    prompt_out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{platform}-{checked_skill_name(skill_name)}.md"
    file_path = prompt_out_dir / filename
    with output_file(prompt_out_dir, filename) as temporary:
        temporary.write_text(prompt_text, encoding="utf-8")
    return file_path


def main():
    args = parse_args()
    toolkit_root = find_toolkit_root(Path.cwd())

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir

    prompt_out_dir = Path(args.prompt_out)
    if not prompt_out_dir.is_absolute():
        prompt_out_dir = Path.cwd() / prompt_out_dir

    if args.mode in ["zip", "both"]:
        out_dir.mkdir(parents=True, exist_ok=True)
    if args.mode in ["prompt", "both"]:
        prompt_out_dir.mkdir(parents=True, exist_ok=True)

    icon_source = Path(args.icon).resolve() if args.icon else None

    # Resolve all candidate bundles
    all_bundles: List[Path] = []
    for sel in args.selectors:
        matched = resolve_bundle_dirs(toolkit_root, sel)
        all_bundles.extend(matched)

    # Deduplicate bundles
    seen = set()
    bundles: List[Path] = []
    for b in all_bundles:
        if b not in seen:
            seen.add(b)
            bundles.append(b)

    if not bundles:
        sys.stderr.write(f"Error: No valid skill bundles found matching selectors: {args.selectors}\n")
        sys.exit(1)

    platforms = []
    if args.tool in ["chatgpt", "both", "all"]:
        platforms.append("chatgpt")
    if args.tool in ["gemini", "both", "all"]:
        platforms.append("gemini")

    results: List[Dict[str, Any]] = []
    generated_prompts_to_copy: List[Tuple[str, str, str]] = []
    budget_violations: List[Tuple[str, int]] = []

    for bundle in bundles:
        # Locate SKILL.md
        skill_path = bundle / "skills" / "SKILL.md"
        if not skill_path.is_file():
            skill_path = bundle / "SKILL.md"
        if not skill_path.is_file():
            sys.stderr.write(f"Warning: SKILL.md not found in {bundle}; skipping.\n")
            continue

        frontmatter, synthesized_content = synthesize_skill_content(skill_path, bundle, args.with_rules)
        skill_name = checked_skill_name(frontmatter.get("name", bundle.name))

        bundle_result: Dict[str, Any] = {
            "name": skill_name,
            "bundle_dir": str(bundle),
            "generated_files": [],
            "prompts": [],
        }

        # 1. Zip generation
        if args.mode in ["zip", "both"]:
            if "chatgpt" in platforms:
                c_zip = package_chatgpt_skill(bundle, synthesized_content, frontmatter, out_dir, icon_source)
                bundle_result["generated_files"].append({
                    "platform": "chatgpt",
                    "type": "zip",
                    "path": str(c_zip),
                    "size_bytes": c_zip.stat().st_size,
                })
                if not args.json:
                    sys.stderr.write(f"  [ChatGPT Zip]    -> {c_zip.relative_to(Path.cwd()) if c_zip.is_relative_to(Path.cwd()) else c_zip} ({c_zip.stat().st_size} bytes)\n")

            if "gemini" in platforms:
                g_zip = package_gemini_skill(bundle, synthesized_content, frontmatter, out_dir)
                bundle_result["generated_files"].append({
                    "platform": "gemini",
                    "type": "zip",
                    "path": str(g_zip),
                    "size_bytes": g_zip.stat().st_size,
                })
                if not args.json:
                    sys.stderr.write(f"  [Gemini Zip]     -> {g_zip.relative_to(Path.cwd()) if g_zip.is_relative_to(Path.cwd()) else g_zip} ({g_zip.stat().st_size} bytes)\n")

        # 2. Prompt generation
        if args.mode in ["prompt", "both"]:
            for plat in platforms:
                p_text, p_metrics = synthesize_structured_prompt(bundle, synthesized_content, frontmatter, plat, args.with_rules)
                p_file = write_prompt_file(prompt_out_dir, plat, skill_name, p_text)
                
                budget_status = "OK <= 8000" if p_metrics["within_chatgpt_limit"] else f"WARN: Exceeds 8,000 char limit ({p_metrics['character_count']} chars)"
                p_entry = {
                    "platform": plat,
                    "type": "prompt",
                    "path": str(p_file),
                    "character_count": p_metrics["character_count"],
                    "estimated_tokens": p_metrics["estimated_tokens"],
                    "within_chatgpt_limit": p_metrics["within_chatgpt_limit"],
                }
                bundle_result["prompts"].append(p_entry)
                generated_prompts_to_copy.append((skill_name, plat, p_text))

                if not args.json:
                    sys.stderr.write(f"  [{plat.capitalize()} Prompt] -> {p_file.relative_to(Path.cwd()) if p_file.is_relative_to(Path.cwd()) else p_file} ({p_metrics['character_count']} chars, ~{p_metrics['estimated_tokens']} tokens) [{budget_status}]\n")

                if args.strict_budget and plat == "chatgpt" and not p_metrics["within_chatgpt_limit"]:
                    budget_violations.append((skill_name, p_metrics["character_count"]))

        results.append(bundle_result)

    # Clipboard copying
    clipboard_message = None
    if args.copy and generated_prompts_to_copy:
        first_skill, first_plat, first_text = generated_prompts_to_copy[0]
        success, msg = copy_to_clipboard(first_text)
        clipboard_message = f"{msg} ({first_skill} - {first_plat})"
        if not args.json:
            sys.stderr.write(f"  [Clipboard]      -> {clipboard_message}\n")

    report = {
        "status": "success",
        "mode": args.mode,
        "zip_output_directory": str(out_dir) if args.mode in ["zip", "both"] else None,
        "prompt_output_directory": str(prompt_out_dir) if args.mode in ["prompt", "both"] else None,
        "clipboard_status": clipboard_message,
        "total_skills_exported": len(results),
        "packages": results,
    }

    if budget_violations:
        for s_name, c_len in budget_violations:
            sys.stderr.write(f"Error: {s_name} prompt exceeds ChatGPT 8,000 character limit ({c_len} chars).\n")
        sys.exit(2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        out_summary = []
        if args.mode in ["zip", "both"]:
            out_summary.append(f"archives in {out_dir}")
        if args.mode in ["prompt", "both"]:
            out_summary.append(f"prompts in {prompt_out_dir}")
        print(f"\nSuccessfully exported {len(results)} skill(s) ({' and '.join(out_summary)})")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(f"Error: {error}")
