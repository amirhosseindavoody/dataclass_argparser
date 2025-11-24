# DataclassArgParser

A utility for creating command-line argument parsers from Python dataclasses.

## Overview

DataclassArgParser provides a simple way to automatically generate argparse-based command-line interfaces from Python dataclasses. It extracts help text from field metadata and provides type-based metavars for better user experience. It also supports loading configuration from YAML or JSON files.

## Features

- **Automatic argument generation** from dataclass fields
- **Type-based metavars** (INT, FLOAT, STRING, etc.)
- **Help text extraction** from field metadata
- **Config file support** (JSON and YAML formats)
- **Command-line override** of config file values
- **Required field validation** with clear error messages
- **Multiple dataclass support** in a single parser
- **Nested dataclass support** with dot notation for field access
- **Literal type support** with choice validation
- **Dictionary type support** with JSON and key=value formats
- **List and tuple type support** for collections
- **Custom flags** for mixing dataclass args with manual flags
- **Configurable config flag** option (e.g., `-c`, `--config`)
- **Modern build system** using pixi-build and Hatchling

## Installation

### Using Pixi

```bash
# Install the latest version from main
pixi add dataclass-argparser --git https://github.com/amirhosseindavoody/dataclass_argparser --branch main

# Install a specific version from tag
pixi add dataclass-argparser --git https://github.com/amirhosseindavoody/dataclass_argparser --tag v2025.10.20
```

### Using pip
```bash
# Install the package in development mode
pip install -e .

# Install with YAML support
pip install -e ".[yaml]"

# Install with test dependencies
pip install -e ".[test]"

# Build the package (uses hatchling)
pip install build
python -m build
```

## Quick Start

```python
from dataclasses import dataclass, field
from typing import Literal
from dataclass_argparser import DataclassArgParser

@dataclass
class Config:
    name: str = field(default="test", metadata={"help": "The name to use"})
    count: int = field(default=5, metadata={"help": "Number of items"})
    rate: float = field(default=0.5, metadata={"help": "Processing rate"})
    debug: bool = field(default=False, metadata={"help": "Enable debug mode"})
    environment: Literal["dev", "staging", "prod"] = field(default="dev", metadata={"help": "Environment"})
    tags: list[str] = field(default_factory=lambda: ["default"], metadata={"help": "List of tags"})
    coordinates: tuple[int, int] = field(default=(0, 0), metadata={"help": "X,Y coordinates"})
    settings: dict[str, str] = field(default_factory=lambda: {"key": "value"}, metadata={"help": "Settings dict"})
    required_field: str = field(metadata={"help": "A required field"})

parser = DataclassArgParser(Config)
result = parser.parse()
config = result['Config']

print(f"Name: {config.name}")
print(f"Count: {config.count}")
print(f"Rate: {config.rate}")
print(f"Debug: {config.debug}")
print(f"Environment: {config.environment}")
print(f"Tags: {config.tags}")
print(f"Coordinates: {config.coordinates}")
print(f"Settings: {config.settings}")
print(f"Required: {config.required_field}")
```

## Usage Examples

### Basic Usage

```bash
# All supported types
python script.py \
  --Config.name "myname" \
  --Config.count 10 \
  --Config.rate 0.75 \
  --Config.debug true \
  --Config.environment "prod" \
  --Config.tags "api,backend" \
  --Config.coordinates "100,200" \
  --Config.settings '{"db": "postgres", "cache": "redis"}' \
  --Config.required_field "value"
```

### Using Config Files

Create a config file `config.json`:
```json
{
  "Config": {
    "name": "from_config",
    "count": 100,
    "rate": 0.8,
    "debug": true,
    "environment": "staging",
    "tags": ["config", "auto"],
    "coordinates": [50, 75],
    "settings": {"database": "mysql", "port": "3306"},
    "required_field": "config_value"
  }
}
```

Then use it:
```bash
python script.py --config config.json
```

