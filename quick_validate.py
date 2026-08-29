#!/usr/bin/env python3
"""Skill 结构快速校验脚本（仅使用标准库）。

用法：python quick_validate.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"


def parse_frontmatter(text):
    """解析 YAML frontmatter，返回 (meta dict 或 None, 正文)。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, text[m.end():]


def check_skill(skill_dir, errors, warnings):
    name = skill_dir.name
    print(f"检查 Skill: {name}")

    # --- SKILL.md ---
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"{name}: 缺少 SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    if meta is None:
        errors.append(f"{name}: SKILL.md 缺少 YAML frontmatter")
    else:
        if meta.get("name") != name:
            errors.append(
                f"{name}: frontmatter name 为 '{meta.get('name')}'，与目录名不一致"
            )
        desc = meta.get("description", "")
        if not desc:
            errors.append(f"{name}: 缺少 description")
        elif len(desc) > 200:
            warnings.append(f"{name}: description 超过 200 字符（当前 {len(desc)}）")
    if not body.strip():
        errors.append(f"{name}: SKILL.md 正文为空")

    # --- agents/openai.yaml ---
    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.is_file():
        errors.append(f"{name}: 缺少 agents/openai.yaml")
    else:
        ytext = openai_yaml.read_text(encoding="utf-8")
        if not ytext.strip():
            errors.append(f"{name}: openai.yaml 为空")
        else:
            try:
                import yaml  # 可选依赖，缺失时回退到正则检查
                data = yaml.safe_load(ytext) or {}
                if data.get("name") != name:
                    errors.append(
                        f"{name}: openai.yaml name 为 '{data.get('name')}'，与目录名不一致"
                    )
            except ImportError:
                m = re.search(r"^name:\s*(\S+)", ytext, re.MULTILINE)
                if not m or m.group(1) != name:
                    errors.append(f"{name}: openai.yaml 缺少正确的 name 字段")

    # --- 非必要脚本检查 ---
    extra = [
        str(p.relative_to(skill_dir))
        for p in skill_dir.rglob("*")
        if p.is_file() and p.suffix in {".py", ".sh", ".js", ".ts"}
    ]
    if extra:
        warnings.append(f"{name}: 存在可能的非必要脚本: {', '.join(extra)}")


def main():
    if not SKILLS_DIR.is_dir():
        print(f"[FAIL] 未找到 skills 目录: {SKILLS_DIR}")
        return 1

    errors, warnings = [], []
    skills = [p for p in SKILLS_DIR.iterdir() if p.is_dir()]
    if not skills:
        errors.append("skills 目录下没有任何 Skill")
    for skill in sorted(skills):
        check_skill(skill, errors, warnings)

    for w in warnings:
        print(f"[WARN] {w}")
    for e in errors:
        print(f"[FAIL] {e}")

    if errors:
        print(f"\n校验失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"\n校验通过：{len(skills)} 个 Skill，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
