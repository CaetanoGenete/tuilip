from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from operator import itemgetter
from typing import Any, Callable, Literal, overload, override


@dataclass(slots=True)
class MapView[T, R](Sequence[R]):
    """Applies `mapfn` to every item in `seq` on-demand.

    Attributes:
        seq: The underlying Sequence object.
        mapfn: Mapping function.
    """

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


@overload
def ShelfView[T0, *Ts](
    seq: Sequence[tuple[T0, *Ts]], index: Literal[0]
) -> MapView[Any, T0]: ...


@overload
def ShelfView[T0, T1, *Ts](
    seq: Sequence[tuple[T0, T1, *Ts]], index: Literal[1]
) -> MapView[Any, T1]: ...


@overload
def ShelfView[T0, T1, T2, *Ts](
    seq: Sequence[tuple[T0, T1, T2, *Ts]], index: Literal[2]
) -> MapView[Any, T2]: ...


@overload
def ShelfView[T0, T1, T2, T3, *Ts](
    seq: Sequence[tuple[T0, T1, T2, T3, *Ts]], index: Literal[3]
) -> MapView[Any, T3]: ...


@overload
def ShelfView[T0, T1, T2, T3, T4, *Ts](
    seq: Sequence[tuple[T0, T1, T2, T3, T4, *Ts]], index: Literal[4]
) -> MapView[Any, T4]: ...


@overload
def ShelfView[T0, T1, T2, T3, T4, T5, *Ts](
    seq: Sequence[tuple[T0, T1, T2, T3, T4, T5, *Ts]], index: Literal[5]
) -> MapView[Any, T5]: ...


@overload
def ShelfView[T0, T1, T2, T3, T4, T5, T6, *Ts](
    seq: Sequence[tuple[T0, T1, T2, T3, T4, T5, T6, *Ts]], index: Literal[6]
) -> MapView[Any, T6]: ...


@overload
def ShelfView[T](seq: Sequence[Sequence[T]], index: int) -> MapView[Any, T]: ...


def ShelfView(seq: Any, index: int) -> Sequence[Any]:
    return MapView(seq, itemgetter(index))


def LazySeq[T](length: int, mapfn: Callable[[int], T]) -> MapView[int, T]:
    return MapView(range(length), mapfn)
