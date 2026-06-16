"""
Build the GitHub Pages site for ogc-llm-skills.

Usage: python3 build_site.py <out_dir> <sha> <repo_url>

Finds all SKILL.md files in the repo, zips each skill directory (contents at
root, no parent path prefix), extracts name/description from frontmatter, and
generates an index.html with download links.
"""

import sys
import re
import zipfile
import html as html_lib
from pathlib import Path

out_dir = Path(sys.argv[1])
sha = sys.argv[2]
repo_url = sys.argv[3]
short_sha = sha[:7]

out_dir.mkdir(parents=True, exist_ok=True)


def parse_frontmatter(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    name, desc = "", ""
    if m:
        for line in m.group(1).splitlines():
            if line.startswith("name:"):
                name = line[5:].strip().strip('"')
            elif line.startswith("description:"):
                desc = line[12:].strip().strip('"')
    return name, desc


skills = []
repo_root = Path(".")

for skill_md in sorted(repo_root.rglob("SKILL.md")):
    parts = skill_md.parts
    if ".git" in parts or out_dir.name in parts or ".github" in parts:
        continue

    skill_dir = skill_md.parent
    # bblocks/authoring -> bblocks-authoring.zip
    zip_name = str(skill_dir).lstrip("./").replace("/", "-") + ".zip"
    zip_path = out_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(skill_dir))

    name, desc = parse_frontmatter(skill_md)
    skills.append({"name": name, "description": desc, "zip": zip_name})
    print(f"  packaged: {zip_name}  ({name})")


def skill_card(s: dict) -> str:
    name = html_lib.escape(s["name"])
    desc = html_lib.escape(s["description"])
    url = f"{s['zip']}?v={short_sha}"
    filename = html_lib.escape(s["zip"])
    return f"""\
  <div class="skill">
    <h2>{name}</h2>
    <p>{desc}</p>
    <a class="download" href="{url}" download>{filename}</a>
  </div>"""


cards = "\n".join(skill_card(s) for s in skills)

index_html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OGC LLM Skills</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 2rem auto; padding: 0 1.25rem; color: #1a1a1a; }}
    h1 {{ border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }}
    .intro {{ color: #444; line-height: 1.6; }}
    .skill {{ margin: 1.5rem 0; padding: 1rem 1.25rem; border: 1px solid #ddd; border-radius: 6px; }}
    .skill h2 {{ margin: 0 0 0.4rem; font-size: 1.05rem; font-family: monospace; }}
    .skill p {{ margin: 0 0 0.75rem; color: #555; font-size: 0.95rem; line-height: 1.5; }}
    a.download {{ display: inline-block; padding: 0.35rem 0.85rem; background: #0969da; color: #fff; border-radius: 4px; text-decoration: none; font-size: 0.9rem; }}
    a.download:hover {{ background: #0550ae; }}
    footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee; font-size: 0.8rem; color: #999; }}
    footer a {{ color: #999; }}
  </style>
</head>
<body>
  <h1>OGC LLM Skills</h1>
  <p class="intro">
    Reusable reference skills for LLM tooling. Download a zip and install it as a
    custom skill in <a href="https://claude.ai">claude.ai</a>, Claude Code, or any
    compatible tool that supports the
    <a href="https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview">Agent Skills</a> format.
  </p>
{cards}
  <footer>
    Built from <a href="{repo_url}/commit/{sha}">{short_sha}</a>
    &middot; <a href="{repo_url}">GitHub</a>
  </footer>
</body>
</html>
"""

(out_dir / "index.html").write_text(index_html, encoding="utf-8")
print(f"Built {len(skills)} skill(s) → {out_dir}/index.html")