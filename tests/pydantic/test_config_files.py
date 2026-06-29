#!/usr/bin/env python3
"""
Tests for DataclassArgParser config file functionality with Pydantic models.

Mirrors ../test_config_files.py for Pydantic BaseModel definitions.
"""

import json
import os
import tempfile
import textwrap
from typing import Literal

from pydantic import BaseModel, Field

from dataclass_argparser import DataclassArgParser


class SampleConfig(BaseModel):
    """Sample configuration for testing."""

    name: str = Field(default="default_name", description="The name")
    count: int = Field(default=5, description="Number of items")
    threshold: float = Field(default=0.5, description="Threshold value")
    mode: Literal["fast", "slow"] = Field(default="fast", description="Mode")


class SecondConfig(BaseModel):
    """Second configuration for testing multiple models."""

    path: str = Field(default="/tmp", description="Path to directory")
    enabled: bool = Field(default=True, description="Enable feature")


class TupleFieldConfig(BaseModel):
    """Configuration with tuple fields for testing config file parsing."""

    coords: tuple[int, int, int] = Field(default=(0, 0, 0), description="Coordinates")
    pair: tuple[str, float] = Field(
        default=("default", 1.0), description="String and float pair"
    )


class TestConfigFiles:
    """Test suite for config file functionality with Pydantic models."""

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
            assert sample_config.mode == "fast"

            assert second_config.path == "/home/user"
            assert not second_config.enabled
        finally:
            os.unlink(config_path)

    def test_cli_override_config(self):
        """Test that CLI values override config file values."""
        config_data = {"SampleConfig": {"name": "from_config", "count": 100}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(SampleConfig)
            result = parser.parse(
                ["--config", config_path, "--SampleConfig.count", "200"]
            )
            config = result["SampleConfig"]
            assert config.name == "from_config"
            assert config.count == 200
        finally:
            os.unlink(config_path)

    def test_yaml_config(self):
        """Test loading from YAML config file."""
        config_content = textwrap.dedent("""
            SampleConfig:
              name: yaml_test
              count: 20
              threshold: 0.9
              mode: slow
            """).strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            parser = DataclassArgParser(SampleConfig)
            result = parser.parse(["--config", config_path])
            config = result["SampleConfig"]
            assert config.name == "yaml_test"
            assert config.count == 20
            assert config.threshold == 0.9
            assert config.mode == "slow"
        finally:
            os.unlink(config_path)

    def test_tuple_from_config(self):
        """Test tuple fields loaded from config file."""
        config_data = {
            "TupleFieldConfig": {
                "coords": [1, 2, 3],
                "pair": ["hello", 2.5],
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            parser = DataclassArgParser(TupleFieldConfig)
            result = parser.parse(["--config", config_path])
            config = result["TupleFieldConfig"]
            assert config.coords == (1, 2, 3)
            assert config.pair == ("hello", 2.5)
        finally:
            os.unlink(config_path)
