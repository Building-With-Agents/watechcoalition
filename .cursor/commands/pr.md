Create a pull request for the current changes.

1. Run `git diff` to see staged and unstaged changes
2. Run `git log --oneline -5` to see recent commit context
3. Write a clear commit message summarizing what changed
4. Stage relevant files (never stage .env or credentials)
5. Commit and push to the current branch
6. Use `gh pr create` to open a pull request with a descriptive title and body
7. Return the PR URL when done
