from typing import Never

from readchar import readchar

from tulip.components.types import Component
from tulip.render import TextView, render
from tulip.render.types import CompNode, Text


def loop[R](*components: Component[R] | Text) -> R:
    def _onrefresh(_: list[TextView]) -> str:
        for comp in reversed(components):
            print(CompNode[Never](comp) if isinstance(comp, Text) else comp.cache)

        print("---")

        key = readchar()
        print("Key pressed: ", str(key.encode("charmap")))
        print("---")

        if key == "\x03":
            raise KeyboardInterrupt()
        return key

    return render(*components, onrefresh=_onrefresh)
