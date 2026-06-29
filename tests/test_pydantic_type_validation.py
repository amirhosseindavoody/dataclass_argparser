#!/usr/bin/env python3
"""
Tests for type validation in DataclassArgParser with Pydantic models.

This module mirrors tests/test_type_validation.py but uses Pydantic BaseModel
classes. Validation is delegated to Pydantic rather than manual type checks.
"""

import json
import os
import tempfile
import textwrap

import pytest

pytest.importorskip("pydantic")

from pydantic import BaseModel, Field, ValidationError

from dataclass_argparser import DataclassArgParser


class BasicTypesConfig(BaseModel):
    """Configuration with basic types for testing type validation."""

    int_field: int = Field(default=0, description="An integer field")
    float_field: float = Field(default=0.0, description="A float field")
    str_field: str = Field(default="", description="A string field")
    bool_field: bool = Field(default=False, description="A boolean field")


class ListTypesConfig(BaseModel):
    """Configuration with list types for testing type validation."""

    int_list: list[int] = Field(default_factory=list, description="List of ints")
    float_list: list[float] = Field(
        default_factory=list, description="List of floats"
    )
    str_list: list[str] = Field(
        default_factory=list, description="List of strings"
    )


class DictTypesConfig(BaseModel):
    """Configuration with dict types for testing type validation."""

    str_int_dict: dict[str, int] = Field(
        default_factory=dict, description="Dict with string keys and int values"
    )
    str_float_dict: dict[str, float] = Field(
        default_factory=dict,
        description="Dict with string keys and float values",
    )


