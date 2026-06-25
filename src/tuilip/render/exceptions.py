from types import GeneratorType
from typing import Any

from tuilip.components.types import Component
from tuilip.render.types import Text


class TooManyChildrenException(Exception):
    def __init__(self, comp: Component[Any]) -> None:
        self.comp: Component[Any] = comp

        gen = comp.gen
        assert not isinstance(gen, Text), "Only generator components should raise this!"

        if isinstance(gen, GeneratorType):
            fname = gen.gi_code.co_filename
            lno = gen.gi_code.co_firstlineno
        else:
            fname = "?"
            lno = "?"

        super().__init__(
            f"Component <{comp.debug_name} id={id(gen)}> defined at {fname}:{lno} "
            "produced too many children! Perhaps yield `None` was forgotten?"
        )
