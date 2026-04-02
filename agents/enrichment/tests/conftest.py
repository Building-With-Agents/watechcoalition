"""Pytest configuration for enrichment tests."""

# Manual CLI script lives beside unit tests; do not collect it as a test module.
collect_ignore = ["test_naics_integration.py", "test_employer_integration.py"]
