import pytest
import argparse
import tempfile
import os
import json
from dataclasses import dataclass, field
from typing import Literal
from unittest.mock import patch
from io import StringIO

from dataclass_argparser import DataclassArgParser


@dataclass
class SampleConfig:
    """Sample configuration dataclass with various field types."""

    string_field: str = field(
        default="default_value", metadata={"help": "A string field for testing"}
    )

    int_field: int = field(
        default=42, metadata={"help": "An integer field for testing"}
    )

    float_field: float = field(
        default=3.14, metadata={"help": "A float field for testing"}
    )

    bool_field: bool = field(
        default=True, metadata={"help": "A boolean field for testing"}
    )

    literal_field: Literal["option1", "option2", "option3"] = field(
        default="option1", metadata={"help": "A literal field with choices"}
    )

    no_help_field: str = field(
        default="no_help"
        # Intentionally no metadata with help
    )


@dataclass
class AnotherConfig:
    """Another test configuration dataclass."""

    path: str = field(
        default="/default/path", metadata={"help": "Path to a file or directory"}
    )

    count: int = field(default=10, metadata={"help": "Number of items to process"})


@dataclass
class RequiredFieldsConfig:
    """Configuration with required fields (no defaults) for testing validation."""

    required_string: str = field(metadata={"help": "A required string field"})
    required_int: int = field(metadata={"help": "A required integer field"})
    optional_field: str = field(
        default="optional_default", metadata={"help": "An optional field with default"}
    )


@dataclass
class RequiredTupleConfig:
    """Configuration with required tuple fields for testing validation."""

    required_tuple: tuple[int, int, int] = field(
        metadata={"help": "A required tuple field"}
    )
    optional_field: str = field(
        default="optional_default", metadata={"help": "An optional field with default"}
    )


