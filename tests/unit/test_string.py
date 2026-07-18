from dataclasses import dataclass
from typing import assert_type

import pytest

from tuilip.render.text import Text
from tuilip.string import cjust, lto, rto


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
def test_rto(test_case: _OTestCase[str]) -> None:
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
def test_lto(test_case: _OTestCase[str | Text]) -> None:
    actual = lto(
        test_case.value,
        test_case.olen,
        ochar=test_case.ochar,
    )

    assert actual == test_case.expected


# str type checks

assert_type(lto("value"), str)
assert_type(lto("value", ochar=".."), str)

# Tulip type checks

assert_type(lto(Text("value"), ochar=Text("..")), Text)
assert_type(lto("value", ochar=Text("")), str | Text)
assert_type(lto(Text("value"), ochar=" "), Text)
assert_type(lto(Text("value")), Text)

assert_type(rto(Text("value"), ochar=Text("..")), Text)
assert_type(rto("value", ochar=Text("..")), str | Text)
assert_type(rto(Text("value"), ochar=" "), Text)
assert_type(rto(Text("value")), Text)

assert_type(cjust(Text("value"), 10, lfill=Text(".."), rfill=Text("..")), Text)
assert_type(cjust(Text("value"), 10, lfill=Text(".."), rfill=".."), Text)
assert_type(cjust(Text("value"), 10, lfill="..", rfill=Text("..")), Text)
assert_type(cjust(Text("value"), 10, lfill="..", rfill=".."), Text)
assert_type(cjust("value", 10, lfill=Text(".."), rfill=Text("..")), Text)
assert_type(cjust("value", 10, lfill=Text(".."), rfill=".."), Text)
assert_type(cjust("value", 10, lfill="..", rfill=Text("..")), Text)
assert_type(cjust("value", 10, lfill="..", rfill=".."), str)
