from enum import IntEnum
from typing import (
    Any,
    Callable,
    Literal,
    Protocol,
    Self,
    Sized,
    cast,
    no_type_check,
    overload,
)


class SStringType[S, T, R](Protocol):
    def __add__(self, value: T, /) -> R: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: slice, /) -> S: ...


class StringType[T, R](Protocol):
    def __add__(self, value: T, /) -> R: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: slice, /) -> Self: ...


DEFAULT_OVERFLOW_LEN = 80
DEFAULT_OVERFLOW_CHAR = "…"


def rto[S, T: Sized, R](
    value: SStringType[S, T, R],
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    ochar: T = DEFAULT_OVERFLOW_CHAR,
    measure: Callable[[T | SStringType[S, T, R]], int] = len,
) -> S | R:
    """Truncates `value` to `olen` characters.

    If `value` is truncated, `ochar` replaces the end of the result.

    Args:
        value: The value to truncate.
        olen: Maximum length of the returned `value`.
        ochar: The overflow indicator.
        measure: Optional measuring function for the length `value` and `ochar`.

    Returns:
        A string, at most `olen` characters in length.
    """

    tlen = measure(value)
    if tlen > olen:
        return (
            cast(SStringType[S, T, R], value[: max(0, olen - measure(ochar))]) + ochar
        )

    return cast(S, value)


def lto[T: StringType[Any, Any], R](
    value: T,
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    ochar: StringType[T, R] = DEFAULT_OVERFLOW_CHAR,
    measure: Callable[[T | StringType[T, R]], int] = len,
) -> T | R:
    """Truncates `value` to `olen` characters from the left.

    If `value` is truncated, `ochar` replaces the beginning of the result.

    Args:
        value: The value to truncate.
        olen: Maximum length of the returned `value`.
        ochar: The overflow indicator.
        measure: Optional measuring function for the length `value` and `ochar`.

    Returns:
        A string, at most `olen` characters in length.
    """

    tlen = measure(value)
    if tlen > olen:
        start = measure(ochar) - olen
        return ochar + value[start if start < 0 else tlen :]

    return value


class JustifyFiller[R](Protocol):
    def __mul__(self, value: int, /) -> R: ...


def ljust[T, R](
    text: StringType[T, R],
    width: int,
    *,
    fill: JustifyFiller[T] = " ",
    measure: Callable[[StringType[T, R]], int] = len,
) -> R:
    """Returns text padded to the right, such that its width equals `width`.

    If `text` exceeds `width`, this is a no-op.

    IMPORTANT: `fill` is NOT measured, and is instead assumed to be unitary in length.

    Args:
        text: The text to justify.
        width: The target width.
        fill: The character (or string) to fill empty space with.
        measure: Optional measuring function for the length of `text`.

    Returns:
        A string, at least `width` in length.
    """
    return text + fill * max(0, width - measure(text))


def cjust[T, L, R, U](
    text: T,
    width: int,
    *,
    lfill: JustifyFiller[StringType[T, StringType[R, U]]] = " ",
    rfill: JustifyFiller[R] = " ",
    measure: Callable[[T], int] = len,
) -> U:
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
        measure: Optional measuring function for the length of `text`.

    Returns:
        A string, at least `width` in length.
    """
    rem = width - measure(text)
    lwidth = max(0, rem // 2)
    rwidth = max(0, rem - lwidth)
    return (lfill * lwidth) + text + (rfill * rwidth)


def rjust[T, R](
    value: T,
    width: int,
    *,
    fill: JustifyFiller[StringType[T, R]] = " ",
    measure: Callable[[T], int] = len,
) -> R:
    """Returns text padded to the left, such that its width equals `width`.

    If `text` exceeds `width`, this is a no-op.

    IMPORTANT: `fill` is NOT measured, and is instead assumed to be unitary in length.

    Args:
        text: The text to justify.
        width: The target width.
        fill: The character (or string) to fill empty space with.
        measure: Optional measuring function for the length of `text`.

    Returns:
        A string, at least `width` in length.
    """
    return (fill * max(0, width - measure(value))) + value


class Justify(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


@overload
def just[T, R](
    text: StringType[T, R],
    width: int,
    mode: Literal[Justify.LEFT],
    *,
    rfill: JustifyFiller[T] = ...,
    measure: Callable[[StringType[T, R]], int] = len,
) -> R: ...


@overload
def just[T, R, U](
    text: T,
    width: int,
    mode: Literal[Justify.CENTER],
    *,
    lfill: JustifyFiller[StringType[T, StringType[R, U]]] = " ",
    rfill: JustifyFiller[R] = ...,
    measure: Callable[[T], int] = ...,
) -> U: ...


@overload
def just[T, R](
    text: T,
    width: int,
    mode: Literal[Justify.RIGHT],
    *,
    lfill: JustifyFiller[StringType[T, R]] = " ",
    measure: Callable[[T], int] = ...,
) -> R: ...


@overload
def just[T, R, U](
    text: T | StringType[T, R],
    width: int,
    mode: Justify,
    *,
    lfill: JustifyFiller[StringType[T, R]]
    | JustifyFiller[StringType[T, StringType[R, U]]] = ...,
    rfill: JustifyFiller[T] | JustifyFiller[R] = ...,
    measure: Callable[[T], int] | Callable[[StringType[T, R]], int] = ...,
) -> R | U: ...


@no_type_check
def just(
    text: Any,
    width: int,
    mode: Justify,
    *,
    lfill: Any = " ",
    rfill: Any = " ",
    measure: Callable[[Any], int] = len,
) -> Any:
    """`ljust`, `cjust` and `rjust` selector function on `mode`.

    Args:
        text: The value to justify.
        width: The minimum width of the resultant text.
        mode: What direction to justify `text`.
        lfill: The character (or string) to fill empty space on the left.
        rfill: The character (or string) to fill empty space on the right.
        measure: Optional measuring function for the length of `text`.

    Returns:
        A string, at least `width` in length.
    """
    match mode:
        case Justify.LEFT:
            return ljust(text, width, fill=lfill, measure=measure)
        case Justify.CENTER:
            return cjust(text, width, lfill=lfill, rfill=rfill, measure=measure)
        case Justify.RIGHT:
            return rjust(text, width, fill=rfill, measure=measure)
