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
from typing import Any, Literal, Type, Union, Optional

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

    def _load_config_file(self, config_path: str) -> dict[str, Any]:
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

    def _tuple_type_factory(self, tuple_type: Any) -> Any:
        """
        Return a function that parses a string into a tuple of the correct type and length.

        Args:
            tuple_type: The typing.Tuple type to parse.

        Returns:
            Callable[[str], tuple]: A function that parses a string into a tuple.
        """

        def parse_tuple(s):
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

    def _list_type_factory(self, list_type: Any) -> Any:
        """
        Return a function that parses a string into a list of the correct type.

        Args:
            list_type: The typing.List type to parse.

        Returns:
            Callable[[str], list]: A function that parses a string into a list.
        """

        def parse_list(s):
            try:
                if s.startswith("[") and s.endswith("]"):
                    s = s[1:-1]
                items = [item.strip() for item in s.split(",") if item.strip()]
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

    def _add_dataclass_arguments(self) -> None:
        """
        Add arguments to the parser based on dataclass fields, including nested dataclasses.
        Handles Literal, tuple, list, and nested dataclass types.
        """

        def add_fields(cls, prefix=None):
            prefix = prefix or cls.__name__
            for field in dataclasses.fields(cls):
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
                if hasattr(arg_type, "__origin__") and arg_type.__origin__ is Literal:
                    choices = arg_type.__args__
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
                if hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
                    tuple,
                    typing.Tuple,
                ):
                    metavar = "TUPLE"
                    self.parser.add_argument(
                        arg_name,
                        type=self._tuple_type_factory(arg_type),
                        help=description,
                        metavar=metavar,
                    )
                    continue

                # List
                if hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
                    list,
                    typing.List,
                ):
                    metavar = "LIST"
                    self.parser.add_argument(
                        arg_name,
                        type=self._list_type_factory(arg_type),
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

        def build_instance(cls, prefix=None, config_section=None):
            prefix = prefix or cls.__name__
            config_section = config_section or config_data.get(cls.__name__, {})
            values = {}
            missing_fields = []
            for field in dataclasses.fields(cls):
                field_name = field.name
                arg_key = f"{prefix}.{field_name}"
                arg_type = field.type if field.type is not dataclasses.MISSING else str

                # 1. Default
                if field.default is not dataclasses.MISSING:
                    value = field.default
                elif field.default_factory is not dataclasses.MISSING:
                    value = field.default_factory()
                else:
                    value = dataclasses.MISSING

                # 2. Config file
                if field_name in config_section:
                    value = config_section[field_name]

                # 3. Command-line
                if arg_key in parsed_args and parsed_args[arg_key] is not None:
                    value = parsed_args[arg_key]

                # Handle tuple of dataclasses
                if (
                    hasattr(arg_type, "__origin__")
                    and arg_type.__origin__ in (tuple, typing.Tuple)
                    and all(
                        dataclasses.is_dataclass(t)
                        for t in getattr(arg_type, "__args__", [])
                    )
                ):
                    elem_types = arg_type.__args__
                    if isinstance(value, list) and len(value) == len(elem_types):
                        value = tuple(
                            t(**v) if isinstance(v, dict) else v
                            for t, v in zip(elem_types, value)
                        )

                # Handle list of dataclasses
                elif (
                    hasattr(arg_type, "__origin__")
                    and arg_type.__origin__ in (list, typing.List)
                    and len(getattr(arg_type, "__args__", [])) == 1
                    and dataclasses.is_dataclass(arg_type.__args__[0])
                ):
                    elem_type = arg_type.__args__[0]
                    if isinstance(value, list):
                        value = [
                            elem_type(**v) if isinstance(v, dict) else v for v in value
                        ]

                # Handle nested dataclass
                elif dataclasses.is_dataclass(arg_type):
                    # Config: get nested dict if present
                    nested_config = (
                        config_section.get(field_name, {})
                        if isinstance(config_section, dict)
                        else {}
                    )

                    def merge_nested(cls_nested, prefix_nested, config_nested):
                        vals = {}
                        for f in dataclasses.fields(cls_nested):
                            k_cli = f"{prefix_nested}.{f.name}"
                            # CLI
                            if k_cli in parsed_args and parsed_args[k_cli] is not None:
                                vals[f.name] = parsed_args[k_cli]
                            # Nested CLI (for deeper nesting)
                            elif any(
                                key.startswith(f"{k_cli}.") for key in parsed_args
                            ):
                                vals[f.name] = merge_nested(
                                    f.type, k_cli, config_nested.get(f.name, {})
                                )
                            # Config
                            elif (
                                isinstance(config_nested, dict)
                                and f.name in config_nested
                            ):
                                vals[f.name] = config_nested[f.name]
                            # Default
                            elif f.default is not dataclasses.MISSING:
                                vals[f.name] = f.default
                            elif f.default_factory is not dataclasses.MISSING:
                                vals[f.name] = f.default_factory()
                            else:
                                missing_fields.append(f"--{k_cli}")
                        return cls_nested(**vals)

                    value = merge_nested(arg_type, arg_key, nested_config)

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

        result = {}
        for cls in self.dataclass_types:
            result[cls.__name__] = build_instance(cls)
        # Collect any custom flags (those not belonging to dataclass fields nor the config key)
        dataclass_dests = set(
            action.dest
            for action in self.parser._actions
            if hasattr(action, "dest") and "." in action.dest
        )
        custom_flags = {
            k: v
            for k, v in parsed_args.items()
            if k != self._config_dest and k not in dataclass_dests
        }

        # Expose custom flags as explicit top-level keys in the returned dict.
        # Avoid overwriting dataclass entries; if a name would collide with an
        # existing key in result, raise a ValueError.
        for k, v in custom_flags.items():
            if k in result:
                raise ValueError(f"Custom flag name collides with result key: {k}")
            result[k] = v

        return result
