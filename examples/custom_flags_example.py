#!/usr/bin/env python3
"""
Example demonstrating how to register and read custom flags alongside
dataclass-generated flags using DataclassArgParser.

This example shows two ways to add flags:
- Pass `flags=` to the constructor for upfront flags
- Call `add_flag(...)` to add additional flags later

It also prints how `parser.parse()` returns dataclass instances and custom flags
as top-level dictionary keys.
"""

from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser


@dataclass
class AppConfig:
    name: str = field(default="example", metadata={"help": "Application name"})
    repeats: int = field(default=1, metadata={"help": "Number of repeats"})


if __name__ == "__main__":
    # Flags passed in the constructor (mixed tuple/dict styles supported)
    constructor_flags = [
        ("--log", {"type": str, "help": "Path to log file"}),
        {"names": "--quiet", "kwargs": {"action": "store_true", "help": "Quiet mode"}},
    ]

    parser = DataclassArgParser(AppConfig, flags=constructor_flags)

    # Add an extra flag after construction
    parser.add_flag(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    # Simulate parsing arguments (replace with `None` to use CLI args)
    args = [
        "--log",
        "/tmp/app.log",
        "--quiet",
        "--verbose",
        "--AppConfig.name",
        "demo",
        "--AppConfig.repeats",
        "3",
    ]

    result = parser.parse(args)

    # Dataclass instances are returned under their class name keys
    cfg = result["AppConfig"]
    print("Dataclass result:")
    print(f"  name: {cfg.name}")
    print(f"  repeats: {cfg.repeats}")

    # Custom flags are returned as explicit top-level keys
    print("Custom flags:")
    print(f"  log: {result.get('log')}")
    print(f"  quiet: {result.get('quiet')}")
    print(f"  verbose: {result.get('verbose')}")
