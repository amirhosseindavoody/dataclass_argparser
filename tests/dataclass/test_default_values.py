#!/usr/bin/env python3
"""
Tests for DataclassArgParser default value display functionality.

This module tests that default values are properly displayed in help text
and command-line argument descriptions.
"""

import io
import sys
from dataclasses import dataclass, field
from typing import Literal

from dataclass_argparser import DataclassArgParser


@dataclass
class ConfigWithDefaults:
    """Configuration with various default values for testing."""

    # Field without default (required) - must come first
    required_field: str = field(metadata={"help": "This field is required"})

    # Fields with defaults
    name: str = field(default="default_name", metadata={"help": "The name to use"})
    count: int = field(default=10, metadata={"help": "Number of items"})
    threshold: float = field(default=0.75, metadata={"help": "Threshold value"})
    enabled: bool = field(default=True, metadata={"help": "Enable feature"})
    mode: Literal["fast", "slow"] = field(
        default="fast", metadata={"help": "Processing mode"}
    )

    # Field without help text but with default
    debug: bool = field(default=False)


@dataclass
class ConfigWithFactory:
    """Configuration using default_factory for testing."""

    items: list = field(default_factory=list, metadata={"help": "List of items"})
    settings: dict = field(
        default_factory=dict, metadata={"help": "Settings dictionary"}
    )


class TestDefaultValues:
    """Test suite for default value display functionality."""

    def test_help_text_includes_defaults(self):
        """Test that help text includes default values."""
        parser = DataclassArgParser(ConfigWithDefaults)

        # Capture help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            # This will cause SystemExit, but we'll catch the help output
            parser.parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout

        help_text = captured_output.getvalue()

        # Check that default values are included in help text
        assert "(default: default_name)" in help_text
        assert "(default: 10)" in help_text
        assert "(default: 0.75)" in help_text
        assert "(default: True)" in help_text
        assert "(default: fast)" in help_text
        assert "(default: False)" in help_text

        # Required field should not have default value shown
        assert "This field is required" in help_text
        assert "required_field" in help_text
        # Make sure no default is shown for required field
        required_line_found = False
        for line in help_text.split("\n"):
            if "ConfigWithDefaults.required_field" in line:
                required_line_found = True
                # The help should be on the next line
                break

        # Find the help text line for required_field
        lines = help_text.split("\n")
        for i, line in enumerate(lines):
            if "ConfigWithDefaults.required_field" in line and i + 1 < len(lines):
                help_line = lines[i + 1].strip()
                if "This field is required" in help_line:
                    assert "(default:" not in help_line
                    required_line_found = True
                    break
        assert required_line_found

    def test_help_text_with_existing_description(self):
        """Test that default values are appended to existing help text."""
        parser = DataclassArgParser(ConfigWithDefaults)

        # Capture help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            parser.parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout

        help_text = captured_output.getvalue()

        # Check that original help text is preserved and default is appended
        assert "The name to use (default: default_name)" in help_text
        assert "Number of items (default: 10)" in help_text
        assert "Threshold value (default: 0.75)" in help_text
        assert "Enable feature (default: True)" in help_text
        assert "Processing mode (default: fast)" in help_text

    def test_help_text_without_description(self):
        """Test that fields without help text still show defaults."""
        parser = DataclassArgParser(ConfigWithDefaults)

        # Capture help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            parser.parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout

        help_text = captured_output.getvalue()

        # Field without help metadata should still show default
        assert "ConfigWithDefaults.debug" in help_text
        assert "(default: False)" in help_text

    def test_default_factory_values(self):
        """Test that default_factory values are properly displayed."""
        parser = DataclassArgParser(ConfigWithFactory)

        # Capture help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            parser.parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout

        help_text = captured_output.getvalue()

        # Check that default_factory values are shown
        assert "(default: [])" in help_text
        assert "(default: {})" in help_text
        assert "List of items (default: [])" in help_text
        assert "Settings dictionary (default: {})" in help_text

    def test_literal_type_with_default(self):
        """Test that Literal types with defaults show the default value."""
        parser = DataclassArgParser(ConfigWithDefaults)

        # Capture help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            parser.parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout

        help_text = captured_output.getvalue()

        # Check that Literal field shows both choices and default
        assert "Processing mode (default: fast)" in help_text
        assert "{fast,slow}" in help_text

    def test_parsing_still_works(self):
        """Test that adding default values to help doesn't break parsing."""
        parser = DataclassArgParser(ConfigWithDefaults)

        # Test with minimal required arguments
        result = parser.parse(["--ConfigWithDefaults.required_field", "test_value"])
        config = result["ConfigWithDefaults"]

        # Check that defaults are still applied
        assert config.name == "default_name"
        assert config.count == 10
        assert config.threshold == 0.75
        assert config.enabled is True
        assert config.mode == "fast"
        assert config.debug is False
        assert config.required_field == "test_value"

        # Test overriding defaults
        result = parser.parse(
            [
                "--ConfigWithDefaults.required_field",
                "test_value",
                "--ConfigWithDefaults.name",
                "custom_name",
                "--ConfigWithDefaults.count",
                "5",
                "--ConfigWithDefaults.mode",
                "slow",
            ]
        )
        config = result["ConfigWithDefaults"]

        assert config.name == "custom_name"
        assert config.count == 5
        assert config.mode == "slow"
        assert config.required_field == "test_value"

    def test_multiple_dataclasses_with_defaults(self):
        """Test that default values work correctly with multiple dataclasses."""

        @dataclass
        class FirstConfig:
            value1: str = field(
                default="first_default", metadata={"help": "First value"}
            )

        @dataclass
        class SecondConfig:
            value2: int = field(default=42, metadata={"help": "Second value"})

        parser = DataclassArgParser(FirstConfig, SecondConfig)

        # Capture help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            parser.parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout

        help_text = captured_output.getvalue()

        # Check that both dataclasses show their defaults
        assert "First value (default: first_default)" in help_text
        assert "Second value (default: 42)" in help_text

        # Test parsing works
        result = parser.parse([])
        assert result["FirstConfig"].value1 == "first_default"
        assert result["SecondConfig"].value2 == 42
