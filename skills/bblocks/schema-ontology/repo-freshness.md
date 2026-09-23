# Checking Local Repositories Are Up to Date

Run this check on **every local git repository you read from or change**. That includes the repo you
are working in, a local clone of an imported register, a sibling bblocks repo, and a clone of
`bblocks-postprocess` or the viewer. Run it **before** you rely on the repo's content or edit it.

## Why this matters for OGC Blocks

A stale clone gives wrong answers that look right:

- Registers commit their build outputs back through CI. Commits titled *"Building blocks
  postprocessing"* land on the default branch without any person pushing, so clones fall behind
  quickly even when nobody is actively editing.
- The viewer and dependent registers read the **published** `register.json`, not your clone. If your
  local `bblocks-config.yaml` says `imports: []` but upstream has since added an import, the viewer's
  import graph shows a dependency you can't find locally.
- Editing an out-of-date copy produces merge conflicts at PR time. This is especially true in the
  generated `build/` tree.

**Worked example:** a register graph showed *OGC Main → OGC API Common*, but the local
`opengeospatial/bblocks` clone had `imports: []`. The clone was about 15 commits behind. One of those
commits had added `imports: ["@ogc/ogcapi-common"]`, and the live `register.json` already listed the
import. Running this check first would have answered the question straight away.

## Procedure

Run these from the repository root with a POSIX shell (Git Bash on Windows).

### 1. Fetch and measure

```bash
git fetch --quiet --all --prune || echo "WARN: fetch failed (offline?) — freshness unknown"
UP=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
# No tracking branch: compare with the default branch of the canonical remote instead
[ -z "$UP" ] && UP=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null)
read AHEAD BEHIND < <(git rev-list --left-right --count HEAD..."$UP")
echo "vs $UP: ahead=$AHEAD behind=$BEHIND"
```

**Forks:** when the clone has more than one remote (for example `origin` and `fork`, or `origin` and
`upstream`), also compare against the **canonical** repository. This is the remote whose URL is the
organisation repo (`opengeospatial/…`, `ogcincubator/…`), not the user's fork. A fork's branch can be
level with the fork and still be behind the canonical repo.

If the fetch fails, tell the user that freshness could not be verified and continue.

### 2. If `BEHIND` is 0

The copy is current. Carry on.

### 3. If `BEHIND` > 0, predict conflicts without touching the working tree

```bash
CONFLICT=0
# (a) Uncommitted changes to files that upstream also changed would block the pull
DIRTY=$(git status --porcelain | cut -c4-)
INCOMING=$(git diff --name-only HEAD..."$UP")
OVERLAP=$(comm -12 <(echo "$DIRTY" | sort -u) <(echo "$INCOMING" | sort -u))
[ -n "$OVERLAP" ] && CONFLICT=1 && echo "Local edits overlap incoming changes:" && echo "$OVERLAP"

# (b) Diverged branches (AHEAD > 0): trial merge in memory
if [ "$AHEAD" -gt 0 ]; then
  git merge-tree --write-tree --name-only HEAD "$UP" >/dev/null 2>&1; RC=$?
  if [ $RC -eq 1 ]; then CONFLICT=1
  elif [ $RC -ne 0 ]; then   # git < 2.38 has no --write-tree (usage error): legacy trial merge
    git merge-tree "$(git merge-base HEAD "$UP")" HEAD "$UP" | grep -q '^+<<<<<<<' && CONFLICT=1
  fi
fi
echo "CONFLICT=$CONFLICT"
```

`git merge-tree --write-tree` (git 2.38 and later) exits 0 for a clean merge and 1 for conflicts.
Older git rejects the option. The legacy form used in that case can miss some conflict types, such as
modify/delete, so treat a clean result from it as likely rather than certain.

### 4. Conflicts predicted: stop and warn

**Stop.** Don't pull, don't make edits, and don't answer questions from the stale content as if it
were current. Tell the user:

- the repository path and the upstream ref
- how far ahead and behind the branch is
- which files would conflict (from `OVERLAP` or `git merge-tree` output)
- the options: commit or stash their local work and then merge, rebase, or continue knowingly against
  the stale copy

Resolving the conflict is the user's decision. Wait for their instruction.

### 5. No conflicts: apply the user's update preference

Look for a stated preference for automatically updating local repositories. Check the agent's
persisted instructions or memory (for example `CLAUDE.md` or a saved memory note) and any earlier
answer in the session:

| Preference | Action |
|---|---|
| **always** | Update now and report it in one line (repo, commits pulled). |
| **ask** (default when nothing is recorded) | Ask the user whether to update this repo. Offer to remember the answer as *always* or *never*. |
| **never** | Don't update. Warn that the copy is `BEHIND` commits stale. |

Automatic updates are **fast-forward only**:

```bash
git merge --ff-only "$UP"
```

A fast-forward never rewrites history or creates merge commits, and it keeps uncommitted edits to
files that upstream didn't change. If the branch has **diverged** (`AHEAD` > 0), even with no conflicts
predicted, integrating needs a merge or rebase. Ask for explicit confirmation every time, whatever the
preference says.

### 6. Continuing with a stale copy

If the user declines the update, say that results reflect the stale copy. When the question is about
the **current** state, read upstream content without changing the working tree:

```bash
git show "$UP":bblocks-config.yaml
git log --oneline HEAD.."$UP"        # what you are missing
```

For registers, the published `register.json` (at the register's `baseURL`) is what the viewer and
importers actually see. Compare its `modified` timestamp with the local copy's.

## Scope notes

- Check each repository once per session, and again before any commit or PR that you prepare.
- The check is read-only up to step 5. Only an approved or pre-authorised fast-forward changes
  anything.
