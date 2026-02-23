Run the test suite for the agent pipeline.

1. Identify which agent is being worked on from the current file context
2. Run `cd agents && pytest <agent>/tests/ -v` for that specific agent
3. If no specific agent context, run `cd agents && pytest tests/ -v` for the full suite
4. Report pass/fail counts and any failures with tracebacks
5. If tests fail, suggest fixes based on the error output
