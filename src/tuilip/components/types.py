from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from tuilip.render.types import Signal, TextLike, Text


type Renderable[R] = "Component[R] | TextLike"
type _ComponentYieldT[R] = "Renderable[R] | Signal | None"
type ComponentGen[R] = Generator[_ComponentYieldT[R], int, R]


@dataclass(slots=True)
class CompNode[R]:
    propkey: bool = True
    children: "list[Component[R] | Text]" = field(
        default_factory=list["Component[R] | Text"]
    )


R_co = TypeVar("R_co", covariant=True)


@dataclass(slots=True)
class Component(Generic[R_co]):
    noreturn: bool
    debug_name: str
    gen: ComponentGen[R_co]
    indent: int = 0
    cache: CompNode[R_co] = field(default_factory=CompNode[R_co])
