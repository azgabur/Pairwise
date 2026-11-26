"""Helpers shared by the pairwise tests"""

import itertools
import json


def parse_configurations(output):
    """Parse the CLI stdout produced with ``--output json`` back into a list of configurations.

    Each configuration is returned as the list of its values. JSON (unlike CSV) is used
    so the values are not subject to CSV quoting and splitting rules.
    """
    return [list(conf.values()) for conf in json.loads(output)["Configurations"]]


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
