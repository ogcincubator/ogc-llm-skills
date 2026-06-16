"""
Build the GitHub Pages site for ogc-llm-skills.

Usage: python3 build_site.py <out_dir> <sha> <repo_url> <site_url>

Finds all SKILL.md files in the repo, zips each skill directory (contents at
root, no parent path prefix), extracts name/description from frontmatter, and
generates an index.html with download links, plus manifest.json and llms.txt
for agent-driven installation.
"""

import sys
import re
import json
import subprocess
import zipfile
import html as html_lib
from pathlib import Path

out_dir = Path(sys.argv[1])
sha = sys.argv[2]
repo_url = sys.argv[3]
site_url = sys.argv[4].rstrip("/")
short_sha = sha[:7]

out_dir.mkdir(parents=True, exist_ok=True)


def get_skill_version(skill_dir: Path) -> tuple[str, str]:
    result = subprocess.run(
        ["git", "log", "--max-count=1", "--format=%H %aI", "--", str(skill_dir)],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        commit, date = result.stdout.strip().split(" ", 1)
        return commit, date.strip()
    return sha, ""


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


UPDATE_SECTION = """
## Updating this skill

This skill was installed from the OGC LLM Skills registry. To check for
updates, read `.version` in this directory — it contains `commit`, `date`,
`zip_url`, and `llms_txt`. Compare `commit` against the registry manifest;
if they differ, delete this directory, re-create it, and extract the new zip
into it. See the `llms_txt` URL for the full update procedure.
"""

skills = []
repo_root = Path(".")
# Collect (skill_dir, zip_stem, files) for the fat zip
all_skill_entries = []

for skill_md in sorted(repo_root.rglob("SKILL.md")):
    parts = skill_md.parts
    if ".git" in parts or out_dir.name in parts or ".github" in parts:
        continue

    skill_dir = skill_md.parent
    # bblocks/authoring -> bblocks-authoring.zip
    zip_stem = str(skill_dir).lstrip("./").replace("/", "-")
    zip_name = zip_stem + ".zip"
    zip_path = out_dir / zip_name

    skill_files = sorted(f for f in skill_dir.rglob("*") if f.is_file())
    commit, date = get_skill_version(skill_dir)
    version_obj = {"commit": commit, "date": date,
                   "zip_url": f"{site_url}/{zip_name}",
                   "llms_txt": f"{site_url}/llms.txt"}

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in skill_files:
            if f == skill_md:
                zf.writestr(str(f.relative_to(skill_dir)),
                            f.read_text(encoding="utf-8") + UPDATE_SECTION)
            else:
                zf.write(f, f.relative_to(skill_dir))
        zf.writestr(".version", json.dumps(version_obj, indent=2))

    name, desc = parse_frontmatter(skill_md)
    skills.append({"name": name, "description": desc, "zip": zip_name,
                   "commit": commit, "date": date})
    all_skill_entries.append((zip_stem, skill_dir, skill_md, skill_files, version_obj))
    print(f"  packaged: {zip_name}  ({name})")

# Fat zip: all skills with their zip-stem as the directory prefix
fat_zip_name = "all-skills.zip"
with zipfile.ZipFile(out_dir / fat_zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
    for zip_stem, skill_dir, skill_md, skill_files, version_obj in all_skill_entries:
        for f in skill_files:
            arc_path = Path(zip_stem) / f.relative_to(skill_dir)
            if f == skill_md:
                zf.writestr(str(arc_path),
                            f.read_text(encoding="utf-8") + UPDATE_SECTION)
            else:
                zf.write(f, arc_path)
        zf.writestr(str(Path(zip_stem) / ".version"), json.dumps(version_obj, indent=2))
print(f"  packaged: {fat_zip_name}  (all skills)")


# manifest.json — machine-readable index for agent-driven installation
manifest = {
    "updated": sha,
    "all_skills_zip": f"{site_url}/{fat_zip_name}",
    "skills": [
        {
            "name": s["name"],
            "description": s["description"],
            "zip_url": f"{site_url}/{s['zip']}",
            "commit": s["commit"],
            "date": s["date"],
        }
        for s in skills
    ],
}
(out_dir / "manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("  wrote: manifest.json")


# llms.txt — plain Markdown entrypoint for LLMs (llmstxt.org convention)
skill_lines = "\n".join(
    f"- [{s['name']}]({site_url}/{s['zip']}): {s['description']}" for s in skills
)
llms_txt = f"""\
# OGC LLM Skills

> Reusable reference skills for LLM tooling — domain knowledge packs that can
> be installed as custom skills in Claude Code or any compatible agent.

## Installation

Each skill zip contains files without a top-level wrapper directory. You must
create the target directory yourself before extracting:

```
mkdir -p ~/.claude/skills/<skill-name>
cd ~/.claude/skills/<skill-name>
unzip /path/to/<skill-name>.zip
```

Requires `unzip` and either `curl` or `wget`. If those are not available in
your environment (e.g. a minimal container), you will need to write a Node.js
script using the built-in `zlib` and `https` modules to download and decompress
the zip.

After extraction, verify success by confirming that
`~/.claude/skills/<skill-name>/SKILL.md` exists and its `name:` frontmatter
field matches the skill name. Each zip also contains a `.version` file (JSON)
with `commit`, `date`, `zip_url`, and `llms_txt` fields — used to check for
updates without re-downloading the zip.

Each `SKILL.md` has YAML frontmatter with `name:` (kebab-case identifier) and
`description:` fields, followed by Markdown content that the agent reads to
understand the skill's scope and sub-files.

All skills: {site_url}/{fat_zip_name}

## Checking for and applying updates

To check whether installed skills are up to date:

1. Fetch `{site_url}/manifest.json`.
2. For each installed skill, read `~/.claude/skills/<skill-name>/.version`
   and compare its `commit` field against the `commit` field in the manifest.
3. If they differ, the skill has been updated. Delete the skill directory,
   re-create it, and extract the new zip into it (same steps as initial
   installation). Do not overwrite in place — deleted or renamed files in
   the new version would otherwise be left behind as stale copies.

## Available skills

{skill_lines}

## Machine-readable manifest

{site_url}/manifest.json
"""
(out_dir / "llms.txt").write_text(llms_txt, encoding="utf-8")
print("  wrote: llms.txt")


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

fat_url = f"{fat_zip_name}?v={short_sha}"

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
    .agent-tip {{ margin: 1rem 0 1.5rem; padding: 0.65rem 1rem; background: #fff8e1; border: 1px solid #f0c040; border-radius: 6px; font-size: 0.9rem; color: #555; line-height: 1.5; }}
    .agent-tip code {{ background: #f3f3f3; padding: 0.1em 0.35em; border-radius: 3px; font-size: 0.88em; }}
    .all-skills {{ margin: 1.5rem 0; padding: 0.75rem 1.25rem; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }}
    .all-skills p {{ margin: 0; color: #555; font-size: 0.95rem; }}
    .skill {{ margin: 1.5rem 0; padding: 1rem 1.25rem; border: 1px solid #ddd; border-radius: 6px; }}
    .skill h2 {{ margin: 0 0 0.4rem; font-size: 1.05rem; font-family: monospace; }}
    .skill p {{ margin: 0 0 0.75rem; color: #555; font-size: 0.95rem; line-height: 1.5; }}
    a.download {{ display: inline-block; padding: 0.35rem 0.85rem; background: #0969da; color: #fff; border-radius: 4px; text-decoration: none; font-size: 0.9rem; white-space: nowrap; }}
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
  <p class="agent-tip">
    Prefer to let your agent handle it? Point it to
    <a href="manifest.json"><code>manifest.json</code></a> or
    <a href="llms.txt"><code>llms.txt</code></a> and ask it to download and install
    the skills you need.
  </p>
  <div class="all-skills">
    <p>Download all skills in one zip — extract into <code>~/.claude/skills/</code> to install everything at once.</p>
    <a class="download" href="{fat_url}" download>{fat_zip_name}</a>
  </div>
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