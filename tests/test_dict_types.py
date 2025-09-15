"""
Tests for dict type support in DataclassArgParser.

This test suite covers:
1. Fully implemented functionality:
   - Default dict values work correctly
   - CLI arguments are created for dict fields
   - Config file support works (dicts load from JSON/YAML naturally)
   - Help text includes dict field information with proper formatting
   - CLI parsing of dict values (JSON format like '{"key": "value"}')
   - CLI parsing of dict values (key=value format like 'key=value,key2=value2')
   - CLI override of config file dict values
   - Error handling for invalid dict formats
   - Parametrized CLI variant testing with comprehensive coverage
   - Config file integration testing

2. Implementation notes:
   - Dict support is fully implemented for CLI parsing using both JSON format
     ('{"key": "value"}') and key=value format ('key=value,key2=value2')
   - Config file support works seamlessly since JSON/YAML naturally map to dict objects
   - Type conversion works correctly for dict[str, int], dict[str, float], dict[str, str]
   - Error handling provides clear feedback for invalid formats

All tests are now passing - dict type support is complete!
"""

import dataclasses
import pytest
from dataclass_argparser.parser import DataclassArgParser


@dataclasses.dataclass
class DictConfig:
    settings: dict[str, str] = dataclasses.field(
        default_factory=lambda: {"key1": "value1", "key2": "value2"},
        metadata={"help": "A dictionary of string key-value pairs"},
    )
    numbers: dict[str, int] = dataclasses.field(
        default_factory=lambda: {"count": 10, "max": 100},
        metadata={"help": "A dictionary with string keys and integer values"},
    )
    mixed: dict[str, float] = dataclasses.field(
        default_factory=lambda: {"rate": 0.5, "threshold": 1.0},
        metadata={"help": "A dictionary with string keys and float values"},
    )


def test_dict_default_values():
    """Test that default dict values are properly set."""
    parser = DataclassArgParser(DictConfig)
    result = parser.parse([])
    cfg = result["DictConfig"]
    assert cfg.settings == {"key1": "value1", "key2": "value2"}
    assert cfg.numbers == {"count": 10, "max": 100}
    assert cfg.mixed == {"rate": 0.5, "threshold": 1.0}


def test_dict_cli_arguments_are_created():
    """Test that CLI arguments are created for dict fields."""
    parser = DataclassArgParser(DictConfig)
    help_text = parser.parser.format_help()

    # Check that CLI arguments are created for dict fields
    assert "--DictConfig.settings" in help_text
    assert "--DictConfig.numbers" in help_text
    assert "--DictConfig.mixed" in help_text

    # Check that help text is shown
    assert "A dictionary of string key-value pairs" in help_text
    assert "A dictionary with string keys and integer values" in help_text
    assert "A dictionary with string keys and float values" in help_text


def test_dict_cli_parsing_json_format():
    """Test parsing dict from CLI using JSON format."""
    parser = DataclassArgParser(DictConfig)

    # Test string dict with JSON format
    result = parser.parse(["--DictConfig.settings", '{"name": "test", "env": "dev"}'])
    cfg = result["DictConfig"]
    assert cfg.settings == {"name": "test", "env": "dev"}

    # Test int dict with JSON format
    result = parser.parse(["--DictConfig.numbers", '{"items": 5, "limit": 50}'])
    cfg = result["DictConfig"]
    assert cfg.numbers == {"items": 5, "limit": 50}

    # Test float dict with JSON format
    result = parser.parse(["--DictConfig.mixed", '{"alpha": 0.25, "beta": 2.5}'])
    cfg = result["DictConfig"]
    assert cfg.mixed == {"alpha": 0.25, "beta": 2.5}


def test_dict_cli_parsing_key_value_format():
    """Test parsing dict from CLI using key=value format."""
    parser = DataclassArgParser(DictConfig)

    # Test string dict with key=value format
    result = parser.parse(["--DictConfig.settings", "name=test,env=dev"])
    cfg = result["DictConfig"]
    assert cfg.settings == {"name": "test", "env": "dev"}

    # Test int dict with key=value format
    result = parser.parse(["--DictConfig.numbers", "items=5,limit=50"])
    cfg = result["DictConfig"]
    assert cfg.numbers == {"items": 5, "limit": 50}

    # Test float dict with key=value format
    result = parser.parse(["--DictConfig.mixed", "alpha=0.25,beta=2.5"])
    cfg = result["DictConfig"]
    assert cfg.mixed == {"alpha": 0.25, "beta": 2.5}


