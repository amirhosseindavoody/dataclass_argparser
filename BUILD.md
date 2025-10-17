# Building the Conda Package

This document describes how to build the `dataclass-argparser` package as a conda package using `pixi build`.

## Prerequisites

1. Install `pixi` if you haven't already:
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/amirhosseindavoody/dataclass_argparser.git
   cd dataclass_argparser
   ```

## Building the Conda Package

The project is configured to build conda packages using `rattler-build`, which is managed by pixi.

### Using pixi build

The simplest way to build the conda package is to use the `pixi build` command:

```bash
pixi build
```

This will:
1. Install the build dependencies (rattler-build) in an isolated environment
2. Read the `recipe.yaml` file for package configuration
3. Build the conda package
4. Output the package to the `output/` directory

### Using the pixi task

Alternatively, you can use the predefined pixi task:

```bash
pixi run build-conda
```

This runs the same `rattler-build build --recipe recipe.yaml` command.

### Build Output

The built conda package will be placed in the `output/` directory with a name like:
```
output/noarch/dataclass-argparser-1.0.0-py_0.tar.bz2
```

## Recipe Configuration

The conda package build is configured in `recipe.yaml` with the following key sections:

- **package**: Package name and version
- **source**: Points to the current directory
- **build**: Build script and settings (noarch python package)
- **requirements**: Build and runtime dependencies
- **test**: Import and basic functionality tests
- **about**: Metadata about the package

## Installing the Built Package

After building, you can install the package locally:

```bash
# Using conda
conda install -c local dataclass-argparser

# Using pixi (add to your pixi.toml)
# [dependencies]
# dataclass-argparser = { path = "output/noarch/dataclass-argparser-1.0.0-py_0.tar.bz2" }
```

## Customizing the Build

To modify the conda package build:

1. Edit `recipe.yaml` to change package metadata, dependencies, or build instructions
2. Edit `pixi.toml` to modify build dependencies or add build tasks
3. Run `pixi run build-conda` to rebuild with your changes

## Cleaning Build Artifacts

To clean up build artifacts:

```bash
pixi run clean
```

This removes:
- `build/` - Python build artifacts
- `dist/` - Python distribution packages
- `output/` - Conda package output
- Various cache and temporary directories

## Troubleshooting

### Build Dependencies Not Found

If you get errors about missing build dependencies, ensure you're using pixi to run the build:
```bash
pixi run build-conda
```

This ensures `rattler-build` is available in the build environment.

### Version Mismatch

Make sure the version in `recipe.yaml` matches the version in `pyproject.toml`:
- `recipe.yaml`: `version: 1.0.0`
- `pyproject.toml`: `version = "1.0.0"`

### Python Version Issues

The package is built as `noarch: python` and supports Python 3.7+. If you need to support specific Python versions, modify the `requirements.run` section in `recipe.yaml`.

## Additional Resources

- [Pixi Build Documentation](https://pixi.sh/latest/build/getting_started/)
- [Rattler-Build Documentation](https://prefix-dev.github.io/rattler-build/)
- [Conda Package Specification](https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html)
