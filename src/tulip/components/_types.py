from dataclasses import dataclass, field
from enum import IntEnum
from typing import Generic, Self, TypeVar, override
from collections.abc import Generator, Iterable

from tulip.string import rto


class Signal(IntEnum):
    NOCHANGE = 1
    NOPROP = 2
    PROP = 3


# Text


NO_STYLE = ""


@dataclass(slots=True)
class Span:
    value: str
    style: str = NO_STYLE
    indent: int = 0


type TextLike = Text | str


class Text:
    __slots__: tuple[str, ...] = "_spans", "_len", "indent"

    def __init__(
        self,
        *parts: TextLike,
        style: str = NO_STYLE,
        indent: int = 0,
    ) -> None:
        self._spans: list[Span] = []
        self._len: int = 0
        self.indent: int = indent

        for value in parts:
            self += value

    def with_indent(self, indent: int) -> "Text":
        """Returns a view of this text object, with the specified `indent`.

        **IMPORTANT**: Non-indent modifications to this Text object will reflect in the
        original.

        Args:
            indent: New indent value

        Returns:
            A view to this object.
        """
        result = Text(indent=indent)
        result._spans = self._spans
        return result

    def spans(self) -> list[Span]:
        return self._spans

    @classmethod
    def ass(cls, parts: "Iterable[Text]") -> "Text":
        result = Text()
        for value in parts:
            result += value

        return result

    def __iadd__(self, other: "Text | str", /) -> Self:
        if isinstance(other, Text):
            self._spans.extend(
                Span(
                    value=span.value,
                    style=span.style,
                    indent=span.indent + other.indent - self.indent,
                )
                for span in other._spans
            )
        else:
            self._spans.append(Span(other))
            self._len += len(other)

        return self

    def __add__(self, other: "Text | str", /) -> "Text":
        result = Text()

        result._spans.extend(self._spans)
        result._len = self._len
        result.indent = self.indent

        result += other
        return result

    def __len__(self) -> int:
        return self._len


# Components


type ComponentYieldT[R] = Component[R] | Signal | TextLike | None
type ComponentGen[R] = Generator[ComponentYieldT[R], str, R]

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

            if curr.comp.indent > 0:
                debug_name += f" indent={curr.comp.indent}"

            if comp.stateless:
                result += f"({debug_name})"
            else:
                result += f"<{debug_name}>"

            stack.extend((child, depth + 1) for child in reversed(curr.children))

        return result