class TestCLITypeValidation:
    """Test suite for CLI type validation with Pydantic models."""

    def test_int_field_with_string_value_cli(self):
        """Test that passing a non-numeric string for int field raises error."""
        parser = DataclassArgParser(BasicTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--BasicTypesConfig.int_field", "not_a_number"])

    def test_int_field_with_float_string_cli(self):
        """Test that passing a float string for int field raises error."""
        parser = DataclassArgParser(BasicTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--BasicTypesConfig.int_field", "1.5"])

    def test_float_field_with_string_value_cli(self):
        """Test that passing a non-numeric string for float field raises error."""
        parser = DataclassArgParser(BasicTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--BasicTypesConfig.float_field", "not_a_number"])

    def test_bool_field_with_invalid_string_cli(self):
        """Test that passing an invalid string for bool field raises error."""
        parser = DataclassArgParser(BasicTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--BasicTypesConfig.bool_field", "maybe"])

    def test_bool_field_with_yes_no_string_cli(self):
        """Test that passing 'yes' or 'no' strings for bool field raises error."""
        parser = DataclassArgParser(BasicTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--BasicTypesConfig.bool_field", "yes"])

    def test_bool_field_valid_values_cli(self):
        """Test that valid boolean string representations work via CLI."""
        parser = DataclassArgParser(BasicTypesConfig)

        result = parser.parse(["--BasicTypesConfig.bool_field", "false"])
        assert result["BasicTypesConfig"].bool_field is False

        result = parser.parse(["--BasicTypesConfig.bool_field", "true"])
        assert result["BasicTypesConfig"].bool_field is True

        result = parser.parse(["--BasicTypesConfig.bool_field", "False"])
        assert result["BasicTypesConfig"].bool_field is False

        result = parser.parse(["--BasicTypesConfig.bool_field", "True"])
        assert result["BasicTypesConfig"].bool_field is True

        result = parser.parse(["--BasicTypesConfig.bool_field", "0"])
        assert result["BasicTypesConfig"].bool_field is False

        result = parser.parse(["--BasicTypesConfig.bool_field", "1"])
        assert result["BasicTypesConfig"].bool_field is True

    def test_list_int_with_string_elements_cli(self):
        """Test that passing non-integer elements in int list raises error."""
        parser = DataclassArgParser(ListTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--ListTypesConfig.int_list", "1,two,3"])

    def test_list_float_with_string_elements_cli(self):
        """Test that passing non-numeric elements in float list raises error."""
        parser = DataclassArgParser(ListTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--ListTypesConfig.float_list", "1.0,not_float,3.0"])

    def test_dict_int_value_with_string_value_cli(self):
        """Test that passing non-integer values in dict[str, int] raises error."""
        parser = DataclassArgParser(DictTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--DictTypesConfig.str_int_dict", "key1=not_int"])

    def test_dict_int_value_with_float_value_cli(self):
        """Test that passing float values in dict[str, int] raises error."""
        parser = DataclassArgParser(DictTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--DictTypesConfig.str_int_dict", "key1=1.5"])

    def test_dict_float_value_with_string_value_cli(self):
        """Test that passing non-numeric values in dict[str, float] raises error."""
        parser = DataclassArgParser(DictTypesConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--DictTypesConfig.str_float_dict", "key1=not_float"])


class TestConfigFileTypeValidation:
    """Test suite for config file type validation with Pydantic models."""

    def test_int_field_with_string_value_config(self):
        """Test that config file with string value for int field raises error."""
        config_data = {"BasicTypesConfig": {"int_field": "not_a_number"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises(ValidationError):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_int_field_with_float_value_config(self):
        """Test that config file with float value for int field raises error."""
        config_data = {"BasicTypesConfig": {"int_field": 1.5}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises(ValidationError):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_float_field_with_string_value_config(self):
        """Test that config file with string value for float field raises error."""
        config_data = {"BasicTypesConfig": {"float_field": "not_a_number"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises(ValidationError):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_bool_field_with_string_value_config(self):
        """Test that Pydantic coerces string 'false' to bool False from config."""
        config_data = {"BasicTypesConfig": {"bool_field": "false"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["BasicTypesConfig"].bool_field is False
        finally:
            os.unlink(config_path)

    def test_bool_field_with_int_value_config(self):
        """Test that Pydantic coerces int 0 to bool False from config."""
        config_data = {"BasicTypesConfig": {"bool_field": 0}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["BasicTypesConfig"].bool_field is False
        finally:
            os.unlink(config_path)

    def test_list_int_with_string_elements_config(self):
        """Test that config file with string elements in int list raises error."""
        config_data = {"ListTypesConfig": {"int_list": [1, "two", 3]}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(ListTypesConfig)
            with pytest.raises(ValidationError):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_list_int_with_float_elements_config(self):
        """Test that config file with float elements in int list raises error."""
        config_data = {"ListTypesConfig": {"int_list": [1, 2.5, 3]}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(ListTypesConfig)
            with pytest.raises(ValidationError):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_dict_int_value_with_string_value_config(self):
        """Test that config file with string values in dict[str, int] raises error."""
        config_data = {"DictTypesConfig": {"str_int_dict": {"key1": "not_int"}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(DictTypesConfig)
            with pytest.raises(ValidationError):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_dict_int_value_with_float_value_config(self):
        """Test that config file with float values in dict[str, int] raises error."""
        config_data = {"DictTypesConfig": {"str_int_dict": {"key1": 1.5}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(DictTypesConfig)
            with pytest.raises(ValidationError):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)


class TestYAMLConfigTypeValidation:
    """Test suite for YAML config file type validation with Pydantic models."""

    def test_int_field_with_string_value_yaml(self):
        """Test that Pydantic coerces quoted YAML string to int."""
        config_content = textwrap.dedent("""
            BasicTypesConfig:
              int_field: "123"
            """).strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["BasicTypesConfig"].int_field == 123
        finally:
            os.unlink(config_path)

    def test_bool_field_with_string_false_yaml(self):
        """Test that Pydantic coerces quoted 'false' string to bool from YAML."""
        config_content = textwrap.dedent("""
            BasicTypesConfig:
              bool_field: "false"
            """).strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["BasicTypesConfig"].bool_field is False
        finally:
            os.unlink(config_path)


class TestValidTypesPass:
    """Test suite to ensure valid types still work correctly with Pydantic models."""

    def test_valid_int_cli(self):
        """Test that valid int values work via CLI."""
        parser = DataclassArgParser(BasicTypesConfig)
        result = parser.parse(["--BasicTypesConfig.int_field", "42"])
        assert result["BasicTypesConfig"].int_field == 42

    def test_valid_float_cli(self):
        """Test that valid float values work via CLI."""
        parser = DataclassArgParser(BasicTypesConfig)
        result = parser.parse(["--BasicTypesConfig.float_field", "3.14"])
        assert result["BasicTypesConfig"].float_field == 3.14

    def test_valid_int_config(self):
        """Test that valid int values work via config file."""
        config_data = {"BasicTypesConfig": {"int_field": 42}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["BasicTypesConfig"].int_field == 42
        finally:
            os.unlink(config_path)

    def test_valid_bool_config(self):
        """Test that valid bool values work via config file."""
        config_data = {"BasicTypesConfig": {"bool_field": True}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["BasicTypesConfig"].bool_field is True
        finally:
            os.unlink(config_path)

    def test_valid_list_int_config(self):
        """Test that valid int list values work via config file."""
        config_data = {"ListTypesConfig": {"int_list": [1, 2, 3]}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(ListTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["ListTypesConfig"].int_list == [1, 2, 3]
        finally:
            os.unlink(config_path)

    def test_valid_dict_int_config(self):
        """Test that valid dict[str, int] values work via config file."""
        config_data = {"DictTypesConfig": {"str_int_dict": {"a": 1, "b": 2}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(DictTypesConfig)
            result = parser.parse(["--config", config_path])
            assert result["DictTypesConfig"].str_int_dict == {"a": 1, "b": 2}
        finally:
            os.unlink(config_path)

    def test_returns_pydantic_model_instance(self):
        """Test that parse returns a Pydantic model instance."""
        parser = DataclassArgParser(BasicTypesConfig)
        result = parser.parse([])
        config = result["BasicTypesConfig"]
        assert isinstance(config, BasicTypesConfig)
