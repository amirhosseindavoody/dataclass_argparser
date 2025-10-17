# Quick Start: Building Conda Package

## TL;DR

```bash
# Build the conda package
pixi build

# or use the task
pixi run build-conda

# Output will be at:
# output/noarch/dataclass-argparser-{version}-py_0.tar.bz2
```

## What Was Added

1. **pixi.toml** - Added `[build-dependencies]` with `rattler-build`
2. **recipe.yaml** - Conda package recipe
3. **BUILD.md** - Full documentation
4. **README.md** - Updated with build instructions

## Key Commands

```bash
# Build conda package
pixi build
pixi run build-conda

# Clean build artifacts
pixi run clean

# Test the package (existing)
pixi run test
pixi run test-verbose
```

## Files Created

- `recipe.yaml` - Conda recipe (package metadata, build instructions, tests)
- `BUILD.md` - Detailed build documentation
- `CONDA_BUILD_SUMMARY.md` - Overview of the setup

## Next Steps

1. Build: `pixi build`
2. Package is in: `output/noarch/`
3. Install locally: `conda install -c local dataclass-argparser`
4. Or upload to conda-forge or other conda channels

## More Info

See [BUILD.md](BUILD.md) for complete documentation.
