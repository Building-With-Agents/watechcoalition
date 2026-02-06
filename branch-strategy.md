# GitFlow Branching Strategy

This project follows the **GitFlow branching strategy**, designed to streamline release management and ensure a
structured development workflow.

## Branches Overview

- **Main Branch**: Contains production-ready code. This is the branch used for releases. Only thoroughly vetted and
  tested changes are merged here.
- **Develop Branch**: Contains pre-production code. All new features are based on this branch and merged back when
  completed.
- **Feature Branches**: Used to develop new features. These are temporary branches based on `develop` and merged back
  when the feature is complete and reviewed.
- **Release Branches**: Used for preparing new production releases. These branches handle final touches and minor bug
  fixes before merging into `main` and `develop`.
- **Hotfix Branches**: Created to address urgent changes in the `main` branch. These fixes are merged back into
  both `main` and `develop`.

#### Policies have been enforced for the following patterns:

- `feature/*`
- `release/*`
- `hotfix/*`

> Please prefix your branches with the appropriate prefix above. Most likely it will be a feature branch.

---

## Workflow Instructions

### 1. Setting Up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://CFA1@dev.azure.com/CFA1/Career%20Services/_git/CoalitionWebsite
   ```
2. Checkout the `develop` branch:
   ```bash
   git checkout develop
   ```

### 2. Creating a Feature Branch

1. Ensure you’re on the `develop` branch:
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

- **Main**: Only production-ready code.
- **Develop**: All completed and reviewed features, ready for release.
- **Feature**: For developing new features, merged into `develop` upon completion.
- **Release**: For preparing releases, merged into both `main` and `develop`.
- **Hotfix**: For urgent fixes, merged into both `main` and `develop`.

---

## Azure Permissions Summary

To align with this workflow, Azure permissions will be set up to enforce branching policies:

- [x] Restrict direct pushes to `main` and `develop`.
- [x] Require pull requests for merging branches.
- [x] Enforce peer reviews for pull requests (Can review own PRs for now).
- [x] Require passing CI/CD checks before merging.

| Action                       | Branch        | Group          | Permission             |
| ---------------------------- | ------------- | -------------- | ---------------------- |
| Push direct                  | main, develop | Contributors   | Deny                   |
| Create pull request          | main, develop | Contributors   | Allow                  |
| Merge via PR                 | main, develop | Contributors   | Allow (after approval) |
| Push feature branches        | feature/\*    | Contributors   | Allow                  |
| Push tags                    | All branches  | Contributors   | Allow                  |
| Check for comment resolution | main          | Contributors   | Required               |
| Check for comment resolution | develop       | Contributors   | Optional               |
| Override policies            | All branches  | Project Admins | Deny                   |
