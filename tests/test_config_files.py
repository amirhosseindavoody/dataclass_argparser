#!/usr/bin/env python3
"""
Tests for DataclassArgParser config file functionality.

This module tests JSON and YAML config file loading, as well as
command-line override functionality.
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
class SampleConfig:
    """Sample configuration for testing."""

    name: str = field(default="default_name", metadata={"help": "The name"})
    count: int = field(default=5, metadata={"help": "Number of items"})
    threshold: float = field(default=0.5, metadata={"help": "Threshold value"})
    mode: Literal["fast", "slow"] = field(default="fast", metadata={"help": "Mode"})


@dataclass
class SecondConfig:
    """Second configuration for testing multiple dataclasses."""

    path: str = field(default="/tmp", metadata={"help": "Path to directory"})
    enabled: bool = field(default=True, metadata={"help": "Enable feature"})


class TestConfigFiles:
    """Test suite for config file functionality."""

    def test_json_config(self):
        """Test loading from JSON config file."""
        config_data = {
            "SampleConfig": {"name": "json_test", "count": 10, "threshold": 0.8},
            "SecondConfig": {"path": "/home/user", "enabled": False},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(SampleConfig, SecondConfig)
            result = parser.parse(["--config", config_path])

            sample_config = result["SampleConfig"]
            second_config = result["SecondConfig"]

            assert sample_config.name == "json_test"
            assert sample_config.count == 10
            assert sample_config.threshold == 0.8
            assert sample_config.mode == "fast"  # default value

            assert second_config.path == "/home/user"
            assert not second_config.enabled
        finally:
            os.unlink(config_path)

    def test_yaml_config(self):
        """Test loading from YAML config file."""
        config_content = textwrap.dedent("""
            SampleConfig:
              name: yaml_test
              count: 15
              mode: slow

            SecondConfig:
              path: /var/log
            """).strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = DataclassArgParser(SampleConfig, SecondConfig)
            result = parser.parse(["--config", config_path])

            sample_config = result["SampleConfig"]
            second_config = result["SecondConfig"]

            assert sample_config.name == "yaml_test"
            assert sample_config.count == 15
            assert sample_config.threshold == 0.5  # default value
            assert sample_config.mode == "slow"

            assert second_config.path == "/var/log"
            assert second_config.enabled  # default value
        finally:
            os.unlink(config_path)

    def test_config_override(self):
        """Test that command-line args override config file values."""
        config_data = {"SampleConfig": {"name": "config_name", "count": 99}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(SampleConfig)
            result = parser.parse(
                [
                    "--config",
                    config_path,
                    "--SampleConfig.name",
                    "cmdline_name",
                    "--SampleConfig.threshold",
                    "0.9",
                ]
            )

            sample_config = result["SampleConfig"]

            assert sample_config.name == "cmdline_name"  # overridden by cmdline
            assert sample_config.count == 99  # from config file
            assert sample_config.threshold == 0.9  # from cmdline
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
