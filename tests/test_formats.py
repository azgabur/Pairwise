"""Tests for input and output formats of the pairwise tool"""

import csv
import io
import json

import pytest
import yaml

from main.main import main
from file_formats import InvalidInputFile  # pylint: disable=wrong-import-order
from parameters_check import InvalidStructure, InvalidWeight  # pylint: disable=wrong-import-order

PARAMETERS = {"P1": ["a", "b"], "P2": ["1", "2"], "P3": ["x", "y"]}
EXPECTED = [
    {"P1": "a", "P2": "2", "P3": "y"},
    {"P1": "a", "P2": "1", "P3": "x"},
    {"P1": "b", "P2": "1", "P3": "y"},
    {"P1": "b", "P2": "2", "P3": "x"},
]

YAML_INPUT = """\
Parameters:
  P1: [a, b]
  P2: ["1", "2"]
  P3:
    - x
    - y
"""


@pytest.mark.parametrize(
    ("data", "file_format", "suffix"),
    [
        ({"Parameters": PARAMETERS}, "json", ".json"),
        ({"Parameters": PARAMETERS}, "yaml", ".yaml"),
        ({"Parameters": PARAMETERS}, "yaml", ".yml"),
        (YAML_INPUT, "yaml", ".yaml"),  # hand-written block and flow YAML styles
        ({"Parameters": PARAMETERS}, "json", ".txt"),  # unknown extension, parsed as JSON
        (YAML_INPUT, "yaml", ".txt"),  # unknown extension, falls back to YAML
    ],
)
def test_input_formats(runner, create_file, data, file_format, suffix):
    """Equivalent JSON and YAML inputs produce the same configurations"""
    filename = create_file(data, file_format, suffix)
    result = runner.invoke(main, ["--output", "json", filename])
    assert result.exit_code == 0, result.exception
    assert json.loads(result.stdout)["Configurations"] == EXPECTED


def test_input_from_stdin(runner):
    """Parameters can be read from stdin when the file argument is '-'"""
    result = runner.invoke(main, ["--output", "json", "-"], input=YAML_INPUT)
    assert result.exit_code == 0, result.exception
    assert json.loads(result.stdout)["Configurations"] == EXPECTED


def test_explicit_input_format(runner, create_file):
    """--input-format overrides the format implied by the file extension"""
    filename = create_file(YAML_INPUT, "yaml", ".json")
    result = runner.invoke(main, [filename])
    assert isinstance(result.exception, InvalidInputFile)

    result = runner.invoke(main, ["--input-format", "yaml", "--output", "json", filename])
    assert result.exit_code == 0, result.exception
    assert json.loads(result.stdout)["Configurations"] == EXPECTED


@pytest.mark.parametrize(
    ("content", "suffix", "error"),
    [
        ('{"Parameters": ', ".json", "not a valid JSON file"),
        ("Parameters: [a, b", ".yaml", "not a valid YAML file"),
        ("Parameters: [a, b", ".txt", "not a valid JSON or YAML file"),
    ],
)
def test_invalid_input_file(runner, create_file, content, suffix, error):
    """Files that cannot be parsed are reported with the attempted formats"""
    filename = create_file(content, suffix=suffix)
    result = runner.invoke(main, [filename])
    assert isinstance(result.exception, InvalidInputFile)
    assert error in str(result.exception)


