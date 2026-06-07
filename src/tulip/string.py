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
        A string no more than `olen` characters in length.
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
        A string no more than `olen` characters in length.
    """

    tlen = measure(value)
    if tlen > olen:
        start = measure(ochar) - olen
        return ochar + value[start if start < 0 else tlen :]

    return value


class JustifyFiller[R](Protocol):
    def __mul__(self, value: int, /) -> R: ...


def ljust[T, R](
    value: StringType[T, R],
    width: int,
    *,
    fill: JustifyFiller[T] = " ",
    measure: Callable[[StringType[T, R]], int] = len,
) -> R:
    return value + fill * max(0, width - measure(value))


def cjust[T, L, R, U](
    value: T,
    width: int,
    *,
    lfill: JustifyFiller[StringType[T, StringType[R, U]]] = " ",
    rfill: JustifyFiller[R] = " ",
    measure: Callable[[T], int] = len,
) -> U:
    cwidth = measure(value)
    lwidth = max(0, (width - cwidth) // 2)
    rwidth = max(0, width - cwidth - lwidth)
    return (lfill * lwidth) + value + (rfill * rwidth)


def rjust[T, R](
    value: T,
    width: int,
    *,
    fill: JustifyFiller[StringType[T, R]] = " ",
    measure: Callable[[T], int] = len,
) -> R:
    return (fill * max(0, width - measure(value))) + value


class Justify(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


@overload
def just[T, R](
    value: StringType[T, R],
    width: int,
    mode: Literal[Justify.LEFT],
    *,
    rfill: JustifyFiller[T] = ...,
    measure: Callable[[StringType[T, R]], int] = len,
) -> R: ...


@overload
def just[T, L, R, U](
    value: T,
    width: int,
    mode: Literal[Justify.CENTER],
    *,
    lfill: JustifyFiller[StringType[T, StringType[R, U]]] = " ",
    rfill: JustifyFiller[R] = ...,
    measure: Callable[[T], int] = ...,
) -> U: ...


@overload
def just[T, R](
    value: T,
    width: int,
    mode: Literal[Justify.RIGHT],
    *,
    lfill: JustifyFiller[StringType[T, R]] = " ",
    measure: Callable[[T], int] = ...,
) -> R: ...


@overload
def just[T, L, R, U](
    value: T | StringType[T, R],
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
    value: Any,
    width: int,
    mode: Justify,
    *,
    lfill: Any = " ",
    rfill: Any = " ",
    measure: Callable[[Any], int] = len,
) -> Any:
    """
    Dispatches to the correct justification method based on the Justify enum.
    """
    match mode:
        case Justify.LEFT:
            return ljust(value, width, fill=lfill, measure=measure)
        case Justify.CENTER:
            return cjust(value, width, lfill=lfill, rfill=rfill, measure=measure)
        case Justify.RIGHT:
            return rjust(value, width, fill=rfill, measure=measure)
