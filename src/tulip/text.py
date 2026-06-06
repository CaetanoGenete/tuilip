from typing import Any, Callable, Protocol, Self, Sized, cast


class SStringType[S, T, R](Protocol):
    def __add__(self, value: T, /) -> R: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: slice, /) -> S: ...


DEFAULT_OVERFLOW_LEN = 80


def rto[S, T: Sized, R](
    value: SStringType[S, T, R],
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    ochar: T = "...",
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
        return cast(SStringType[S, T, R], value[: olen - measure(ochar)]) + ochar

    return cast(S, value)


class StringType[T, R](Protocol):
    def __add__(self, value: T, /) -> R: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: slice, /) -> Self: ...


def lto[T: StringType[Any, Any], R](
    value: T,
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    ochar: StringType[T, R] = "...",
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
        return ochar + value[olen - measure(ochar) :]

    return value
