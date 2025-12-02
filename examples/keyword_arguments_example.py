#!/usr/bin/env python3
"""
Example demonstrating keyword argument support in DataclassArgParser.

This example shows how to use keyword arguments to specify custom names for
dataclass arguments in the result dictionary, and demonstrates the reserved
keyword handling for 'flags', 'config', and 'config_flag'.
"""

from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser


@dataclass
class GlobalConfig:
    """Global configuration settings."""
    name: str = field(default="example", metadata={"help": "Application name"})
    version: str = field(default="1.0", metadata={"help": "Application version"})
    debug: bool = field(default=False, metadata={"help": "Enable debug mode"})


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = field(default="localhost", metadata={"help": "Database host"})
    port: int = field(default=5432, metadata={"help": "Database port"})


def example_basic_keyword_arguments():
    """Example: Basic keyword argument usage."""
    print("=" * 60)
    print("Example 1: Basic Keyword Arguments")
    print("=" * 60)
    
    # Use keyword arguments to specify custom names
    parser = DataclassArgParser(
        global_config=GlobalConfig,
        db_config=DatabaseConfig
    )
    
    # Parse with defaults
    result = parser.parse([])
    
    # Access using the custom names
    print(f"Global Config Name: {result['global_config'].name}")
    print(f"Global Config Version: {result['global_config'].version}")
    print(f"Database Host: {result['db_config'].host}")
    print(f"Database Port: {result['db_config'].port}")
    print()


def example_mixed_arguments():
    """Example: Mixing positional and keyword arguments."""
    print("=" * 60)
    print("Example 2: Mixed Positional and Keyword Arguments")
    print("=" * 60)
    
    # Mix positional and keyword arguments
    parser = DataclassArgParser(
        GlobalConfig,  # positional - uses class name 'GlobalConfig'
        db_config=DatabaseConfig  # keyword - uses custom name 'db_config'
    )
    
    result = parser.parse([])
    
    # Positional uses class name
    print(f"GlobalConfig (positional): {result['GlobalConfig'].name}")
    # Keyword uses custom name
    print(f"db_config (keyword): {result['db_config'].host}")
    print()


def example_with_custom_flags():
    """Example: Keyword arguments with custom flags."""
    print("=" * 60)
    print("Example 3: Keyword Arguments with Custom Flags")
    print("=" * 60)
    
    parser = DataclassArgParser(
        global_config=GlobalConfig,
        flags=[
            (('-v', '--verbose'), {'action': 'store_true', 'help': 'Enable verbose output'}),
            (('--dry-run',), {'action': 'store_true', 'help': 'Dry run mode'}),
        ],
        config_flag=('-c', '--config'),  # Custom config flag
    )
    
    result = parser.parse(['--verbose'])
    
    print(f"Global Config: {result['global_config'].name}")
    print(f"Verbose: {result.get('verbose', False)}")
    print(f"Dry Run: {result.get('dry_run', False)}")
    print()


def example_cli_override():
    """Example: CLI override of keyword arguments."""
    print("=" * 60)
    print("Example 4: CLI Override")
    print("=" * 60)
    
    parser = DataclassArgParser(app_config=GlobalConfig)
    
    result = parser.parse([
        '--app_config.name', 'MyApp',
        '--app_config.version', '2.0',
        '--app_config.debug', 'true'
    ])
    
    print(f"Name: {result['app_config'].name}")
    print(f"Version: {result['app_config'].version}")
    print(f"Debug: {result['app_config'].debug}")
    print()


def example_config_as_dataclass_argument():
    """Example: Using 'config' as a dataclass argument name."""
    print("=" * 60)
    print("Example 5: Using 'config' as Dataclass Argument Name")
    print("=" * 60)
    
    # When 'config' is used as a keyword argument, config file loading is disabled
    parser = DataclassArgParser(config=GlobalConfig)
    
    result = parser.parse([
        '--config.name', 'ConfigExample',
        '--config.version', '3.0'
    ])
    
    print(f"Config Name: {result['config'].name}")
    print(f"Config Version: {result['config'].version}")
    print("Note: Config file loading is disabled when 'config' is used as a dataclass argument name")
    print()


def example_reserved_keywords():
    """Example: Demonstrating reserved keyword errors."""
    print("=" * 60)
    print("Example 6: Reserved Keyword Errors")
    print("=" * 60)
    
    # Try to use 'flags' as a keyword argument (should fail)
    try:
        parser = DataclassArgParser(flags=GlobalConfig)
        print("ERROR: Should have raised ValueError for 'flags'")
    except ValueError as e:
        print(f"✓ Expected error for 'flags': {e}")
    
    # Try to use 'config_flag' as a keyword argument (should fail)
    try:
        parser = DataclassArgParser(config_flag=GlobalConfig)
        print("ERROR: Should have raised ValueError for 'config_flag'")
    except ValueError as e:
        print(f"✓ Expected error for 'config_flag': {e}")
    
    print()


if __name__ == "__main__":
    example_basic_keyword_arguments()
    example_mixed_arguments()
    example_with_custom_flags()
    example_cli_override()
    example_config_as_dataclass_argument()
    example_reserved_keywords()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