### Override Config with Command Line

```bash
python script.py --config config.json --Config.count 200
```

This will use values from `config.json` but override `count` to 200.

#### Override Examples for All Supported Types

Create a comprehensive config file `example_config.json`:
```json
{
  "AppConfig": {
    "name": "config_name",
    "port": 8080,
    "rate": 0.5,
    "debug": false,
    "environment": "dev",
    "tags": ["config", "default"],
    "coordinates": [10, 20, 30],
    "database": {"host": "localhost", "port": "5432"},
    "features": {"cache": true, "logging": false}
  }
}
```

**Basic Types Override:**
```bash
# Override string
python script.py --config example_config.json --AppConfig.name "override_name"

# Override integer
python script.py --config example_config.json --AppConfig.port 9000

# Override float
python script.py --config example_config.json --AppConfig.rate 0.75

# Override boolean
python script.py --config example_config.json --AppConfig.debug true
```

**Literal Types Override:**
```bash
# Override Literal choice (assuming environment: Literal["dev", "staging", "prod"])
python script.py --config example_config.json --AppConfig.environment "prod"
```

**List Types Override:**
```bash
# Override list with comma-separated values
python script.py --config example_config.json --AppConfig.tags "production,release"

# Override list with bracket notation
python script.py --config example_config.json --AppConfig.tags "[api,backend]"
```

**Tuple Types Override:**
```bash
# Override tuple with comma-separated values
python script.py --config example_config.json --AppConfig.coordinates "100,200,300"

# Override tuple with parentheses
python script.py --config example_config.json --AppConfig.coordinates "(50,75,100)"
```

**Dict Types Override:**
```bash
# Override dict with JSON format
python script.py --config example_config.json --AppConfig.database '{"host": "prod-db", "port": "3306"}'

# Override dict with key=value format
python script.py --config example_config.json --AppConfig.features "cache=false,logging=true"

# Override with empty dict
python script.py --config example_config.json --AppConfig.database "{}"
```

**Multiple Overrides:**
```bash
# Override multiple fields at once
python script.py --config example_config.json \
  --AppConfig.name "production" \
  --AppConfig.port 443 \
  --AppConfig.debug false \
  --AppConfig.tags "prod,live" \
  --AppConfig.database '{"host": "prod-db", "port": "5432", "ssl": "true"}'
```

## Priority Order

Values are resolved in this priority order (highest to lowest):
1. Command-line arguments
2. Config file values
3. Dataclass default values

## Development and Testing

### Running Tests with Pixi

```bash
# Run tests with verbose output (recommended)
pixi run test-verbose

# Run basic tests
pixi run test

# Run tests with coverage report (HTML, terminal, and XML)
pixi run test-coverage

# Run all tests including examples validation
pixi run test-all
```

### Running Tests with pytest

```bash
# Run tests directly
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/dataclass_argparser --cov-report=html --cov-report=term
```

### Building the Package

```bash
# Build with pixi-build (conda packages)
pixi run build

# Build with Hatchling (PyPI packages)
pixi run build-pypi

# Clean build artifacts
pixi run clean
```

### Running Examples

```bash
# Show basic example help
pixi run run-basic-example

# Show override example help
pixi run run-override-example

# Run full demo
pixi run demo
```

## API Reference

### DataclassArgParser

Main class for creating argument parsers from dataclasses.

#### Constructor

```python
DataclassArgParser(
    *dataclass_types: Type[Any],
    flags: Optional[list] = None,
    config_flag: Union[str, list[str], tuple[str, ...]] = "--config",
    **dataclass_kwargs: Type[Any]
)
```

