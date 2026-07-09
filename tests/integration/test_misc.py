from contextlib import nullcontext
from typing import ContextManager, final, override

import pytest
from tuilip.components import component
from tuilip.components.types import ComponentGen
from tuilip.input import BlockingInputHandler
from tuilip.render import loop
from tuilip.input.keys import Key
from tuilip.render.exceptions import TooManyChildrenException


@component
def bad_component() -> ComponentGen[None]:
    """Component that never waits for keyboard input."""

    while True:
        yield "Some text"


@final
class NullInputHandler(BlockingInputHandler):
    @override
    def read(self) -> int:
        return Key.NULL

    @override
    def raw(self) -> ContextManager[None]:
        return nullcontext()

    @override
    def interrupt(self) -> None:
        pass


def test_infinite_component_error() -> None:
    """Checks a component which never yields POLLINPUT, eventually errors."""

    bad_comp = bad_component()
    with pytest.raises(TooManyChildrenException) as e:
        loop(
            bad_comp,
            input_handler=NullInputHandler(),
            draw=lambda _: None,
        )

    assert e.value.comp == bad_comp

    errmsg = str(e.value)
    assert __file__ in errmsg
    assert bad_comp.debug_name in errmsg
