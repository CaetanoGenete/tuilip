from __future__ import annotations

from enum import IntEnum
from typing import (
    TYPE_CHECKING,
    overload,
)

from tuilip.render.text import Text

if TYPE_CHECKING:
    pass


DEFAULT_OVERFLOW_LEN = 80
DEFAULT_OVERFLOW_CHAR = "…"


@overload
def rto(
    value: str,
    olen: int = ...,
    *,
    ochar: str = ...,
) -> str: ...


@overload
def rto(
    value: str,
    olen: int = ...,
    *,
    ochar: Text,
) -> str | Text: ...


@overload
def rto(
    value: Text,
    olen: int = ...,
    *,
    ochar: str | Text = ...,
) -> Text: ...


def rto(
    value: str | Text,
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    ochar: str | Text = DEFAULT_OVERFLOW_CHAR,
) -> str | Text:
    """Truncates `value` to `olen` characters.

    If `value` is truncated, `ochar` replaces the end of the result.

    Args:
        value: The value to truncate.
        olen: Maximum length of the returned `value`.
        ochar: The overflow indicator.

    Returns:
        A string, at most `olen` characters in length.
    """

    tlen = len(value)
    if tlen > olen:
        return value[: max(0, olen - len(ochar))] + ochar

    return value


@overload
def lto(
    value: str,
    olen: int = ...,
    *,
    ochar: str = ...,
) -> str: ...


@overload
def lto(
    value: str,
    olen: int = ...,
    *,
    ochar: Text,
) -> str | Text: ...


@overload
def lto(
    value: Text,
    olen: int = ...,
    *,
    ochar: str | Text = ...,
) -> Text: ...


def lto(
    value: str | Text,
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    ochar: str | Text = DEFAULT_OVERFLOW_CHAR,
) -> str | Text:
    """Truncates `value` to `olen` characters from the left.

    If `value` is truncated, `ochar` replaces the beginning of the result.

    Args:
        value: The value to truncate.
        olen: Maximum length of the returned `value`.
        ochar: The overflow indicator.

    Returns:
        A string, at most `olen` characters in length.
    """

    tlen = len(value)
    if tlen > olen:
        start = len(ochar) - olen
        return ochar + value[start if start < 0 else tlen :]

    return value


@overload
def ljust(
    text: str,
    width: int,
    *,
    fill: str = ...,
) -> str: ...


@overload
def ljust(
    text: Text,
    width: int,
    *,
    fill: str | Text,
) -> Text: ...


@overload
def ljust(
    text: str | Text,
    width: int,
    *,
    fill: Text,
) -> Text: ...


def ljust(
    text: str | Text,
    width: int,
    *,
    fill: str | Text = " ",
) -> str | Text:
    """Returns text padded to the right, such that its width equals `width`.

    If `text` exceeds `width`, this is a no-op.

    IMPORTANT: `fill` is NOT measured, and is instead assumed to be unitary in length.

    Args:
        text: The text to justify.
        width: The target width.
        fill: The character (or string) to fill empty space with.

    Returns:
        A string, at least `width` in length.
    """
    return text + fill * max(0, width - len(text))


@overload
def cjust(
    text: str,
    width: int,
    *,
    lfill: str = ...,
    rfill: str = ...,
) -> str: ...


@overload
def cjust(
    text: Text,
    width: int,
    *,
    lfill: str | Text = ...,
    rfill: str | Text = ...,
) -> Text: ...


@overload
def cjust(
    text: str | Text,
    width: int,
    *,
    lfill: Text,
    rfill: str | Text = ...,
) -> Text: ...


@overload
def cjust(
    text: str | Text,
    width: int,
    *,
    lfill: str | Text = ...,
    rfill: Text,
) -> Text: ...


def cjust(
    text: str | Text,
    width: int,
    *,
    lfill: str | Text = " ",
    rfill: str | Text = " ",
) -> str | Text:
    """Returns text padded, such that its width equals `width` and is positioned
    centrally.

    If `text` exceeds `width`, this is a no-op.

    IMPORTANT: `lfill` and `rfill` are NOT measured, and are instead assumed to be
    unitary in length.

    Args:
        text: The text to justify.
        width: The target width.
        lfill: The character (or string) to fill empty space to the left.
        rfill: The character (or string) to fill empty space to the right.

    Returns:
        A string, at least `width` in length.
    """
    rem = width - len(text)
    lwidth = max(0, rem // 2)
    rwidth = max(0, rem - lwidth)
    return (lfill * lwidth) + text + (rfill * rwidth)


@overload
def rjust(
    value: str,
    width: int,
    *,
    fill: str = ...,
) -> str: ...


@overload
def rjust(
    value: Text,
    width: int,
    *,
    fill: str | Text,
) -> Text: ...


@overload
def rjust(
    value: str | Text,
    width: int,
    *,
    fill: Text,
) -> Text: ...


def rjust(
    value: str | Text,
    width: int,
    *,
    fill: str | Text = " ",
) -> str | Text:
    """Returns text padded to the left, such that its width equals `width`.

    If `text` exceeds `width`, this is a no-op.

    IMPORTANT: `fill` is NOT measured, and is instead assumed to be unitary in length.

    Args:
        text: The text to justify.
        width: The target width.
        fill: The character (or string) to fill empty space with.

    Returns:
        A string, at least `width` in length.
    """
    return (fill * max(0, width - len(value))) + value


class Justify(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


def just(
    text: str | Text,
    width: int,
    mode: Justify,
    *,
    lfill: str | Text = " ",
    rfill: str | Text = " ",
) -> str | Text:
    """`ljust`, `cjust` and `rjust` selector function on `mode`.

    Args:
        text: The value to justify.
        width: The minimum width of the resultant text.
        mode: What direction to justify `text`.
        lfill: The character (or string) to fill empty space on the left.
        rfill: The character (or string) to fill empty space on the right.

    Returns:
        A string, at least `width` in length.
    """
    match mode:
        case Justify.LEFT:
            return ljust(text, width, fill=lfill)
        case Justify.CENTER:
            return cjust(text, width, lfill=lfill, rfill=rfill)
        case Justify.RIGHT:
            return rjust(text, width, fill=rfill)
