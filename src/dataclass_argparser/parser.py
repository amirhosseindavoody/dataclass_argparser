"""
DataclassArgParser - A utility for creating command-line argument parsers from dataclasses.

This module provides a simple way to automatically generate argparse-based command-line
interfaces from Python dataclasses, extracting help text from field metadata and
providing type-based metavars for better user experience. It also supports loading
configuration from YAML or JSON files.
"""

import argparse
import ast
import dataclasses
import json
import os
import typing
from typing import Any, Dict, Literal, Type

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class DataclassArgParser:
    """
    A command-line argument parser that automatically generates arguments from dataclasses.

    This class takes one or more dataclass types and creates an argparse.ArgumentParser
    with arguments corresponding to each field in the dataclasses. Help text is extracted
    from the 'help' key in field metadata, and metavars are generated based on field types.

    Supports loading configuration from YAML or JSON files via the --config argument.

    Example:
        @dataclass
        class Config:
            name: str = field(default="test", metadata={"help": "The name to use"})
            count: int = field(default=5, metadata={"help": "Number of items"})

        parser = DataclassArgParser(Config)
        result = parser.parse()
        config = result['Config']

        # Or load from config file:
        # python script.py --config config.yaml
    """

    def __init__(self, *dataclass_types: Type[Any]):
        """
        Initialize the parser with one or more dataclass types.

        Args:
            *dataclass_types: One or more dataclass types to generate arguments from
        """
        self.dataclass_types = dataclass_types
        self.parser = argparse.ArgumentParser()
        self._add_config_argument()
        self._add_dataclass_arguments()

    def _add_config_argument(self):
        """Add the --config argument for loading configuration from files."""
        self.parser.add_argument(
            "--config",
            type=str,
            metavar="FILE",
            help="Path to configuration file (YAML or JSON format)",
        )

    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML or JSON file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Dictionary containing the configuration data

        Raises:
            FileNotFoundError: If the config file doesn't exist
            ValueError: If the file format is not supported or invalid
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        file_ext = os.path.splitext(config_path)[1].lower()

        with open(config_path, "r") as f:
            if file_ext in [".yaml", ".yml"]:
                if not HAS_YAML:
                    raise ValueError(
                        "YAML support not available. Please install PyYAML: pip install PyYAML"
                    )
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML file: {e}")
            elif file_ext == ".json":
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON file: {e}")
            else:
                raise ValueError(
                    f"Unsupported file format: {file_ext}. "
                    "Supported formats are: .yaml, .yml, .json"
                )

    def _add_dataclass_arguments(self):
        """Add arguments to the parser based on dataclass fields."""

        def tuple_type_factory(tuple_type):
            # Returns a function that parses a string into a tuple of the correct type and length
            def parse_tuple(s):
                # Accepts formats like "(1, 2, 3)" or "1,2,3"
                try:
                    if s.startswith("(") and s.endswith(")"):
                        s = s[1:-1]
                    items = [item.strip() for item in s.split(",") if item.strip()]
                    expected_types = tuple_type.__args__
                    if len(items) != len(expected_types):
                        raise argparse.ArgumentTypeError(
                            f"Expected {len(expected_types)} values, got {len(items)}"
                        )
                    result = []
                    for item, typ in zip(items, expected_types):
                        # Support int, float, str, etc.
                        try:
                            value = (
                                ast.literal_eval(item)
                                if typ in (int, float, bool)
                                else item
                            )
                            value = typ(value)
                        except Exception:
                            raise argparse.ArgumentTypeError(
                                f"Could not convert '{item}' to {typ.__name__}"
                            )
                        result.append(value)
                    return tuple(result)
                except Exception as e:
                    raise argparse.ArgumentTypeError(f"Invalid tuple value: {s} ({e})")

            return parse_tuple

        def list_type_factory(list_type):
            # Returns a function that parses a string into a list of the correct type
            def parse_list(s):
                # Accepts formats like "[1, 2, 3]" or "1,2,3"
                try:
                    if s.startswith("[") and s.endswith("]"):
                        s = s[1:-1]
                    items = [item.strip() for item in s.split(",") if item.strip()]
                    # Get the type of the list elements
                    elem_type = (
                        list_type.__args__[0]
                        if hasattr(list_type, "__args__") and list_type.__args__
                        else str
                    )
                    result = []
                    for item in items:
                        try:
                            value = (
                                ast.literal_eval(item)
                                if elem_type in (int, float, bool)
                                else item
                            )
                            value = elem_type(value)
                        except Exception:
                            raise argparse.ArgumentTypeError(
                                f"Could not convert '{item}' to {elem_type.__name__}"
                            )
                        result.append(value)
                    return result
                except Exception as e:
                    raise argparse.ArgumentTypeError(f"Invalid list value: {s} ({e})")

            return parse_list

        for cls in self.dataclass_types:
            for field in dataclasses.fields(cls):
                arg_name = f"--{cls.__name__}.{field.name}"
                arg_type = field.type if field.type is not dataclasses.MISSING else str
                # Get field help text from metadata
                description = field.metadata.get("help", "")

                # Determine default value for help text
                default_value = None
                if field.default is not dataclasses.MISSING:
                    default_value = field.default
                elif field.default_factory is not dataclasses.MISSING:
                    default_value = field.default_factory()

                # Add default value to help text if available
                if default_value is not None:
                    if description:
                        description = f"{description} (default: {default_value})"
                    else:
                        description = f"(default: {default_value})"

                # Handle Literal types
                if hasattr(arg_type, "__origin__") and arg_type.__origin__ is Literal:
                    choices = arg_type.__args__
                    # Use the literal choices as metavar
                    metavar = "{" + ",".join(str(choice) for choice in choices) + "}"
                    self.parser.add_argument(
                        arg_name,
                        type=str,
                        choices=choices,
                        help=description,
                        metavar=metavar,
                    )
                # Handle tuple types
                elif hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
                    tuple,
                    tuple,
                    typing.Tuple,
                ):
                    metavar = "TUPLE"
                    self.parser.add_argument(
                        arg_name,
                        type=tuple_type_factory(arg_type),
                        help=description,
                        metavar=metavar,
                    )
                # Handle list types
                elif hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
                    list,
                    typing.List,
                ):
                    metavar = "LIST"
                    self.parser.add_argument(
                        arg_name,
                        type=list_type_factory(arg_type),
                        help=description,
                        metavar=metavar,
                    )
                else:
                    # Create type-based metavar
                    if arg_type is int:
                        metavar = "INT"
                    elif arg_type is float:
                        metavar = "FLOAT"
                    elif arg_type is str:
                        metavar = "STRING"
                    elif arg_type is bool:
                        metavar = "BOOL"
                    else:
                        # For other types, use the type name in uppercase
                        metavar = arg_type.__name__.upper()

                    self.parser.add_argument(
                        arg_name,
                        type=arg_type,
                        help=description,
                        metavar=metavar,
                    )

    def parse(self, args=None) -> Dict[str, Any]:
        """
        Parse command-line arguments and return dataclass instances.

        Args:
            args: Optional list of arguments to parse. If None, uses sys.argv.

        Returns:
            Dict mapping dataclass names to their instantiated objects with
            parsed values.

        Raises:
            SystemExit: If required fields (those without default values) are not
            provided either as command-line arguments or in the config file.
        """
        parsed_args = vars(self.parser.parse_args(args))

        # Check if config file is provided
        config_data = {}
        if parsed_args.get("config"):
            config_data = self._load_config_file(parsed_args["config"])

        result = {}
        for cls in self.dataclass_types:
            values = {}

            # First, use default values from dataclass
            for field in dataclasses.fields(cls):
                if field.default is not dataclasses.MISSING:
                    values[field.name] = field.default
                elif field.default_factory is not dataclasses.MISSING:
                    values[field.name] = field.default_factory()

            # Then, override with config file values if present
            cls_config = config_data.get(cls.__name__, {})
            for field_name, field_value in cls_config.items():
                if any(f.name == field_name for f in dataclasses.fields(cls)):
                    values[field_name] = field_value

            # Finally, override with command-line arguments (highest priority)
            for field in dataclasses.fields(cls):
                key = f"{cls.__name__}.{field.name}"
                if key in parsed_args and parsed_args[key] is not None:
                    values[field.name] = parsed_args[key]

            # Validate that all required fields (without defaults) have values
            missing_fields = []
            for field in dataclasses.fields(cls):
                if (
                    field.default is dataclasses.MISSING
                    and field.default_factory is dataclasses.MISSING
                    and field.name not in values
                ):
                    missing_fields.append(f"--{cls.__name__}.{field.name}")

            if missing_fields:
                error_msg = (
                    f"Missing required arguments for {cls.__name__}: {', '.join(missing_fields)}. "
                    f"These must be provided either as command-line arguments or in the config file."
                )
                self.parser.error(error_msg)

            result[cls.__name__] = cls(**values)
        return result
