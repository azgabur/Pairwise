# Pairwise
Pairwise is a tool for generating configurations using pairwise algorithm with weights.
## Installation
1. Clone this repo and change to cloned directory.
2. Install pipenv using pip: `pip install pipenv`
3. Install required packages: `pipenv install`

## Usage
Usage of this tool is very simple. 

First you need a file with parameters in JSON or YAML format, e.g. `parameters.json`
```json
{
  "Parameters": {
    "P1": ["a", "b"],
    "P2": ["1", "2"],
    "P3": ["x", "y"]
  }
}
```
or the equivalent `parameters.yaml`
```yaml
Parameters:
  P1: [a, b]
  P2: ["1", "2"]
  P3: [x, y]
```
Then you can run it as `pipenv run pairwise parameters.json`

You must always run it from the root directory (/path/to/repository/Pairwise).

The input format is detected from the file extension (`.json`, `.yaml`, `.yml`). For other file names,
or when reading from stdin (`-` instead of the file name), JSON is tried first with YAML as a fallback.
The format can also be set explicitly with `--input-format {json,yaml}`.

All parameter values must be strings: they are only labels with no numeric or logical meaning.
Note that YAML reads some unquoted values as other types: `1` and `4.20` become numbers, `true` a boolean,
`2024-01-01` a date and `~` null. Such values are rejected, quote them (`"4.20"`) to keep them as strings.
Weights must be numbers.

The generated configurations are printed to stdout, as CSV by default:
```
P1,P2,P3
a,2,y
a,1,x
b,1,y
b,2,x
```
Use `--output {csv,json,yaml}` to choose a different format. JSON and YAML outputs list the configurations
under the `Configurations` key:
```yaml
Configurations:
- P1: a
  P2: '2'
  P3: y
- P1: a
  P2: '1'
  P3: x
...
```
To save the configurations, redirect stdout into a file, e.g. `pipenv run pairwise -o yaml parameters.yaml > configurations.yaml`.
Warnings and the `--count` statistics are printed to stderr, so they never end up in the redirected output.

You can also set weights for each parameter. e.g.
```json
{
  "Parameters": {
    "P1": ["a", "b"],
    "P2": ["1", "2"],
    "P3": ["x", "y"]
  },
  "Weights": {
    "a": 1,
    "x": 2
  }
}
```
Weight represents the ratio in which you want to parameters appear in generated configuratations.
Default weight for each parameter is 1.

Additionally, you can use some of the available options:
* `-i, --input-format {json,yaml}` format of the parameters file (default: detected from the file extension)
* `-o, --output {csv,json,yaml}` format of the generated configurations printed to stdout (default: csv)
* `-m, --margin {float}` margin of weights, some wiggle room for weight representation in generated configurations (default: 0.05)
* `--count` prints to stderr how many times was each parameter used during configuration generation

e.g. `pipenv run pairwise --output json --margin 0.04 --count parameters.yaml > configurations.json`

## Container image
The tool is also available as a container image `quay.io/rhn_support_azgabur/pairwise:latest`,
built from the `Containerfile` and published by GitHub Actions on every push to `master`.

Mount the directory with the parameters file into the container and pass the path as the argument:
```
podman run --rm -v "$PWD":/data:Z quay.io/rhn_support_azgabur/pairwise /data/parameters.json
```
The configurations are printed to stdout, so they can be saved by redirecting the output:   
```
podman run --rm -v "$PWD":/data:Z quay.io/rhn_support_azgabur/pairwise -o yaml /data/parameters.yaml > configurations.yaml
```
The parameters can also be passed through stdin without mounting any directory:
```
podman run --rm -i quay.io/rhn_support_azgabur/pairwise -o json - < parameters.yaml > configurations.json
```
To build the image locally run `podman build -t pairwise -f Containerfile .` 