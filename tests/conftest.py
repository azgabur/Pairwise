"""Conftest for pairwise tests"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

# main.py uses imports like ``from pairwise import Pairwise``, so its package
# directory must be importable when the command is invoked in-process.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "main"))


@pytest.fixture()
def runner():
    """Click test runner for invoking the CLI in-process"""
    return CliRunner()


@pytest.fixture()
def create_file(request):
    """Create input file from given parameters"""

    def _create_file(data):
        fd, filename = tempfile.mkstemp(suffix=".json")
        request.addfinalizer(lambda: os.remove(filename))
        with os.fdopen(fd, "w", encoding="utf-8") as outfile:
            json.dump(data, outfile)
        return filename

    return _create_file
