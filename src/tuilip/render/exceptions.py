from __future__ import annotations

from types import GeneratorType
from typing import TYPE_CHECKING, Any
from tuilip.render.text import Text


if TYPE_CHECKING:
    from tuilip.components.types import Component


class TooManyChildrenException(Exception):
    def __init__(self, comp: Component[Any]) -> None:
        self.comp: Component[Any] = comp

        gen = comp.gen
        assert not isinstance(gen, Text), "Only generator components should raise this!"

        if isinstance(gen, GeneratorType):
            fname = gen.gi_code.co_filename
            lno = str(gen.gi_code.co_firstlineno)
        else:
            fname = "?"
            lno = "?"

        super().__init__(
            f"Component <{comp.debug_name} id={id(gen)}> defined at {fname}:{lno} "
            "produced too many children! Perhaps yield `None` was forgotten?"
        )
