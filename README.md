# OGC LLM Skills

Reusable reference skills for LLM tooling, covering OGC standards and tooling.
Each skill packages domain-specific knowledge so Claude (or any compatible model)
can answer questions and assist with tasks in that domain without needing the
information repeated in every conversation.

Skills follow the [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
format: a directory with a `SKILL.md` entry point (containing YAML frontmatter)
and supporting reference files. This format is supported by claude.ai, Claude
Code, and the Claude API.

---

## Available skills

| Skill | Description |
|-------|-------------|
| [`bblocks/authoring`](bblocks/authoring/SKILL.md) | Authoring OGC Blocks registers: source file structure, metadata, schemas, examples, tests, semantic annotations, transforms, and validation. |
| [`bblocks/consuming`](bblocks/consuming/SKILL.md) | Consuming published OGC Blocks registers: resolving `bblocks://` refs, validating data, semantic uplift, and the `bblocks-client-python` library. |
| [`bblocks/schema-ontology`](bblocks/schema-ontology/SKILL.md) | Retrofitting formal semantics to an existing schema OGC Block: authoring a reusable ontology block and binding it via a JSON-LD context, with optional semantic uplift. |

More skill sets are planned — see the [open issues](https://github.com/ogcincubator/ogc-llm-skills/issues) for what's coming.

---

## Installing a skill

Skills are published as zip files on the
[GitHub Pages index](https://ogcincubator.github.io/ogc-llm-skills/).
Download the zip for the skill you want, then follow the instructions for your tool.

An `all-skills.zip` bundling every skill is also published, alongside a
[`manifest.json`](https://ogcincubator.github.io/ogc-llm-skills/manifest.json) and
[`llms.txt`](https://ogcincubator.github.io/ogc-llm-skills/llms.txt) — machine-readable
entrypoints meant for an agent to fetch directly and use to install or update skills
on the user's behalf, without a human downloading anything by hand.

### claude.ai

1. Go to **Settings → Features → Skills**.
2. Upload the zip file.
3. The skill is now available in your conversations.

See [How to create custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
in the Claude Help Center.

### Claude Code

**`npx skills` (recommended if you have it)**

```bash
npx skills add https://github.com/ogcincubator/ogc-llm-skills/tree/master/bblocks/authoring
```

Swap in the path of the skill you want (see the table above), or install
everything at once with:

```bash
npx skills add https://github.com/ogcincubator/ogc-llm-skills/tree/master --full-depth
```

This installs straight from source, so it skips the `.version` file and the
"Updating this skill" section that the published zips carry — use the manual
method below if you want those.

**Manual**

Each zip wraps its contents in a top-level directory named after the skill
(e.g. `bblocks-authoring/`), so extract it directly into a skills directory:

```bash
# macOS / Linux — project-level (only available in this project)
mkdir -p .claude/skills
unzip bblocks-authoring.zip -d .claude/skills

# macOS / Linux — user-level (available in all projects)
mkdir -p ~/.claude/skills
unzip bblocks-authoring.zip -d ~/.claude/skills
```

```powershell
# Windows — user-level (available in all projects)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills" | Out-Null
Expand-Archive -Path bblocks-authoring.zip -DestinationPath "$env:USERPROFILE\.claude\skills" -Force
```

Claude Code discovers skills automatically at startup.

### Claude API

Upload the skill via the Skills API and reference it in your requests.
See [Use Skills with the Claude API](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

---

## Adding a new skill

1. Create a directory under an appropriate namespace (e.g. `bblocks/consuming/`).
2. Add a `SKILL.md` with required YAML frontmatter:

   ```markdown
   ---
   name: your-skill-name
   description: "What this skill covers and when to use it."
   ---

   # Your Skill Title
   ...
   ```

   `name`: lowercase letters, numbers, hyphens, max 64 characters.
   `description`: plain text, max 1024 characters, should state both what
   the skill covers and when Claude should use it.

3. Add supporting reference files (additional `.md` files, `examples/`, etc.)
   in the same directory. Keep each file focused on a single lookup unit.

4. Open a pull request — the Pages workflow will publish the new skill
   automatically when the PR is merged.

---

## How publishing works

On every push to `master` (and on manual trigger), a GitHub Actions workflow:

1. Finds all `SKILL.md` files in the repository.
2. Zips each skill directory, with contents wrapped in a top-level folder
   named after the skill, plus a generated `.version` file (`commit`, `date`,
   `zip_url`, `manifest_url`, `llms_txt`) and an "Updating this skill" section
   appended to `SKILL.md` — neither of which lives in the source directory.
3. Names each zip after its directory path with slashes replaced by hyphens
   (e.g. `bblocks/authoring/` → `bblocks-authoring.zip`, containing a
   `bblocks-authoring/` folder).
4. Builds `all-skills.zip`, bundling every skill the same way.
5. Generates `manifest.json` and `llms.txt` for agent-driven install/update.
6. Generates an `index.html` listing all skills with download links.
7. Deploys everything to GitHub Pages.

Download links include a `?v=<sha>` query parameter to prevent stale cached
downloads when skills are updated.