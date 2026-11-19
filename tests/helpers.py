"""Helpers shared by the pairwise tests"""

import ast
import itertools


def parse_configurations(output):
    """Parse the CLI stdout back into a list of configurations.

    Each printed line has the form ``N: [value, value, ...]``; the part after
    ``": "`` is a Python list literal. ``ast.literal_eval`` (not ``eval``) is
    used so the mixed ``str``/``int`` values round-trip to their real types.
    """
    configurations = []
    for line in output.splitlines():
        if ": " in line:
            configurations.append(ast.literal_eval(line.split(": ", 1)[1]))
    return configurations


def expected_pairs(parameters):
    """All value pairs drawn from two different parameter kinds.

    This is the pairwise-coverage obligation the tool must satisfy; it is
    derived independently from the generator so the test acts as an oracle.
    """
    pairs = set()
    for kind1, kind2 in itertools.combinations(parameters, 2):
        for value1 in parameters[kind1]:
            for value2 in parameters[kind2]:
                pairs.add(frozenset((value1, value2)))
    return pairs


def covered_pairs(configurations):
    """All value pairs actually present across the generated configurations."""
    pairs = set()
    for conf in configurations:
        for value1, value2 in itertools.combinations(conf, 2):
            pairs.add(frozenset((value1, value2)))
    return pairs
