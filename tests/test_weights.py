"""Tests for pairwise weights"""

import math

import pytest

from main.main import main
from main.pairwise import Pairwise
from tests.helpers import covered_pairs, expected_pairs, parse_configurations


def test_unfulfillable_weight(runner, create_file):
    """Test warn message when weights cannot be fulfilled"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]}, "Weights": {"a": 2, "x": 3}}
    filename = create_file(data)
    with pytest.warns(UserWarning, match="No more unique configuration meeting the requirements"):
        runner.invoke(main, [filename], catch_exceptions=False)


def test_weight(runner, create_file):
    """Test pairwise weights"""
    data = {
        "Parameters": {"P1": ["a", "b", "c", "d"], "P2": ["e", "f", "g", "h"], "P3": ["x", "y"], "P4": ["1", "2"]},
        "Weights": {"a": 2, "e": 0},
    }
    filename = create_file(data)
    result = runner.invoke(main, ["--count", filename])
    assert "('a', 7)" in result.stderr
    assert "('b', 4)" in result.stderr
    assert "('c', 4)" in result.stderr
    assert "('d', 4)" in result.stderr
    assert "('e', 4)" in result.stderr
    # Counts go to stderr so that stdout carries only the configurations.
    assert "('a', 7)" not in result.stdout

    result = runner.invoke(main, ["--count", "--margin", "0", filename])
    assert "('e', 4)" in result.stderr


def kl_divergence(spec, configurations):
    """KL divergence of each value's observed share from the share its weight asks for.

    Computed from the configurations alone, independently of the generator. A value
    with no weight counts as weight 1.
    """
    weights = spec.get("Weights", {})
    divergence = {}
    for kind, values in spec["Parameters"].items():
        counts = {value: sum(conf[kind] == value for conf in configurations) for value in values}
        total_count = sum(counts.values())
        total_weight = sum(weights.get(value, 1) for value in values)
        for value in values:
            observed = counts[value] / total_count
            wanted = weights.get(value, 1) / total_weight
            divergence[value] = observed * math.log(observed / wanted)
    return divergence


@pytest.mark.parametrize("margin", [0.05, 0.2])
@pytest.mark.parametrize(
    "spec",
    [
        {"Parameters": {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]}, "Weights": {"a": 2}},
        {
            "Parameters": {"P1": ["a", "b", "c", "d"], "P2": ["e", "f", "g", "h"], "P3": ["x", "y"], "P4": ["1", "2"]},
            "Weights": {"a": 2},
        },
    ],
)
def test_weights_within_margin(spec, margin):
    """When generation succeeds, every value's share is within the margin of its weight"""
    pairwise = Pairwise(spec, margin)
    assert pairwise.generate_configurations()
    divergence = kl_divergence(spec, pairwise.configurations)
    over = {value: d for value, d in divergence.items() if abs(d) > margin}
    assert not over, f"values outside margin {margin}: {over}"


@pytest.mark.parametrize(
    "spec",
    [
        # A weight above 1 asks for extra configurations containing "a".
        {"Parameters": {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]}, "Weights": {"a": 2}},
        # A weight of 0 marks "a" as needed only for pairwise coverage.
        {"Parameters": {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]}, "Weights": {"a": 0}},
        # Both kinds of weight on a larger, asymmetric input.
        {
            "Parameters": {"P1": ["a", "b", "c", "d"], "P2": ["e", "f", "g", "h"], "P3": ["x", "y"], "P4": ["1", "2"]},
            "Weights": {"a": 2, "e": 0},
        },
    ],
)
def test_weighted_pairwise_covers_all_pairs(runner, create_file, spec):
    """Weights may add configurations, but must never cost pairwise coverage"""
    filename = create_file(spec)
    result = runner.invoke(main, ["--output", "json", filename])
    assert result.exit_code == 0
    configurations = parse_configurations(result.stdout)
    missing = expected_pairs(spec["Parameters"]) - covered_pairs(configurations)
    assert not missing, f"uncovered pairs: {missing}"


def test_exhausted_weights_still_cover_all_pairs(runner, create_file):
    """When the weights can't be met, the tool warns but still covers every pair"""
    parameters = {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]}
    filename = create_file({"Parameters": parameters, "Weights": {"a": 0, "x": 3}})
    with pytest.warns(UserWarning, match="No more unique configuration meeting the requirements"):
        result = runner.invoke(main, ["--output", "json", filename], catch_exceptions=False)
    configurations = parse_configurations(result.stdout)
    missing = expected_pairs(parameters) - covered_pairs(configurations)
    assert not missing, f"uncovered pairs: {missing}"
