from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
)

if TYPE_CHECKING:
    from tuilip.render.types import Signal
    from tuilip.render.text import TextLike, Text


type StaticRenderable = TextLike
type Renderable[R] = Component[R] | StaticRenderable

type ComponentYieldT[R] = Renderable[R] | Signal | None
type ComponentGen[R] = Generator[ComponentYieldT[R], int, R]


@dataclass(slots=True)
class CompCache[R]:
    propkey: bool = True
    children: list[Component[R] | Text] = field(default_factory=list[Any])


R_co = TypeVar("R_co", covariant=True)


@dataclass(slots=True)
class Component(Generic[R_co]):
    noreturn: bool
    debug_name: str
    gen: ComponentGen[R_co]
    indent: int = 0
    cache: CompCache[R_co] = field(default_factory=CompCache[R_co])
