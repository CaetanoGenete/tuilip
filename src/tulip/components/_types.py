from dataclasses import dataclass, field
from tulip.math import divup
from enum import IntEnum
from typing import Generic, Self, TypeVar, override
from collections.abc import Generator

from tulip.text import rto


class Signal(IntEnum):
    NOCHANGE = 1
    NOPROP = 2
    PROP = 3


def flip_slice(s: slice, seq_len: int) -> slice:
    start, stop, step = s.indices(seq_len)

    nsteps = divup(abs(stop - start), abs(step))
    rstop = start - step

    return slice(
        start + (nsteps - 1) * step,
        None if (step > 0 and rstop < 0) else rstop,
        -step,
    )


# Text

NO_STYLE = ""


@dataclass(slots=True)
class Span:
    value: str
    style: str
    indent: int


type TextLike = Text | str


class Text:
    __slots__: tuple[str, ...] = "_spans", "_len"

    def __init__(
        self,
        *parts: TextLike,
        style: str = NO_STYLE,
        indent: int = 0,
    ) -> None:
        self._spans: list[Span] = []
        self._len: int = 0

        for value in parts:
            self.__append(value, style=style, indent=indent)

    def __append(
        self,
        other: TextLike,
        *,
        style: str = NO_STYLE,
        indent: int = 0,
    ) -> None:
        if isinstance(other, Text):
            self._spans.extend(other._spans)
        else:
            self._spans.append(Span(other, style=style, indent=indent))

        self._len += len(other)

    def __iadd__(self, other: TextLike, /) -> Self:
        self.__append(other)
        return self

    def __add__(self, other: TextLike, /) -> "Text":
        result = Text()

        result._spans.extend(self._spans)
        result._len = self._len
        result += other

        return result

    def __radd__(self, other: str, /) -> "Text":
        result = Text()

        result += other
        result += self

        return result

    def spans(self) -> list[Span]:
        """Returns the underlying splan objects.

        IMPORTANT: avoid mutating span lenghts as __len__ is cached!
        """
        return self._spans

    @override
    def __str__(self) -> str:
        return "".join(span.value for span in self._spans)

    def __len__(self) -> int:
        return self._len

    def __getitem__(self, ts: "slice[int | None, int | None, int | None]") -> "Text":
        result = Text()

        step = 1 if ts.step is None else ts.step
        # Note: Handling reverse iteration by doing three flips:
        # 1. Flip slip
        # 2. Flip span texts
        # 3. Flip result span order
        if step < 0:
            ts = flip_slice(ts, self._len)

        absstep = abs(step)
        start = 0 if ts.start is None else ts.start
        stop = self._len if ts.stop is None else ts.stop

        for span in self._spans:
            if stop <= start:
                break

            spanlen = len(span.value)
            if start < spanlen:
                ss = slice(start, stop, absstep)
                result._spans.append(
                    Span(
                        substr := span.value[
                            ss if step > 0 else flip_slice(ss, spanlen)
                        ],
                        style=span.style,
                        indent=span.indent,
                    )
                )
                result._len += len(substr)

                start += divup(spanlen - start, absstep) * absstep

            stop -= spanlen
            start -= spanlen

        if step < 0:
            result._spans.reverse()

        return result


# Components


type Renderable[R] = Component[R] | TextLike
type _ComponentYieldT[R] = Renderable[R] | Signal | None
type ComponentGen[R] = Generator[_ComponentYieldT[R], str, R]


R_co = TypeVar("R_co", covariant=True)


@dataclass(slots=True)
class Component(Generic[R_co]):
    stateless: bool
    debug_name: str
    gen: ComponentGen[R_co]
    indent: int = 0
    cache: "CompNode[R_co] | None" = None


@dataclass(slots=True)
class CompNode[R]:
    comp: Component[R] | Text
    propkey: bool = True
    children: list[Self] = field(default_factory=list)

    @override
    def __str__(self) -> str:
        result = ""

        stack: list[tuple[CompNode[R], int]] = [(self, 0)]
        while stack:
            curr, depth = stack.pop()
            comp = curr.comp

            if depth > 0:
                result += "\n"

            result += " " * (depth * 2)
            if isinstance(comp, Text):
                raw = "".join(x.value for x in comp.spans())
                result += f'"{rto(raw.replace("\n", r"\n").replace('"', r"\""))}"'
                continue

            debug_name = f"{comp.debug_name}"
            if not curr.propkey:
                debug_name += " noprop"

            if comp.indent > 0:
                debug_name += f" indent={comp.indent}"

            if comp.stateless:
                result += f"[{debug_name}]"
            else:
                result += f"<{debug_name}>"

            stack.extend((child, depth + 1) for child in reversed(curr.children))

        return result
