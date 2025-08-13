import dataclasses
import pytest
from dataclass_argparser.parser import DataclassArgParser


@dataclasses.dataclass
class ListConfig:
    numbers: list[int] = dataclasses.field(
        default_factory=lambda: [1, 2, 3], metadata={"help": "A list of integers"}
    )
    names: list[str] = dataclasses.field(
        default_factory=lambda: ["a", "b"], metadata={"help": "A list of strings"}
    )


def test_list_int_parsing():
    parser = DataclassArgParser(ListConfig)
    # Test default
    result = parser.parse([])
    cfg = result["ListConfig"]
    assert cfg.numbers == [1, 2, 3]
    assert cfg.names == ["a", "b"]
    # Test CLI override
    result = parser.parse(["--ListConfig.numbers", "4,5,6"])
    cfg = result["ListConfig"]
    assert cfg.numbers == [4, 5, 6]
    # Test with brackets
    result = parser.parse(["--ListConfig.numbers", "[7,8,9]"])
    cfg = result["ListConfig"]
    assert cfg.numbers == [7, 8, 9]
    # Test string list
    result = parser.parse(["--ListConfig.names", "x,y,z"])
    cfg = result["ListConfig"]
    assert cfg.names == ["x", "y", "z"]
    # Test with brackets
    result = parser.parse(["--ListConfig.names", "[foo,bar]"])
    cfg = result["ListConfig"]
    assert cfg.names == ["foo", "bar"]


@pytest.mark.parametrize(
    "cli,expected",
    [
        (["--ListConfig.numbers", "10,20,30"], [10, 20, 30]),
        (["--ListConfig.numbers", "[100,200]"], [100, 200]),
        (["--ListConfig.names", "hello,world"], ["hello", "world"]),
        (["--ListConfig.names", "[abc,def]"], ["abc", "def"]),
    ],
)
def test_list_cli_variants(cli, expected):
    parser = DataclassArgParser(ListConfig)
    if "numbers" in cli[0]:
        cfg = parser.parse(cli)["ListConfig"]
        assert cfg.numbers == expected
    else:
        cfg = parser.parse(cli)["ListConfig"]
        assert cfg.names == expected