**Parameters:**
- `*dataclass_types`: One or more dataclass types to generate arguments from (positional arguments). The class name will be used as the key in the result dictionary.
- `flags` (optional): A list of custom flags to add to the parser. Each item can be:
  - A tuple: `(name_or_names, kwargs_dict)` where `name_or_names` is a string like `'--verbose'` or a list like `['-v', '--verbose']`, and `kwargs_dict` contains argparse keyword arguments
  - A dict: `{'names': name_or_names, 'kwargs': {...}}` with the same structure

  Examples:
  ```python
  flags=[
      ("--verbose", {"action": "store_true", "help": "Verbose mode"}),
      (["--log", "-l"], {"type": str, "help": "Log file"}),
      {"names": "--debug", "kwargs": {"action": "store_true"}},
  ]
  ```
- `config_flag` (optional): Customize the config file option. Accepts:
  - A single string: `"--config"` or `"--cfg"`
  - A list/tuple: `['-c', '--config']` or `('-c', '--cfg')`

  Default is `"--config"`. The parser will accept the specified option(s) for loading configuration files.
- `**dataclass_kwargs`: Dataclass types passed as keyword arguments. The keyword name will be used as the key in the result dictionary instead of the class name. This allows custom naming and more Pythonic usage.

**Reserved Keywords:**
- `flags`: Reserved for custom flag specification. Cannot be used as a dataclass keyword argument name.
- `config_flag`: Reserved for config file flag specification. Cannot be used as a dataclass keyword argument name.
- `config`: Can be used as a dataclass keyword argument name, but doing so will disable the default config file loading mechanism. The `config` keyword will then be treated as a regular dataclass argument.

#### Methods

##### add_flag(*names: str, **kwargs: Any) -> None

Add an individual command-line flag/argument to the parser.

**Parameters:**
- `*names`: One or more option strings (e.g., `'--verbose'` or `'-v'`, `'--verbose'`)
- `**kwargs`: Keyword arguments passed through to `argparse.ArgumentParser.add_argument()`

**Example:**
```python
parser.add_flag('--verbose', '-v', action='store_true', help='Enable verbose output')
parser.add_flag('--output', type=str, default='out.txt', help='Output file')
```

##### parse(args=None) -> Dict[str, Any]

Parse command-line arguments and return dataclass instances.

**Parameters:**
- `args`: Optional list of arguments to parse. If None, uses sys.argv.

**Returns:**
- Dict mapping dataclass names (or custom keyword names) to their instantiated objects with parsed values. Custom flags are included as top-level keys in the dictionary.

**Raises:**
- `SystemExit`: If required fields are not provided either as command-line arguments or in the config file.

## Keyword Arguments for Dataclasses

You can pass dataclass types as keyword arguments to customize the names used in the result dictionary. This provides a more flexible and Pythonic interface.

### Basic Keyword Arguments

```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class GlobalConfig:
    name: str = field(default="test", metadata={"help": "The name to use"})

# Use keyword argument to specify custom name
parser = DataclassArgParser(global_config=GlobalConfig)
result = parser.parse()

# Access using the custom name
config = result["global_config"]
print(config.name)
```

### Mixing Positional and Keyword Arguments

You can mix positional and keyword arguments. Positional arguments use the class name as the key, while keyword arguments use the custom name:

```python
@dataclass
class AppConfig:
    version: str = field(default="1.0", metadata={"help": "App version"})

# Mix positional and keyword
parser = DataclassArgParser(
    GlobalConfig,           # Uses "GlobalConfig" as key
    app_config=AppConfig    # Uses "app_config" as key
)
result = parser.parse()

print(result["GlobalConfig"].name)  # Positional
print(result["app_config"].version)  # Keyword
```

### Example from Command Line

When using keyword arguments, the CLI argument names reflect the custom names:

```bash
# With keyword argument name "global_config"
python script.py --global_config.name "myname" --global_config.count 10

# With positional argument (uses class name "GlobalConfig")
python script.py --GlobalConfig.name "myname" --GlobalConfig.count 10
```

### Reserved Keywords

Three keywords are reserved and have special behavior:

1. **`flags`**: Reserved for custom flag specification. Attempting to use it as a dataclass keyword will raise a `ValueError`.

