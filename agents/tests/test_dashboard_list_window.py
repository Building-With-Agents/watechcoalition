"""Tests for dashboard list window clamping."""

from __future__ import annotations

from agents.dashboard.streamlit_app import _clamp_list_window


class TestClampListWindow:
    def test_defaults_within_bounds(self) -> None:
        assert _clamp_list_window(500, 0) == (500, 0)

    def test_limit_capped_high(self) -> None:
        assert _clamp_list_window(99_999, 0)[0] == 5000

    def test_limit_floor(self) -> None:
        assert _clamp_list_window(0, 0)[0] == 1

    def test_offset_non_negative(self) -> None:
        assert _clamp_list_window(100, -5)[1] == 0
