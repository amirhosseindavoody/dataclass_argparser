#!/usr/bin/env python3
"""
Example demonstrating config file override functionality.

This script shows how values from a config file can be overridden
by command-line arguments, demonstrating the priority system:
1. Command-line arguments (highest priority)
2. Config file values
3. Dataclass defaults (lowest priority)
"""

from dataclasses import dataclass, field
from dataclass_argparser import DataclassArgParser


@dataclass
class SimulationConfig:
    hspice_path: str = field(
        default="/default/hspice", metadata={"help": "Path to HSPICE"}
    )
    temperature: float = field(
        default=27.0, metadata={"help": "Temperature in Celsius"}
    )
    num_simulations: int = field(
        default=100, metadata={"help": "Number of simulations"}
    )


@dataclass
class NetbatchConfig:
    nb_max_jobs: int = field(default=10, metadata={"help": "Max number of jobs"})
    nbpool: str = field(default="default_pool", metadata={"help": "Netbatch pool"})


if __name__ == "__main__":
    parser = DataclassArgParser(SimulationConfig, NetbatchConfig)

    # Test with config file and command-line override
    print("Testing override functionality...")
    print("=" * 50)

    result = parser.parse(
        [
            "--config",
            "dataclass_argparser/examples/override_config.json",
            "--SimulationConfig.temperature",
            "25.0",
        ]
    )

    sim_config = result["SimulationConfig"]
    nb_config = result["NetbatchConfig"]

    print("Results:")
    print("-" * 20)
    print(f"Temperature: {sim_config.temperature}°C")  # Should be 25.0 (overridden)
    print(
        f"Num simulations: {sim_config.num_simulations}"
    )  # Should be 1000 (from config)
    print(f"Max jobs: {nb_config.nb_max_jobs}")  # Should be 1000 (from config)
    print(f"Pool: {nb_config.nbpool}")  # Should be pdx_dts (from config)

    print("\nPriority demonstration:")
    print("1. Default temperature was: 27.0")
    print("2. Config file set it to: 85.0")
    print(f"3. Command line overrode it to: {sim_config.temperature}")

    print("\nThis demonstrates that command-line arguments have the highest priority!")
    print(
        "Try running with different --SimulationConfig.temperature values to see the override in action."
    )
