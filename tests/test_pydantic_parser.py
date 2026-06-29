#!/usr/bin/env python3
"""
Tests for DataclassArgParser with Pydantic BaseModel classes.

Mirrors core tests from tests/test_parser.py for Pydantic model definitions.
"""

import argparse
import io
import json
import os
import tempfile
from typing import Literal
from unittest.mock import patch

import pytest

pytest.importorskip("pydantic")

from pydantic import BaseModel, Field

from dataclass_argparser import DataclassArgParser


class SampleConfig(BaseModel):
    """Sample configuration model with various field types."""

    string_field: str = Field(
        default="default_value", description="A string field for testing"
    )
    int_field: int = Field(default=42, description="An integer field for testing")
    float_field: float = Field(default=3.14, description="A float field for testing")
    bool_field: bool = Field(default=True, description="A boolean field for testing")
    literal_field: Literal["option1", "option2", "option3"] = Field(
        default="option1", description="A literal field with choices"
    )
    no_help_field: str = Field(default="no_help")


class AnotherConfig(BaseModel):
    """Another test configuration model."""

    path: str = Field(default="/default/path", description="Path to a file or directory")
    count: int = Field(default=10, description="Number of items to process")


class RequiredFieldsConfig(BaseModel):
    """Configuration with required fields for testing validation."""

    required_string: str = Field(description="A required string field")
    required_int: int = Field(description="A required integer field")
    optional_field: str = Field(
        default="optional_default", description="An optional field with default"
    )


class RequiredTupleConfig(BaseModel):
    """Configuration with required tuple fields for testing validation."""

    required_tuple: tuple[int, int, int] = Field(description="A required tuple field")
    optional_field: str = Field(
        default="optional_default", description="An optional field with default"
    )


class TestPydanticArgParser:
    """Test suite for DataclassArgParser with Pydantic models."""

    def test_initialization_single_model(self):
        """Test parser initialization with a single Pydantic model."""
        parser = DataclassArgParser(SampleConfig)
        assert parser.dataclass_types == (SampleConfig,)
        assert isinstance(parser.parser, argparse.ArgumentParser)

    def test_initialization_multiple_models(self):
        """Test parser initialization with multiple Pydantic models."""
        parser = DataclassArgParser(SampleConfig, AnotherConfig)
        assert parser.dataclass_types == (SampleConfig, AnotherConfig)
        assert isinstance(parser.parser, argparse.ArgumentParser)

    def test_help_extraction_from_field_description(self):
        """Test that help text is correctly extracted from Field descriptions."""
        parser = DataclassArgParser(SampleConfig)

        with patch("sys.stdout", new_callable=io.StringIO):
            with pytest.raises(SystemExit):
                parser.parser.parse_args(["--help"])

        help_text = parser.parser.format_help()
        assert "A string field for testing" in help_text
        assert "An integer field for testing" in help_text
        assert "default_value" in help_text

    def test_parse_with_defaults(self):
        """Test parsing with all default values."""
        parser = DataclassArgParser(SampleConfig)
        result = parser.parse([])

        config = result["SampleConfig"]
        assert isinstance(config, SampleConfig)
        assert config.string_field == "default_value"
        assert config.int_field == 42
        assert config.float_field == 3.14
        assert config.bool_field is True
        assert config.literal_field == "option1"

    def test_parse_with_cli_overrides(self):
        """Test parsing with command-line overrides."""
        parser = DataclassArgParser(SampleConfig)
        result = parser.parse(
            [
                "--SampleConfig.string_field",
                "custom",
                "--SampleConfig.int_field",
                "100",
                "--SampleConfig.bool_field",
                "false",
            ]
        )

        config = result["SampleConfig"]
        assert config.string_field == "custom"
        assert config.int_field == 100
        assert config.bool_field is False

    def test_parse_multiple_models(self):
        """Test parsing with multiple Pydantic models."""
        parser = DataclassArgParser(SampleConfig, AnotherConfig)
        result = parser.parse(
            [
                "--SampleConfig.int_field",
                "99",
                "--AnotherConfig.path",
                "/custom/path",
            ]
        )

        assert result["SampleConfig"].int_field == 99
        assert result["AnotherConfig"].path == "/custom/path"

    def test_required_fields_missing_raises_error(self):
        """Test that missing required fields raise an error."""
        parser = DataclassArgParser(RequiredFieldsConfig)

        with pytest.raises(SystemExit):
            parser.parse([])

    def test_required_fields_provided_via_cli(self):
        """Test that required fields work when provided via CLI."""
        parser = DataclassArgParser(RequiredFieldsConfig)
        result = parser.parse(
            [
                "--RequiredFieldsConfig.required_string",
                "hello",
                "--RequiredFieldsConfig.required_int",
                "42",
            ]
        )

        config = result["RequiredFieldsConfig"]
        assert config.required_string == "hello"
        assert config.required_int == 42
        assert config.optional_field == "optional_default"

    def test_required_fields_from_config(self):
        """Test that required fields can be provided via config file."""
        config_data = {
            "RequiredFieldsConfig": {
                "required_string": "from_config",
                "required_int": 7,
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(RequiredFieldsConfig)
            result = parser.parse(["--config", config_path])
            config = result["RequiredFieldsConfig"]
            assert config.required_string == "from_config"
            assert config.required_int == 7
        finally:
            os.unlink(config_path)

    def test_literal_field_choices(self):
        """Test that Literal fields enforce choices."""
        parser = DataclassArgParser(SampleConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--SampleConfig.literal_field", "invalid_option"])

    def test_required_tuple_from_cli(self):
        """Test required tuple field from CLI."""
        parser = DataclassArgParser(RequiredTupleConfig)
        result = parser.parse(
            [
                "--RequiredTupleConfig.required_tuple",
                "1,2,3",
            ]
        )

        assert result["RequiredTupleConfig"].required_tuple == (1, 2, 3)

    def test_invalid_type_raises_type_error_on_init(self):
        """Test that non-schema types raise TypeError on initialization."""

        class NotASchema:
            pass

        with pytest.raises(TypeError, match="must be a dataclass or Pydantic BaseModel"):
            DataclassArgParser(NotASchema)
