"""Tests for keyword argument support in DataclassArgParser."""
import pytest
from dataclasses import dataclass, field
from typing import Literal
from unittest.mock import patch
from io import StringIO

from dataclass_argparser import DataclassArgParser


@dataclass
class GlobalConfig:
    name: str = field(default="test", metadata={"help": "The name to use"})
    count: int = field(default=5, metadata={"help": "Number of items"})


@dataclass
class AppConfig:
    version: str = field(default="1.0", metadata={"help": "Application version"})
    debug: bool = field(default=False, metadata={"help": "Enable debug mode"})


@dataclass
class RequiredConfig:
    required_field: str = field(metadata={"help": "A required field"})


class TestKeywordArguments:
    """Test suite for keyword argument support."""

    def test_basic_keyword_argument(self):
        """Test basic keyword argument passing."""
        parser = DataclassArgParser(global_config=GlobalConfig)
        result = parser.parse([])
        
        # Check that the keyword name is used as the key
        assert "global_config" in result
        assert isinstance(result["global_config"], GlobalConfig)
        assert result["global_config"].name == "test"
        assert result["global_config"].count == 5

    def test_keyword_argument_with_cli_override(self):
        """Test that CLI arguments work with keyword dataclass arguments."""
        parser = DataclassArgParser(global_config=GlobalConfig)
        result = parser.parse([
            "--global_config.name", "custom_name",
            "--global_config.count", "10"
        ])
        
        assert result["global_config"].name == "custom_name"
        assert result["global_config"].count == 10

    def test_multiple_keyword_arguments(self):
        """Test multiple dataclass keyword arguments."""
        parser = DataclassArgParser(
            global_config=GlobalConfig,
            app_config=AppConfig
        )
        result = parser.parse([])
        
        assert "global_config" in result
        assert "app_config" in result
        assert isinstance(result["global_config"], GlobalConfig)
        assert isinstance(result["app_config"], AppConfig)

    def test_mixed_positional_and_keyword_arguments(self):
        """Test mixing positional and keyword dataclass arguments."""
        parser = DataclassArgParser(
            GlobalConfig,  # positional
            app_config=AppConfig  # keyword
        )
        result = parser.parse([])
        
        # Positional uses class name
        assert "GlobalConfig" in result
        # Keyword uses provided name
        assert "app_config" in result
        assert isinstance(result["GlobalConfig"], GlobalConfig)
        assert isinstance(result["app_config"], AppConfig)

    def test_keyword_with_custom_flags(self):
        """Test keyword arguments with custom flags."""
        parser = DataclassArgParser(
            global_config=GlobalConfig,
            flags=[(
                ('-v', '--verbose'),
                {'action': 'store_true', 'help': 'Enable verbose output'}
            )],
        )
        result = parser.parse(['--verbose'])
        
        assert "global_config" in result
        assert "verbose" in result
        assert result["verbose"] is True

    def test_reserved_keyword_flags_raises_error(self):
        """Test that using 'flags' as a dataclass keyword raises an error."""
        with pytest.raises(ValueError) as exc_info:
            DataclassArgParser(flags=GlobalConfig)
        
        assert "reserved for non-dataclass arguments" in str(exc_info.value)

    def test_reserved_keyword_config_flag_raises_error(self):
        """Test that using 'config_flag' as a dataclass keyword raises an error."""
        with pytest.raises(ValueError) as exc_info:
            DataclassArgParser(config_flag=GlobalConfig)
        
        assert "reserved for specifying the flag for config files" in str(exc_info.value)

    def test_config_keyword_disables_default_config(self):
        """Test that using 'config' as a dataclass keyword disables config file loading."""
        parser = DataclassArgParser(config=GlobalConfig)
        
        # Check that config argument is not in the parser
        # The config flag should not be added
        dest_names = [action.dest for action in parser.parser._actions if hasattr(action, "dest")]
        # The default 'config' dest should not exist for config file loading
        # Since 'config' is disabled, we shouldn't see it as a file loading option
        
        # Instead, we should have 'config.name' and 'config.count' as dataclass fields
        assert "config.name" in dest_names
        assert "config.count" in dest_names

    def test_config_keyword_as_dataclass_argument_name(self):
        """Test using 'config' as a dataclass keyword argument name."""
        parser = DataclassArgParser(config=GlobalConfig)
        result = parser.parse([
            "--config.name", "my_config",
            "--config.count", "7"
        ])
        
        assert "config" in result
        assert isinstance(result["config"], GlobalConfig)
        assert result["config"].name == "my_config"
        assert result["config"].count == 7

    def test_help_with_keyword_arguments(self):
        """Test that help text uses the keyword argument name."""
        parser = DataclassArgParser(my_config=GlobalConfig)
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                parser.parser.parse_args(["--help"])
            help_output = mock_stdout.getvalue()
        
        # Check that help uses the keyword name
        assert "--my_config.name" in help_output
        assert "--my_config.count" in help_output

    def test_invalid_dataclass_type_raises_error(self):
        """Test that passing a non-dataclass as keyword argument raises an error."""
        class NotADataclass:
            pass
        
        with pytest.raises(ValueError) as exc_info:
            DataclassArgParser(my_config=NotADataclass)
        
        assert "is not a dataclass type" in str(exc_info.value)

    def test_keyword_with_required_fields(self):
        """Test keyword arguments with required fields."""
        parser = DataclassArgParser(my_config=RequiredConfig)
        
        # Should raise error when required field is missing
        with pytest.raises(SystemExit):
            parser.parse([])
        
        # Should succeed when required field is provided
        result = parser.parse(["--my_config.required_field", "value"])
        assert result["my_config"].required_field == "value"

    def test_example_from_issue(self):
        """Test the exact example from the issue."""
        @dataclass
        class GlobalConfig:
            name: str = field(default="test", metadata={"help": "The name to use"})

        parser = DataclassArgParser(
            global_config=GlobalConfig,
            flags=[(
                ('-v', '--verbose'),
                {'action': 'store_true', 'help': 'Enable verbose output'}
            )],
            config_flag=('-c', '--config'),
        )
        res = parser.parse([])

        global_config: GlobalConfig = res["global_config"]
        assert isinstance(global_config, GlobalConfig)

        verbose: bool = res.get("verbose", False)
        assert isinstance(verbose, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
