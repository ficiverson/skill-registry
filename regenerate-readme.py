#!/usr/bin/env python3
"""Regenerate README.md from index.json."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "index.json"
README_PATH = ROOT / "README.md"
INDEX_HTML_PATH = ROOT / "index.html"
FORGE_REPO = "https://github.com/ficiverson/skills-forge"


def _format_size(size_bytes: object) -> str:
    if not isinstance(size_bytes, int) or size_bytes < 0:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _pick_latest_version(skill: dict) -> dict:
    latest = skill.get("latest", "")
    versions = skill.get("versions", [])
    if not isinstance(versions, list):
        return {}

    # Prefer explicit version match to avoid semver parsing edge cases.
    for version in versions:
        if isinstance(version, dict) and version.get("version", "") == latest:
            return version

    # Fallback to last version entry if latest isn't found.
    for version in reversed(versions):
        if isinstance(version, dict):
            return version
    return {}


def _render_skill_table(skills: list[dict], base_url: str) -> str:
    header = "\n".join(
        [
            "| Category | Skill | Latest | Owner | Published At | Size | SHA256 | Tags | Description | Download |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    rows: list[str] = []

    for skill in sorted(skills, key=lambda s: (s.get("category", ""), s.get("name", ""))):
        category = skill.get("category", "")
        name = skill.get("name", "")
        latest = skill.get("latest", "")
        description = str(skill.get("description", "")).replace("\n", " ").replace("|", "\\|")
        tags = skill.get("tags", [])
        tags_text = ", ".join(f"`{tag}`" for tag in tags) if isinstance(tags, list) else ""
        owner = skill.get("owner", {})
        owner_name = owner.get("name", "") if isinstance(owner, dict) else ""
        owner_email = owner.get("email", "") if isinstance(owner, dict) else ""
        owner_text = f"{owner_name} ({owner_email})" if owner_name and owner_email else (owner_name or owner_email)

        latest_version = _pick_latest_version(skill)
        version = latest_version.get("version", "")
        sha256 = latest_version.get("sha256", "")
        published_at = latest_version.get("published_at", "")
        size = _format_size(latest_version.get("size_bytes"))
        pack_path = latest_version.get("path", "")
        download_url = f"{base_url.rstrip('/')}/{pack_path}" if pack_path else ""
        download = f"[download]({download_url})" if download_url else ""

        rows.append(
            f"| `{category}` | `{name}` | `{version or latest}` | `{owner_text}` | `{published_at}` | `{size}` | `{sha256}` | {tags_text} | {description} | {download} |"
        )

    if not rows:
        rows.append("| - | - | - | - | - | - | - | - | - | - |")

    return "\n".join([header, *rows])


def _update_index_html(index_data: dict) -> None:
    import re

    html = INDEX_HTML_PATH.read_text(encoding="utf-8")
    json_str = json.dumps(index_data, indent=4)
    indented = "\n".join(
        "            " + line if i > 0 else line
        for i, line in enumerate(json_str.split("\n"))
    )
    new_html = re.sub(
        r"const registryData = \{[\s\S]*?\};",
        f"const registryData = {indented};",
        html,
        count=1,
    )
    INDEX_HTML_PATH.write_text(new_html, encoding="utf-8")


def main() -> int:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    skills = index.get("skills", [])
    base_url = index.get("base_url", "")
    registry_name = index.get("registry_name", "skill-registry")
    updated_at = index.get("updated_at", "")
    skill_count = len(skills) if isinstance(skills, list) else 0
    owner_names = sorted(
        {
            skill.get("owner", {}).get("name", "")
            for skill in skills
            if isinstance(skill, dict) and isinstance(skill.get("owner", {}), dict)
        }
        - {""}
    )
    categories = sorted(
        {skill.get("category", "") for skill in skills if isinstance(skill, dict)} - {""}
    )

    content = "\n".join(
        [
            f"# {registry_name}",
            "",
            "This registry was created and is maintained with [skills-forge]"
            f"({FORGE_REPO}).",
            "",
            "## Registry index",
            "",
            f"- `format_version`: `{index.get('format_version', '')}`",
            f"- `base_url`: `{base_url}`",
            f"- `updated_at`: `{updated_at}`",
            f"- `skills_count`: `{skill_count}`",
            f"- `categories`: `{', '.join(categories)}`",
            f"- `owners`: `{', '.join(owner_names)}`",
            "",
            "## Skills",
            "",
            _render_skill_table(skills, base_url),
            "",
            "## Maintainer workflow",
            "",
            "- Regenerate docs manually with `python3 regenerate-readme.py`.",
            "- Wire a local git pre-push hook to enforce it:",
            "",
            "```bash",
            "mkdir -p .git/hooks",
            "cp .githooks/pre-push .git/hooks/pre-push",
            "chmod +x .git/hooks/pre-push",
            "```",
            "",
            "<!-- Generated by regenerate-readme.py -->",
            "",
        ]
    )

    README_PATH.write_text(content, encoding="utf-8")
    _update_index_html(index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
