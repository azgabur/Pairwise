"""Parameters check class for pairwise tool"""

from file_formats import load_input

ALLOWED_KEYS = ("Parameters", "Weights")


class ParametersCheck:
    """Parameters check class"""

    def __init__(self, input_file, input_format=None):
        self.weights = None
        self.parameters = None
        self.file = None
        self.input_file = input_file
        self.input_format = input_format

    def check_parameters(self):
        """Checks if input paramateres are correct"""
        self.try_load()
        self._check_structure()
        self._check_kind_count()
        self._check_empty_kind()
        self._check_duplicate_parameter()
        self._check_nonexistent_weight()
        self._check_negative_weight()

    def try_load(self):
        """Try to load input file in JSON or YAML format"""
        self.file = load_input(self.input_file, self.input_format)

    def _check_structure(self):
        """
        Checks that the loaded file has the expected structure:
            Parameters: mapping of kind name (string) to a list of values (strings), mandatory
            Weights: mapping of value (string) to weight (number), optional, may be empty
        """
        self._check_top_level()
        self.parameters = self.file["Parameters"]
        self.weights = self.file.get("Weights") or {}
        self._check_parameters_structure()
        self._check_weights_structure()

    def _check_top_level(self):
        """Checks that the file is a mapping with mandatory 'Parameters' and no unknown keys"""
        if not isinstance(self.file, dict):
            raise InvalidStructure(f"\nParameters file must contain a mapping with keys {list(ALLOWED_KEYS)}.")
        if "Parameters" not in self.file:
            raise InvalidStructure("\nParameters file is missing the mandatory 'Parameters' key.")
        unknown = [key for key in self.file if key not in ALLOWED_KEYS]
        if unknown:
            raise InvalidStructure(f"\nUnknown keys {unknown} in parameters file, allowed are {list(ALLOWED_KEYS)}.")

    def _check_parameters_structure(self):
        """Checks that 'Parameters' maps kind names to lists of string values"""
        if not isinstance(self.parameters, dict):
            raise InvalidStructure("\n'Parameters' must be a mapping of parameter kinds to lists of values.")
        for kind, values in self.parameters.items():
            if not isinstance(kind, str):
                raise InvalidStructure(f"\nParameter kind {kind!r} must be a string.")
            if not isinstance(values, list):
                raise InvalidStructure(f"\nParameters for {kind} must be a list.")
            for value in values:
                if not isinstance(value, str):
                    raise InvalidStructure(
                        f"\nValue {value!r} of {kind} must be a string."
                        f'\nIn YAML, quote values that are not read as strings, e.g. "4.20" or "true".'
                    )

    def _check_weights_structure(self):
        """Checks that 'Weights' maps string values to numeric weights"""
        if not isinstance(self.weights, dict):
            raise InvalidStructure("\n'Weights' must be a mapping of parameter values to numbers.")
        for param, weight in self.weights.items():
            if not isinstance(param, str):
                raise InvalidStructure(f"\nWeight key {param!r} must be a string.")
            if isinstance(weight, bool) or not isinstance(weight, (int, float)):
                raise InvalidWeight(f"Weight for parameter '{param}' is not a number.")

    def _check_kind_count(self):
        """Checks if there are at least two parameter kinds, otherwise no pairs can be formed"""
        if len(self.parameters) < 2:
            raise InsufficientKinds(
                f"\nAt least two parameter kinds are required for pairwise testing, got {len(self.parameters)}."
            )

    def _check_empty_kind(self):
        """Checks if any parameters list is empty"""
        for kind, parameters in self.parameters.items():
            if not parameters:
                raise EmptyList(f"\nList of parameters for {kind} is empty.")

    def _check_duplicate_parameter(self):
        """Checks if any parameter is present more tha once"""
        seen = set()
        duplicates = set()
        lst = []
        for params in self.parameters.values():
            lst.extend(params)
        for item in lst:
            if item in seen:
                duplicates.add(item)
            seen.add(item)

        if len(duplicates) != 0:
            raise DuplicateParameter(
                f"\nParameters {list(duplicates)} are present more than once."
                f"\nPlease use unique name for each parameter."
            )

    def _check_nonexistent_weight(self):
        """Checks if there is weight set for nonexistent parameter"""
        lst = []
        for params in self.parameters.values():
            lst.extend(params)
        for weight in self.weights.keys():
            if weight not in lst:
                raise InvalidWeight(f"Parameter '{weight}' doesn't exists.")

    def _check_negative_weight(self):
        """Checks if there is negative weight set for any parameter"""
        for k, v in self.weights.items():
            if v < 0:
                raise InvalidWeight(f"Weight for parameter '{k}' is negative.")


class InsufficientKinds(Exception):
    """Exception class for fewer than two parameter kinds"""


class EmptyList(Exception):
    """Exception class for empty parameters list"""


class DuplicateParameter(Exception):
    """Exception class for duplicate parameter"""


class InvalidStructure(Exception):
    """Exception class for parameters file with unexpected structure"""


class InvalidWeight(Exception):
    """Exception class for invalid parameter weight"""
