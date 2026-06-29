#!/usr/bin/env python3
"""
Tests for Optional type support in DataclassArgParser with Pydantic models.

Mirrors ../test_optional_types.py for Pydantic BaseModel definitions.
"""

import json
import os
import tempfile
from typing import Optional

from pydantic import BaseModel, Field

from dataclass_argparser import DataclassArgParser


class OptionalFieldsConfig(BaseModel):
    """Configuration with Optional fields for testing."""

    optional_str: Optional[str] = Field(
        default=None, description="An optional string field"
    )
    optional_int: Optional[int] = Field(
        default=None, description="An optional integer field"
    )
    optional_float: Optional[float] = Field(
        default=None, description="An optional float field"
    )
    optional_bool: Optional[bool] = Field(
        default=None, description="An optional boolean field"
    )
    required_str: str = Field(
        default="required", description="A required string field"
    )


class OptionalWithDefaultsConfig(BaseModel):
    """Configuration with Optional fields that have non-None defaults."""

    optional_str: Optional[str] = Field(
        default="default_value", description="Optional string with default"
    )
    optional_int: Optional[int] = Field(
        default=42, description="Optional int with default"
    )


class TestOptionalTypes:
    """Test suite for Optional type support with Pydantic models."""

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

    def test_optional_from_config(self):
        """Test parsing Optional fields from config file."""
        config_data = {
            "OptionalFieldsConfig": {
                "optional_str": "from_config",
                "optional_int": 99,
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
            assert config.optional_int == 99
        finally:
            os.unlink(config_path)

    def test_optional_with_non_none_defaults(self):
        """Test Optional fields with non-None default values."""
        parser = DataclassArgParser(OptionalWithDefaultsConfig)
        result = parser.parse([])
        config = result["OptionalWithDefaultsConfig"]
        assert config.optional_str == "default_value"
        assert config.optional_int == 42
