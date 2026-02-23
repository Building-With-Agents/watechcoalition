Verify the agent pipeline is healthy after recent changes.

1. Run `cd agents && ruff check .` — lint check
2. Run `cd agents && pytest tests/ -v` — full test suite
3. If the Streamlit dashboard exists, verify it imports cleanly: `python -c "import agents.dashboard.streamlit_app"`
4. Summarize: which agents pass, which fail, any lint issues
5. If any failures, prioritize them by severity
