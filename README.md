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
from dataclass_argparser import DataclassArgParser

@dataclass
class Config:
    name: str = field(default="test", metadata={"help": "The name to use"})
    count: int = field(default=5, metadata={"help": "Number of items"})
    required_field: str = field(metadata={"help": "A required field"})

parser = DataclassArgParser(Config)
result = parser.parse()
config = result['Config']

print(f"Name: {config.name}")
print(f"Count: {config.count}")
print(f"Required: {config.required_field}")
```

## Usage Examples

### Basic Usage

```bash
python script.py --Config.name "myname" --Config.count 10 --Config.required_field "value"
```

### Using Config Files

Create a config file `config.json`:
```json
{
  "Config": {
    "name": "from_config",
    "count": 100,
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
DataclassArgParser(*dataclass_types: Type[Any])
```

**Parameters:**
- `*dataclass_types`: One or more dataclass types to generate arguments from

#### Methods

##### parse(args=None) -> Dict[str, Any]

Parse command-line arguments and return dataclass instances.

**Parameters:**
- `args`: Optional list of arguments to parse. If None, uses sys.argv.

**Returns:**
- Dict mapping dataclass names to their instantiated objects with parsed values.

**Raises:**
- `SystemExit`: If required fields are not provided either as command-line arguments or in the config file.

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
- Custom types (uses type name as metavar)

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
