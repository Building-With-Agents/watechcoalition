# Branch Strategy

This document describes the repository branching model, workflows, and collaboration practices for the **Building with Agents** program.

---

## Repository and Remote

- **URL**: `https://github.com/Building-With-Agents/watechcoalition.git`
- **Default branch**: `development`

```bash
git clone https://github.com/Building-With-Agents/watechcoalition.git
cd watechcoalition
```

After cloning you will be on `development` automatically.

---

## Branch Model Overview

```
development          ← default branch, protected (PRs required)
  │
  ├── ricardo-week-3-source-pilot        (solo or paired work)
  ├── angel-week-3-source-pilot
  ├── fatima-week-3-database-storage
  ├── bryan-week-3-event-bus
  └── ...
```

| Branch | Purpose | Who merges |
|--------|---------|------------|
| `development` | Stable integration branch. All experiments branch from here and merge back via PR. | Lead (after review) |
| `main` | Production releases only. Updated from `development` at program milestones. | Lead only |
| `<name>-week-N-<task>` | Your working branch for the current week's experiment or task. | You open the PR; lead merges. |

> **Rule:** Nobody pushes directly to `development` or `main`. All changes go through pull requests.

---

## Developer Workflow

### 1. Start of each week — create your branch

Always branch from the latest `development`:

```bash
git checkout development
git pull origin development
git checkout -b <your-name>-week-<N>-<task>
```

**Naming convention:** `<first-name>-week-<N>-<task>`

| Example | Experiment |
|---------|------------|
| `ricardo-week-3-source-pilot` | EXP-001 |
| `fatima-week-3-database-storage` | EXP-002 |
| `nestor-week-3-dedup-strategy` | EXP-003 |
| `bryan-week-3-event-bus` | EXP-004 |
| `juan-week-3-scheduling` | EXP-005 |
| `enrique-week-3-observability` | EXP-006 |
| `fabian-week-3-multi-agent-framework` | EXP-007 |

### 2. Work and commit frequently

Make small, focused commits as you go. Don't wait until everything is done.

```bash
git add <files-you-changed>
git commit -m "add jsearch adapter with rate limiting"
```

Good commit messages are short and describe **what** you did:
- `add base source adapter ABC`
- `fix dedup hash collision on salary field`
- `add test for event bus throughput`

Avoid vague messages like `update`, `fix stuff`, or `wip`.

### 3. Push upstream daily

Push your branch to GitHub **at least once per day**, even if work is incomplete. This ensures:
- Your work is backed up
- Teammates on paired experiments can see your progress
- Your lead can check in without asking

```bash
git push origin <your-branch>
```

First push requires the `-u` flag to set the upstream tracking:

```bash
git push -u origin ricardo-week-3-source-pilot
```

After that, `git push` is enough.

### 4. Open a Draft PR early

As soon as you have your first push, open a **Draft PR** against `development`. This is not a request to merge — it's a signal that says "here's where I am."

```bash
gh pr create --draft \
  --title "EXP-001: source pilot (Ricardo)" \
  --body "Work in progress — source adapter implementation for Crawl4AI and JSearch." \
  --base development
```

Or use the GitHub web UI: when creating a PR, click the dropdown arrow on the green button and select **Create draft pull request**.

**Why draft PRs matter:**
- Teammates on your experiment can see exactly what you've pushed
- Your lead can leave early feedback before you're "done"
- You get a clear diff of everything you've changed vs `development`
- The CI checks (Python tests) run on every push so you catch issues early

When your work is ready for review, convert the draft to a regular PR by clicking **Ready for review** on the PR page.

### 5. Keep your branch up to date

`development` may receive merges from other experiments while you're working. Pull those changes into your branch regularly to avoid big merge conflicts later.

```bash
git checkout <your-branch>
git pull origin development
```

If there are conflicts, Git will tell you. See the **Resolving Merge Conflicts** section below.

**Do this at least once per day**, ideally at the start of your work session.

### 6. PR review and merge

When your experiment is complete:

1. Convert your draft PR to **Ready for review** (if not already).
2. Ensure CI checks pass (Python tests must be green).
3. Your lead reviews the PR.
4. Lead merges the PR into `development`.
5. Delete your branch after merge (GitHub offers a button for this).

---

## Collaborative Experiments (Paired Work)

Some experiments are assigned to pairs:

| Experiment | Team | Notes |
|------------|------|-------|
| EXP-001 — Source Pilot | Ricardo + Angel | Two source adapters, shared test fixtures |
| EXP-004 — Event Bus | Bryan + Emilio | One owns implementation, one owns test harness |

### How paired experiments work

Each person keeps their **own branch** — you do NOT share a single branch. This avoids stepping on each other's files and makes individual contributions visible.

```
ricardo-week-3-source-pilot    ← Ricardo's branch
angel-week-3-source-pilot      ← Angel's branch
```

**Coordination approach:**

1. **Divide the work clearly.** Before coding, agree on who owns which files. Write it down in your PR description. Example for EXP-001:
   - Ricardo: `jsearch_adapter.py`, `crawl4ai_indeed.py`
   - Angel: `crawl4ai_usajobs.py`, `scraper_adapter.py`, shared test fixtures

