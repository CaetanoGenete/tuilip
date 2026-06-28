from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from tuilip.render.types import CompNode, Signal, TextLike


type Renderable[R] = "Component[R] | TextLike"
type _ComponentYieldT[R] = "Renderable[R] | Signal | None"
type ComponentGen[R] = Generator[_ComponentYieldT[R], int, R]


R_co = TypeVar("R_co", covariant=True)


@dataclass(slots=True)
class Component(Generic[R_co]):
    noreturn: bool
    debug_name: str
    gen: ComponentGen[R_co]
    indent: int = 0
    cache: "CompNode[R_co] | None" = None
