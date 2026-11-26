"""Conftest for pairwise tests"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml
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

    def _create_file(data, file_format="json", suffix=None):
        """
        :param data: Content of the file, serialized as JSON or YAML; a string is written verbatim
        :param file_format: "json" or "yaml"
        :param suffix: File name suffix, by default derived from the format
        """
        fd, filename = tempfile.mkstemp(suffix=f".{file_format}" if suffix is None else suffix)
        request.addfinalizer(lambda: os.remove(filename))
        with os.fdopen(fd, "w", encoding="utf-8") as outfile:
            if isinstance(data, str):
                outfile.write(data)
            elif file_format == "yaml":
                yaml.safe_dump(data, outfile)
            else:
                json.dump(data, outfile)
        return filename

    return _create_file
