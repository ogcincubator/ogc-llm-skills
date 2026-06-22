"""
Build the GitHub Pages site for ogc-llm-skills.

Usage: python3 build_site.py <out_dir> <sha> <repo_url> <site_url>

Finds all SKILL.md files in the repo, zips each skill directory (contents
wrapped in a top-level folder named after the skill), extracts name/description
from frontmatter, and generates an index.html with download links, plus
manifest.json and llms.txt for agent-driven installation.
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
if they differ, delete this directory entirely, then extract the new zip
into its parent skills directory (the zip recreates this directory itself).
See the `llms_txt` URL for the full update procedure.
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
            arc_path = Path(zip_stem) / f.relative_to(skill_dir)
            if f == skill_md:
                zf.writestr(str(arc_path),
                            f.read_text(encoding="utf-8") + UPDATE_SECTION)
            else:
                zf.write(f, arc_path)
        zf.writestr(str(Path(zip_stem) / ".version"), json.dumps(version_obj, indent=2))

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


# install-skill.js — Node.js fallback for environments without curl/unzip
install_script = """\
// Downloads and extracts an OGC LLM Skills zip using only Node.js built-ins.
// Usage: node install-skill.js <zip-url> <dest-dir>
// Handles deflate and stored zip entries; no external dependencies required.
const https = require("https");
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

function extractZip(buf, destDir) {
  let off = 0;
  while (off + 30 < buf.length) {
    if (buf.readUInt32LE(off) !== 0x04034b50) break;
    const method  = buf.readUInt16LE(off + 8);
    const csize   = buf.readUInt32LE(off + 18);
    const fnLen   = buf.readUInt16LE(off + 26);
    const exLen   = buf.readUInt16LE(off + 28);
    const name    = buf.slice(off + 30, off + 30 + fnLen).toString();
    const dataOff = off + 30 + fnLen + exLen;
    const entry   = buf.slice(dataOff, dataOff + csize);
    const outPath = path.join(destDir, name);
    if (name.endsWith("/")) {
      fs.mkdirSync(outPath, { recursive: true });
    } else {
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, method === 8 ? zlib.inflateRawSync(entry) : entry);
    }
    off = dataOff + csize;
  }
}

const [zipUrl, destDir] = process.argv.slice(2);
if (!zipUrl || !destDir) {
  console.error("Usage: node install-skill.js <zip-url> <dest-dir>");
  process.exit(1);
}

function bail(e) { console.error(e.message); process.exit(1); }

function handleResponse(res) {
  if (res.statusCode !== 200) {
    console.error(`HTTP ${res.statusCode}`); process.exit(1);
  }
  const chunks = [];
  res.on("data", c => chunks.push(c));
  res.on("end", () => {
    fs.mkdirSync(destDir, { recursive: true });
    extractZip(Buffer.concat(chunks), destDir);
    console.log("done");
  });
}

https.get(zipUrl, res => {
  if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
    https.get(res.headers.location, handleResponse).on("error", bail);
    return;
  }
  handleResponse(res);
}).on("error", bail);
"""
(out_dir / "install-skill.js").write_text(install_script, encoding="utf-8")
print("  wrote: install-skill.js")

# llms.txt — plain Markdown entrypoint for LLMs (llmstxt.org convention)
skill_lines = "\n".join(
    f"- [{s['name']}]({site_url}/{s['zip']}): {s['description']}" for s in skills
)
llms_txt = f"""\
# OGC LLM Skills

> Reusable reference skills for LLM tooling — domain knowledge packs that can
> be installed as custom skills in Claude Code or any compatible agent.