2. **`config_flag`**: Reserved for specifying the config file flag. Attempting to use it as a dataclass keyword will raise a `ValueError`.

3. **`config`**: Can be used as a dataclass keyword argument name, but doing so disables the default config file loading mechanism. When `config` is used as a dataclass name, it becomes a regular argument and config file loading is turned off.

```python
# This raises an error
try:
    parser = DataclassArgParser(flags=GlobalConfig)
except ValueError as e:
    print(e)  # "The keyword 'flags' is reserved..."

# This is allowed but disables config file loading
parser = DataclassArgParser(config=GlobalConfig)
result = parser.parse(["--config.name", "value"])
print(result["config"].name)  # Uses "config" as dataclass argument
```

### Complete Example with Keyword Arguments

```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class GlobalConfig:
    name: str = field(default="test", metadata={"help": "The name to use"})

parser = DataclassArgParser(
    global_config=GlobalConfig,
    flags=[(
        ('-v', '--verbose'),
        {'action': 'store_true', 'help': 'Enable verbose output'}
    )],
    config_flag=('-c', '--config'),
)
result = parser.parse()

global_config: GlobalConfig = result["global_config"]
verbose: bool = result.get("verbose", False)

print(f"Name: {global_config.name}")
print(f"Verbose: {verbose}")
```

## Custom flags and configurable config-file option

- Custom flags added via the `flags` constructor argument or via `add_flag()` are passed through to the underlying `argparse.ArgumentParser`. After `parse()` returns, any flags that are not dataclass fields (and are not the configured config-file option) appear as top-level keys in the returned dict using their argparse destination names. The parser protects dataclass entries from being overwritten; if a custom flag would collide with a dataclass key a `ValueError` is raised.

- The config-file option name can be customized with the `config_flag` constructor parameter. Provide a single option string (e.g. `'--cfg'`) or a sequence like `('-c', '--config')`. The parser records the argparse destination name for the config option so configuration loading works regardless of the option strings you choose.

Example mixing custom flags and a short config flag:

```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class Config:
  name: str = field(default="test", metadata={"help": "The name to use"})

parser = DataclassArgParser(
  Config,
  flags=[(
    ('-v', '--verbose'),
    {'action': 'store_true', 'help': 'Enable verbose output'}
  )],
  config_flag=('-c', '--config'),
)
res = parser.parse()
# res will contain: {'Config': Config(...), 'verbose': True} if --verbose passed
```

## Field Metadata

Use the `metadata` parameter in `field()` to provide help text:

```python
@dataclass
class Config:
    value: int = field(metadata={"help": "Description of this field"})
```

## Supported Types

- `str` - String values
- `int` - Integer values
- `float` - Float values
- `bool` - Boolean values
- `Literal[...]` - Choice from predefined options (e.g., `Literal["dev", "staging", "prod"]`)
- `list[T]` - List of values of type T (e.g., `list[int]`, `list[str]`)
- `tuple[T1, T2, ...]` - Tuple of fixed types (e.g., `tuple[int, float, str]`)
- `dict[K, V]` - Dictionary with key type K and value type V (e.g., `dict[str, int]`, `dict[str, str]`)
- Nested dataclasses - Dataclass types as fields with dot notation access
- Custom types (uses type name as metavar)

### List and Tuple Arguments

You can use list and tuple types in your dataclasses. The parser will handle them from the command line:

```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class ListTupleConfig:
  numbers: list[int] = field(default_factory=lambda: [1, 2, 3], metadata={"help": "A list of integers"})
  coords: tuple[int, int, int] = field(default=(0, 0, 0), metadata={"help": "A tuple of three integers"})

parser = DataclassArgParser(ListTupleConfig)
result = parser.parse()
cfg = result['ListTupleConfig']
print(cfg.numbers)
print(cfg.coords)
```

#### Command-line usage:

