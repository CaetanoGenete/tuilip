from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Self, TypeVar, override
from collections.abc import Generator

from tulip.string import rto


class Signal(Enum):
    NO_CHANGE = object()


# Components


type ComponentYieldT[R] = Component[R] | Signal | str | None
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
    comp: Component[R] | str
    children: list[Self] = field(default_factory=list)

    @override
    def __str__(self) -> str:
        if isinstance(self.comp, str):
            result = rto(self.comp.replace("\n", r"\n").replace('"', r"\""))
            result = f'"{result}"'
        elif self.comp.stateless:
            result = f"({self.comp.debug_name})"
        else:
            result = f"<{self.comp.debug_name}>"

        for i, child in enumerate(self.children):
            if i + 1 == len(self.children):
                result += f"\n└{str(child).replace('\n', '\n  ')}"
            else:
                result += f"\n├{str(child).replace('\n', '\n│ ')}"

        return result
