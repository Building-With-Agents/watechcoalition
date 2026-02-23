Lint and format-check the Python agent code.

1. Run `cd agents && ruff check . --output-format=concise`
2. Run `cd agents && ruff format --check .`
3. Report any issues found
4. If there are auto-fixable issues, ask if I should run `ruff check --fix .` and `ruff format .`