```bash
# List values can be provided as comma-separated or bracketed:
python script.py --ListTupleConfig.numbers 4,5,6
python script.py --ListTupleConfig.numbers "[7,8,9]"

# Tuple values can be provided as comma-separated or parenthesized:
python script.py --ListTupleConfig.coords 1,2,3
python script.py --ListTupleConfig.coords "(4,5,6)"
```

The parser will convert these arguments to the correct Python types.

### Dict Arguments

You can use dict types in your dataclasses. The parser supports multiple input formats for dictionaries:

```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class DictConfig:
    settings: dict[str, str] = field(
        default_factory=lambda: {"env": "dev", "region": "us-east"},
        metadata={"help": "Application settings"}
    )
    limits: dict[str, int] = field(
        default_factory=lambda: {"max_users": 100, "timeout": 30},
        metadata={"help": "System limits"}
    )
    rates: dict[str, float] = field(
        default_factory=lambda: {"cpu": 0.8, "memory": 0.6},
        metadata={"help": "Resource utilization rates"}
    )

parser = DataclassArgParser(DictConfig)
result = parser.parse()
cfg = result['DictConfig']
print(cfg.settings)
print(cfg.limits)
print(cfg.rates)
```

#### Command-line usage for dicts:

```bash
# JSON format (recommended for complex values)
python script.py --DictConfig.settings '{"env": "prod", "region": "us-west", "debug": "false"}'

# Key=value format (convenient for simple cases)
python script.py --DictConfig.limits "max_users=500,timeout=60"

# Mixed types work correctly
python script.py --DictConfig.rates '{"cpu": 0.9, "memory": 0.75, "disk": 0.5}'

# Empty dictionaries
python script.py --DictConfig.settings "{}"
python script.py --DictConfig.limits ""
```

**Dict Type Support:**
- `dict[str, str]` - String keys and values
- `dict[str, int]` - String keys, integer values
- `dict[str, float]` - String keys, float values
- Automatic type conversion based on annotations
- Both JSON and key=value input formats supported

### Nested Dataclasses

DataclassArgParser supports nested dataclasses, allowing you to organize configuration hierarchically:

```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class DatabaseConfig:
    host: str = field(default="localhost", metadata={"help": "Database host"})
    port: int = field(default=5432, metadata={"help": "Database port"})
    name: str = field(default="mydb", metadata={"help": "Database name"})

@dataclass
class ServerConfig:
    host: str = field(default="0.0.0.0", metadata={"help": "Server host"})
    port: int = field(default=8000, metadata={"help": "Server port"})

@dataclass
class AppConfig:
    app_name: str = field(default="MyApp", metadata={"help": "Application name"})
    database: DatabaseConfig = field(default_factory=DatabaseConfig, metadata={"help": "Database configuration"})
    server: ServerConfig = field(default_factory=ServerConfig, metadata={"help": "Server configuration"})

parser = DataclassArgParser(AppConfig)
result = parser.parse()
config = result['AppConfig']

print(f"App: {config.app_name}")
print(f"Database: {config.database.host}:{config.database.port}/{config.database.name}")
print(f"Server: {config.server.host}:{config.server.port}")
```

#### Command-line usage for nested dataclasses:

```bash
# Override nested fields using dot notation
python script.py \
  --AppConfig.app_name "ProductionApp" \
  --AppConfig.database.host "prod-db.example.com" \
  --AppConfig.database.port 3306 \
  --AppConfig.database.name "prod_db" \
  --AppConfig.server.port 443
```

#### Config file for nested dataclasses:

```json
{
  "AppConfig": {
    "app_name": "ProductionApp",
    "database": {
      "host": "prod-db.example.com",
      "port": 3306,
      "name": "prod_db"
    },
    "server": {
      "host": "0.0.0.0",
      "port": 443
    }
  }
}
```

You can also override specific nested fields from command line while loading the rest from config:

```bash
python script.py --config app_config.json --AppConfig.database.port 5433
```

