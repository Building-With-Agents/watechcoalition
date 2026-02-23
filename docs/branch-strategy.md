# Branch Strategy

This document describes the repository remote, branch naming, and workflows for both the **intern program (12-week curriculum)** and **core team releases (GitFlow)**.

---

## Repository and Remote

The project uses the following remote:

- **URL**: `https://github.com/Building-With-Agents/watechcoalition.git`
- **Default branch**: `main`

When cloning or adding the remote, use:

```bash
git clone https://github.com/Building-With-Agents/watechcoalition.git
# or, if adding a remote:
git remote add origin https://github.com/Building-With-Agents/watechcoalition.git
```

---

## Intern Program (12-Week Curriculum)

Interns work in **separate branches** and do **not** merge directly into `main`. Multiple interns may work on the same curriculum items, which would cause conflicts if merged individually. The workflow uses a **staging** branch to consolidate chosen outcomes before production.

### Intern branch naming

Use this convention:

```
<their-name>-<week-#>-<description>
```

- **&lt;their-name&gt;** — Intern's first name or agreed identifier (e.g. `jordan`, `sam`).
- **&lt;week-#&gt;** — Curriculum week: `week-1`, `week-2`, … `week-12`.
- **&lt;description&gt;** — Short, kebab-case description of the work (e.g. `ingestion-agent`, `first-scrape`).

**Examples:**

- `jordan-week-1-first-scrape`
- `sam-week-3-normalization-agent`
- `jordan-week-5-streamlit-dashboard`

### Important: Do not merge intern branches into main

- Intern branches are **not** merged into `main`.
- The team reviews different outcomes together and decides which work to promote.

### Staging workflow

1. **Interns** do all work on their own branches (`<name>-week-N-<description>`). Push to `origin` for backup and review.
2. **Team** meets to review outcomes (e.g. different implementations for the same week).
3. **Leads** select which changes to promote and merge them into a **staging** branch (e.g. `staging` or `staging-week-N`).
4. **Staging** is tested and, after approval, merged into `main`.

Flow:

```
intern branches  →  (review & choose)  →  staging  →  (approval)  →  main
```

### Intern setup (clone and branch)

1. Clone the repository (see **Repository and Remote** above).
2. Create your branch from `main` (or from the branch your lead specifies):

   ```bash
   git checkout main
   git pull origin main
   git checkout -b <your-name>-week-<N>-<description>
   ```

3. Push your branch to the remote (do **not** open a PR to `main`):

   ```bash
   git push -u origin <your-name>-week-<N>-<description>
   ```

4. When the team decides to promote work, a lead will merge selected branches into `staging`; after approval, `staging` is merged into `main`.

---

## Core Team: GitFlow (Releases and Hotfixes)

The **core team** uses a GitFlow-style workflow for production releases. This applies to release management and hotfixes, not to intern curriculum branches.

### Branches overview

- **Main**: Production-ready code. Used for releases. Only vetted, approved changes (e.g. from `staging` or release/hotfix branches).
- **Staging**: Consolidation branch for approved intern work and pre-production integration. Merged into `main` upon approval.
- **Develop** (optional): Pre-production integration for core features. Feature branches may target `develop` when not using `staging`.
- **Feature Branches**: For new features, based on `develop` (or `main`), merged when complete and reviewed.
- **Release Branches**: For preparing releases; merged into `main` and back into `develop`.
- **Hotfix Branches**: Urgent fixes from `main`; merged into both `main` and `develop`.

#### Branch patterns (core team)

- `feature/*`
- `release/*`
- `hotfix/*`

> Core team: prefix branches with the appropriate prefix above. Interns use `<name>-week-N-<description>` only.

---

## Workflow Instructions

### 1. Setting Up the Development Environment

1. Clone the repository (see **Repository and Remote** for current URL):
   ```bash
   git clone https://github.com/Building-With-Agents/watechcoalition.git
   cd watechcoalition
   ```
2. Checkout the default branch and pull latest:
   ```bash
   git checkout main
   git pull origin main
   ```
   **Interns:** then create your branch using the naming convention in **Intern Program** above. **Core team:** use `develop` if your workflow uses it, or branch from `main` for feature/release/hotfix work.

### 2. Creating a Feature Branch

1. Ensure you're on the `develop` branch:
   ```bash
   git checkout develop
   ```
