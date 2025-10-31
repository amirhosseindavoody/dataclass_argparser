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

        def parse_tuple(input_string):
            try:
                if input_string.startswith("(") and input_string.endswith(")"):
                    input_string = input_string[1:-1]
                string_items = [item.strip() for item in input_string.split(",") if item.strip()]
                expected_types = tuple_type.__args__
                if len(string_items) != len(expected_types):
                    raise argparse.ArgumentTypeError(
                        f"Expected {len(expected_types)} values, got {len(string_items)}"
                    )
                parsed_values = []
                for string_item, expected_type in zip(string_items, expected_types):
                    try:
                        converted_value = (
                            ast.literal_eval(string_item)
                            if expected_type in (int, float, bool)
                            else string_item
                        )
                        converted_value = expected_type(converted_value)
                    except Exception:
                        raise argparse.ArgumentTypeError(
                            f"Could not convert '{string_item}' to {expected_type.__name__}"
                        )
                    parsed_values.append(converted_value)
                return tuple(parsed_values)
            except Exception as e:
                raise argparse.ArgumentTypeError(f"Invalid tuple value: {input_string} ({e})")

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

        def parse_list(input_string):
            try:
                if input_string.startswith("[") and input_string.endswith("]"):
                    input_string = input_string[1:-1]
                string_items = [item.strip() for item in input_string.split(",") if item.strip()]
                element_type = (
                    list_type.__args__[0]
                    if hasattr(list_type, "__args__") and list_type.__args__
                    else str
                )
                parsed_values = []
                for string_item in string_items:
                    try:
                        converted_value = (
                            ast.literal_eval(string_item)
                            if element_type in (int, float, bool)
                            else string_item
                        )
                        converted_value = element_type(converted_value)
                    except Exception:
                        raise argparse.ArgumentTypeError(
                            f"Could not convert '{string_item}' to {element_type.__name__}"
                        )
                    parsed_values.append(converted_value)
                return parsed_values
            except Exception as e:
                raise argparse.ArgumentTypeError(f"Invalid list value: {input_string} ({e})")

        return parse_list

    def _dict_type_factory(self, dict_type: Any) -> typing.Callable[[str], dict]:
        """
        Return a function that parses a string into a dict of the correct type.

        Args:
            dict_type: The typing.Dict type to parse.

        Returns:
            Callable[[str], dict]: A function that parses a string into a dict.
        """

        def parse_dict(input_string):
            try:
                # Handle empty string as empty dict
                if not input_string.strip():
                    return {}

                # Try JSON format first
                if input_string.strip().startswith("{") and input_string.strip().endswith("}"):
                    try:
                        parsed_dict = json.loads(input_string)
                        if not isinstance(parsed_dict, dict):
                            raise argparse.ArgumentTypeError(
                                f"JSON value must be an object/dict, got {type(parsed_dict).__name__}"
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
                        typed_dict = {}
                        for dict_key, dict_value in parsed_dict.items():
                            # Convert key
                            try:
                                if key_type is not str:
                                    dict_key = key_type(dict_key)
                            except Exception:
                                raise argparse.ArgumentTypeError(
                                    f"Could not convert key '{dict_key}' to {key_type.__name__}"
                                )

                            # Convert value
                            try:
                                if value_type in (int, float, bool):
                                    # For basic types, the JSON parsing should handle this correctly
                                    if not isinstance(dict_value, value_type):
                                        dict_value = value_type(dict_value)
                                elif value_type is not str:
                                    dict_value = value_type(dict_value)
                            except Exception:
                                raise argparse.ArgumentTypeError(
                                    f"Could not convert value '{dict_value}' to {value_type.__name__}"
                                )

                            typed_dict[dict_key] = dict_value

                        return typed_dict
                    except json.JSONDecodeError as json_error:
                        raise argparse.ArgumentTypeError(f"Invalid JSON format: {json_error}")

                # Try key=value,key2=value2 format
                else:
                    parsed_dict = {}
                    # Get the expected key and value types
                    key_type = str  # Default to str
                    value_type = str  # Default to str
                    if hasattr(dict_type, "__args__") and dict_type.__args__:
                        if len(dict_type.__args__) >= 1:
                            key_type = dict_type.__args__[0]
                        if len(dict_type.__args__) >= 2:
                            value_type = dict_type.__args__[1]

                    key_value_pairs = [pair.strip() for pair in input_string.split(",") if pair.strip()]
                    for key_value_pair in key_value_pairs:
                        if "=" not in key_value_pair:
                            raise argparse.ArgumentTypeError(
                                f"Invalid key=value format: '{key_value_pair}' (missing '=')"
                            )

                        dict_key, dict_value = key_value_pair.split("=", 1)  # Split only on first =
                        dict_key = dict_key.strip()
                        dict_value = dict_value.strip()

                        # Convert key
                        try:
                            if key_type is not str:
                                dict_key = key_type(dict_key)
                        except Exception:
                            raise argparse.ArgumentTypeError(
                                f"Could not convert key '{dict_key}' to {key_type.__name__}"
                            )

                        # Convert value
                        try:
                            if value_type in (int, float, bool):
                                dict_value = (
                                    ast.literal_eval(dict_value)
                                    if value_type in (int, float, bool)
                                    else dict_value
                                )
                                dict_value = value_type(dict_value)
                            elif value_type is not str:
                                dict_value = value_type(dict_value)
                        except Exception:
                            raise argparse.ArgumentTypeError(
                                f"Could not convert value '{dict_value}' to {value_type.__name__}"
                            )

                        parsed_dict[dict_key] = dict_value

                    return parsed_dict

            except Exception as parsing_error:
                if isinstance(parsing_error, argparse.ArgumentTypeError):
                    raise
                raise argparse.ArgumentTypeError(f"Invalid dict value: {input_string} ({parsing_error})")

        return parse_dict

    def _add_dataclass_arguments(self) -> None:
        """
        Add arguments to the parser based on dataclass fields, including nested dataclasses.
        Handles Literal, tuple, list, dict, and nested dataclass types.
        """

        def add_fields(dataclass_type, field_prefix=None):
            field_prefix = field_prefix or dataclass_type.__name__
            for dataclass_field in dataclasses.fields(dataclass_type):
                argument_name = f"--{field_prefix}.{dataclass_field.name}"
                field_type = dataclass_field.type if dataclass_field.type is not dataclasses.MISSING else str
                help_text = dataclass_field.metadata.get("help", "")

                field_default_value = None
                if dataclass_field.default is not dataclasses.MISSING:
                    field_default_value = dataclass_field.default
                elif dataclass_field.default_factory is not dataclasses.MISSING:
                    field_default_value = dataclass_field.default_factory()

                if field_default_value is not None:
                    if help_text:
                        help_text = f"{help_text} (default: {field_default_value})"
                    else:
                        help_text = f"(default: {field_default_value})"

                # Nested dataclass support
                if dataclasses.is_dataclass(field_type) and not isinstance(
                    field_default_value, type
                ):
                    add_fields(field_type, field_prefix=f"{field_prefix}.{dataclass_field.name}")
                    continue

                # Literal
                if hasattr(field_type, "__origin__") and field_type.__origin__ is Literal:
                    literal_choices = field_type.__args__
                    metavar_text = "{" + ",".join(str(choice) for choice in literal_choices) + "}"
                    self.parser.add_argument(
                        argument_name,
                        type=str,
                        choices=literal_choices,
                        help=help_text,
                        metavar=metavar_text,
                    )
                    continue

                # Tuple
                if hasattr(field_type, "__origin__") and field_type.__origin__ in (
                    tuple,
                    typing.Tuple,
                ):
                    metavar_text = "TUPLE"
                    self.parser.add_argument(
                        argument_name,
                        type=self._tuple_type_factory(field_type),
                        help=help_text,
                        metavar=metavar_text,
                    )
                    continue

                # List
                if hasattr(field_type, "__origin__") and field_type.__origin__ in (
                    list,
                    typing.List,
                ):
                    metavar_text = "LIST"
                    self.parser.add_argument(
                        argument_name,
                        type=self._list_type_factory(field_type),
                        help=help_text,
                        metavar=metavar_text,
                    )
                    continue

                # Dict
                if hasattr(field_type, "__origin__") and field_type.__origin__ in (
                    dict,
                    typing.Dict,
                ):
                    metavar_text = "DICT"
                    self.parser.add_argument(
                        argument_name,
                        type=self._dict_type_factory(field_type),
                        help=help_text,
                        metavar=metavar_text,
                    )
                    continue

                # Basic types
                if field_type is int:
                    metavar_text = "INT"
                elif field_type is float:
                    metavar_text = "FLOAT"
                elif field_type is str:
                    metavar_text = "STRING"
                elif field_type is bool:
                    metavar_text = "BOOL"
                else:
                    metavar_text = field_type.__name__.upper()

                self.parser.add_argument(
                    argument_name,
                    type=field_type,
                    help=help_text,
                    metavar=metavar_text,
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

        parsing_result = {}
        # Add dataclass instances
        dataclass_argument_names = set()
        for dataclass_type in self.dataclass_types:
            dataclass_instance = self._build_instance(dataclass_type, parsed_args, config_data)
            parsing_result[dataclass_type.__name__] = dataclass_instance
            # Collect all dataclass argument keys
            for dataclass_field in dataclasses.fields(dataclass_type):
                dataclass_argument_names.add(f"{dataclass_type.__name__}.{dataclass_field.name}")

        # Add custom flags (not associated with dataclass fields)
        for argument_key, argument_value in parsed_args.items():
            if argument_key not in dataclass_argument_names and argument_key != self._config_dest:
                parsing_result[argument_key] = argument_value
        return parsing_result

    def _build_instance(
        self,
        dataclass_type: Type[Any],
        parsed_args: dict[str, Any],
        config_data: dict[str, Any],
        field_prefix: Optional[str] = None,
        config_section: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Build an instance of the dataclass `dataclass_type` using parsed arguments and config data.
        Handles required fields and nested dataclasses.
        """
        field_prefix = field_prefix or dataclass_type.__name__
        config_section = config_section or config_data.get(dataclass_type.__name__, {})
        field_values = {}
        missing_required_fields = []
        for dataclass_field in dataclasses.fields(dataclass_type):
            field_name = dataclass_field.name
            argument_key = f"{field_prefix}.{field_name}"
            field_type = dataclass_field.type if dataclass_field.type is not dataclasses.MISSING else str

            resolved_value = self._resolve_field_value(
                dataclass_field, argument_key, field_type, config_section, parsed_args, config_data
            )

            # Type-specific handling
            resolved_value = self._handle_field_type(resolved_value, field_type)

            if resolved_value is dataclasses.MISSING:
                missing_required_fields.append(f"--{argument_key}")
            else:
                field_values[field_name] = resolved_value

        if missing_required_fields:
            error_message = (
                f"Missing required arguments for {dataclass_type.__name__}: {', '.join(missing_required_fields)}. "
                f"These must be provided either as command-line arguments or in the config file."
            )
            self.parser.error(error_message)
        return dataclass_type(**field_values)

    def _resolve_field_value(
        self,
        dataclass_field: dataclasses.Field,
        argument_key: str,
        field_type: Any,
        config_section: dict[str, Any],
        parsed_args: dict[str, Any],
        config_data: dict[str, Any],
    ) -> Any:
        """
        Resolve the value for a dataclass field from defaults, config, CLI, and nested overrides.
        """
        # 1. Default
        if dataclass_field.default is not dataclasses.MISSING:
            resolved_value = dataclass_field.default
        elif dataclass_field.default_factory is not dataclasses.MISSING:
            resolved_value = dataclass_field.default_factory()
        else:
            resolved_value = dataclasses.MISSING

        # 2. Config file
        if dataclass_field.name in config_section:
            resolved_value = config_section[dataclass_field.name]

        # 3. Command-line
        if argument_key in parsed_args and parsed_args[argument_key] is not None:
            resolved_value = parsed_args[argument_key]

        # 4. Nested dataclass: check for overrides
        if dataclasses.is_dataclass(field_type):
            nested_config_section = (
                config_section.get(dataclass_field.name, {})
                if isinstance(config_section, dict)
                else {}
            )
            nested_field_prefix = f"{argument_key}."
            has_cli_override = any(
                key.startswith(nested_field_prefix) and parsed_args[key] is not None
                for key in parsed_args
            )

            def check_config_has_override(config_dict):
                if isinstance(config_dict, dict):
                    if config_dict:
                        return True
                    for config_value in config_dict.values():
                        if check_config_has_override(config_value):
                            return True
                return False

            if not has_cli_override:
                has_cli_override = check_config_has_override(nested_config_section)
            if has_cli_override:
                resolved_value = self._merge_nested(
                    field_type, argument_key, nested_config_section, parsed_args, config_data
                )
        return resolved_value

    def _handle_field_type(self, field_value: Any, field_type: Any) -> Any:
        """
        Handle type-specific conversion for lists and tuples of dataclasses.
        """
        # Handle tuple of dataclasses
        if (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ in (tuple, typing.Tuple)
            and all(
                dataclasses.is_dataclass(element_type) for element_type in getattr(field_type, "__args__", [])
            )
        ):
            tuple_element_types = field_type.__args__
            if isinstance(field_value, list) and len(field_value) == len(tuple_element_types):
                field_value = tuple(
                    element_type(**element_value) if isinstance(element_value, dict) else element_value
                    for element_type, element_value in zip(tuple_element_types, field_value)
                )
        # Handle list of dataclasses
        elif (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ in (list, typing.List)
            and len(getattr(field_type, "__args__", [])) == 1
            and dataclasses.is_dataclass(field_type.__args__[0])
        ):
            list_element_type = field_type.__args__[0]
            if isinstance(field_value, list):
                field_value = [list_element_type(**element_value) if isinstance(element_value, dict) else element_value for element_value in field_value]
        return field_value

    def _merge_nested(
        self,
        nested_dataclass_type: Type[Any],
        nested_field_prefix: str,
        nested_config_section: dict[str, Any],
        parsed_args: dict[str, Any],
        config_data: dict[str, Any],
    ) -> Any:
        """
        Recursively merge nested dataclass values from CLI, config, and defaults.
        """
        field_values = {}
        missing_required_fields = []
        for nested_field in dataclasses.fields(nested_dataclass_type):
            cli_argument_key = f"{nested_field_prefix}.{nested_field.name}"
            # CLI
            if cli_argument_key in parsed_args and parsed_args[cli_argument_key] is not None:
                field_values[nested_field.name] = parsed_args[cli_argument_key]
            # Nested CLI (for deeper nesting)
            elif any(key.startswith(f"{cli_argument_key}.") for key in parsed_args):
                field_values[nested_field.name] = self._merge_nested(
                    nested_field.type,
                    cli_argument_key,
                    nested_config_section.get(nested_field.name, {}),
                    parsed_args,
                    config_data,
                )
            # Config
            elif isinstance(nested_config_section, dict) and nested_field.name in nested_config_section:
                field_values[nested_field.name] = nested_config_section[nested_field.name]
            # Default
            elif nested_field.default is not dataclasses.MISSING:
                field_values[nested_field.name] = nested_field.default
            elif nested_field.default_factory is not dataclasses.MISSING:
                field_values[nested_field.name] = nested_field.default_factory()
            else:
                missing_required_fields.append(f"--{cli_argument_key}")
        if missing_required_fields:
            error_message = (
                f"Missing required arguments for {nested_dataclass_type.__name__}: {', '.join(missing_required_fields)}. "
                f"These must be provided either as command-line arguments or in the config file."
            )
            self.parser.error(error_message)
        return nested_dataclass_type(**field_values)