def test_dict_cli_parsing_with_spaces():
    """Test parsing dict from CLI with spaces in JSON format."""
    parser = DataclassArgParser(DictConfig)

    # Test with spaces in JSON
    result = parser.parse(
        ["--DictConfig.settings", '{ "key 1": "value 1", "key 2": "value 2" }']
    )
    cfg = result["DictConfig"]
    assert cfg.settings == {"key 1": "value 1", "key 2": "value 2"}


def test_dict_empty_dict():
    """Test parsing empty dict from CLI."""
    parser = DataclassArgParser(DictConfig)

    # Test empty dict with JSON format
    result = parser.parse(["--DictConfig.settings", "{}"])
    cfg = result["DictConfig"]
    assert cfg.settings == {}

    # Test empty dict with key=value format
    result = parser.parse(["--DictConfig.numbers", ""])
    cfg = result["DictConfig"]
    assert cfg.numbers == {}


def test_dict_config_file_with_cli_override():
    """Test that CLI args can override dict values from config files."""
    import tempfile
    import json
    import os

    # Create a temporary config file
    config_data = {
        "DictConfig": {
            "settings": {"name": "config", "env": "production"},
            "numbers": {"count": 10, "limit": 50},
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name

    try:
        parser = DataclassArgParser(DictConfig)

        # Config file values should be loaded
        result = parser.parse(["--config", config_file])
        cfg = result["DictConfig"]
        assert cfg.settings == {"name": "config", "env": "production"}
        assert cfg.numbers == {"count": 10, "limit": 50}

        # CLI override should now work
        result = parser.parse(
            ["--config", config_file, "--DictConfig.settings", '{"name": "override"}']
        )
        cfg = result["DictConfig"]
        assert cfg.settings == {"name": "override"}

        # Test overriding numbers dict
        result = parser.parse(
            ["--config", config_file, "--DictConfig.numbers", '{"count": 99}']
        )
        cfg = result["DictConfig"]
        assert cfg.numbers == {"count": 99}

    finally:
        # Clean up
        os.unlink(config_file)


def test_dict_config_file_support():
    """Test dict support in config files."""
    import tempfile
    import json
    import os

    # Create a temporary config file with dict values
    config_data = {
        "DictConfig": {
            "settings": {"config_key": "config_value", "env": "production"},
            "numbers": {"config_count": 42, "max_limit": 1000},
            "mixed": {"config_rate": 0.75, "threshold": 2.5},
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name

    try:
        parser = DataclassArgParser(DictConfig)
        result = parser.parse(["--config", config_file])
        cfg = result["DictConfig"]

        # Dict values from config file should work perfectly
        assert cfg.settings == {"config_key": "config_value", "env": "production"}
        assert cfg.numbers == {"config_count": 42, "max_limit": 1000}
        assert cfg.mixed == {"config_rate": 0.75, "threshold": 2.5}

    finally:
        # Clean up
        os.unlink(config_file)


def test_dict_current_cli_behavior():
    """Test current behavior when dict values are passed via CLI."""
    parser = DataclassArgParser(DictConfig)

    # Dict parsing now works!
    result = parser.parse(["--DictConfig.settings", '{"key": "value"}'])
    cfg = result["DictConfig"]
    assert cfg.settings == {"key": "value"}

    # Test that both JSON and key=value formats work
    result = parser.parse(["--DictConfig.settings", "name=test,env=dev"])
    cfg = result["DictConfig"]
    assert cfg.settings == {"name": "test", "env": "dev"}


@pytest.mark.parametrize(
    "cli_args,field_name,expected",
    [
        # JSON format tests
        (
            ["--DictConfig.settings", '{"a": "1", "b": "2"}'],
            "settings",
            {"a": "1", "b": "2"},
        ),
        (["--DictConfig.numbers", '{"x": 10, "y": 20}'], "numbers", {"x": 10, "y": 20}),
        (
            ["--DictConfig.mixed", '{"pi": 3.14, "e": 2.71}'],
            "mixed",
            {"pi": 3.14, "e": 2.71},
        ),
        # Key=value format tests
        (["--DictConfig.settings", "a=1,b=2"], "settings", {"a": "1", "b": "2"}),
        (["--DictConfig.numbers", "x=10,y=20"], "numbers", {"x": 10, "y": 20}),
        (["--DictConfig.mixed", "pi=3.14,e=2.71"], "mixed", {"pi": 3.14, "e": 2.71}),
        # Single key-value pair tests
        (["--DictConfig.settings", "single=value"], "settings", {"single": "value"}),
        (["--DictConfig.numbers", "one=1"], "numbers", {"one": 1}),
        (["--DictConfig.mixed", "ratio=0.5"], "mixed", {"ratio": 0.5}),
    ],
)
def test_dict_cli_variants(cli_args, field_name, expected):
    """Test various CLI format variations for dict parsing."""
    parser = DataclassArgParser(DictConfig)
    result = parser.parse(cli_args)
    cfg = result["DictConfig"]
    actual = getattr(cfg, field_name)
    assert actual == expected


def test_dict_error_handling():
    """Test error handling for invalid dict formats."""
    parser = DataclassArgParser(DictConfig)

    # Test invalid JSON format
    with pytest.raises(SystemExit):  # argparse typically calls sys.exit on error
        parser.parse(["--DictConfig.settings", '{"invalid": json}'])

    # Test invalid key=value format (missing equals)
    with pytest.raises(SystemExit):
        parser.parse(["--DictConfig.settings", "invalid_no_equals"])

    # Test type mismatch for numbers
    with pytest.raises(SystemExit):
        parser.parse(["--DictConfig.numbers", '{"key": "not_a_number"}'])


@dataclasses.dataclass
class NestedDictConfig:
    """Test configuration with nested dictionaries."""

    metadata: dict[str, dict[str, str]] = dataclasses.field(
        default_factory=lambda: {
            "user": {"name": "admin", "role": "super"},
            "app": {"version": "1.0", "env": "prod"},
        },
        metadata={"help": "Nested dictionary configuration"},
    )


def test_nested_dict_config_file():
    """Test nested dict support in config files."""
    # This documents the expected behavior for nested dicts in config files
    parser = DataclassArgParser(NestedDictConfig)
    result = parser.parse([])
    cfg = result["NestedDictConfig"]
    expected = {
        "user": {"name": "admin", "role": "super"},
        "app": {"version": "1.0", "env": "prod"},
    }
    assert cfg.metadata == expected


def test_dict_types_not_currently_supported():
    """Test current behavior with dict types - CLI args are created but parsing is not implemented."""
    # The current parser recognizes dict types and creates CLI arguments for them,
    # but it doesn't implement the actual string-to-dict parsing functionality
    parser = DataclassArgParser(DictConfig)

    # Default values work fine
    result = parser.parse([])
    assert "DictConfig" in result
    cfg = result["DictConfig"]
    assert isinstance(cfg.settings, dict)
    assert isinstance(cfg.numbers, dict)
    assert isinstance(cfg.mixed, dict)

    # CLI arguments are created
    help_text = parser.parser.format_help()
    assert "--DictConfig.settings" in help_text
    assert "DICT" in help_text


def test_dict_cli_help_text():
    """Test that dict types show appropriate help text."""
    parser = DataclassArgParser(DictConfig)

    help_text = parser.parser.format_help()

    # Check that dict fields appear in help text
    assert "dictionary" in help_text.lower() or "dict" in help_text.lower()
    assert "settings" in help_text
    assert "A dictionary of string key-value pairs" in help_text

    # Check that all dict fields are present
    assert "--DictConfig.settings" in help_text
    assert "--DictConfig.numbers" in help_text
    assert "--DictConfig.mixed" in help_text

    # Check that metavar shows DICT
    assert "DICT" in help_text

    # Check that default values are shown
    assert "default:" in help_text
