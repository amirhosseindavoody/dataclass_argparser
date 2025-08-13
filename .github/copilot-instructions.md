# Copilot Instructions for DataclassArgParser

## Project Overview
- This project provides a utility (`DataclassArgParser`) for generating argparse-based CLIs from Python dataclasses.
- Major logic is in `src/dataclass_argparser/parser.py`.
- Supports nested dataclasses, lists, tuples, and Literal types as CLI/config arguments.
- Configuration can be loaded from YAML/JSON files and overridden by CLI args.

## Key Patterns & Architecture
- **DataclassArgParser**: Main entry point. Accepts one or more dataclass types and generates CLI arguments for each field.
- **Field Naming**: CLI arguments use the format `--ClassName.field_name` (e.g., `--Config.name`). Nested fields use dot notation (e.g., `--Outer.inner.x`).
- **Type Handling**: Handles `int`, `float`, `str`, `bool`, `Literal`, `list[T]`, `tuple[T1, T2, ...]`, and nested dataclasses. Lists/tuples of dataclasses are supported for config files (not CLI).
- **Config Precedence**: Values are resolved in this order: CLI > config file > dataclass default.
- **Help Text**: Extracted from `metadata={"help": ...}` in dataclass fields.
- **Required Fields**: If a required field is missing from both CLI and config, the parser exits with an error.

## Developer Workflows
- **Install**: `pixi add --pypi --editable dataclass-argparser@file:///absolute/path/to/dataclass_argparser/folder`
- **Run Tests**: `pixi run test-verbose` (preferred), or `pixi run python -m pytest tests/`
- **Build**: `pixi run python -m build` (uses Hatchling)
- **Test Coverage**: `pixi run python -m pytest tests/ --cov=dataclass_argparser`

## Project-Specific Conventions
- **Tests**: Located in `tests/`, organized by feature (e.g., `test_list_types.py`, `test_nested_types.py`).
- **Examples**: See `examples/` for usage patterns and config file formats.
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

## Key Files
- `src/dataclass_argparser/parser.py`: Core logic for argument parsing and config loading.
- `tests/`: Test suite for all supported features and edge cases.
- `examples/`: Example scripts and config files.
- `README.md`: Full usage, API, and supported types documentation.

---
If you are unsure about a pattern or workflow, check the README and the test files for concrete examples.
