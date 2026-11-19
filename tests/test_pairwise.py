"""Test for pairwise tool"""

import csv

import pytest

from main.main import main
from tests.helpers import covered_pairs, expected_pairs, parse_configurations


@pytest.fixture()
def input_file(create_file):
    """Create file with input parameters"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"]}}
    return create_file(data)


def test_pairwise(runner, input_file):
    """Legacy test: exact output for the smallest input, kept from the original suite"""
    result = runner.invoke(main, [input_file])
    assert result.exit_code == 0
    assert "1: ['a', 2, 'y']\n2: ['a', 1, 'x']\n3: ['b', 1, 'y']\n4: ['b', 2, 'x']\n" == result.output


@pytest.mark.parametrize(
    "parameters",
    [
        {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"]},  # symmetric
        {"P1": ["a", "b", "c", "d"], "P2": [1, 2], "P3": ["x", "y"]},  # asymmetric, drives triplet logic
        {"P1": ["a", "b"], "P2": [1, 2]},  # two kinds
        {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"], "P4": ["m", "n"]},  # four kinds
        {"P1": ["a", "b", "c"], "P2": [1, 2, 3], "P3": ["x", "y", "z"]},  # three values per kind
        {"P1": ["a", "b", "c", "d", "e"], "P2": [1, 2, 3], "P3": ["x", "y"]},  # all arities differ
        {"P1": ["a"], "P2": [1, 2], "P3": ["x", "y"]},  # single-value kind
    ],
)
def test_pairwise_covers_all_pairs(runner, create_file, parameters):
    """The generated configurations must cover every cross-kind value pair"""
    filename = create_file({"Parameters": parameters})
    result = runner.invoke(main, [filename])
    assert result.exit_code == 0
    configurations = parse_configurations(result.output)
    missing = expected_pairs(parameters) - covered_pairs(configurations)
    assert not missing, f"uncovered pairs: {missing}"


@pytest.mark.xfail(
    raises=KeyError,
    strict=True,
    reason="Bug: with a single kind there are no pairs, and _next_quantity_param indexes an empty dict",
)
def test_single_kind(runner, create_file):
    """A single parameter kind should produce one configuration per value"""
    filename = create_file({"Parameters": {"P1": ["a", "b"]}})
    result = runner.invoke(main, [filename], catch_exceptions=False)
    assert parse_configurations(result.output) == [["a"], ["b"]]


def test_output_to_csv(runner, input_file, tmp_path):
    """Test output to csv file: the file exists and its content matches stdout"""
    csv_path = tmp_path / "out.csv"
    result = runner.invoke(main, ["--output", str(csv_path), input_file])
    assert result.exit_code == 0
    assert "1: ['a', 2, 'y']\n2: ['a', 1, 'x']\n3: ['b', 1, 'y']\n4: ['b', 2, 'x']\n" == result.output
    assert csv_path.is_file()

    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        rows = list(csv.reader(csv_file))
    header, data_rows = rows[0], rows[1:]
    assert header == ["P1", "P2", "P3"]
    # One data row per generated configuration.
    assert len(data_rows) == len(parse_configurations(result.output))