### Custom Flags

DataclassArgParser allows you to mix custom command-line flags with auto-generated dataclass arguments:

```python
from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser

@dataclass
class AppConfig:
    name: str = field(default="example", metadata={"help": "Application name"})
    port: int = field(default=8080, metadata={"help": "Port number"})

# Method 1: Add flags in constructor
parser = DataclassArgParser(
    AppConfig,
    flags=[
        ("--verbose", {"action": "store_true", "help": "Enable verbose output"}),
        {"names": ["--quiet", "-q"], "kwargs": {"action": "store_true", "help": "Quiet mode"}},
        (["--log-file", "-l"], {"type": str, "help": "Path to log file"}),
    ],
    config_flag=["-c", "--config"],  # Customize config flag
)

# Method 2: Add flags after construction using add_flag()
parser.add_flag("--debug", "-d", action="store_true", help="Enable debug mode")
parser.add_flag("--output", "-o", type=str, default="output.txt", help="Output file path")

result = parser.parse()

# Access dataclass instance
config = result["AppConfig"]
print(f"App name: {config.name}, Port: {config.port}")

# Access custom flags
if result.get("verbose"):
    print("Verbose mode enabled")
if result.get("debug"):
    print("Debug mode enabled")
if result.get("log_file"):
    print(f"Logging to: {result['log_file']}")
```

#### Command-line usage with custom flags:

```bash
python script.py \
  --AppConfig.name "MyApp" \
  --AppConfig.port 9000 \
  --verbose \
  --debug \
  --log-file /var/log/app.log \
  -o results.json
```

**Custom Flag Features:**
- Add flags via `flags` parameter in constructor
- Add flags dynamically with `add_flag()` method
- Support for short and long option names (e.g., `-v`, `--verbose`)
- Custom flags appear as top-level keys in the result dictionary
- Automatic conflict detection with dataclass field names
- Full support for all argparse argument types and options

## Config File Formats

### JSON
```json
{
  "ConfigClass": {
    "field_name": "value"
  }
}
```

### YAML (requires PyYAML)
```yaml
ConfigClass:
  field_name: value
```

## Error Handling

The parser provides clear error messages for:
- **Missing required fields**: Shows which fields need to be provided via CLI or config file
- **Invalid config file formats**: Detects malformed JSON/YAML with specific error details
- **Type validation errors**: Reports when values cannot be converted to expected types
- **Invalid literal choices**: Shows allowed values when an invalid choice is provided
- **File not found**: Clear message when config file path is invalid
- **Flag name conflicts**: Prevents custom flags from colliding with dataclass field names
- **Dict parsing errors**: Helpful messages for malformed dictionary inputs (JSON or key=value format)
- **Tuple/List length mismatches**: Validates correct number of elements for typed tuples

All errors are surfaced through argparse's error mechanism, providing consistent error reporting with usage information.

## Project Structure

```
dataclass_argparser/
├── src/
│   └── dataclass_argparser/
│       ├── __init__.py
│       └── parser.py          # Main implementation
├── tests/
│   ├── test_parser.py         # Core functionality tests
│   ├── test_list_types.py     # List type support tests
│   ├── test_tuple_types.py    # Tuple type support tests
│   ├── test_dict_types.py     # Dictionary type support tests
│   ├── test_nested_types.py   # Nested dataclass tests
│   ├── test_config_files.py   # Config file loading tests
│   ├── test_custom_flags.py   # Custom flags tests
│   └── test_default_values.py # Default value handling tests
├── examples/
│   ├── basic_example.py       # Basic usage example
│   ├── override_example.py    # Config override example
│   ├── custom_flags_example.py # Custom flags example
│   ├── example_config.json    # Sample config file
│   └── override_config.json   # Override config file
├── pixi.toml                  # Pixi package configuration
├── pyproject.toml             # Python package metadata
└── README.md                  # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.
