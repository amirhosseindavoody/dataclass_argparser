import dataclasses
import pytest
from dataclass_argparser.parser import DataclassArgParser


@dataclasses.dataclass
class TupleConfig:
    coords: tuple[int, int, int] = dataclasses.field(
        default=(1, 2, 3), metadata={"help": "A tuple of three integers"}
    )
    pair: tuple[str, float] = dataclasses.field(
        default=("x", 1.5), metadata={"help": "A tuple of string and float"}
    )


def test_tuple_int_parsing():
    parser = DataclassArgParser(TupleConfig)
    # Test default
    result = parser.parse([])
    cfg = result["TupleConfig"]
    assert cfg.coords == (1, 2, 3)
    assert cfg.pair == ("x", 1.5)
    # Test CLI override
    result = parser.parse(["--TupleConfig.coords", "4,5,6"])
    cfg = result["TupleConfig"]
    assert cfg.coords == (4, 5, 6)
    # Test with parentheses
    result = parser.parse(["--TupleConfig.coords", "(7,8,9)"])
    cfg = result["TupleConfig"]
    assert cfg.coords == (7, 8, 9)
    # Test string/float tuple
    result = parser.parse(["--TupleConfig.pair", "foo,2.5"])
    cfg = result["TupleConfig"]
    assert cfg.pair == ("foo", 2.5)
    # Test with parentheses
    result = parser.parse(["--TupleConfig.pair", "(bar,3.14)"])
    cfg = result["TupleConfig"]
    assert cfg.pair == ("bar", 3.14)


@pytest.mark.parametrize(
    "cli,expected",
    [
        (["--TupleConfig.coords", "10,20,30"], (10, 20, 30)),
        (["--TupleConfig.coords", "(100,200,300)"], (100, 200, 300)),
        (["--TupleConfig.pair", "hello,4.2"], ("hello", 4.2)),
        (["--TupleConfig.pair", "(abc,5.5)"], ("abc", 5.5)),
    ],
)
def test_tuple_cli_variants(cli, expected):
    parser = DataclassArgParser(TupleConfig)
    if "coords" in cli[0]:
        cfg = parser.parse(cli)["TupleConfig"]
        assert cfg.coords == expected
    else:
        cfg = parser.parse(cli)["TupleConfig"]
        assert cfg.pair == expected


def test_tuple_length_validation():
    """Test that tuples with incorrect length are rejected."""
    parser = DataclassArgParser(TupleConfig)

    # Test coords tuple with wrong length (needs 3, but giving 2)
    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.coords", "1,2"])

    # Test coords tuple with wrong length (needs 3, but giving 4)
    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.coords", "1,2,3,4"])

    # Test pair tuple with wrong length (needs 2, but giving 1)
    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.pair", "hello"])

    # Test pair tuple with wrong length (needs 2, but giving 3)
    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.pair", "hello,1.5,extra"])


def test_tuple_type_validation():
    """Test that tuples with incorrect types are rejected."""
    parser = DataclassArgParser(TupleConfig)

    # Test coords tuple with invalid int types (string instead of int)
    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.coords", "abc,2,3"])

    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.coords", "1,def,3"])

    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.coords", "1,2,xyz"])

    # Test pair tuple with invalid float type (string that can't be converted to float)
    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.pair", "hello,notafloat"])

    # Test pair tuple with invalid types (string where float expected)
    with pytest.raises(SystemExit):
        parser.parse(["--TupleConfig.pair", "validstring,invalidfloat"])


def test_tuple_type_coercion():
    """Test that valid type coercions work correctly."""
    parser = DataclassArgParser(TupleConfig)

    # Test that float strings can be converted to int (1.5 -> 1)
    # This is valid Python behavior: int(1.5) == 1
    result = parser.parse(["--TupleConfig.coords", "1.5,2,3"])
    cfg = result["TupleConfig"]
    assert cfg.coords == (1, 2, 3)  # 1.5 gets truncated to 1

    # Test that int strings can be converted to float
    result = parser.parse(["--TupleConfig.pair", "hello,42"])
    cfg = result["TupleConfig"]
    assert cfg.pair == ("hello", 42.0)  # 42 gets converted to 42.0
