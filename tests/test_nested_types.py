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


@dataclasses.dataclass
class SecondaryOuter:
    outer: Outer = dataclasses.field(
        default_factory=Outer, metadata={"help": "Outer dataclass"}
    )
    label: str = dataclasses.field(default="main", metadata={"help": "Secondary label"})


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


def test_double_nested_defaults():
    parser = DataclassArgParser(SecondaryOuter)
    result = parser.parse([])
    cfg = result["SecondaryOuter"]
    assert isinstance(cfg, SecondaryOuter)
    assert isinstance(cfg.outer, Outer)
    assert isinstance(cfg.outer.inner, Inner)
    assert cfg.outer.inner.x == 1
    assert cfg.outer.inner.y == "foo"
    assert cfg.outer.z == 3.14
    assert cfg.label == "main"


def test_double_nested_override():
    parser = DataclassArgParser(SecondaryOuter)
    result = parser.parse(
        [
            "--SecondaryOuter.outer.inner.x",
            "99",
            "--SecondaryOuter.outer.inner.y",
            "deep",
            "--SecondaryOuter.outer.z",
            "7.77",
            "--SecondaryOuter.label",
            "deep_label",
        ]
    )
    cfg = result["SecondaryOuter"]
    assert cfg.outer.inner.x == 99
    assert cfg.outer.inner.y == "deep"
    assert cfg.outer.z == 7.77
    assert cfg.label == "deep_label"


@pytest.mark.parametrize(
    "cli,expected_x,expected_y,expected_z,expected_label",
    [
        (["--SecondaryOuter.outer.inner.x", "123"], 123, "foo", 3.14, "main"),
        (["--SecondaryOuter.outer.inner.y", "abc"], 1, "abc", 3.14, "main"),
        (["--SecondaryOuter.outer.z", "2.5"], 1, "foo", 2.5, "main"),
        (["--SecondaryOuter.label", "lbl"], 1, "foo", 3.14, "lbl"),
        (
            [
                "--SecondaryOuter.outer.inner.x",
                "5",
                "--SecondaryOuter.outer.inner.y",
                "hi",
                "--SecondaryOuter.outer.z",
                "8.8",
                "--SecondaryOuter.label",
                "lbl2",
            ],
            5,
            "hi",
            8.8,
            "lbl2",
        ),
    ],
)
def test_double_nested_combinations(
    cli, expected_x, expected_y, expected_z, expected_label
):
    parser = DataclassArgParser(SecondaryOuter)
    cfg = parser.parse(cli)["SecondaryOuter"]
    assert cfg.outer.inner.x == expected_x
    assert cfg.outer.inner.y == expected_y
    assert cfg.outer.z == expected_z
    assert cfg.label == expected_label
