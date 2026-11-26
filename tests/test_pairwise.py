"""Test for pairwise tool"""

import pytest

from main.main import main
from parameters_check import InsufficientKinds  # pylint: disable=wrong-import-order
from tests.helpers import covered_pairs, expected_pairs, parse_configurations


@pytest.fixture()
def input_file(create_file):
    """Create file with input parameters"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]}}
    return create_file(data)


def test_pairwise(runner, input_file):
    """Legacy test: exact output (default CSV format) for the smallest input, kept from the original suite"""
    result = runner.invoke(main, [input_file])
    assert result.exit_code == 0
    assert "P1,P2,P3\na,2,y\na,1,x\nb,1,y\nb,2,x\n" == result.stdout


@pytest.mark.parametrize(
    "parameters",
    [
        {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]},  # symmetric
        {"P1": ["a", "b", "c", "d"], "P2": ["1", "2"], "P3": ["x", "y"]},  # asymmetric, drives triplet logic
        {"P1": ["a", "b"], "P2": ["1", "2"]},  # two kinds
        {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"], "P4": ["m", "n"]},  # four kinds
        {"P1": ["a", "b", "c"], "P2": ["1", "2", "3"], "P3": ["x", "y", "z"]},  # three values per kind
        {"P1": ["a", "b", "c", "d", "e"], "P2": ["1", "2", "3"], "P3": ["x", "y"]},  # all arities differ
        {"P1": ["a"], "P2": ["1", "2"], "P3": ["x", "y"]},  # single-value kind
    ],
)
def test_pairwise_covers_all_pairs(runner, create_file, parameters):
    """The generated configurations must cover every cross-kind value pair"""
    filename = create_file({"Parameters": parameters})
    result = runner.invoke(main, ["--output", "json", filename])
    assert result.exit_code == 0
    configurations = parse_configurations(result.stdout)
    missing = expected_pairs(parameters) - covered_pairs(configurations)
    assert not missing, f"uncovered pairs: {missing}"


@pytest.mark.parametrize(
    "parameters",
    [
        {},  # no kinds
        {"P1": ["a", "b"]},  # single kind
    ],
)
def test_insufficient_kinds_rejected(runner, create_file, parameters):
    """Fewer than two parameter kinds form no pairs and must be rejected by input validation"""
    filename = create_file({"Parameters": parameters})
    result = runner.invoke(main, [filename])
    assert isinstance(result.exception, InsufficientKinds)
    assert "At least two parameter kinds are required" in str(result.exception)
