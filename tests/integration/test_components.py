import pytest
from tulip.components import component
from tulip.components.types import ComponentGen
from tulip.render import render
from tulip.render.exceptions import TooManyChildrenException


@component
def bad_component() -> ComponentGen[None]:
    """Component which never waits for keyboard input."""

    while True:
        yield "Some text"


def test_infinite_component_errors() -> None:
    bad_comp = bad_component()
    with pytest.raises(TooManyChildrenException) as e:
        render(
            bad_comp,
            onrefresh=lambda x: "",
        )

    assert e.value.comp == bad_comp

    errmsg = str(e.value)
    assert __file__ in errmsg
    assert bad_comp.debug_name in errmsg
