"""Conftest for pairwise tests"""

import json
import os
import tempfile

import pytest


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
