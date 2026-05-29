from dataclasses import dataclass, field
from enum import Enum
from itertools import chain
from typing import Generic, Self, TypeVar, override
from collections.abc import Generator, Iterable

from tulip.string import rto


class Signal(Enum):
    NO_CHANGE = object()


# Text


NO_STYLE = ""


@dataclass(slots=True)
class Span:
    value: str
    style: str = NO_STYLE
    indent: int = 0


type TextLike = Text | str


class Text:
    def __init__(self, *parts: TextLike, style: str = NO_STYLE) -> None:
        self.set_spans(
            span
            for value in parts
            for span in (
                (Span(value, style),) if isinstance(value, str) else value._spans
            )
        )

    def set_spans(self, spans: Iterable[Span]) -> None:
        self._spans: list[Span] = list(spans)
        self._len: int = sum(len(span.value) for span in self._spans)

    def spans(self) -> list[Span]:
        return self._spans

    @classmethod
    def ass(cls, parts: "Iterable[Text]") -> "Text":
        result = cls()
        result.set_spans(span for part in parts for span in part._spans)
        return result

    def __len__(self) -> int:
        return self._len

    def __add__(self, other: "Text | str", /) -> "Text":
        result = Text()
        result.set_spans(
            chain(self._spans, other._spans)
            if isinstance(other, Text)
            else chain(self._spans, (Span(other),))
        )
        return result


# Components


type ComponentYieldT[R] = Component[R] | Signal | TextLike | None
type ComponentGen[R] = Generator[ComponentYieldT[R], str, R]

R_co = TypeVar("R_co", covariant=True)


@dataclass(slots=True)
class Component(Generic[R_co]):
    stateless: bool
    debug_name: str
    gen: ComponentGen[R_co]
    cache: "CompNode[R_co] | None" = None


@dataclass(slots=True)
class CompNode[R]:
    comp: Component[R] | Text
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

            elif comp.stateless:
                result += f"({comp.debug_name})"
            else:
                result += f"<{comp.debug_name}>"

            stack.extend((child, depth + 1) for child in reversed(curr.children))

        return result
