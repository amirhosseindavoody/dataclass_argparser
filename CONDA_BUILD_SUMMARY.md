# Conda Package Build Setup - Summary

## What Was Done

This repository now supports building as a conda package using `pixi build`. The following changes were made:

### 1. Updated pixi.toml
- Added `[build-dependencies]` section with `rattler-build >= 0.20.0`
- Added `build-conda` task for building the conda package
- Updated `clean` task to remove the `output/` directory

### 2. Created recipe.yaml
A complete conda recipe file with:
- Package metadata (name, version)
- Source configuration (local path)
- Build configuration (noarch python, pip-based installation)
- Requirements (host and run dependencies)
- Test configuration (import tests)
- About section (license, URLs, description)

### 3. Created BUILD.md
Comprehensive documentation covering:
- Prerequisites and setup
- Building the conda package
- Using the built package
- Customizing the build
- Troubleshooting

### 4. Updated README.md
Added conda build instructions to the Installation section with reference to BUILD.md

## How to Use

### Building the Package

With pixi installed, you can build the conda package in two ways:

```bash
# Method 1: Direct pixi build
pixi build

# Method 2: Using the task
pixi run build-conda
```

Both commands will:
1. Set up an isolated build environment
2. Install rattler-build
3. Build the conda package
4. Output to `output/` directory

### Output Location

The built package will be at:
```
output/noarch/dataclass-argparser-1.0.0-py_0.tar.bz2
```

### Installing the Built Package

```bash
# Using conda
conda install -c local dataclass-argparser

# Or specify the full path
conda install output/noarch/dataclass-argparser-1.0.0-py_0.tar.bz2
```

## Key Files

- **pixi.toml**: Pixi project configuration with build dependencies and tasks
- **recipe.yaml**: Conda recipe defining package metadata and build process
- **BUILD.md**: Detailed build documentation
- **pyproject.toml**: Python package metadata (used by the build process)

## Build Process Flow

1. `pixi build` is invoked
2. Pixi creates an isolated environment with rattler-build
3. Rattler-build reads `recipe.yaml`
4. Build script runs: `python -m pip install . --no-deps --ignore-installed -vv`
5. Package is tested (import checks)
6. Conda package is created in `output/` directory

## Benefits

- **Reproducible builds**: Build dependencies are pinned and managed by pixi
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Isolated**: Build happens in an isolated environment
- **Standard**: Follows conda packaging conventions
- **Easy to use**: Single command to build (`pixi build`)

## Next Steps

Users can now:
1. Build the package: `pixi build`
2. Distribute the built conda package
3. Upload to conda channels (e.g., conda-forge)
4. Install from local builds for testing

## Version Management

When releasing new versions:
1. Update version in `pyproject.toml`
2. Update version in `recipe.yaml`
3. Run `pixi build` to create new package
4. The version number will be part of the package filename

## Notes

- The package is built as `noarch: python` since it's pure Python
- Python 3.7+ is supported (as specified in pyproject.toml)
- Build artifacts in `output/` are gitignored
- The recipe uses the existing pyproject.toml for package metadata
