from contextlib import nullcontext
from typing import ContextManager, final, override

import pytest
from tuilip.components import component, seqn
from tuilip.tester import ComponentTester, MockCompState, mockcomp
from tuilip.render import loop
from tuilip.components.types import ComponentGen
from tuilip.input import BlockingInputHandler
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
    def read(self, timeout: float) -> int:
        del timeout
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
            draw=lambda _, __: None,
            animation_period=1 / 10,
        )

    assert e.value.comp == bad_comp

    errmsg = str(e.value)
    assert __file__ in errmsg
    assert bad_comp.debug_name in errmsg


def test_component_builds_only_once() -> None:
    """Checks a component, which appears multiple times in the layout tree, builds only
    once per cycle.
    """

    comp_state = MockCompState()
    comp = mockcomp(comp_state)

    tester = ComponentTester(seqn(comp, comp))

    assert comp_state.builds == 0
    tester.next(Key.A)
    assert comp_state.builds == 1
