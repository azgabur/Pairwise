"""Pairwise tool for generating configurations"""

import sys
import warnings

import click

from file_formats import INPUT_FORMATS, OUTPUT_FORMATS, write_configurations
from pairwise import Pairwise
from parameters_check import ParametersCheck


@click.command()
@click.argument("parameters", type=click.File("r"))
@click.option(
    "-i",
    "--input-format",
    help="Format of the parameters file, detected from the file extension by default",
    type=click.Choice(INPUT_FORMATS, case_sensitive=False),
)
@click.option(
    "-o",
    "--output",
    help="Format of the generated configurations printed to stdout",
    type=click.Choice(OUTPUT_FORMATS, case_sensitive=False),
    default=OUTPUT_FORMATS[0],
    show_default=True,
)
@click.option(
    "-m",
    "--margin",
    help="Margin of weights, default is 0.05",
    type=click.FLOAT,
)
@click.option("--count", help="Print to stderr how many times was each parameter used", is_flag=True)
def main(parameters, input_format, output, count, margin):
    """Main function for pairwise tool"""
    check = ParametersCheck(parameters, input_format)
    check.check_parameters()
    pairwise = Pairwise({"Parameters": check.parameters, "Weights": check.weights}, margin)
    generated_all = pairwise.generate_configurations()
    if not generated_all:
        warnings.warn("No more unique configuration meeting the requirements")
    write_configurations(pairwise.configurations, sys.stdout, output)
    if count:
        pairwise.print_quantity(sys.stderr)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
