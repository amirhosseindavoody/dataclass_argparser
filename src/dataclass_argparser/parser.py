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
from result import Result, Ok, Err

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _get_optional_inner_type(type_hint: Any) -> Optional[Any]:
    """
    If type_hint is Optional[T] (i.e., Union[T, None]), return T.
    Otherwise, return None.
    """
    origin = getattr(type_hint, "__origin__", None)
    if origin is Union:
        args = type_hint.__args__
        # Optional[T] is Union[T, None], so we check for exactly two args with one being NoneType
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1 and type(None) in args:
            return non_none_args[0]
    return None


def _strict_bool(value: str) -> bool:
    """
    Parse a string to a boolean value strictly.

    Only accepts 'True', 'true', 'False', 'false', '1', '0' as valid values.
    Raises argparse.ArgumentTypeError for any other string.
    """
    if value in ("True", "true", "1"):
        return True
    elif value in ("False", "false", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid boolean value: '{value}'. Must be one of: True, true, False, false, 1, 0"
        )


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
        """
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
        """
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

    def _list_type_factory(self, list_type: Any) -> typing.Callable[[str], list]:
        """
        Return a function that parses a string into a list of the correct type.
        """
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

    def _dict_type_factory(self, dict_type: Any) -> typing.Callable[[str], dict]:
        """
        Return a function that parses a string into a dict of the correct type.

        Args:
            dict_type: The typing.Dict type to parse.

        Returns:
            Callable[[str], dict]: A function that parses a string into a dict.
        """

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

                        # Get the expected key and value types
                        key_type = str  # Default to str
                        value_type = str  # Default to str
                        if hasattr(dict_type, "__args__") and dict_type.__args__:
                            if len(dict_type.__args__) >= 1:
                                key_type = dict_type.__args__[0]
                            if len(dict_type.__args__) >= 2:
                                value_type = dict_type.__args__[1]

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

                            # Strict type validation for value
                            if value_type is int:
                                if not isinstance(v, int) or isinstance(v, bool):
                                    raise argparse.ArgumentTypeError(
                                        f"Expected int for value, got {type(v).__name__}: {v!r}"
                                    )
                            elif value_type is float:
                                if not isinstance(v, (int, float)) or isinstance(
                                    v, bool
                                ):
                                    raise argparse.ArgumentTypeError(
                                        f"Expected float for value, got {type(v).__name__}: {v!r}"
                                    )
                                v = float(v)
                            elif value_type is bool:
                                if not isinstance(v, bool):
                                    raise argparse.ArgumentTypeError(
                                        f"Expected bool for value, got {type(v).__name__}: {v!r}"
                                    )
                            elif value_type is str:
                                if not isinstance(v, str):
                                    raise argparse.ArgumentTypeError(
                                        f"Expected str for value, got {type(v).__name__}: {v!r}"
                                    )
                            else:
                                try:
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
                    # Get the expected key and value types
                    key_type = str  # Default to str
                    value_type = str  # Default to str
                    if hasattr(dict_type, "__args__") and dict_type.__args__:
                        if len(dict_type.__args__) >= 1:
                            key_type = dict_type.__args__[0]
                        if len(dict_type.__args__) >= 2:
                            value_type = dict_type.__args__[1]

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

                        # Convert value with strict type checking
                        try:
                            parsed_value = ast.literal_eval(value)
                        except (ValueError, SyntaxError):
                            # Not a literal, treat as string
                            parsed_value = value

                        if value_type is int:
                            if not isinstance(parsed_value, int) or isinstance(
                                parsed_value, bool
                            ):
                                raise argparse.ArgumentTypeError(
                                    f"Expected int for value, got {type(parsed_value).__name__}: {value!r}"
                                )
                            value = parsed_value
                        elif value_type is float:
                            if not isinstance(parsed_value, (int, float)) or isinstance(
                                parsed_value, bool
                            ):
                                raise argparse.ArgumentTypeError(
                                    f"Expected float for value, got {type(parsed_value).__name__}: {value!r}"
                                )
                            value = float(parsed_value)
                        elif value_type is bool:
                            if isinstance(parsed_value, bool):
                                value = parsed_value
                            elif value in ("True", "true", "1"):
                                value = True
                            elif value in ("False", "false", "0"):
                                value = False
                            else:
                                raise argparse.ArgumentTypeError(
                                    f"Expected bool for value, got: {value!r}"
                                )
                        elif value_type is str:
                            value = value  # Keep as string
                        else:
                            try:
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
            for field in dataclasses.fields(cls):
                arg_name = f"--{prefix}.{field.name}"
                arg_type = field.type if field.type is not dataclasses.MISSING else str
                description = field.metadata.get("help", "")

                # Handle Optional[T] by extracting the inner type
                inner_type = _get_optional_inner_type(arg_type)
                if inner_type is not None:
                    arg_type = inner_type

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

                # Dict
                if hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
                    dict,
                    typing.Dict,
                ):
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
                    parser_type = int
                elif arg_type is float:
                    metavar = "FLOAT"
                    parser_type = float
                elif arg_type is str:
                    metavar = "STRING"
                    parser_type = str
                elif arg_type is bool:
                    metavar = "BOOL"
                    parser_type = _strict_bool
                else:
                    metavar = arg_type.__name__.upper()
                    parser_type = arg_type

                self.parser.add_argument(
                    arg_name,
                    type=parser_type,
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
            # Collect all dataclass argument keys
            for field in dataclasses.fields(cls):
                dataclass_field_names.add(f"{cls.__name__}.{field.name}")

        # Add custom flags (not associated with dataclass fields)
        for key, value in parsed_args.items():
            if key not in dataclass_field_names and key != self._config_dest:
                result[key] = value
        return result

    # TODO: Add tests for safe_parse
    def safe_parse(
        self, args: Optional[list[str]] = None
    ) -> Result[dict[str, Any], str]:
        """
        Safely parse command-line arguments and return dataclass instances, including nested dataclasses.

        Args:
            args (Optional[list[str]]): Optional list of arguments to parse. If None, uses sys.argv.
        Returns:
            Result[dict[str, Any], str]:
                - Ok[dict[str, Any]] with dict mapping dataclass names to their instantiated objects with parsed values,
                - Err with error message if parsing fails.
        """
        try:
            parsed_result = self.parse(args)
            return Ok(parsed_result)
        except Exception as e:
            return Err(str(e))

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
        for field in dataclasses.fields(cls):
            field_name = field.name
            arg_key = f"{prefix}.{field_name}"
            arg_type = field.type if field.type is not dataclasses.MISSING else str

            value = self._resolve_field_value(
                field, arg_key, arg_type, config_section, parsed_args, config_data
            )

            # Type-specific handling
            value = self._handle_field_type(value, arg_type)

            # Validate type (for config file values; CLI values are validated by argparse)
            self._validate_type(value, arg_type, f"{prefix}.{field_name}")

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
            has_override = any(
                key.startswith(nested_prefix) and parsed_args[key] is not None
                for key in parsed_args
            )

            def config_has_override(cfg):
                if isinstance(cfg, dict):
                    if cfg:
                        return True
                    for v in cfg.values():
                        if config_has_override(v):
                            return True
                return False

            if not has_override:
                has_override = config_has_override(nested_config)
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
        if (
            hasattr(arg_type, "__origin__")
            and arg_type.__origin__ in (tuple, typing.Tuple)
            and all(
                dataclasses.is_dataclass(t) for t in getattr(arg_type, "__args__", [])
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
                value = [elem_type(**v) if isinstance(v, dict) else v for v in value]
        return value

    def _validate_type(self, value: Any, arg_type: Any, field_name: str) -> None:
        """
        Validate that a value matches the expected type.

        Raises TypeError or ValueError if the value doesn't match the expected type.

        Args:
            value: The value to validate.
            arg_type: The expected type.
            field_name: The name of the field (for error messages).

        Raises:
            TypeError: If the value is not of the expected type.
            ValueError: If the value cannot be interpreted as the expected type.
        """
        if value is dataclasses.MISSING:
            return

        # Handle Optional types: if value is None, it's valid for Optional
        # Otherwise, validate against the inner type
        inner_type = _get_optional_inner_type(arg_type)
        if inner_type is not None:
            if value is None:
                return
            arg_type = inner_type

        # Skip validation for nested dataclasses (they are handled separately)
        if dataclasses.is_dataclass(arg_type) and not isinstance(arg_type, type):
            return

        # Handle basic types
        if arg_type is int:
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(
                    f"Field '{field_name}' expects int, got {type(value).__name__}: {value!r}"
                )
        elif arg_type is float:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(
                    f"Field '{field_name}' expects float, got {type(value).__name__}: {value!r}"
                )
        elif arg_type is bool:
            if not isinstance(value, bool):
                raise TypeError(
                    f"Field '{field_name}' expects bool, got {type(value).__name__}: {value!r}"
                )
        elif arg_type is str:
            if not isinstance(value, str):
                raise TypeError(
                    f"Field '{field_name}' expects str, got {type(value).__name__}: {value!r}"
                )

        # Handle List types
        elif hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
            list,
            typing.List,
        ):
            if not isinstance(value, list):
                raise TypeError(
                    f"Field '{field_name}' expects list, got {type(value).__name__}: {value!r}"
                )
            if hasattr(arg_type, "__args__") and arg_type.__args__:
                elem_type = arg_type.__args__[0]
                # Skip if element type is a dataclass
                if not dataclasses.is_dataclass(elem_type):
                    for i, elem in enumerate(value):
                        self._validate_type(elem, elem_type, f"{field_name}[{i}]")

        # Handle Tuple types
        elif hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
            tuple,
            typing.Tuple,
        ):
            if not isinstance(value, (list, tuple)):
                raise TypeError(
                    f"Field '{field_name}' expects tuple, got {type(value).__name__}: {value!r}"
                )
            if hasattr(arg_type, "__args__") and arg_type.__args__:
                elem_types = arg_type.__args__
                # Skip if all element types are dataclasses
                if not all(dataclasses.is_dataclass(t) for t in elem_types):
                    if len(value) != len(elem_types):
                        raise ValueError(
                            f"Field '{field_name}' expects tuple of length {len(elem_types)}, "
                            f"got length {len(value)}"
                        )
                    for i, (elem, elem_type) in enumerate(zip(value, elem_types)):
                        if not dataclasses.is_dataclass(elem_type):
                            self._validate_type(elem, elem_type, f"{field_name}[{i}]")

        # Handle Dict types
        elif hasattr(arg_type, "__origin__") and arg_type.__origin__ in (
            dict,
            typing.Dict,
        ):
            if not isinstance(value, dict):
                raise TypeError(
                    f"Field '{field_name}' expects dict, got {type(value).__name__}: {value!r}"
                )
            if hasattr(arg_type, "__args__") and arg_type.__args__:
                key_type = arg_type.__args__[0] if len(arg_type.__args__) >= 1 else str
                value_type = (
                    arg_type.__args__[1] if len(arg_type.__args__) >= 2 else str
                )
                for k, v in value.items():
                    self._validate_type(k, key_type, f"{field_name} key '{k}'")
                    self._validate_type(v, value_type, f"{field_name}['{k}']")

        # Handle Literal types
        elif hasattr(arg_type, "__origin__") and arg_type.__origin__ is Literal:
            choices = arg_type.__args__
            if value not in choices:
                raise ValueError(
                    f"Field '{field_name}' expects one of {choices}, got {value!r}"
                )

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
        for f in dataclasses.fields(cls_nested):
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
