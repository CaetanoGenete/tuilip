from dataclasses import replace
from itertools import repeat
from pathlib import Path

from tulip.components import (
    TabController,
    select,
    tabview,
    tabview_compact,
    tabviewn,
)
from tulip.input.keys import Key
from tulip.tester import ComponentTester, MockCompState, mock_comp


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
    tab1 = MockCompState(id="tab1")
    tab2 = MockCompState(id="tab2")

    tester = ComponentTester(
        tabviewn(
            ("tab 1", mock_comp(tab1)),
            ("tab 2", mock_comp(tab2)),
        ),
    )

    with tester.record(snapshot_path, compare=True):
        tester.next(Key.LEFT)
        assert tab1.key == Key.LEFT

        last_tab1_state = replace(tab1)

        tester.next(Key.RIGHT)
        assert tab1 == last_tab1_state
        assert tab2.key == Key.NULL

        tester.next(Key.RIGHT)
        assert tab1 == last_tab1_state
        assert tab2.key == Key.RIGHT

        last_tab2_state = replace(tab2)

        tester.next(Key.LEFT)
        assert tab1.key == Key.NULL
        assert tab2 == last_tab2_state

        tester.next(Key.LEFT)
        assert tab1.key == Key.LEFT
        assert tab2 == last_tab2_state


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


def test_no_rebuild_on_page_change(snapshot_path: Path) -> None:
    tester = ComponentTester(
        tabviewn(
            ("tab 1", mock_comp(id="tab1")),
            ("tab 2", mock_comp(id="tab2")),
            heading=tabview_compact(3, " "),
        ),
    )

    with tester.record(snapshot_path, compare=True):
        tester.next(Key.RIGHT)
        tester.next(Key.LEFT)


def test_no_change(snapshot_path: Path) -> None:
    tester = ComponentTester(
        tabviewn(
            ("tab 1", mock_comp(id="tab1")),
            ("tab 2", mock_comp(id="tab2")),
            heading=tabview_compact(3, " "),
        ),
    )

    with tester.record(snapshot_path, compare=True):
        tester.next(Key.DOWN)

        assert (comp := tester.find("./tabview"))
        assert not comp.rebuilt

        tester.next(Key.RIGHT)
        tester.next(Key.DOWN)

        assert (comp := tester.find("./tabview"))
        assert not comp.rebuilt
