"""Tests for pairwise weights"""

import pytest

from main.main import main


def test_unfulfillable_weight(runner, create_file):
    """Test warn message when weights cannot be fulfilled"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"]}, "Weights": {"a": 2, "x": 3}}
    filename = create_file(data)
    with pytest.warns(UserWarning, match="No more unique configuration meeting the requirements"):
        runner.invoke(main, [filename], catch_exceptions=False)


def test_weight(runner, create_file):
    """Test pairwise weights"""
    data = {
        "Parameters": {"P1": ["a", "b", "c", "d"], "P2": ["e", "f", "g", "h"], "P3": ["x", "y"], "P4": [1, 2]},
        "Weights": {"a": 2, "e": 0},
    }
    filename = create_file(data)
    result = runner.invoke(main, ["--count", filename])
    assert "('a', 7)" in result.output
    assert "('b', 4)" in result.output
    assert "('c', 4)" in result.output
    assert "('d', 4)" in result.output
    assert "('e', 4)" in result.output

    result = runner.invoke(main, ["--count", "--margin", "0", filename])
    assert "('e', 4)" in result.output