2. Create a new feature branch:
   ```bash
   git checkout -b feature/[feature-name]
   ```
3. Implement your feature, commit changes frequently:
   ```bash
   git add .
   git commit -m "Describe your changes"
   ```
4. Push the feature branch to the remote repository:
   ```bash
   git push -u origin feature/[feature-name]
   ```
5. Once complete, open a PR to merge into `develop`:
   - Code review by at least one person is required.
   - Code review can be completed by the submitter for simple changes.
   - It is encouraged to request review by another developer.
6. Once the feature branch is merged into `develop`. Delete the feature branch:
   ```bash
   git branch -d feature/[feature-name]
   git push origin --delete feature/[feature-name]
   ```

### 3. Creating a Release Branch

1. Create a release branch from `develop`:
   ```bash
   git checkout develop
   git checkout -b release/[release-version]
   ```
2. Push release branch upstream.

   ```bash
   git push -u origin release/[release-version]
   ```

3. Applying fixes to the release branch should be done as follows:
   - Ensure you are on the correct release branch.
     ```bash
     git checkout release/[release-version]
     git checkout -b fix/[release-version]/[fix-description]
     ```
   - Commit your fix and push upstream.
     ```bash
     git add .
     git commit -m "Description of fix"
     git push -u origin fix/[release-version]/[fix-description]
     ```
   - Open a pull request to merge fix into `release/[release-version]` branch.
   - Once successfully merged into `release/[release-version]` update your local `release/[release-version]` branch.
   - Delete your fix branch.

4. Create a pull request to merge into `develop`.
5. After successful merge into `develop` update your local `develop` branch.

### 4. Merging release into `main`.

1. Before merging release into `main` UAT issues, and all open bug fixes need resolved. In addition, any copy and
   navigation should be signed off by marketing team.
2. Open PR to merge `release/[release-version]` into `main`.
3. After successful merge into `main`:
   - Tag the release:
     ```bash
     git checkout main
     git tag -a [release-version] -m "Release [release-version]"
     git push --tags
     ```
4. Open a PR to merge the release branch back into `develop`:

5. Once the release branch has been successfully merged into `develop`. Delete the release branch:
   ```bash
   git branch -d release/[release-version]
   git push origin --delete release/[release-version]
   ```

#### 5. Creating a Hotfix Branch

1. Create a hotfix branch from `main`:
   ```bash
   git checkout main
   git checkout -b hotfix/[hotfix-description]
   ```
2. Apply the hotfix, commit changes, and push upstream:
   ```bash
   git add .
   git commit -m "Apply hotfix [hotfix-description]"
   git push -u origin hotfix/[hotfix-description]
   ```
3. Create pull requests to merge the hotfix into both `main` and `develop`.
4. After successful merge into `main`:
   - Tag the hotfix release. This can be done either through Azure or by checking out `main` locally and using the CLI
     commands:
     ```bash
     git tag -a [hotfix-version] -m "Hotfix [hotfix-version]"
     git push --tags
     ```
5. After successful merge into `develop`, delete the hotfix branch:
   ```bash
   git branch -d hotfix/[hotfix-description]
   git push origin --delete hotfix/[hotfix-description]
   ```

---

## Summary of Branching Rules

- **Main**: Only production-ready code. Updated from `staging` (after approval) or from release/hotfix branches.
- **Staging**: Consolidation branch for approved intern work; merged into `main` upon approval. **Intern branches are never merged directly into `main`.**
- **Intern branches** (`<name>-week-N-<description>`): For 12-week curriculum work. Pushed to remote for review; selected outcomes are merged into `staging` by leads.
- **Develop**: (Optional) Pre-production integration for core team; all completed and reviewed features, ready for release.
- **Feature**: Core team — new features, merged into `develop` (or target branch) upon completion.
- **Release**: Core team — preparing releases, merged into both `main` and `develop`.
- **Hotfix**: Core team — urgent fixes, merged into both `main` and `develop`.

---

## Branch Protection (GitHub)

If using GitHub for this repository, configure branch protection to align with this workflow:

- Restrict direct pushes to `main` and `staging`.
- Require pull requests to merge into `main` and `staging`.
- Require review (and optionally passing checks) before merging to `main`.
- Allow interns and contributors to push their named branches (e.g. `*-week-*`, `feature/*`) without merging them into `main` directly.
