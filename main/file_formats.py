"""Reading of input parameters and writing of generated configurations in supported formats"""

import csv
import json
import os

import yaml

INPUT_FORMATS = ("json", "yaml")
OUTPUT_FORMATS = ("csv", "json", "yaml")

_INPUT_EXTENSIONS = {".json": "json", ".yaml": "yaml", ".yml": "yaml"}


def detect_input_format(file):
    """
    :param file: Opened input file
    :return: Input format derived from the file name extension, None if the extension is not recognized
    """
    extension = os.path.splitext(getattr(file, "name", ""))[1].lower()
    return _INPUT_EXTENSIONS.get(extension)


def load_input(file, file_format=None):
    """
    Load the parameters file
    :param file: Opened input file
    :param file_format: "json" or "yaml"; when None, it is detected from the file extension and if that
        is not possible, JSON parsing is tried first with YAML as a fallback
    :return: Deserialized content of the file
    """
    file_format = file_format or detect_input_format(file)
    content = file.read()
    candidates = [file_format] if file_format else list(INPUT_FORMATS)

    errors = []
    for candidate in candidates:
        try:
            if candidate == "json":
                return json.loads(content)
            return yaml.safe_load(content)
        except (ValueError, yaml.YAMLError) as e:
            errors.append(f"{candidate.upper()}: {e}")

    raise InvalidInputFile(
        f"\nGiven parameters file is not a valid {' or '.join(c.upper() for c in candidates)} file.\n"
        + "\n".join(errors)
    )


def write_configurations(configurations, output, file_format):
    """
    Write generated configurations to the output stream
    :param configurations: List of configurations, each one a mapping of parameter kind to its value
    :param output: Writable text stream
    :param file_format: "csv", "json" or "yaml"
    """
    if file_format == "csv":
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(configurations[0].keys())
        for conf in configurations:
            writer.writerow(conf.values())
    elif file_format == "json":
        json.dump({"Configurations": configurations}, output, indent=2)
        output.write("\n")
    elif file_format == "yaml":
        yaml.safe_dump({"Configurations": configurations}, output, sort_keys=False, allow_unicode=True)
    else:
        raise ValueError(f"Unsupported output format '{file_format}'")


class InvalidInputFile(Exception):
    """Exception class for a parameters file that cannot be parsed"""