2. **Stay in your lane.** If you need to change a file your partner owns, talk to them first. Don't both edit the same file at the same time.

3. **Check each other's PRs.** Read your partner's draft PR daily. Leave comments if something affects your work. A quick "looks good" or "heads up, I'm depending on the return type here" goes a long way.

4. **Merge sequentially.** When both are ready, the lead merges one PR first, then the second person rebases and resolves any conflicts before their PR is merged.

### Communication expectations for pairs

- **Daily check-in** (Slack/Discord, 5 min): "What I did, what I'm doing, any blockers."
- **Before starting work**: Pull latest `development` to pick up anything your partner merged.
- **Before editing a shared file**: Message your partner — "I need to update `base_adapter.py`, are you working on it?"
- **When you push**: Let your partner know — "Just pushed my adapter tests, take a look when you can."

---

## Git Cheat Sheet

### Everyday commands

```bash
# Start of day — sync up
git checkout development
git pull origin development
git checkout <your-branch>
git pull origin development            # bring new changes into your branch

# Work cycle
git status                              # see what changed
git diff                                # see the actual changes
git add <file1> <file2>                 # stage specific files
git commit -m "description of change"   # commit
git push                                # push to GitHub

# End of day — always push
git push
```

### Branch management

```bash
# Create a new branch from development
git checkout development
git pull origin development
git checkout -b <your-name>-week-<N>-<task>

# First push (sets upstream tracking)
git push -u origin <your-branch>

# Switch between branches
git checkout development
git checkout <your-branch>

# See all branches
git branch -a

# Delete a branch locally after it's been merged
git branch -d <branch-name>
```

### Pull request commands (GitHub CLI)

```bash
# Open a draft PR
gh pr create --draft \
  --title "EXP-001: source pilot (Ricardo)" \
  --body "WIP — implementing source adapters" \
  --base development

# Check PR status
gh pr status

# View your PR in the browser
gh pr view --web

# Mark draft as ready for review
gh pr ready

# See CI check results
gh pr checks
```

### Checking what's going on

```bash
# See recent commits on your branch
git log --oneline -10

# See what files you've changed vs development
git diff development --name-only

# See who changed a specific file recently
git log --oneline -5 -- <file-path>
```

---

## Avoiding Merge Conflicts

Merge conflicts happen when two people edit the same lines in the same file. They're normal, but you can minimize them.

### Prevention

1. **Pull `development` into your branch daily.** Small frequent merges are easy. One big merge at the end is painful.
   ```bash
   git pull origin development
   ```

2. **Don't edit files outside your experiment scope.** If your experiment is EXP-003 (dedup), don't modify event bus files. If you find a bug in shared code, tell your lead instead of fixing it yourself.

3. **For paired experiments, divide file ownership.** Each person edits different files. If you both need to touch the same file, coordinate before editing.

4. **Commit and push often.** Small commits are easier to merge than one giant commit at the end of the week.

5. **Don't reformat files you didn't change.** Auto-formatters and linters can cause conflicts across every line. Only format files you actually modified.

### Resolving Merge Conflicts

When `git pull origin development` shows conflicts:

```bash
# Git tells you which files have conflicts
# Open each conflicted file — look for conflict markers:

<<<<<<< HEAD
your version of the code
=======
the other version from development
>>>>>>> origin/development
```

**Steps to resolve:**
1. Open the file and find the `<<<<<<<` markers.
2. Decide which version to keep (yours, theirs, or a combination).
3. Delete the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
4. Save the file.
5. Stage and commit:
   ```bash
   git add <resolved-file>
   git commit -m "resolve merge conflict in <file>"
   ```

**If you're stuck**, ask your lead or partner for help. Don't force-push or reset to make conflicts "go away" — that loses work.

---

## Branch Protection Rules

| Branch | Direct push | PRs required | Required checks | Force push |
|--------|-------------|-------------|-----------------|------------|
| `development` | Blocked | Yes | `python-tests` must pass | Lead only |
| `main` | Blocked | Yes | `python-tests` + `build` | Lead only |
| `<name>-week-*` | Allowed | No (but draft PR encouraged) | CI runs on PR | Allowed |

---

## Core Team: GitFlow (Releases and Hotfixes)

> This section applies to the core team managing production releases, not to weekly experiment work.

### Branches

| Branch | Purpose |
|--------|---------|
| `main` | Production releases only |
| `development` | Integration branch (default) |
| `feature/*` | New features (core team) |
| `release/*` | Release preparation |
| `hotfix/*` | Urgent production fixes |

### Release workflow

1. Create release branch from `development`:
   ```bash
   git checkout development
   git checkout -b release/<version>
   ```
2. Apply release fixes on the release branch.
3. Merge release into `main` via PR. Tag the release:
   ```bash
   git checkout main
   git tag -a <version> -m "Release <version>"
   git push --tags
   ```
4. Merge release back into `development`.
5. Delete the release branch.

### Hotfix workflow

1. Branch from `main`:
   ```bash
   git checkout main
   git checkout -b hotfix/<description>
   ```
2. Fix, commit, push. Open PRs to both `main` and `development`.
3. Tag the hotfix on `main` after merge.
4. Delete the hotfix branch.
