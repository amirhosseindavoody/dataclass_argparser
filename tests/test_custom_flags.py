import pytest
from dataclasses import dataclass, field
from unittest.mock import patch
from io import StringIO

from dataclass_argparser import DataclassArgParser


@dataclass
class SampleConfigForFlags:
    string_field: str = field(
        default="default_value", metadata={"help": "A string field"}
    )


def test_add_flag_method_and_help_and_parse():
    parser = DataclassArgParser(SampleConfigForFlags)

    # Add a custom boolean flag via the method
    parser.add_flag("--verbose", "-v", action="store_true", help="Enable verbose")

    # Check that help includes the new flag
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        with pytest.raises(SystemExit):
            parser.parser.parse_args(["--help"])
        help_output = mock_stdout.getvalue()

    assert "--verbose" in help_output
    assert "Enable verbose" in help_output

    # Check that parsing sets the flag and dataclass args still parse
    ns = parser.parser.parse_args(
        ["--verbose", "--SampleConfigForFlags.string_field", "custom"]
    )
    assert hasattr(ns, "verbose") and ns.verbose is True

    result = parser.parse(
        ["--verbose", "--SampleConfigForFlags.string_field", "custom"]
    )
    cfg = result["SampleConfigForFlags"]
    assert cfg.string_field == "custom"
    # custom flag should be present as a top-level key in parse result
    assert "verbose" in result
    assert result.get("verbose") is True


def test_flags_via_constructor_accepts_multiple_formats_and_parse_help():
    # Provide flags via constructor in both tuple and dict forms
    flags = [
        ("--log", {"type": str, "help": "Log file path"}),
        {"names": "--quiet", "kwargs": {"action": "store_true", "help": "Quiet mode"}},
    ]

    parser = DataclassArgParser(SampleConfigForFlags, flags=flags)

    # Help should contain both flags
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        with pytest.raises(SystemExit):
            parser.parser.parse_args(["--help"])
        help_output = mock_stdout.getvalue()

    assert "--log" in help_output
    assert "Log file path" in help_output
    assert "--quiet" in help_output
    assert "Quiet mode" in help_output

    # Parsing should accept the flags without interfering with dataclass parsing
    ns = parser.parser.parse_args(["--log", "/tmp/log.txt", "--quiet"])
    assert ns.log == "/tmp/log.txt"
    assert ns.quiet is True

    result = parser.parse(
        [
            "--log",
            "/tmp/log.txt",
            "--quiet",
            "--SampleConfigForFlags.string_field",
            "abc",
        ]
    )
    cfg = result["SampleConfigForFlags"]
    assert cfg.string_field == "abc"
    assert "log" in result
    assert result.get("log") == "/tmp/log.txt"
    assert "quiet" in result
    assert result.get("quiet") is True


def test_conflict_between_constructor_and_add_flag_raises():
    # Provide a flag via constructor
    flags = [("--conflict", {"action": "store_true", "help": "From constructor"})]
    parser = DataclassArgParser(SampleConfigForFlags, flags=flags)

    # Attempting to add the same flag again should raise ValueError
    with pytest.raises(ValueError) as exc:
        parser.add_flag("--conflict", action="store_true", help="From add_flag")

    assert "Flag name conflict" in str(exc.value)
    # Also ensure the flag is present when parsing and is returned as top-level
    res = parser.parse(["--conflict", "--SampleConfigForFlags.string_field", "x"])
    assert "conflict" in res
    assert res.get("conflict") is True
