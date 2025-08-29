import dataclasses
import json
import pytest
from dataclass_argparser.parser import DataclassArgParser


@dataclasses.dataclass
class InnerWithNoDefaults:
    a: int
    b: int


@dataclasses.dataclass
class OuterWithFactory:
    inner: InnerWithNoDefaults = dataclasses.field(
        default_factory=lambda: InnerWithNoDefaults(a=1, b=2)
    )


def test_outer_with_default_factory_and_inner_no_defaults():
    parser = DataclassArgParser(OuterWithFactory)
    result = parser.parse([])
    cfg: OuterWithFactory = result["OuterWithFactory"]
    assert isinstance(cfg, OuterWithFactory)
    assert isinstance(cfg.inner, InnerWithNoDefaults)
    assert cfg.inner.a == 1
    assert cfg.inner.b == 2


def test_outer_with_default_factory_and_inner_no_defaults_from_config(tmp_path):
    """Test that a nested dataclass with a default_factory for the outer class and
    no defaults for the inner class can be correctly loaded from a config file.
    Verifies that config values override the default_factory and that the inner
    dataclass fields are set from the config.
    """
    config = {"OuterWithFactory": {"inner": {"a": 5, "b": 6}}}

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    parser = DataclassArgParser(OuterWithFactory)
    result = parser.parse(["--config", str(config_path)])
    cfg: OuterWithFactory = result["OuterWithFactory"]
    assert isinstance(cfg, OuterWithFactory)
    assert isinstance(cfg.inner, InnerWithNoDefaults)
    assert cfg.inner.a == 5
    assert cfg.inner.b == 6


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


@dataclasses.dataclass
class OuterWithList:
    inners: list[Inner] = dataclasses.field(
        default_factory=lambda: [Inner(), Inner(x=2, y="bar")],
        metadata={"help": "List of Inner dataclasses"},
    )
    z: float = dataclasses.field(default=3.14, metadata={"help": "Outer z"})


@dataclasses.dataclass
class OuterWithTuple:
    pair: tuple[Inner, Inner] = dataclasses.field(
        default=(Inner(), Inner(x=2, y="bar")),
        metadata={"help": "Tuple of Inner dataclasses"},
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


def test_list_of_dataclasses_defaults():
    parser = DataclassArgParser(OuterWithList)
    result = parser.parse([])
    cfg = result["OuterWithList"]
    assert isinstance(cfg.inners, list)
    assert len(cfg.inners) == 2
    assert isinstance(cfg.inners[0], Inner)
    assert isinstance(cfg.inners[1], Inner)
    assert cfg.inners[0].x == 1
    assert cfg.inners[0].y == "foo"
    assert cfg.inners[1].x == 2
    assert cfg.inners[1].y == "bar"
    assert cfg.z == 3.14


# Note: CLI parsing for list of dataclasses is not supported by the parser, but config file loading is.
def test_list_of_dataclasses_from_config(tmp_path):
    config = {
        "OuterWithList": {
            "inners": [
                {"x": 10, "y": "a"},
                {"x": 20, "y": "b"},
            ],
            "z": 9.99,
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    parser = DataclassArgParser(OuterWithList)
    result = parser.parse(["--config", str(config_path)])
    cfg = result["OuterWithList"]
    assert len(cfg.inners) == 2
    assert isinstance(cfg.inners[0], Inner)
    assert isinstance(cfg.inners[1], Inner)
    assert cfg.inners[0].x == 10
    assert cfg.inners[0].y == "a"
    assert cfg.inners[1].x == 20
    assert cfg.inners[1].y == "b"
    assert cfg.z == 9.99


def test_tuple_of_dataclasses_defaults():
    parser = DataclassArgParser(OuterWithTuple)
    result = parser.parse([])
    cfg = result["OuterWithTuple"]
    assert isinstance(cfg.pair, tuple)
    assert len(cfg.pair) == 2
    assert isinstance(cfg.pair[0], Inner)
    assert isinstance(cfg.pair[1], Inner)
    assert cfg.pair[0].x == 1
    assert cfg.pair[0].y == "foo"
    assert cfg.pair[1].x == 2
    assert cfg.pair[1].y == "bar"
    assert cfg.z == 3.14


# Note: CLI parsing for tuple of dataclasses is not supported by the parser, but config file loading is.
def test_tuple_of_dataclasses_from_config(tmp_path):
    config = {
        "OuterWithTuple": {
            "pair": [{"x": 10, "y": "a"}, {"x": 20, "y": "b"}],
            "z": 9.99,
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    parser = DataclassArgParser(OuterWithTuple)
    result = parser.parse(["--config", str(config_path)])
    cfg = result["OuterWithTuple"]
    assert isinstance(cfg.pair, tuple)
    assert isinstance(cfg.pair[0], Inner)
    assert isinstance(cfg.pair[1], Inner)
    assert len(cfg.pair) == 2
    assert cfg.pair[0].x == 10
    assert cfg.pair[0].y == "a"
    assert cfg.pair[1].x == 20
    assert cfg.pair[1].y == "b"
    assert cfg.z == 9.99
