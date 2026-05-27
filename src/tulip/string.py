from typing import Any, Callable, Protocol, Self, overload

DEFAULT_OVERFLOW_LEN = 80


class StringType(Protocol):
    def __add__(self, value: Self | str, /) -> Self: ...

    def __len__(self) -> int: ...

    def __getitem__(self, index: slice, /) -> Self: ...


@overload
def rto[T: StringType](
    value: T,
    olen: int = ...,
    *,
    suffix: T | None = ...,
    ochar: T,
    measure: Callable[[T], int] = len,
) -> T: ...


@overload
def rto[T: StringType](
    value: T,
    olen: int = ...,
    *,
    suffix: T | None = ...,
    ochar: str = ...,
    measure: Callable[[T | str], int] = len,
) -> T: ...


def rto[T: StringType](
    value: T,
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    suffix: T | None = None,
    ochar: T | str = "…",
    measure: Callable[[Any], int] = len,
) -> T:
    tlen = measure(value)
    if suffix is not None:
        tlen += measure(suffix)

    if tlen > olen:
        value = value[: olen - measure(ochar)] + ochar

    if suffix is None:
        return value
    return value + suffix


def lto[T: StringType](
    value: T,
    olen: int = DEFAULT_OVERFLOW_LEN,
    *,
    ochar: T,
    prefix: T | None = None,
    measure: Callable[[T], int] = len,
) -> T:
    tlen = measure(value)
    if prefix is not None:
        tlen += measure(prefix)

    if tlen > olen:
        value = value[measure(ochar) - olen :]

    if prefix is None:
        return ochar + value
    return prefix + ochar + value
