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
- **Literal type support** with choice validation
- **Modern build system** using Hatchling for packaging

## Installation

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

## Testing

```bash
# Run tests
python -m pytest dataclass_argparser/tests/

# Run with coverage
python -m pytest dataclass_argparser/tests/ --cov=dataclass_argparser
```

## API Reference

### DataclassArgParser

Main class for creating argument parsers from dataclasses.

#### Constructor

```python
DataclassArgParser(*dataclass_types: Type[Any], flags: Optional[list] = None, config_flag: Union[str, list[str], tuple[str, ...]] = "--config")
```

**Parameters:**
- `*dataclass_types`: One or more dataclass types to generate arguments from
- `flags` (optional): A list of custom flags to add to the underlying parser. Each item may be either:
  - a tuple/list of `(short_flag, long_flag, kwargs_dict)` where `short_flag` and `long_flag` are option strings (e.g. `'-v'`, `'--verbose'`), and `kwargs_dict` is a dict of keyword args forwarded to `argparse.ArgumentParser.add_argument`; or
  - a dict of the form `{'names': name_or_list, 'kwargs': {...}}`.
  This lets you mix manually-declared flags (for example `--verbose`, `--dry-run`) with auto-generated dataclass arguments.
- `config_flag` (optional): Customize the command-line option(s) used to load a config file. Accepts a single string (e.g. `'--cfg'`) or a list/tuple of option strings (e.g. `['-c', '--config']`). The default is `"--config"`.

#### Methods

##### parse(args=None) -> Dict[str, Any]

Parse command-line arguments and return dataclass instances.

**Parameters:**
- `args`: Optional list of arguments to parse. If None, uses sys.argv.

**Returns:**
- Dict mapping dataclass names to their instantiated objects with parsed values.

**Raises:**
- `SystemExit`: If required fields are not provided either as command-line arguments or in the config file.

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
- `Literal` - Choice from predefined options
- `list[T]` - List of values of type T (e.g., `list[int]`, `list[str]`)
- `tuple[T1, T2, ...]` - Tuple of fixed types (e.g., `tuple[int, float, str]`)
- `dict[K, V]` - Dictionary with key type K and value type V (e.g., `dict[str, int]`, `dict[str, str]`)
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
- Missing required fields
- Invalid config file formats
- Type validation errors
- Invalid literal choices

## License

This project is licensed under the MIT License.
