from itertools import repeat
from pathlib import Path

from tulip.components.types import ComponentGen
from tulip.functional import rpadfn

from tulip.components import (
    SelectController,
    TabController,
    component,
    select,
    tabview,
    tabview_compact,
    tabviewn,
)
from tulip.input.keys import Key
from tulip.render.types import Signal
from tulip.tester import ComponentTester


def test_compact(snapshot_path: Path) -> None:
    """Tests tabview component:

    1. Doesn't overflow to the left.
    2. Switches from page 1 -> 2
    3. Doesn't overflow to the right.
    4. Switches from page 2 -> 1
    """

    tabs_per_page = 3

    tester = ComponentTester(
        tabview(
            [(f"tab {i}", f"Content for tab: tab {i}") for i in range(4)],
            heading=tabview_compact(tabs_per_page, " "),
        ),
    )

    with tester.record(snapshot_path, compare=True):
        tester.next(Key.LEFT)
        tester.next(*repeat(Key.RIGHT, tabs_per_page + 1))
        tester.next(Key.LEFT)


def test_with_interactible_tab(snapshot_path: Path) -> None:
    """Tests tabview tab remains interactible."""

    tester = ComponentTester(
        tabviewn(
            ("tab 1", "Some text"),
            ("tab 2", select([f"item {i}" for i in range(5)])),
            heading=tabview_compact(3, " "),
        ),
    )

    with tester.record(snapshot_path, compare=True):
        assert tester.find(".//select") is None
        tester.next(Key.RIGHT)
        assert tester.find(".//select") is not None
        tester.next(Key.DOWN)
        assert tester.find(".//select") is not None


def test_noyield(snapshot_path: Path) -> None:
    tester = ComponentTester(
        tabviewn(
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
            heading=tabview_compact(3, " "),
            commands={
                Key.LEFT: rpadfn(TabController.prev),
                Key.RIGHT: TabController.next,
            },
        ),
    )

    with tester.record(snapshot_path, compare=True):
        tester.next(Key.DOWN)
        tester.next(*repeat(Key.RIGHT, 3))
        tester.next(Key.LEFT)


def test_controller(snapshot_path: Path) -> None:
    controller = TabController(tab=1)
    tester = ComponentTester(
        tabview(
            [(f"tab {i}", f"Content for tab: tab {i}") for i in range(4)],
            heading=tabview_compact(3, " "),
            controller=controller,
        ),
    )

    with tester.record(snapshot_path, compare=True):
        for tab in (2, 0, 3):
            controller.tab = tab
            controller.refresh = True
            tester.next(Key.NULL)

        # Tab change should have no effect unless refresh = True
        controller.tab = 1
        tester.next(Key.NULL)

        tester.next(Key.RIGHT)


@component
def rebuilding_component() -> ComponentGen[None]:
    idx = 0
    while True:
        yield f"Value: {idx}"
        if (yield Signal.POLLINPUT) != Key.NULL:
            idx += 1


def test_no_rebuild_on_page_change(snapshot_path: Path) -> None:
    tester = ComponentTester(
        tabviewn(
            ("tab 1", rebuilding_component()),
            ("tab 2", rebuilding_component()),
            heading=tabview_compact(3, " "),
        ),
    )

    with tester.record(snapshot_path, compare=True):
        tester.next(Key.RIGHT)
        tester.next(Key.LEFT)
