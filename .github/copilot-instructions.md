# Copilot Instructions for DataclassArgParser

## Project Overview
- This project provides a utility (`DataclassArgParser`) for generating argparse-based CLIs from Python dataclasses.
- Major logic is in `src/dataclass_argparser/parser.py`.
- Supports nested dataclasses, lists, tuples, dictionaries, and Literal types as CLI/config arguments.
- Configuration can be loaded from YAML/JSON files and overridden by CLI args.
- Supports custom flags alongside dataclass-generated arguments.

## Key Patterns & Architecture
- **DataclassArgParser**: Main entry point. Accepts one or more dataclass types and generates CLI arguments for each field.
- **Field Naming**: CLI arguments use the format `--ClassName.field_name` (e.g., `--Config.name`). Nested fields use dot notation (e.g., `--Outer.inner.x`).
- **Type Handling**: Handles `int`, `float`, `str`, `bool`, `Literal`, `list[T]`, `tuple[T1, T2, ...]`, `dict[K, V]`, and nested dataclasses. Lists/tuples of dataclasses are supported for config files (not CLI).
- **Dict Support**: Dictionaries can be provided via JSON format (`'{"key": "value"}'`) or key=value format (`"key1=value1,key2=value2"`). Supports `dict[str, str]`, `dict[str, int]`, `dict[str, float]`, etc.
- **Custom Flags**: Supports adding custom flags via `flags` parameter in constructor or via `add_flag()` method. Custom flags coexist with dataclass arguments in the returned dict.
- **Config Flag Customization**: The config file option can be customized (e.g., `--config`, `-c`, or `['-c', '--config']`) via the `config_flag` parameter.
- **Config Precedence**: Values are resolved in this order: CLI > config file > dataclass default.
- **Help Text**: Extracted from `metadata={"help": ...}` in dataclass fields.
- **Required Fields**: If a required field is missing from both CLI and config, the parser exits with an error.

## Developer Workflows
- **Install**: `pixi add --pypi --editable dataclass-argparser@file:///absolute/path/to/dataclass_argparser/folder` or install from git: `pixi add dataclass-argparser --git https://github.com/amirhosseindavoody/dataclass_argparser --branch main`
- **Run Tests**:
  - `pixi run test-verbose` (verbose output, preferred)
  - `pixi run test` (basic test run)
  - `pixi run test-coverage` (with coverage report in HTML, term, and XML)
  - `pixi run test-all` (tests + examples validation)
- **Build**:
  - `pixi run build` (builds using pixi-build, outputs to dist/)
  - `pixi run build-pypi` (builds using python-build/Hatchling)
  - `pixi run clean` (removes build artifacts)
- **Run Examples**:
  - `pixi run run-basic-example` (shows basic example help)
  - `pixi run run-override-example` (shows override example help)
  - `pixi run demo` (runs full demo with examples)
- **Package Manager**: Uses `pixi` with pixi-build for conda packages and Hatchling for PyPI packages

## Project-Specific Conventions
- **Tests**: Located in `tests/`, organized by feature:
  - `test_parser.py` - Core parser functionality
  - `test_list_types.py` - List type support
  - `test_tuple_types.py` - Tuple type support
  - `test_dict_types.py` - Dictionary type support
  - `test_nested_types.py` - Nested dataclass support
  - `test_config_files.py` - Config file loading (JSON/YAML)
  - `test_custom_flags.py` - Custom flag integration
  - `test_default_values.py` - Default value handling
- **Examples**: See `examples/` for usage patterns:
  - `basic_example.py` - Simple dataclass CLI generation
  - `override_example.py` - Config file with CLI overrides
  - `custom_flags_example.py` - Custom flags alongside dataclass args
  - `example_config.json`, `override_config.json` - Sample config files
- **No CLI parsing for lists/tuples of dataclasses**: These are only supported via config files, not command-line args.
- **Field Metadata**: Always use `metadata={"help": ...}` for user-facing help.
- **Error Handling**: All user-facing errors are surfaced via argparse's error mechanism.

## Integration & Extensibility
- **YAML Support**: Optional, requires `PyYAML`.
- **Extending Types**: To add new supported types, update `_add_dataclass_arguments` and `parse` logic in `parser.py`.
- **Adding New Features**: Follow the pattern of type-based argument generation and recursive parsing for nested/complex types.

## Example: Adding a New Dataclass
```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class MyConfig:
    foo: int = field(default=1, metadata={"help": "Foo value"})
    bar: str = field(default="baz", metadata={"help": "Bar value"})

parser = DataclassArgParser(MyConfig)
result = parser.parse()
config: MyConfig = result["MyConfig"]
```

## Example: Custom Flags and Config Flag Customization
```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class AppConfig:
    name: str = field(default="example", metadata={"help": "Application name"})

# Add custom flags and customize config flag
parser = DataclassArgParser(
    AppConfig,
    flags=[
        ("--verbose", {"action": "store_true", "help": "Enable verbose output"}),
        {"names": "--quiet", "kwargs": {"action": "store_true", "help": "Quiet mode"}},
    ],
    config_flag=("-c", "--config"),  # Customize config flag
)

# Add additional flags after construction
parser.add_flag("--log", type=str, help="Path to log file")

result = parser.parse()
config = result["AppConfig"]  # Dataclass instance
verbose = result["verbose"]  # Custom flag value
quiet = result["quiet"]  # Custom flag value
log = result["log"]  # Custom flag value
```

## Key Files
- `src/dataclass_argparser/parser.py`: Core logic for argument parsing and config loading.
- `tests/`: Test suite for all supported features and edge cases.
- `examples/`: Example scripts and config files.
- `README.md`: Full usage, API, and supported types documentation.

---
If you are unsure about a pattern or workflow, check the README and the test files for concrete examples.

## Compatibility
- **Python Versions**: This project is compatible with Python 3.9 and above.
    - For typehints use `from typing import Any, Literal, Type, Union, Optional`
- **Dataclass Support**: Requires Python 3.9+ for dataclass support.
- **YAML Support**: Optional, requires `PyYAML` for YAML config files.

## CI/CD and GitHub Actions
- **Workflow**: The project uses GitHub Actions with pixi for CI/CD (`.github/workflows/ci.yml`)
- **Test Matrix**: Tests run on Ubuntu, macOS, and Windows
- **Build Process**: Uses pixi for building both conda and PyPI packages
- **Coverage**: Test coverage is generated and uploaded to Codecov (Ubuntu only)
- **Examples**: All examples are tested as part of CI to ensure they work correctly

