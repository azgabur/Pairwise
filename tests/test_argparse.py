"""Test for argument parsing of pairwise tools"""

import pytest

from main.main import main


@pytest.fixture()
def valid_parameters(create_file):
    """Creates file with valid paramaters data"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"]}}
    return create_file(data)


@pytest.fixture()
def empty_list(create_file):
    """Creates file with empty parameters list"""
    data = {"Parameters": {"P1": [], "P2": [1, 2], "P3": ["x", "y"]}}
    return create_file(data)


@pytest.fixture()
def invalid_weight(create_file):
    """Creates file with valid invalid parameter weight"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"]}, "Weights": {"invalid": 1}}
    return create_file(data)


@pytest.fixture()
def negative_weight(create_file):
    """Creates file with valid negative parameter weight"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"]}, "Weights": {"a": -1}}
    return create_file(data)


@pytest.fixture()
def not_file():
    """Returns filename that doesn't exist"""
    return "not_file.json"


def test_empty_arg(runner):
    """Test error message from empty arguments"""
    result = runner.invoke(main, [])
    assert "Error: Missing argument 'PARAMETERS'" in result.stderr


def test_valid_parameters(runner, valid_parameters):
    """Test that no error message is present with valid arguments"""
    result = runner.invoke(main, [valid_parameters])
    assert result.exit_code == 0
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("data", "error"),
    [
        ("empty_list", "List of parameters for P1 is empty"),
        ("invalid_weight", "Parameter 'invalid' doesn't exists."),
        ("negative_weight", "Weight for parameter 'a' is negative."),
        ("not_file", "Error: Invalid value for 'PARAMETERS': 'not_file.json': No such file or directory"),
    ],
)
def test_invalid_parameters(request, runner, data, error):
    """Test error message for different invalid parameters"""
    filename = request.getfixturevalue(data)
    result = runner.invoke(main, [filename])
    # Click prints usage errors (e.g. a bad file argument) to stderr, while the
    # tool's own validation raises exceptions that invoke() captures instead.
    reported = result.stderr + (str(result.exception) if result.exception else "")
    assert error in reported


@pytest.mark.parametrize(
    ("option", "error"),
    [
        (["--invalid"], "Error: No such option '--invalid'."),
        (["--margin", "invalid"], "Error: Invalid value for '-m' / '--margin': 'invalid' is not a valid float."),
    ],
)
def test_invalid_option(runner, valid_parameters, option, error):
    """Test error message for different invalid options"""
    result = runner.invoke(main, option + [valid_parameters])
    assert error in result.stderr
