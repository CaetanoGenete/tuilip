from dataclasses import dataclass
from typing import Any, Literal, assert_type

import pytest
from rich.text import Text as RichText

from tulip.string import lto, rto
from tulip.render.types import Text


@dataclass
class _OTestCase[T]:
    value: T
    olen: int
    ochar: str
    expected: T


@pytest.mark.parametrize(
    "test_case",
    [
        _OTestCase(
            value="abcdefg",
            olen=4,
            ochar="!",
            expected="abc!",
        ),
        _OTestCase(
            value="abcd",
            olen=3,
            ochar="!",
            expected="ab!",
        ),
        _OTestCase(
            value="abcd",
            olen=4,
            ochar="!",
            expected="abcd",
        ),
        _OTestCase(
            value="abc",
            olen=4,
            ochar="!",
            expected="abc",
        ),
        _OTestCase(
            value="",
            olen=4,
            ochar="!",
            expected="",
        ),
        _OTestCase(
            value="abcde",
            olen=4,
            ochar="...",
            expected="a...",
        ),
        _OTestCase(
            value="abcde",
            olen=3,
            ochar="...",
            expected="...",
        ),
        _OTestCase(
            value="abcde",
            olen=2,
            ochar="...",
            expected="...",
        ),
    ],
)
def test_rto(test_case: _OTestCase[Any]) -> None:
    actual = rto(
        test_case.value,
        test_case.olen,
        ochar=test_case.ochar,
    )

    assert actual == test_case.expected


@pytest.mark.parametrize(
    "test_case",
    [
        _OTestCase(
            value="abcdefg",
            olen=4,
            ochar="!",
            expected="!efg",
        ),
        _OTestCase(
            value="abcd",
            olen=3,
            ochar="!",
            expected="!cd",
        ),
        _OTestCase(
            value="abcd",
            olen=4,
            ochar="!",
            expected="abcd",
        ),
        _OTestCase(
            value="abc",
            olen=4,
            ochar="!",
            expected="abc",
        ),
        _OTestCase(
            value="",
            olen=4,
            ochar="!",
            expected="",
        ),
        _OTestCase(
            value="abcde",
            olen=4,
            ochar="...",
            expected="...e",
        ),
        _OTestCase(
            value="abcde",
            olen=3,
            ochar="...",
            expected="...",
        ),
        _OTestCase(
            value="abcde",
            olen=2,
            ochar="...",
            expected="...",
        ),
    ],
)
def test_lto(test_case: _OTestCase[Any]) -> None:
    actual = lto(
        test_case.value,
        test_case.olen,
        ochar=test_case.ochar,
    )

    assert actual == test_case.expected


# str type checks

_ = assert_type(lto("value"), str)

# Rich type checks

_ = assert_type(lto(RichText("value"), ochar=RichText("..")), RichText)
_ = assert_type(lto("value", ochar=RichText("")), Literal["value"] | RichText)
_ = assert_type(rto(RichText("value"), ochar=RichText("..")), RichText)
_ = assert_type(rto(RichText("value")), RichText)

# Tulip type checks

_ = assert_type(lto(Text("value"), ochar=Text("..")), Text)
_ = assert_type(lto("value", ochar=Text("")), Literal["value"] | Text)
_ = assert_type(rto(Text("value"), ochar=Text("..")), Text)
_ = assert_type(rto(Text("value")), Text)
