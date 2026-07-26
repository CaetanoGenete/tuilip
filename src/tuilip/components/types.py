from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Never
from typing_extensions import TypeVar


if TYPE_CHECKING:
    from tuilip.render.anim import AnimatedText
    from tuilip.render.types import Loop
    from tuilip.render.text import TextLike, Text


TOrNever = TypeVar("TOrNever", default=Never)


type Renderable[R] = Component[R] | TextLike | AnimatedText
type ComponentYieldT[R] = Renderable[R] | Loop | None
type ComponentGen[R] = Generator[ComponentYieldT[R], int, R]


type CompCacheChild[R] = Component[R] | Text | AnimatedText


@dataclass(slots=True)
class CompCache[R]:
    build_index: int = -1
    propkey: bool = True
    children: list[CompCacheChild[R]] = field(default_factory=list[Any])


R_co = TypeVar("R_co", covariant=True)


@dataclass(slots=True)
class Component(Generic[R_co]):
    noreturn: bool
    debug_name: str
    gen: ComponentGen[R_co]
    indent: int = 0
    cache: CompCache[R_co] = field(default_factory=CompCache[R_co])