@pytest.mark.parametrize(
    ("content", "exception", "error"),
    [
        # top level
        ("- a\n- b\n", InvalidStructure, "must contain a mapping"),
        ("Weights: {a: 1}\n", InvalidStructure, "missing the mandatory 'Parameters' key"),
        ("Parameters: {P1: [a], P2: [b]}\nWeight: {a: 1}\n", InvalidStructure, "Unknown keys ['Weight']"),
        # parameters
        ("Parameters: [a, b]\n", InvalidStructure, "'Parameters' must be a mapping"),
        ("Parameters: {1: [a], P2: [b]}\n", InvalidStructure, "Parameter kind 1 must be a string"),
        ("Parameters: {P1: a, P2: [b]}\n", InvalidStructure, "Parameters for P1 must be a list"),
        # parameter values must be strings, YAML resolves unquoted scalars to other types
        ("Parameters: {P1: [a, 1], P2: [b]}\n", InvalidStructure, "Value 1 of P1 must be a string"),
        ("Parameters: {P1: [a, 4.20], P2: [b]}\n", InvalidStructure, "Value 4.2 of P1 must be a string"),
        ("Parameters: {P1: [a, true], P2: [b]}\n", InvalidStructure, "Value True of P1 must be a string"),
        ("Parameters: {P1: [a, ~], P2: [b]}\n", InvalidStructure, "Value None of P1 must be a string"),
        ("Parameters: {P1: [a, 2024-01-01], P2: [b]}\n", InvalidStructure, "Value datetime.date(2024, 1, 1) of P1"),
        ("Parameters: {P1: [a, {b: c}], P2: [d]}\n", InvalidStructure, "Value {'b': 'c'} of P1 must be a string"),
        # weights
        ("Parameters: {P1: [a, b], P2: [c]}\nWeights: [a]\n", InvalidStructure, "'Weights' must be a mapping"),
        ("Parameters: {P1: [a, b], P2: [c]}\nWeights: {1: 2}\n", InvalidStructure, "Weight key 1 must be a string"),
        ("Parameters: {P1: [a, b], P2: [c]}\nWeights: {a: high}\n", InvalidWeight, "is not a number"),
        ("Parameters: {P1: [a, b], P2: [c]}\nWeights: {a: true}\n", InvalidWeight, "is not a number"),
    ],
)
def test_invalid_structure(runner, create_file, content, exception, error):
    """Structurally invalid input is rejected before generation"""
    filename = create_file(content, "yaml")
    result = runner.invoke(main, [filename])
    assert isinstance(result.exception, exception)
    assert error in str(result.exception)


def test_empty_weights_allowed(runner, create_file):
    """An empty 'Weights' key (null in YAML) is treated as no weights"""
    filename = create_file(YAML_INPUT + "Weights:\n", "yaml")
    result = runner.invoke(main, ["--output", "json", filename])
    assert result.exit_code == 0, result.exception
    assert json.loads(result.stdout)["Configurations"] == EXPECTED


def test_csv_output(runner, create_file):
    """CSV is the default output format: a header row followed by one row per configuration"""
    filename = create_file({"Parameters": PARAMETERS})
    result = runner.invoke(main, [filename])
    assert result.exit_code == 0
    assert result.stdout == runner.invoke(main, ["--output", "csv", filename]).stdout
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == ["P1", "P2", "P3"]
    assert rows[1:] == [list(conf.values()) for conf in EXPECTED]


@pytest.mark.parametrize(("file_format", "loader"), [("json", json.loads), ("yaml", yaml.safe_load)])
def test_structured_output(runner, create_file, file_format, loader):
    """JSON and YAML outputs hold the configurations as mappings of kind to value"""
    filename = create_file({"Parameters": PARAMETERS})
    result = runner.invoke(main, ["--output", file_format, filename])
    assert result.exit_code == 0
    assert loader(result.stdout) == {"Configurations": EXPECTED}


def test_output_format_case_insensitive(runner, create_file):
    """Format names are accepted regardless of case"""
    filename = create_file({"Parameters": PARAMETERS})
    result = runner.invoke(main, ["-o", "YAML", filename])
    assert result.exit_code == 0
    assert yaml.safe_load(result.stdout) == {"Configurations": EXPECTED}


def test_yaml_output_preserves_string_values(runner, create_file):
    """Strings that look like numbers stay strings in YAML output, so the output can be read back"""
    parameters = {"OCP": ["4.20", "4.21"], "P2": ["1", "true"]}
    filename = create_file({"Parameters": parameters})
    result = runner.invoke(main, ["--output", "yaml", filename])
    assert result.exit_code == 0
    values = {v for conf in yaml.safe_load(result.stdout)["Configurations"] for v in conf.values()}
    assert values == {"4.20", "4.21", "1", "true"}


def test_invalid_output_format(runner, create_file):
    """Unsupported output formats are rejected by the argument parser"""
    filename = create_file({"Parameters": PARAMETERS})
    result = runner.invoke(main, ["--output", "xml", filename])
    assert result.exit_code == 2
    assert "Invalid value for '-o' / '--output'" in result.stderr
