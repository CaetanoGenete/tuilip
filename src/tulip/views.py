from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from operator import itemgetter
from typing import Any, Callable, Literal, no_type_check, overload, override


@dataclass(slots=True)
class MapView[T, R](Sequence[R]):
    seq: Sequence[T]
    mapfn: Callable[[T], R]

    @overload
    def __getitem__(self, index: int) -> R: ...

    @overload
    def __getitem__(
        self, index: "slice[int | None, int | None, int | None]"
    ) -> "MapView[T, R]": ...

    @override
    def __getitem__(
        self,
        index: "int | slice[int | None, int | None, int | None]",
    ) -> "R | MapView[T, R]":
        if isinstance(index, int):
            return self.mapfn(self.seq[index])

        return MapView(self.seq[index], self.mapfn)

    @override
    def __len__(self) -> int:
        return len(self.seq)

    @override
    def __iter__(self) -> Iterator[R]:
        return map(self.mapfn, self.seq)

    @override
    def __reversed__(self) -> Iterator[R]:
        return map(self.mapfn, reversed(self.seq))


class ShelfView:
    @overload
    def __new__[T0, *Ts](
        cls, seq: Sequence[tuple[T0, *Ts]], index: Literal[0]
    ) -> MapView[T0, T0]: ...

    @overload
    def __new__[T0, T1, *Ts](
        cls, seq: Sequence[tuple[T0, T1, *Ts]], index: Literal[1]
    ) -> MapView[T1, T1]: ...

    @overload
    def __new__[T0, T1, T2, *Ts](
        cls, seq: Sequence[tuple[T0, T1, T2, *Ts]], index: Literal[2]
    ) -> MapView[T2, T2]: ...

    @overload
    def __new__[T0, T1, T2, T3, *Ts](
        cls, seq: Sequence[tuple[T0, T1, T2, T3, *Ts]], index: Literal[3]
    ) -> MapView[T3, T3]: ...

    @overload
    def __new__[T0, T1, T2, T3, T4, *Ts](
        cls, seq: Sequence[tuple[T0, T1, T2, T3, T4, *Ts]], index: Literal[4]
    ) -> MapView[T4, T4]: ...

    @overload
    def __new__[T0, T1, T2, T3, T4, T5, *Ts](
        cls, seq: Sequence[tuple[T0, T1, T2, T3, T4, T5, *Ts]], index: Literal[5]
    ) -> MapView[T5, T5]: ...

    @overload
    def __new__[T0, T1, T2, T3, T4, T5, T6, *Ts](
        cls, seq: Sequence[tuple[T0, T1, T2, T3, T4, T5, T6, *Ts]], index: Literal[6]
    ) -> MapView[T6, T6]: ...

    @overload
    def __new__[T](cls, seq: Sequence[Sequence[T]], index: int) -> MapView[T, T]: ...

    @no_type_check
    def __new__(cls, seq: Any, index: int) -> Sequence[Any]:
        return MapView(seq, itemgetter(index))


class LazySeq[T]:
    def __new__(cls, length: int, mapfn: Callable[[int], T]) -> MapView[int, T]:
        return MapView(range(length), mapfn)
