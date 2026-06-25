from typing import Never

from tuilip.components.types import Component
from tuilip.input import DefaultInputHandler
from tuilip.input.types import InputHandler
from tuilip.render import TextView, render
from tuilip.render.types import CompNode, Text


def loop[R](
    *components: Component[R] | Text,
    input_handler: InputHandler = DefaultInputHandler(),
) -> R:
    def _onrefresh(_: list[TextView]) -> int:
        for comp in reversed(components):
            print(CompNode[Never](comp) if isinstance(comp, Text) else comp.cache)

        print("---")

        key = input_handler.read()
        print("Key pressed: ", str(key))
        print("---")

        if key == 0x03:
            raise KeyboardInterrupt()
        return key

    with input_handler.raw():
        return render(*components, onrefresh=_onrefresh)
