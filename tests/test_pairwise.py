"""Test for pairwise tool"""

import os

import pytest

from main.main import main


@pytest.fixture()
def input_file(create_file):
    """Create file with input parameters"""
    data = {"Parameters": {"P1": ["a", "b"], "P2": [1, 2], "P3": ["x", "y"]}}
    return create_file(data)


def test_pairwise(runner, input_file):
    """Test correct configuration generation"""
    result = runner.invoke(main, [input_file])
    assert result.exit_code == 0
    assert "1: ['a', 2, 'y']\n2: ['a', 1, 'x']\n3: ['b', 1, 'y']\n4: ['b', 2, 'x']\n" == result.output


def test_output_to_csv(runner, input_file, tmp_path):
    """Test output to csv file"""
    csv_path = tmp_path / "out.csv"
    result = runner.invoke(main, ["--output", str(csv_path), input_file])
    assert result.exit_code == 0
    assert "1: ['a', 2, 'y']\n2: ['a', 1, 'x']\n3: ['b', 1, 'y']\n4: ['b', 2, 'x']\n" == result.output
    assert os.path.isfile(csv_path)
