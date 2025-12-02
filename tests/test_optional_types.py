#!/usr/bin/env python3
"""
Tests for Optional type support in DataclassArgParser.

This module tests that the parser correctly handles Optional[T] fields
in dataclasses, including parsing from CLI and config files.
"""

import json
import os
import tempfile
from dataclasses import dataclass, field
from typing import Optional

import pytest

from dataclass_argparser import DataclassArgParser


@dataclass
class OptionalFieldsConfig:
    """Configuration with Optional fields for testing."""

    optional_str: Optional[str] = field(
        default=None, metadata={"help": "An optional string field"}
    )
    optional_int: Optional[int] = field(
        default=None, metadata={"help": "An optional integer field"}
    )
    optional_float: Optional[float] = field(
        default=None, metadata={"help": "An optional float field"}
    )
    optional_bool: Optional[bool] = field(
        default=None, metadata={"help": "An optional boolean field"}
    )
    required_str: str = field(
        default="required", metadata={"help": "A required string field"}
    )


@dataclass
class OptionalWithDefaultsConfig:
    """Configuration with Optional fields that have non-None defaults."""

    optional_str: Optional[str] = field(
        default="default_value", metadata={"help": "Optional string with default"}
    )
    optional_int: Optional[int] = field(
        default=42, metadata={"help": "Optional int with default"}
    )


class TestOptionalTypes:
    """Test suite for Optional type support."""

    def test_optional_fields_with_none_default(self):
        """Test that Optional fields with None default work correctly."""
        parser = DataclassArgParser(OptionalFieldsConfig)
        result = parser.parse([])
        config = result["OptionalFieldsConfig"]

        assert config.optional_str is None
        assert config.optional_int is None
        assert config.optional_float is None
        assert config.optional_bool is None
        assert config.required_str == "required"

    def test_optional_str_from_cli(self):
        """Test parsing Optional[str] from command line."""
        parser = DataclassArgParser(OptionalFieldsConfig)
        result = parser.parse(["--OptionalFieldsConfig.optional_str", "hello"])
        config = result["OptionalFieldsConfig"]

        assert config.optional_str == "hello"

    def test_optional_int_from_cli(self):
        """Test parsing Optional[int] from command line."""
        parser = DataclassArgParser(OptionalFieldsConfig)
        result = parser.parse(["--OptionalFieldsConfig.optional_int", "123"])
        config = result["OptionalFieldsConfig"]

        assert config.optional_int == 123

    def test_optional_float_from_cli(self):
        """Test parsing Optional[float] from command line."""
        parser = DataclassArgParser(OptionalFieldsConfig)
        result = parser.parse(["--OptionalFieldsConfig.optional_float", "3.14"])
        config = result["OptionalFieldsConfig"]

        assert config.optional_float == 3.14

    def test_optional_bool_from_cli(self):
        """Test parsing Optional[bool] from command line."""
        parser = DataclassArgParser(OptionalFieldsConfig)
        result = parser.parse(["--OptionalFieldsConfig.optional_bool", "true"])
        config = result["OptionalFieldsConfig"]

        assert config.optional_bool is True

    def test_optional_fields_from_config_file(self):
        """Test parsing Optional fields from a config file."""
        config_data = {
            "OptionalFieldsConfig": {
                "optional_str": "from_config",
                "optional_int": 456,
                "optional_float": 2.71,
                "optional_bool": False,
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(OptionalFieldsConfig)
            result = parser.parse(["--config", config_path])
            config = result["OptionalFieldsConfig"]

            assert config.optional_str == "from_config"
            assert config.optional_int == 456
            assert config.optional_float == 2.71
            assert config.optional_bool is False
        finally:
            os.unlink(config_path)

    def test_optional_fields_cli_overrides_config(self):
        """Test that CLI arguments override config file values for Optional fields."""
        config_data = {
            "OptionalFieldsConfig": {
                "optional_str": "from_config",
                "optional_int": 100,
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(OptionalFieldsConfig)
            result = parser.parse(
                [
                    "--config",
                    config_path,
                    "--OptionalFieldsConfig.optional_str",
                    "from_cli",
                ]
            )
            config = result["OptionalFieldsConfig"]

            assert config.optional_str == "from_cli"  # Overridden by CLI
            assert config.optional_int == 100  # From config
        finally:
            os.unlink(config_path)

    def test_optional_with_non_none_defaults(self):
        """Test Optional fields that have non-None default values."""
        parser = DataclassArgParser(OptionalWithDefaultsConfig)
        result = parser.parse([])
        config = result["OptionalWithDefaultsConfig"]

        assert config.optional_str == "default_value"
        assert config.optional_int == 42

    def test_optional_with_non_none_defaults_override(self):
        """Test overriding Optional fields that have non-None default values."""
        parser = DataclassArgParser(OptionalWithDefaultsConfig)
        result = parser.parse(
            [
                "--OptionalWithDefaultsConfig.optional_str",
                "overridden",
                "--OptionalWithDefaultsConfig.optional_int",
                "99",
            ]
        )
        config = result["OptionalWithDefaultsConfig"]

        assert config.optional_str == "overridden"
        assert config.optional_int == 99

    def test_optional_null_in_config_file(self):
        """Test that null in config file sets Optional field to None."""
        config_data = {
            "OptionalFieldsConfig": {
                "optional_str": None,
                "optional_int": None,
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(OptionalFieldsConfig)
            result = parser.parse(["--config", config_path])
            config = result["OptionalFieldsConfig"]

            assert config.optional_str is None
            assert config.optional_int is None
        finally:
            os.unlink(config_path)


class TestOptionalListTypes:
    """Test suite for Optional list types."""

    @dataclass
    class OptionalListConfig:
        """Configuration with Optional list fields."""

        optional_list: Optional[list[int]] = field(
            default=None, metadata={"help": "An optional list of integers"}
        )

    def test_optional_list_default_none(self):
        """Test Optional[list[int]] with None default."""
        parser = DataclassArgParser(self.OptionalListConfig)
        result = parser.parse([])
        config = result["OptionalListConfig"]

        assert config.optional_list is None

    def test_optional_list_from_cli(self):
        """Test parsing Optional[list[int]] from command line."""
        parser = DataclassArgParser(self.OptionalListConfig)
        result = parser.parse(["--OptionalListConfig.optional_list", "1,2,3"])
        config = result["OptionalListConfig"]

        assert config.optional_list == [1, 2, 3]


class TestOptionalDictTypes:
    """Test suite for Optional dict types."""

    @dataclass
    class OptionalDictConfig:
        """Configuration with Optional dict fields."""

        optional_dict: Optional[dict[str, int]] = field(
            default=None, metadata={"help": "An optional dict"}
        )

    def test_optional_dict_default_none(self):
        """Test Optional[dict[str, int]] with None default."""
        parser = DataclassArgParser(self.OptionalDictConfig)
        result = parser.parse([])
        config = result["OptionalDictConfig"]

        assert config.optional_dict is None

    def test_optional_dict_from_cli(self):
        """Test parsing Optional[dict[str, int]] from command line."""
        parser = DataclassArgParser(self.OptionalDictConfig)
        result = parser.parse(["--OptionalDictConfig.optional_dict", "a=1,b=2"])
        config = result["OptionalDictConfig"]

        assert config.optional_dict == {"a": 1, "b": 2}
