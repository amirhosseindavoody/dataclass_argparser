import dataclasses
import pytest
from dataclass_argparser.parser import DataclassArgParser


@dataclasses.dataclass
class Inner:
    x: int = dataclasses.field(default=1, metadata={"help": "Inner x"})
    y: str = dataclasses.field(default="foo", metadata={"help": "Inner y"})


@dataclasses.dataclass
class Outer:
    inner: Inner = dataclasses.field(
        default_factory=Inner, metadata={"help": "Nested inner object"}
    )
    z: float = dataclasses.field(default=3.14, metadata={"help": "Outer z"})


def test_nested_defaults():
    parser = DataclassArgParser(Outer)
    result = parser.parse([])
    cfg = result["Outer"]
    assert isinstance(cfg.inner, Inner)
    assert cfg.inner.x == 1
    assert cfg.inner.y == "foo"
    assert cfg.z == 3.14


def test_nested_override():
    parser = DataclassArgParser(Outer)
    result = parser.parse(
        ["--Outer.inner.x", "42", "--Outer.inner.y", "bar", "--Outer.z", "2.71"]
    )
    cfg = result["Outer"]
    assert cfg.inner.x == 42
    assert cfg.inner.y == "bar"
    assert cfg.z == 2.71


@pytest.mark.parametrize(
    "cli,expected_x,expected_y,expected_z",
    [
        (["--Outer.inner.x", "100"], 100, "foo", 3.14),
        (["--Outer.inner.y", "baz"], 1, "baz", 3.14),
        (["--Outer.z", "1.23"], 1, "foo", 1.23),
        (
            ["--Outer.inner.x", "7", "--Outer.inner.y", "hi", "--Outer.z", "9.9"],
            7,
            "hi",
            9.9,
        ),
    ],
)
def test_nested_combinations(cli, expected_x, expected_y, expected_z):
    parser = DataclassArgParser(Outer)
    cfg = parser.parse(cli)["Outer"]
    assert cfg.inner.x == expected_x
    assert cfg.inner.y == expected_y
    assert cfg.z == expected_z
