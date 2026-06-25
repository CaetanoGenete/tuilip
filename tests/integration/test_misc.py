import pytest
from tuilip.components import component
from tuilip.components.types import ComponentGen
from tuilip.render import render
from tuilip.render.exceptions import TooManyChildrenException


@component
def bad_component() -> ComponentGen[None]:
    """Component that never waits for keyboard input."""

    while True:
        yield "Some text"


def test_infinite_component_error() -> None:
    """Checks a component which never yields POLLINPUT, eventually errors."""

    bad_comp = bad_component()
    with pytest.raises(TooManyChildrenException) as e:
        render(
            bad_comp,
            onrefresh=lambda x: 0,
        )

    assert e.value.comp == bad_comp

    errmsg = str(e.value)
    assert __file__ in errmsg
    assert bad_comp.debug_name in errmsg
