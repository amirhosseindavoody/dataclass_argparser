#!/usr/bin/env python3
"""
Tests for nested Pydantic model support in DataclassArgParser.

Mirrors ../test_nested_types.py for Pydantic BaseModel definitions.
"""

import json

from pydantic import BaseModel, Field

from dataclass_argparser.parser import DataclassArgParser


class InnerWithNoDefaults(BaseModel):
    a: int
    b: int


class OuterWithFactory(BaseModel):
    inner: InnerWithNoDefaults = Field(
        default_factory=lambda: InnerWithNoDefaults(a=1, b=2)
    )


def test_outer_with_default_factory_and_inner_no_defaults():
    parser = DataclassArgParser(OuterWithFactory)
    result = parser.parse([])
    cfg = result["OuterWithFactory"]
    assert isinstance(cfg, OuterWithFactory)
    assert isinstance(cfg.inner, InnerWithNoDefaults)
    assert cfg.inner.a == 1
    assert cfg.inner.b == 2


def test_outer_with_default_factory_and_inner_no_defaults_from_config(tmp_path):
    """Nested model with default_factory loads correctly from config file."""
    config = {"OuterWithFactory": {"inner": {"a": 5, "b": 6}}}

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    parser = DataclassArgParser(OuterWithFactory)
    result = parser.parse(["--config", str(config_path)])
    cfg = result["OuterWithFactory"]
    assert isinstance(cfg, OuterWithFactory)
    assert isinstance(cfg.inner, InnerWithNoDefaults)
    assert cfg.inner.a == 5
    assert cfg.inner.b == 6


class Inner(BaseModel):
    x: int = Field(default=1, description="Inner x")
    y: str = Field(default="foo", description="Inner y")


class Outer(BaseModel):
    inner: Inner = Field(default_factory=Inner, description="Nested inner object")
    z: float = Field(default=3.14, description="Outer z")


class SecondaryOuter(BaseModel):
    outer: Outer = Field(default_factory=Outer, description="Outer model")
    label: str = Field(default="main", description="Secondary label")


class OuterWithList(BaseModel):
    inners: list[Inner] = Field(
        default_factory=lambda: [Inner(), Inner(x=2, y="bar")],
        description="List of Inner models",
    )
    z: float = Field(default=3.14, description="Outer z")


def test_nested_defaults():
    parser = DataclassArgParser(Outer)
    result = parser.parse([])
    cfg = result["Outer"]
    assert cfg.inner.x == 1
    assert cfg.inner.y == "foo"
    assert cfg.z == 3.14


def test_nested_cli_override():
    parser = DataclassArgParser(Outer)
    result = parser.parse(
        [
            "--Outer.inner.x",
            "42",
            "--Outer.inner.y",
            "hello",
        ]
    )
    cfg = result["Outer"]
    assert cfg.inner.x == 42
    assert cfg.inner.y == "hello"
    assert cfg.z == 3.14


def test_nested_from_config(tmp_path):
    config = {"Outer": {"inner": {"x": 10, "y": "bar"}, "z": 2.5}}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    parser = DataclassArgParser(Outer)
    result = parser.parse(["--config", str(config_path)])
    cfg = result["Outer"]
    assert cfg.inner.x == 10
    assert cfg.inner.y == "bar"
    assert cfg.z == 2.5


def test_deeply_nested_defaults():
    parser = DataclassArgParser(SecondaryOuter)
    result = parser.parse([])
    cfg = result["SecondaryOuter"]
    assert cfg.label == "main"
    assert cfg.outer.inner.x == 1
    assert cfg.outer.z == 3.14


def test_deeply_nested_cli_override():
    parser = DataclassArgParser(SecondaryOuter)
    result = parser.parse(
        [
            "--SecondaryOuter.outer.inner.x",
            "99",
            "--SecondaryOuter.label",
            "custom",
        ]
    )
    cfg = result["SecondaryOuter"]
    assert cfg.label == "custom"
    assert cfg.outer.inner.x == 99


def test_list_of_nested_from_config(tmp_path):
    config = {
        "OuterWithList": {
            "inners": [{"x": 3, "y": "a"}, {"x": 4, "y": "b"}],
            "z": 1.0,
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    parser = DataclassArgParser(OuterWithList)
    result = parser.parse(["--config", str(config_path)])
    cfg = result["OuterWithList"]
    assert len(cfg.inners) == 2
    assert cfg.inners[0].x == 3
    assert cfg.inners[1].y == "b"
