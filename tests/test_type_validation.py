#!/usr/bin/env python3
"""
Tests for type validation in DataclassArgParser.

This module tests that the parser correctly raises errors when values
don't match the declared types in the dataclass.
"""

import json
import os
import tempfile
import textwrap
from dataclasses import dataclass, field
from typing import Literal

import pytest

from dataclass_argparser import DataclassArgParser


@dataclass
class BasicTypesConfig:
    """Configuration with basic types for testing type validation."""

    int_field: int = field(default=0, metadata={"help": "An integer field"})
    float_field: float = field(default=0.0, metadata={"help": "A float field"})
    str_field: str = field(default="", metadata={"help": "A string field"})
    bool_field: bool = field(default=False, metadata={"help": "A boolean field"})


@dataclass
class ListTypesConfig:
    """Configuration with list types for testing type validation."""

    int_list: list[int] = field(default_factory=list, metadata={"help": "List of ints"})
    float_list: list[float] = field(
        default_factory=list, metadata={"help": "List of floats"}
    )
    str_list: list[str] = field(
        default_factory=list, metadata={"help": "List of strings"}
    )


@dataclass
class DictTypesConfig:
    """Configuration with dict types for testing type validation."""

    str_int_dict: dict[str, int] = field(
        default_factory=dict, metadata={"help": "Dict with string keys and int values"}
    )
    str_float_dict: dict[str, float] = field(
        default_factory=dict,
        metadata={"help": "Dict with string keys and float values"},
    )


class TestCLITypeValidation:
    """Test suite for CLI type validation."""

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

        # Invalid boolean values should raise an error
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

        # Test lowercase 'false'
        result = parser.parse(["--BasicTypesConfig.bool_field", "false"])
        assert result["BasicTypesConfig"].bool_field is False

        # Test lowercase 'true'
        result = parser.parse(["--BasicTypesConfig.bool_field", "true"])
        assert result["BasicTypesConfig"].bool_field is True

        # Test uppercase 'False' and 'True'
        result = parser.parse(["--BasicTypesConfig.bool_field", "False"])
        assert result["BasicTypesConfig"].bool_field is False

        result = parser.parse(["--BasicTypesConfig.bool_field", "True"])
        assert result["BasicTypesConfig"].bool_field is True

        # Test '0' and '1'
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
    """Test suite for config file type validation."""

    def test_int_field_with_string_value_config(self):
        """Test that config file with string value for int field raises error."""
        config_data = {"BasicTypesConfig": {"int_field": "not_a_number"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises((TypeError, ValueError)):
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
            with pytest.raises((TypeError, ValueError)):
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
            with pytest.raises((TypeError, ValueError)):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_bool_field_with_string_value_config(self):
        """Test that config file with string 'false' for bool field raises error."""
        config_data = {"BasicTypesConfig": {"bool_field": "false"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises((TypeError, ValueError)):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_bool_field_with_int_value_config(self):
        """Test that config file with int 0/1 for bool field raises error."""
        config_data = {"BasicTypesConfig": {"bool_field": 0}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises((TypeError, ValueError)):
                parser.parse(["--config", config_path])
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
            with pytest.raises((TypeError, ValueError)):
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
            with pytest.raises((TypeError, ValueError)):
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
            with pytest.raises((TypeError, ValueError)):
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
            with pytest.raises((TypeError, ValueError)):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)


class TestYAMLConfigTypeValidation:
    """Test suite for YAML config file type validation."""

    def test_int_field_with_string_value_yaml(self):
        """Test that YAML config with quoted string for int field raises error."""
        # YAML treats quoted values as strings
        config_content = textwrap.dedent("""
            BasicTypesConfig:
              int_field: "123"
            """).strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises((TypeError, ValueError)):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_bool_field_with_string_false_yaml(self):
        """Test that YAML config with quoted 'false' string for bool raises error."""
        config_content = textwrap.dedent("""
            BasicTypesConfig:
              bool_field: "false"
            """).strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = DataclassArgParser(BasicTypesConfig)
            with pytest.raises((TypeError, ValueError)):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)


class TestValidTypesPass:
    """Test suite to ensure valid types still work correctly."""

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
