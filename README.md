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

More skill sets are planned — see the [open issues](https://github.com/ogcincubator/ogc-llm-skills/issues) for what's coming.

---

## Installing a skill

Skills are published as zip files on the
[GitHub Pages index](https://ogcincubator.github.io/ogc-llm-skills/).
Download the zip for the skill you want, then follow the instructions for your tool:

### claude.ai

1. Go to **Settings → Features → Skills**.
2. Upload the zip file.
3. The skill is now available in your conversations.

See [How to create custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
in the Claude Help Center.

### Claude Code

Extract the zip into a skills directory:

```bash
# Project-level (only available in this project)
mkdir -p .claude/skills
unzip bblocks-authoring.zip -d .claude/skills/bblocks-authoring

# User-level (available in all projects)
mkdir -p ~/.claude/skills
unzip bblocks-authoring.zip -d ~/.claude/skills/bblocks-authoring
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

On every push to `main` (and on manual trigger), a GitHub Actions workflow:

1. Finds all `SKILL.md` files in the repository.
2. Zips each skill directory (contents at the zip root, no parent path prefix).
3. Names each zip after its directory path with slashes replaced by hyphens
   (e.g. `bblocks/authoring/` → `bblocks-authoring.zip`).
4. Generates an `index.html` listing all skills with download links.
5. Deploys everything to GitHub Pages.

Download links include a `?v=<sha>` query parameter to prevent stale cached
downloads when skills are updated.