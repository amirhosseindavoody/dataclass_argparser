"""
DataclassArgParser - A utility for creating command-line argument parsers from dataclasses.

This package provides a simple way to automatically generate argparse-based command-line
interfaces from Python dataclasses, extracting help text from field metadata and
providing type-based metavars for better user experience. It also supports loading
configuration from YAML or JSON files.
"""

from .parser import DataclassArgParser

__version__ = "1.0.0"
__all__ = ["DataclassArgParser"]