class TestDataclassArgParser:
    """Test suite for DataclassArgParser class."""

    def test_initialization_single_dataclass(self):
        """Test parser initialization with a single dataclass."""
        parser = DataclassArgParser(SampleConfig)
        assert parser.dataclass_types == (SampleConfig,)
        assert isinstance(parser.parser, argparse.ArgumentParser)

    def test_initialization_multiple_dataclasses(self):
        """Test parser initialization with multiple dataclasses."""
        parser = DataclassArgParser(SampleConfig, AnotherConfig)
        assert parser.dataclass_types == (SampleConfig, AnotherConfig)
        assert isinstance(parser.parser, argparse.ArgumentParser)

    def test_help_extraction_from_metadata(self):
        """Test that help text is correctly extracted from field metadata."""
        parser = DataclassArgParser(SampleConfig)

        # Capture help output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                parser.parser.parse_args(["--help"])
            help_output = mock_stdout.getvalue()

        # Check that help text from metadata is included
        assert "A string field for testing" in help_output
        assert "An integer field for testing" in help_output
        assert "A float field for testing" in help_output
        assert "A boolean field for testing" in help_output
        assert "A literal field with choices" in help_output

        # Check that argument names are formatted correctly
        assert "--SampleConfig.string_field" in help_output
        assert "--SampleConfig.int_field" in help_output
        assert "--SampleConfig.float_field" in help_output
        assert "--SampleConfig.bool_field" in help_output
        assert "--SampleConfig.literal_field" in help_output
        assert "--SampleConfig.no_help_field" in help_output

    def test_help_empty_when_no_metadata(self):
        """Test that fields without help metadata show only default value."""
        parser = DataclassArgParser(SampleConfig)

        # Find the argument for no_help_field
        for action in parser.parser._actions:
            if hasattr(action, "dest") and action.dest == "SampleConfig.no_help_field":
                # Help should show only default when no metadata is provided
                assert action.help == "(default: no_help)"
                break
        else:
            pytest.fail("Could not find SampleConfig.no_help_field argument")

    def test_literal_field_choices(self):
        """Test that Literal fields have correct choices set."""
        parser = DataclassArgParser(SampleConfig)

        # Find the literal field argument
        for action in parser.parser._actions:
            if hasattr(action, "dest") and action.dest == "SampleConfig.literal_field":
                assert action.choices == ("option1", "option2", "option3")
                assert action.help == "A literal field with choices (default: option1)"
                break
        else:
            pytest.fail("Could not find SampleConfig.literal_field argument")

    def test_multiple_dataclasses_help(self):
        """Test help text generation with multiple dataclasses."""
        parser = DataclassArgParser(SampleConfig, AnotherConfig)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                parser.parser.parse_args(["--help"])
            help_output = mock_stdout.getvalue()

        # Check help text from both dataclasses
        assert "A string field for testing" in help_output
        assert "Path to a file or directory" in help_output
        assert "Number of items to process" in help_output

        # Check argument names from both dataclasses
        assert "--SampleConfig.string_field" in help_output
        assert "--AnotherConfig.path" in help_output
        assert "--AnotherConfig.count" in help_output

    def test_parse_with_defaults(self):
        """Test parsing with default values."""
        parser = DataclassArgParser(SampleConfig)
        result = parser.parse([])

        config = result["SampleConfig"]
        assert config.string_field == "default_value"
        assert config.int_field == 42
        assert config.float_field == 3.14
        assert config.bool_field is True
        assert config.literal_field == "option1"
        assert config.no_help_field == "no_help"

    def test_parse_with_custom_values(self):
        """Test parsing with custom command line arguments."""
        parser = DataclassArgParser(SampleConfig)
        args = [
            "--SampleConfig.string_field",
            "custom_string",
            "--SampleConfig.int_field",
            "100",
            "--SampleConfig.float_field",
            "2.71",
            "--SampleConfig.literal_field",
            "option2",
            "--SampleConfig.no_help_field",
            "custom_no_help",
        ]
        result = parser.parse(args)

        config = result["SampleConfig"]
        assert config.string_field == "custom_string"
        assert config.int_field == 100
        assert config.float_field == 2.71
        # Note: bool_field parsing with argparse is complex, so we skip testing it here
        assert config.literal_field == "option2"
        assert config.no_help_field == "custom_no_help"

    def test_parse_multiple_dataclasses_with_values(self):
        """Test parsing multiple dataclasses with custom values."""
        parser = DataclassArgParser(SampleConfig, AnotherConfig)
        args = [
            "--SampleConfig.string_field",
            "test_string",
            "--SampleConfig.int_field",
            "999",
            "--AnotherConfig.path",
            "/custom/path",
            "--AnotherConfig.count",
            "50",
        ]
        result = parser.parse(args)

        test_config = result["SampleConfig"]
        another_config = result["AnotherConfig"]

        assert test_config.string_field == "test_string"
        assert test_config.int_field == 999
        assert test_config.float_field == 3.14  # Default value

        assert another_config.path == "/custom/path"
        assert another_config.count == 50

    def test_literal_field_validation(self):
        """Test that Literal fields validate choices correctly."""
        parser = DataclassArgParser(SampleConfig)

        # Valid choice should work
        result = parser.parse(["--SampleConfig.literal_field", "option2"])
        assert result["SampleConfig"].literal_field == "option2"

        # Invalid choice should raise SystemExit (argparse error)
        with pytest.raises(SystemExit):
            parser.parse(["--SampleConfig.literal_field", "invalid_option"])

    def test_argument_names_format(self):
        """Test that argument names are formatted as --ClassName.field_name."""
        parser = DataclassArgParser(SampleConfig, AnotherConfig)

        # Check all expected argument names are present
        dest_names = [
            action.dest for action in parser.parser._actions if hasattr(action, "dest")
        ]

        expected_names = [
            "SampleConfig.string_field",
            "SampleConfig.int_field",
            "SampleConfig.float_field",
            "SampleConfig.bool_field",
            "SampleConfig.literal_field",
            "SampleConfig.no_help_field",
            "AnotherConfig.path",
            "AnotherConfig.count",
        ]

        for expected_name in expected_names:
            assert expected_name in dest_names

    def test_help_text_content_accuracy(self):
        """Test that the exact help text content matches metadata."""
        parser = DataclassArgParser(SampleConfig)

        expected_help_mapping = {
            "SampleConfig.string_field": "A string field for testing (default: default_value)",
            "SampleConfig.int_field": "An integer field for testing (default: 42)",
            "SampleConfig.float_field": "A float field for testing (default: 3.14)",
            "SampleConfig.bool_field": "A boolean field for testing (default: True)",
            "SampleConfig.literal_field": "A literal field with choices (default: option1)",
            "SampleConfig.no_help_field": "(default: no_help)",  # Only default for no metadata
        }

        for action in parser.parser._actions:
            if hasattr(action, "dest") and action.dest in expected_help_mapping:
                expected_help = expected_help_mapping[action.dest]
                assert action.help == expected_help, (
                    f"Help text mismatch for {action.dest}"
                )

    def test_config_file_json(self):
        """Test loading configuration from JSON file."""
        config_data = {"SampleConfig": {"string_field": "from_json", "int_field": 999}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(SampleConfig)
            result = parser.parse(["--config", config_path])

            config = result["SampleConfig"]
            assert config.string_field == "from_json"
            assert config.int_field == 999
            assert config.float_field == 3.14  # default value
        finally:
            os.unlink(config_path)

    def test_config_file_override(self):
        """Test that command-line arguments override config file values."""
        config_data = {
            "SampleConfig": {"string_field": "from_config", "int_field": 888}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(SampleConfig)
            result = parser.parse(
                ["--config", config_path, "--SampleConfig.string_field", "from_cmdline"]
            )

            config = result["SampleConfig"]
            assert config.string_field == "from_cmdline"  # overridden by cmdline
            assert config.int_field == 888  # from config file
        finally:
            os.unlink(config_path)

    def test_config_argument_in_help(self):
        """Test that --config argument appears in help output."""
        parser = DataclassArgParser(SampleConfig)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                parser.parser.parse_args(["--help"])
            help_output = mock_stdout.getvalue()

        assert "--config FILE" in help_output
        assert "Path to configuration file (YAML or JSON format)" in help_output

    def test_custom_config_flag(self):
        """Test that a custom config flag name is accepted and used."""
        config_data = {"SampleConfig": {"string_field": "from_json"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Use custom flag name --cfg instead of --config
            parser = DataclassArgParser(SampleConfig, config_flag="--cfg")
            result = parser.parse(["--cfg", config_path])

            config = result["SampleConfig"]
            assert config.string_field == "from_json"
        finally:
            os.unlink(config_path)

    def test_required_fields_missing_cmdline_error(self):
        """Test that parser raises error when required fields are missing from command line."""
        parser = DataclassArgParser(RequiredFieldsConfig)

        # Should raise SystemExit when required fields are missing
        with pytest.raises(SystemExit):
            parser.parse([])

    def test_required_fields_partial_cmdline_error(self):
        """Test that parser raises error when some required fields are missing."""
        parser = DataclassArgParser(RequiredFieldsConfig)

        # Provide only one of the two required fields
        with pytest.raises(SystemExit):
            parser.parse(["--RequiredFieldsConfig.required_string", "test"])

    def test_required_fields_provided_cmdline_success(self):
        """Test that parser succeeds when all required fields are provided via command line."""
        parser = DataclassArgParser(RequiredFieldsConfig)

        result = parser.parse(
            [
                "--RequiredFieldsConfig.required_string",
                "test_string",
                "--RequiredFieldsConfig.required_int",
                "42",
            ]
        )

        config = result["RequiredFieldsConfig"]
        assert config.required_string == "test_string"
        assert config.required_int == 42
        assert config.optional_field == "optional_default"

    def test_required_fields_provided_config_success(self):
        """Test that parser succeeds when all required fields are provided via config file."""
        config_data = {
            "RequiredFieldsConfig": {
                "required_string": "from_config",
                "required_int": 123,
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
            assert config.required_int == 123
            assert config.optional_field == "optional_default"
        finally:
            os.unlink(config_path)

    def test_required_fields_partial_config_error(self):
        """Test that parser raises error when config file doesn't provide all required fields."""
        config_data = {
            "RequiredFieldsConfig": {
                "required_string": "from_config"
                # missing required_int
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(RequiredFieldsConfig)
            with pytest.raises(SystemExit):
                parser.parse(["--config", config_path])
        finally:
            os.unlink(config_path)

    def test_required_fields_mixed_sources_success(self):
        """Test that parser succeeds when required fields come from both config and command line."""
        config_data = {
            "RequiredFieldsConfig": {
                "required_string": "from_config"
                # missing required_int, but will be provided via cmdline
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(RequiredFieldsConfig)
            result = parser.parse(
                ["--config", config_path, "--RequiredFieldsConfig.required_int", "456"]
            )

            config = result["RequiredFieldsConfig"]
            assert config.required_string == "from_config"
            assert config.required_int == 456
            assert config.optional_field == "optional_default"
        finally:
            os.unlink(config_path)

    def test_required_tuple_field_success(self):
        """Test that parser succeeds when all required fields of a tuple are provided."""
        parser = DataclassArgParser(RequiredTupleConfig)

        result = parser.parse(
            [
                "--RequiredTupleConfig.required_tuple",
                "(1, 2, 3)",
            ]
        )

        config = result["RequiredTupleConfig"]
        assert isinstance(config, RequiredTupleConfig)
        assert config.required_tuple == (1, 2, 3)
        assert config.optional_field == "optional_default"

    def test_required_tuple_field_error(self):
        """Test that parser raises error when required fields of a tuple are missing."""
        parser = DataclassArgParser(RequiredTupleConfig)

        with pytest.raises(SystemExit):
            parser.parse(["--RequiredTupleConfig.required_tuple", "(1, 2)"])


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__, "-v"])
