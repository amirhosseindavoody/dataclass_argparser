#!/usr/bin/env python3
"""
Example script demonstrating the usage of DataclassArgParser.

This script shows how to define dataclasses with different field types
and use DataclassArgParser to create a command-line interface.
"""

from dataclasses import dataclass, field

from dataclass_argparser import DataclassArgParser


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""

    name: str = field(metadata={"help": "Name of the simulation"})
    temperature: float = field(
        default=27.0, metadata={"help": "Temperature in Celsius"}
    )
    num_simulations: int = field(
        default=100, metadata={"help": "Number of simulations to run"}
    )
    output_dir: str = field(
        default="/tmp/output", metadata={"help": "Output directory path"}
    )
    verbose: bool = field(default=False, metadata={"help": "Enable verbose output"})


@dataclass
class ProcessConfig:
    """Configuration for process parameters."""

    # Updated to accept arbitrary process type strings to match example_config.json
    process_type: str = field(
        default="typeA", metadata={"help": "Type of processing to use"}
    )
    max_workers: int = field(
        default=4, metadata={"help": "Maximum number of worker processes"}
    )
    timeout: float = field(default=300.0, metadata={"help": "Timeout in seconds"})


def main() -> None:
    """Main function demonstrating the parser."""
    parser = DataclassArgParser(SimulationConfig, ProcessConfig)

    # Provide short alias flags that map to the dataclass-style dest names.
    # This makes the example runnable with simplified flags like `--name`.
    parser.add_flag(
        "--name",
        dest="SimulationConfig.name",
        type=str,
        help="Short alias for Simulation name",
    )
    parser.add_flag(
        "--temperature",
        dest="SimulationConfig.temperature",
        type=float,
        help="Short alias for temperature",
    )

    print("DataclassArgParser Example")
    print("=" * 50)
    print()

    result = parser.parse()

    sim_config = result["SimulationConfig"]
    proc_config = result["ProcessConfig"]

    print("Parsed Configuration:")
    print("-" * 30)
    print(f"Simulation Name: {sim_config.name}")
    print(f"Temperature: {sim_config.temperature}°C")
    print(f"Number of Simulations: {sim_config.num_simulations}")
    print(f"Output Directory: {sim_config.output_dir}")
    print(f"Verbose: {sim_config.verbose}")
    print()
    print(f"Process Type: {proc_config.process_type}")
    print(f"Max Workers: {proc_config.max_workers}")
    print(f"Timeout: {proc_config.timeout}s")


if __name__ == "__main__":
    main()
