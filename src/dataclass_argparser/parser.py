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
from functools import lru_cache
from typing import Any, Literal, Type, Union, Optional

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# Helper functions for type checking with caching
@lru_cache(maxsize=256)
def _get_type_origin(type_hint: Any) -> Any:
    """Get the origin of a type hint with caching."""
    return getattr(type_hint, "__origin__", None)


@lru_cache(maxsize=256)
def _get_type_args(type_hint: Any) -> tuple:
    """Get the args of a type hint with caching."""
    return getattr(type_hint, "__args__", ())


@lru_cache(maxsize=256)
def _is_literal_type(type_hint: Any) -> bool:
    """Check if a type is a Literal type with caching."""
    origin = _get_type_origin(type_hint)
    return origin is Literal


@lru_cache(maxsize=256)
def _is_tuple_type(type_hint: Any) -> bool:
    """Check if a type is a tuple type with caching."""
    origin = _get_type_origin(type_hint)
    return origin in (tuple, typing.Tuple)


@lru_cache(maxsize=256)
def _is_list_type(type_hint: Any) -> bool:
    """Check if a type is a list type with caching."""
    origin = _get_type_origin(type_hint)
    return origin in (list, typing.List)


@lru_cache(maxsize=256)
def _is_dict_type(type_hint: Any) -> bool:
    """Check if a type is a dict type with caching."""
    origin = _get_type_origin(type_hint)
    return origin in (dict, typing.Dict)


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

    def __init__(
        self,
        *dataclass_types: Type[Any],
        flags: Optional[list] = None,
        config_flag: Union[str, list[str], tuple[str, ...]] = "--config",
    ) -> None:
        """
        Initialize the DataclassArgParser with one or more dataclass types.

        Args:
            *dataclass_types: One or more dataclass types to generate arguments from.
        """
        self.dataclass_types: tuple[Type[Any], ...] = dataclass_types
        self.parser: argparse.ArgumentParser = argparse.ArgumentParser()
        # store the requested option string(s) for the config file flag so it
        # can be customized by the caller (default: "--config").
        self._requested_config_flag = config_flag
        # actual dest name for the config argument (populated when added)
        self._config_dest: str = "config"
        # Cache for dataclass fields to avoid repeated calls
        self._field_cache: dict[Type[Any], tuple] = {}
        self._add_config_argument(self._requested_config_flag)

        # Add any individual flags provided by the caller before dataclass args
        # Each item in `flags` may be one of:
        # - (name, kwargs) where name is a str or a tuple/list of option strings and kwargs is a dict
        # - {'names': name_or_list, 'kwargs': {...}}
        if flags:
            for item in flags:
                if isinstance(item, dict) and "names" in item:
                    names = item["names"]
                    kwargs = item.get("kwargs", {})
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    names, kwargs = item
                else:
                    raise ValueError(
                        "Each flag must be (names, kwargs) tuple or {'names': ..., 'kwargs': ...} dict"
                    )

                # Normalize single name to tuple for add_argument
                if isinstance(names, str):
                    names = (names,)

                self.add_flag(*names, **(kwargs or {}))

        self._add_dataclass_arguments()

    def add_flag(self, *names: str, **kwargs: Any) -> None:
        """
        Add an individual command-line flag/argument to the parser.

        Example:
            parser.add_flag('--verbose', '-v', action='store_true', help='Enable verbose')

        Args:
            *names: One or more option strings (e.g. '--foo' or '-f', '--foo').
            **kwargs: Keyword arguments passed through to argparse.ArgumentParser.add_argument.
        """
        # Check for name conflicts with existing option strings
        for n in names:
            if n in self.parser._option_string_actions:
                raise ValueError(f"Flag name conflict: {n}")

        # Simply forward to the underlying argparse parser. This provides a
        # convenient way to mix manually-declared flags with auto-generated
        # dataclass arguments.
        self.parser.add_argument(*names, **kwargs)

    def _add_config_argument(
        self, config_flag: Union[str, list[str], tuple[str, ...]] = "--config"
    ) -> None:
        """
        Add the config argument for loading configuration from YAML or JSON files.

        The caller may provide either a single option string (e.g. "--cfg") or a
        list/tuple of option strings (e.g. ["-c", "--cfg"]). The destination
        name created by argparse is recorded in `self._config_dest` so the rest
        of the code can look up the parsed value regardless of the option name.
        """
        # Normalize to sequence of option strings
        if isinstance(config_flag, str):
            names = (config_flag,)
        else:
            names = tuple(config_flag)

        self.parser.add_argument(
            *names,
            type=str,
            metavar="FILE",
            help="Path to configuration file (YAML or JSON format)",
        )

        # Record the dest name created by argparse for the config argument.
        # The most-recently-added action corresponds to this argument.
        if self.parser._actions:
            self._config_dest = self.parser._actions[-1].dest

    def _get_fields(self, cls: Type[Any]) -> tuple:
        """Get dataclass fields with caching to avoid repeated lookups."""
        if cls not in self._field_cache:
            self._field_cache[cls] = dataclasses.fields(cls)
        return self._field_cache[cls]

    def _load_config_file(self, config_path: str) -> dict[str, Any]:
        """
        Load configuration from a YAML or JSON file.
        """
        """
        Load configuration from a YAML or JSON file.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            dict[str, Any]: Dictionary containing the configuration data.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            ValueError: If the file format is not supported or invalid.
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

    def _tuple_type_factory(self, tuple_type: Any) -> typing.Callable[[str], tuple]:
        """
        Return a function that parses a string into a tuple of the correct type and length.

        Args:
            tuple_type: The typing.Tuple type to parse.

        Returns:
            Callable[[str], tuple]: A function that parses a string into a tuple.
        """
        # Cache type args to avoid repeated lookups
        expected_types = _get_type_args(tuple_type)

        def parse_tuple(s):
            try:
                if s.startswith("(") and s.endswith(")"):
                    s = s[1:-1]
                items = [item.strip() for item in s.split(",") if item.strip()]
                if len(items) != len(expected_types):
                    raise argparse.ArgumentTypeError(
                        f"Expected {len(expected_types)} values, got {len(items)}"
                    )
                result = []
                for item, typ in zip(items, expected_types):
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

    def _list_type_factory(self, list_type: Any) -> typing.Callable[[str], list]:
        """
        Return a function that parses a string into a list of the correct type.

        Args:
            list_type: The typing.List type to parse.

        Returns:
            Callable[[str], list]: A function that parses a string into a list.
        """
        # Cache type args to avoid repeated lookups
        type_args = _get_type_args(list_type)
        elem_type = type_args[0] if type_args else str

        def parse_list(s):
            try:
                if s.startswith("[") and s.endswith("]"):
                    s = s[1:-1]
                items = [item.strip() for item in s.split(",") if item.strip()]
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

    def _dict_type_factory(self, dict_type: Any) -> typing.Callable[[str], dict]:
        """
        Return a function that parses a string into a dict of the correct type.

        Args:
            dict_type: The typing.Dict type to parse.

        Returns:
            Callable[[str], dict]: A function that parses a string into a dict.
        """
        # Cache type args to avoid repeated lookups
        type_args = _get_type_args(dict_type)
        key_type = type_args[0] if type_args and len(type_args) >= 1 else str
        value_type = type_args[1] if type_args and len(type_args) >= 2 else str

        def parse_dict(s):
            try:
                # Handle empty string as empty dict
                if not s.strip():
                    return {}

                # Try JSON format first
                if s.strip().startswith("{") and s.strip().endswith("}"):
                    try:
                        result = json.loads(s)
                        if not isinstance(result, dict):
                            raise argparse.ArgumentTypeError(
                                f"JSON value must be an object/dict, got {type(result).__name__}"
                            )

                        # Convert keys and values to the expected types
                        typed_result = {}
                        for k, v in result.items():
                            # Convert key
                            try:
                                if key_type is not str:
                                    k = key_type(k)
                            except Exception:
                                raise argparse.ArgumentTypeError(
                                    f"Could not convert key '{k}' to {key_type.__name__}"
                                )

                            # Convert value
                            try:
                                if value_type in (int, float, bool):
                                    # For basic types, the JSON parsing should handle this correctly
                                    if not isinstance(v, value_type):
                                        v = value_type(v)
                                elif value_type is not str:
                                    v = value_type(v)
                            except Exception:
                                raise argparse.ArgumentTypeError(
                                    f"Could not convert value '{v}' to {value_type.__name__}"
                                )

                            typed_result[k] = v

                        return typed_result
                    except json.JSONDecodeError as e:
                        raise argparse.ArgumentTypeError(f"Invalid JSON format: {e}")

                # Try key=value,key2=value2 format
                else:
                    result = {}
                    pairs = [pair.strip() for pair in s.split(",") if pair.strip()]
                    for pair in pairs:
                        if "=" not in pair:
                            raise argparse.ArgumentTypeError(
                                f"Invalid key=value format: '{pair}' (missing '=')"
                            )

                        key, value = pair.split("=", 1)  # Split only on first =
                        key = key.strip()
                        value = value.strip()

                        # Convert key
                        try:
                            if key_type is not str:
                                key = key_type(key)
                        except Exception:
                            raise argparse.ArgumentTypeError(
                                f"Could not convert key '{key}' to {key_type.__name__}"
                            )

                        # Convert value
                        try:
                            if value_type in (int, float, bool):
                                value = (
                                    ast.literal_eval(value)
                                    if value_type in (int, float, bool)
                                    else value
                                )
                                value = value_type(value)
                            elif value_type is not str:
                                value = value_type(value)
                        except Exception:
                            raise argparse.ArgumentTypeError(
                                f"Could not convert value '{value}' to {value_type.__name__}"
                            )

                        result[key] = value

                    return result

            except Exception as e:
                if isinstance(e, argparse.ArgumentTypeError):
                    raise
                raise argparse.ArgumentTypeError(f"Invalid dict value: {s} ({e})")

        return parse_dict

    def _add_dataclass_arguments(self) -> None:
        """
        Add arguments to the parser based on dataclass fields, including nested dataclasses.
        Handles Literal, tuple, list, dict, and nested dataclass types.
        """

        def add_fields(cls, prefix=None):
            prefix = prefix or cls.__name__
            for field in self._get_fields(cls):
                arg_name = f"--{prefix}.{field.name}"
                arg_type = field.type if field.type is not dataclasses.MISSING else str
                description = field.metadata.get("help", "")

                default_value = None
                if field.default is not dataclasses.MISSING:
                    default_value = field.default
                elif field.default_factory is not dataclasses.MISSING:
                    default_value = field.default_factory()

                if default_value is not None:
                    if description:
                        description = f"{description} (default: {default_value})"
                    else:
                        description = f"(default: {default_value})"

                # Nested dataclass support
                if dataclasses.is_dataclass(arg_type) and not isinstance(
                    default_value, type
                ):
                    add_fields(arg_type, prefix=f"{prefix}.{field.name}")
                    continue

                # Literal
                if _is_literal_type(arg_type):
                    choices = _get_type_args(arg_type)
                    metavar = "{" + ",".join(str(choice) for choice in choices) + "}"
                    self.parser.add_argument(
                        arg_name,
                        type=str,
                        choices=choices,
                        help=description,
                        metavar=metavar,
                    )
                    continue

                # Tuple
                if _is_tuple_type(arg_type):
                    metavar = "TUPLE"
                    self.parser.add_argument(
                        arg_name,
                        type=self._tuple_type_factory(arg_type),
                        help=description,
                        metavar=metavar,
                    )
                    continue

                # List
                if _is_list_type(arg_type):
                    metavar = "LIST"
                    self.parser.add_argument(
                        arg_name,
                        type=self._list_type_factory(arg_type),
                        help=description,
                        metavar=metavar,
                    )
                    continue

                # Dict
                if _is_dict_type(arg_type):
                    metavar = "DICT"
                    self.parser.add_argument(
                        arg_name,
                        type=self._dict_type_factory(arg_type),
                        help=description,
                        metavar=metavar,
                    )
                    continue

                # Basic types
                if arg_type is int:
                    metavar = "INT"
                elif arg_type is float:
                    metavar = "FLOAT"
                elif arg_type is str:
                    metavar = "STRING"
                elif arg_type is bool:
                    metavar = "BOOL"
                else:
                    metavar = arg_type.__name__.upper()

                self.parser.add_argument(
                    arg_name,
                    type=arg_type,
                    help=description,
                    metavar=metavar,
                )

        for cls in self.dataclass_types:
            add_fields(cls)

    def parse(self, args: Optional[list[str]] = None) -> dict[str, Any]:
        """
        Parse command-line arguments and return dataclass instances, including nested dataclasses.

        Args:
            args (Optional[list[str]]): Optional list of arguments to parse. If None, uses sys.argv.

        Returns:
            dict[str, Any]: Dict mapping dataclass names to their instantiated objects with parsed values.

        Raises:
            SystemExit: If required fields (those without defaults) are not provided either as command-line arguments or in the config file.
        """

        parsed_args = vars(self.parser.parse_args(args))

        # Check if config file is provided (use recorded dest name to support custom flag)
        config_data = {}
        if parsed_args.get(self._config_dest):
            config_data = self._load_config_file(parsed_args[self._config_dest])

        result = {}
        # Add dataclass instances
        dataclass_field_names = set()
        for cls in self.dataclass_types:
            instance = self._build_instance(cls, parsed_args, config_data)
            result[cls.__name__] = instance
            # Collect all dataclass argument keys using cached fields
            for field in self._get_fields(cls):
                dataclass_field_names.add(f"{cls.__name__}.{field.name}")

        # Add custom flags (not associated with dataclass fields)
        for key, value in parsed_args.items():
            if key not in dataclass_field_names and key != self._config_dest:
                result[key] = value
        return result

    def _build_instance(
        self,
        cls: Type[Any],
        parsed_args: dict[str, Any],
        config_data: dict[str, Any],
        prefix: Optional[str] = None,
        config_section: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Build an instance of the dataclass `cls` using parsed arguments and config data.
        Handles required fields and nested dataclasses.
        """
        prefix = prefix or cls.__name__
        config_section = config_section or config_data.get(cls.__name__, {})
        values = {}
        missing_fields = []
        for field in self._get_fields(cls):
            field_name = field.name
            arg_key = f"{prefix}.{field_name}"
            arg_type = field.type if field.type is not dataclasses.MISSING else str

            value = self._resolve_field_value(
                field, arg_key, arg_type, config_section, parsed_args, config_data
            )

            # Type-specific handling
            value = self._handle_field_type(value, arg_type)

            if value is dataclasses.MISSING:
                missing_fields.append(f"--{arg_key}")
            else:
                values[field_name] = value

        if missing_fields:
            error_msg = (
                f"Missing required arguments for {cls.__name__}: {', '.join(missing_fields)}. "
                f"These must be provided either as command-line arguments or in the config file."
            )
            self.parser.error(error_msg)
        return cls(**values)

    def _resolve_field_value(
        self,
        field: dataclasses.Field,
        arg_key: str,
        arg_type: Any,
        config_section: dict[str, Any],
        parsed_args: dict[str, Any],
        config_data: dict[str, Any],
    ) -> Any:
        """
        Resolve the value for a dataclass field from defaults, config, CLI, and nested overrides.
        """
        # 1. Default
        if field.default is not dataclasses.MISSING:
            value = field.default
        elif field.default_factory is not dataclasses.MISSING:
            value = field.default_factory()
        else:
            value = dataclasses.MISSING

        # 2. Config file
        if field.name in config_section:
            value = config_section[field.name]

        # 3. Command-line
        if arg_key in parsed_args and parsed_args[arg_key] is not None:
            value = parsed_args[arg_key]

        # 4. Nested dataclass: check for overrides
        if dataclasses.is_dataclass(arg_type):
            nested_config = (
                config_section.get(field.name, {})
                if isinstance(config_section, dict)
                else {}
            )
            nested_prefix = f"{arg_key}."
            # More efficient: check if any key starts with nested_prefix using a generator
            # This avoids creating intermediate lists
            has_override = any(
                parsed_args.get(key) is not None
                for key in parsed_args
                if key.startswith(nested_prefix)
            )

            if not has_override and nested_config:
                # Simplified config override check - if nested_config is non-empty dict, consider it an override
                has_override = isinstance(nested_config, dict) and bool(nested_config)

            if has_override:
                value = self._merge_nested(
                    arg_type, arg_key, nested_config, parsed_args, config_data
                )
        return value

    def _handle_field_type(self, value: Any, arg_type: Any) -> Any:
        """
        Handle type-specific conversion for lists and tuples of dataclasses.
        """
        # Handle tuple of dataclasses
        if _is_tuple_type(arg_type):
            type_args = _get_type_args(arg_type)
            if type_args and all(dataclasses.is_dataclass(t) for t in type_args):
                if isinstance(value, list) and len(value) == len(type_args):
                    value = tuple(
                        t(**v) if isinstance(v, dict) else v
                        for t, v in zip(type_args, value)
                    )
        # Handle list of dataclasses
        elif _is_list_type(arg_type):
            type_args = _get_type_args(arg_type)
            if type_args and len(type_args) == 1 and dataclasses.is_dataclass(type_args[0]):
                elem_type = type_args[0]
                if isinstance(value, list):
                    value = [elem_type(**v) if isinstance(v, dict) else v for v in value]
        return value

    def _merge_nested(
        self,
        cls_nested: Type[Any],
        prefix_nested: str,
        config_nested: dict[str, Any],
        parsed_args: dict[str, Any],
        config_data: dict[str, Any],
    ) -> Any:
        """
        Recursively merge nested dataclass values from CLI, config, and defaults.
        """
        vals = {}
        missing_fields = []
        for f in self._get_fields(cls_nested):
            k_cli = f"{prefix_nested}.{f.name}"
            # CLI
            if k_cli in parsed_args and parsed_args[k_cli] is not None:
                vals[f.name] = parsed_args[k_cli]
            # Nested CLI (for deeper nesting)
            elif any(key.startswith(f"{k_cli}.") for key in parsed_args):
                vals[f.name] = self._merge_nested(
                    f.type,
                    k_cli,
                    config_nested.get(f.name, {}),
                    parsed_args,
                    config_data,
                )
            # Config
            elif isinstance(config_nested, dict) and f.name in config_nested:
                vals[f.name] = config_nested[f.name]
            # Default
            elif f.default is not dataclasses.MISSING:
                vals[f.name] = f.default
            elif f.default_factory is not dataclasses.MISSING:
                vals[f.name] = f.default_factory()
            else:
                missing_fields.append(f"--{k_cli}")
        if missing_fields:
            error_msg = (
                f"Missing required arguments for {cls_nested.__name__}: {', '.join(missing_fields)}. "
                f"These must be provided either as command-line arguments or in the config file."
            )
            self.parser.error(error_msg)
        return cls_nested(**vals)