This file is an installation guide for an agent acting on a user's explicit
request to install one or more of these skills (e.g. "install the bblocks-authoring
skill from ogc-llm-skills"). It is not a directive to act on automatically
when encountered incidentally — only follow the steps below if the user
asked for a skill from this repository.

## Installation

Each skill zip contains a single top-level directory named after the skill
(kebab-case). Extract it directly into `~/.claude/skills`:

```
mkdir -p ~/.claude/skills
unzip /path/to/<skill-name>.zip -d ~/.claude/skills
```

Before proceeding, check that the required tools are available:

```
which curl unzip wget
```

If either unzip or both wget and curl are missing, download `{site_url}/install-skill.js` and run it instead
(uses only Node.js built-ins — no external dependencies). Inspect the script
before running it, as with any code fetched from the network:

```
node install-skill.js <zip-url> ~/.claude/skills
```

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
3. If they differ, the skill has been updated. Delete the skill directory
   (`~/.claude/skills/<skill-name>`) entirely, then extract the new zip into
   `~/.claude/skills` (same steps as initial installation). Do not overwrite
   in place — deleted or renamed files in the new version would otherwise be
   left behind as stale copies.

## Available skills

{skill_lines}

## Machine-readable manifest

{site_url}/manifest.json
"""
(out_dir / "llms.txt").write_text(llms_txt, encoding="utf-8")
print("  wrote: llms.txt")


def install_block(unix_cmd: str, win_cmd: str) -> str:
    unix_esc = html_lib.escape(unix_cmd)
    win_esc = html_lib.escape(win_cmd)
    unix_attr = html_lib.escape(unix_cmd, quote=True)
    win_attr = html_lib.escape(win_cmd, quote=True)
    return f"""\
  <div class="install-block">
    <div class="install-header">
      <span class="install-title">Install on Claude Code</span>
      <div class="os-tabs">
        <button class="os-tab" data-os="unix">macOS / Linux</button>
        <button class="os-tab" data-os="win">Windows</button>
      </div>
    </div>
    <div class="install-cmd" data-os="unix">
      <div class="install-cmd-code"><code>{unix_esc}</code></div>
      <button class="copy-btn" data-clipboard="{unix_attr}">Copy</button>
    </div>
    <div class="install-cmd" data-os="win">
      <div class="install-cmd-code"><code>{win_esc}</code></div>
      <button class="copy-btn" data-clipboard="{win_attr}">Copy</button>
    </div>
  </div>"""


def skill_card(s: dict) -> str:
    name = html_lib.escape(s["name"])
    desc = html_lib.escape(s["description"])
    url = f"{s['zip']}?v={short_sha}"
    filename = html_lib.escape(s["zip"])
    zip_url = f"{site_url}/{s['zip']}"
    zip_name_esc = s["zip"]
    unix_cmd = (
        f"mkdir -p ~/.claude/skills && "
        f"curl -fsSL \"{zip_url}\" -o /tmp/{zip_name_esc} && "
        f"unzip -q /tmp/{zip_name_esc} -d ~/.claude/skills"
    )
    win_cmd = (
        f"New-Item -ItemType Directory -Force -Path "
        f"\"$env:USERPROFILE\\.claude\\skills\" | Out-Null; "
        f"Invoke-WebRequest -Uri \"{zip_url}\" "
        f"-OutFile \"$env:TEMP\\{zip_name_esc}\"; "
        f"Expand-Archive -Path \"$env:TEMP\\{zip_name_esc}\" "
        f"-DestinationPath \"$env:USERPROFILE\\.claude\\skills\" -Force"
    )
    block = install_block(unix_cmd, win_cmd)
    return f"""\
  <div class="skill">
    <h2>{name}</h2>
    <p>{desc}</p>
    <a class="download" href="{url}" download>{filename}</a>
{block}
  </div>"""


cards = "\n".join(skill_card(s) for s in skills)

fat_url = f"{fat_zip_name}?v={short_sha}"
fat_zip_url = f"{site_url}/{fat_zip_name}"
fat_unix_cmd = (
    f"mkdir -p ~/.claude/skills && "
    f"curl -fsSL \"{fat_zip_url}\" -o /tmp/{fat_zip_name} && "
    f"unzip -q /tmp/{fat_zip_name} -d ~/.claude/skills/"
)
fat_win_cmd = (
    f"New-Item -ItemType Directory -Force -Path "
    f"\"$env:USERPROFILE\\.claude\\skills\" | Out-Null; "
    f"Invoke-WebRequest -Uri \"{fat_zip_url}\" "
    f"-OutFile \"$env:TEMP\\{fat_zip_name}\"; "
    f"Expand-Archive -Path \"$env:TEMP\\{fat_zip_name}\" "
    f"-DestinationPath \"$env:USERPROFILE\\.claude\\skills\" -Force"
)
fat_block = install_block(fat_unix_cmd, fat_win_cmd)

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
    .all-skills {{ margin: 1.5rem 0; padding: 0.75rem 1.25rem; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; }}
    .all-skills-top {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; }}
    .all-skills-top p {{ margin: 0; color: #555; font-size: 0.95rem; }}
    .skill {{ margin: 1.5rem 0; padding: 1rem 1.25rem; border: 1px solid #ddd; border-radius: 6px; }}
    .skill h2 {{ margin: 0 0 0.4rem; font-size: 1.05rem; font-family: monospace; }}
    .skill p {{ margin: 0 0 0.75rem; color: #555; font-size: 0.95rem; line-height: 1.5; }}
    a.download {{ display: inline-block; padding: 0.35rem 0.85rem; background: #0969da; color: #fff; border-radius: 4px; text-decoration: none; font-size: 0.9rem; white-space: nowrap; }}
    a.download:hover {{ background: #0550ae; }}
    .install-block {{ margin-top: 0.85rem; }}
    .install-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.35rem; }}
    .install-title {{ font-size: 0.82rem; font-weight: 600; color: #444; }}
    .os-tabs {{ display: flex; border: 1px solid #d0d7de; border-radius: 4px; overflow: hidden; }}
    .os-tab {{ padding: 0.18rem 0.6rem; font-size: 0.75rem; background: #fff; border: none; border-right: 1px solid #d0d7de; cursor: pointer; color: #555; line-height: 1.6; }}
    .os-tab:last-child {{ border-right: none; }}
    .os-tab.active {{ background: #0969da; color: #fff; }}
    .os-tab:hover:not(.active) {{ background: #f0f0f0; }}
    .install-cmd {{ display: flex; align-items: flex-start; gap: 0.5rem; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px; padding: 0.5rem 0.75rem; }}
    .install-cmd.hidden {{ display: none; }}
    .install-cmd-code {{ flex: 1; overflow-x: auto; }}
    .install-cmd code {{ font-size: 0.78rem; white-space: pre; font-family: ui-monospace, monospace; }}
    .copy-btn {{ flex-shrink: 0; align-self: flex-start; padding: 0.15rem 0.55rem; font-size: 0.72rem; background: #fff; border: 1px solid #d0d7de; border-radius: 3px; cursor: pointer; color: #555; white-space: nowrap; }}
    .copy-btn:hover {{ background: #f0f0f0; }}
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
    <div class="all-skills-top">
      <p>Download all skills in one zip — installs everything at once.</p>
      <a class="download" href="{fat_url}" download>{fat_zip_name}</a>
    </div>
{fat_block}
  </div>
{cards}
  <footer>
    Built from <a href="{repo_url}/commit/{sha}">{short_sha}</a>
    &middot; <a href="{repo_url}">GitHub</a>
  </footer>
  <script>
    var OS_KEY = "ogc-skills-os";
    function setOS(os) {{
      localStorage.setItem(OS_KEY, os);
      document.querySelectorAll(".os-tab").forEach(function(t) {{
        t.classList.toggle("active", t.dataset.os === os);
      }});
      document.querySelectorAll(".install-cmd").forEach(function(el) {{
        el.classList.toggle("hidden", el.dataset.os !== os);
      }});
    }}
    document.querySelectorAll(".os-tab").forEach(function(btn) {{
      btn.addEventListener("click", function() {{ setOS(btn.dataset.os); }});
    }});
    setOS(localStorage.getItem(OS_KEY) || "unix");
    document.querySelectorAll(".copy-btn").forEach(function(btn) {{
      btn.addEventListener("click", function() {{
        navigator.clipboard.writeText(btn.dataset.clipboard).then(function() {{
          var orig = btn.textContent;
          btn.textContent = "Copied!";
          setTimeout(function() {{ btn.textContent = orig; }}, 1500);
        }});
      }});
    }});
  </script>
</body>
</html>
"""

(out_dir / "index.html").write_text(index_html, encoding="utf-8")
print(f"Built {len(skills)} skill(s) → {out_dir}/index.html")