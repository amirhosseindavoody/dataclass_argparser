#!/usr/bin/env python3
"""
Example demonstrating config file override functionality.

This script shows how values from a config file can be overridden
by command-line arguments, demonstrating the priority system:
1. Command-line arguments (highest priority)
2. Config file values
3. Dataclass defaults (lowest priority)
"""

import sys
from dataclasses import dataclass, field

from dataclass_argparser import DataclassArgParser


@dataclass
class ConfigurationA:
    path: str = field(default="/default/path", metadata={"help": "A filesystem path"})
    float_field: float = field(default=0.0, metadata={"help": "A float field"})
    int_field: int = field(default=0, metadata={"help": "An integer field"})


@dataclass
class ConfigurationB:
    int_field_2: int = field(default=0, metadata={"help": "Another integer field"})
    string_field: str = field(default="", metadata={"help": "A string field"})


if __name__ == "__main__":
    parser = DataclassArgParser(ConfigurationA, ConfigurationB)

    result = parser.parse()

    a = result.get("ConfigurationA")
    b = result.get("ConfigurationB")

    print("Results:")
    print("-" * 20)
    print(f"ConfigurationA.path: {a.path}")
    print(f"ConfigurationA.float_field: {a.float_field}")
    print(f"ConfigurationA.int_field: {a.int_field}")

    print(f"ConfigurationB.int_field_2: {b.int_field_2}")
    print(f"ConfigurationB.string_field: {b.string_field}")

    print("\nPriority demonstration (config file vs defaults vs CLI):")
    print("See printed values above for how precedence is applied.")
