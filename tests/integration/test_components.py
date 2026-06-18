from typing import Iterator
from tulip.functional import rpadfn

import pytest

from tulip.components import (
    SelectController,
    TabController,
    component,
    select,
    tabview,
    tabview_compact,
)
from tulip.components.types import ComponentGen
from tulip.input.keys import Key
from tulip.render import render
from tulip.render.exceptions import TooManyChildrenException
from tulip.tester import ComponentTester, component_test


@component
def bad_component() -> ComponentGen[None]:
    """Component that never waits for keyboard input."""

    while True:
        yield "Some text"


def test_infinite_component_error() -> None:
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


@component_test(
    tabview(
        [(f"tab {i}", f"Content for tab: tab {i}") for i in range(4)],
        heading=tabview_compact(3, " "),
    ),
    snapshots=True,
)
def test_tabview_compact(_: ComponentTester) -> Iterator[Key]:
    yield Key.LEFT
    yield from (Key.RIGHT,) * 4
    yield Key.LEFT


@component_test(
    tabview(
        tabs=[
            ("tab 1", "Some text"),
            ("tab 2", select([f"item {i}" for i in range(5)])),
        ],
        heading=tabview_compact(3, " "),
    ),
    snapshots=True,
)
def test_tabview_with_interactible_tab(tester: ComponentTester) -> Iterator[Key]:
    assert tester.find(".//select") is None
    yield Key.RIGHT
    assert tester.find(".//select") is not None
    yield Key.DOWN
    assert tester.find(".//select") is not None


@component_test(
    tabview(
        tabs=[
            (
                "tab 1",
                select(
                    [f"item {i}" for i in range(5)],
                    commands={
                        Key.RIGHT: SelectController.next,
                        Key.DOWN: SelectController.next,
                    },
                ),
            ),
            (
                "tab 2",
                select(
                    [f"elem {i}" for i in range(4)],
                    commands={Key.RIGHT: SelectController.next},
                ),
            ),
        ],
        heading=tabview_compact(3, " "),
        commands={
            Key.LEFT: rpadfn(TabController.prev),
            Key.RIGHT: TabController.next,
        },
    ),
    snapshots=True,
)
def test_tabview_noyield(_: ComponentTester) -> Iterator[Key]:
    yield Key.DOWN
    yield Key.RIGHT
    yield Key.RIGHT
    yield Key.RIGHT
    yield Key.LEFT
