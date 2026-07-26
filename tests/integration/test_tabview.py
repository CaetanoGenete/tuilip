from dataclasses import replace
from typing import assert_type, Never
from more_itertools import one
from itertools import repeat
from pathlib import Path

from tests.utils import identitycomp
from tuilip.components.types import Component
from tuilip.components import (
    TabController,
    select,
    tabview,
    tabview_compact,
    tabviewn,
)
from tuilip.functional import atend
from tuilip.input.keys import Key
from tuilip.tester import component_tester, MockCompState, mockcomp


def test_compact(snapshot_path: Path) -> None:
    """Tests tabview component:

    1. Doesn't overflow to the left.
    2. Switches from page 1 -> 2
    3. Doesn't overflow to the right.
    4. Switches from page 2 -> 1
    """

    tabs_per_page = 3

    comp = tabview(
        [(f"tab {i}", f"Content for tab: tab {i}") for i in range(4)],
        heading=tabview_compact(tabs_per_page, " "),
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        tester.next(Key.LEFT)
        tester.next(*repeat(Key.RIGHT, tabs_per_page + 1))
        tester.next(Key.LEFT)


def test_with_interactible_tab(snapshot_path: Path) -> None:
    """Tests tabview tab remains interactible."""

    comp = tabviewn(
        ("tab 1", "Some text"),
        ("tab 2", select([f"item {i}" for i in range(5)])),
        heading=tabview_compact(3, " "),
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        assert atend(tester.find(".//select"))
        tester.next(Key.RIGHT)
        assert not atend(tester.find(".//select"))
        tester.next(Key.DOWN)
        assert not atend(tester.find(".//select"))


def test_noprop(snapshot_path: Path) -> None:
    """Tests tabview blocks key propogating on tab change."""

    tab1 = MockCompState(id="tab1")
    tab2 = MockCompState(id="tab2")

    comp = tabviewn(
        ("tab 1", mockcomp(tab1)),
        ("tab 2", mockcomp(tab2)),
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        # Check key still propogates if overflowing to the left.
        tester.next(Key.LEFT)
        assert tab1.key == Key.LEFT

        last_tab1_state = replace(tab1)

        # Check no-prop if tab change from left->right.
        tester.next(Key.RIGHT)
        assert tab1 == last_tab1_state
        assert tab2.key == Key.NULL

        # Check key still propogates if overflowing to the right.
        tester.next(Key.RIGHT)
        assert tab1 == last_tab1_state
        assert tab2.key == Key.RIGHT

        last_tab2_state = replace(tab2)

        # Check no-prop if tab change from rigth->left.
        tester.next(Key.LEFT)
        assert tab1.key == Key.NULL
        assert tab2 == last_tab2_state

        # Check initial behaviour hasn't changed.
        tester.next(Key.LEFT)
        assert tab1.key == Key.LEFT
        assert tab2 == last_tab2_state


def test_controller(snapshot_path: Path) -> None:
    """Tests tab controller.

    1. Tabs can be changed with just the controller.
    2. Tabs only change if refresh=True.
    """

    controller = TabController(tab=1)
    comp = tabview(
        [(f"tab {i}", f"Content for tab: tab {i}") for i in range(4)],
        heading=tabview_compact(3, " "),
        controller=controller,
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        for tab in (2, 0, 3):
            controller.tab = tab
            controller.refresh = True
            tester.next(Key.NULL)

        # Tab change should have no effect unless refresh = True
        controller.tab = 1
        tester.next(Key.NULL)
        assert not one(tester.find("./tabview")).rebuilt

        tester.next(Key.RIGHT)


def test_no_rebuild(snapshot_path: Path) -> None:
    """Tests tabview doesn't rebuild if pressed key not in commands."""

    comp = tabviewn(
        ("tab 1", mockcomp(id="tab1")),
        ("tab 2", mockcomp(id="tab2")),
        heading=tabview_compact(3, " "),
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        tester.next(Key.DOWN)
        assert not one(tester.find("./tabview")).rebuilt

        tester.next(Key.RIGHT)

        tester.next(Key.DOWN)
        assert not one(tester.find("./tabview")).rebuilt


# type checks

assert_type(
    tabview([("test-tab", "content")]),
    Component[Never],
)
assert_type(
    tabviewn(("test-tab", "content")),
    Component[Never],
)

assert_type(
    tabview([("test-tab", identitycomp(10))]),
    Component[int],
)
assert_type(
    tabviewn(("test-tab", identitycomp(10))),
    Component[int],
)

assert_type(
    tabview([("test-tab", identitycomp(31.2))]),
    Component[float],
)
assert_type(
    tabviewn(("test-tab", identitycomp(31.2))),
    Component[float],
)

assert_type(
    tabview([("test-tab-1", "content 1"), ("test-tab-2", "content 2")]),
    Component[Never],
)
assert_type(
    tabviewn(("test-tab-1", "content 1"), ("test-tab-2", "content 2")),
    Component[Never],
)

assert_type(
    tabview([("test-tab-1", identitycomp(10)), ("test-tab-2", "content 2")]),
    Component[int],
)
assert_type(
    tabviewn(("test-tab-1", identitycomp(10)), ("test-tab-2", "content 2")),
    Component[int],
)

assert_type(
    tabview([("test-tab-1", identitycomp(10)), ("test-tab-2", identitycomp("str"))]),
    Component[int | str],
)
assert_type(
    tabviewn(("test-tab-1", identitycomp(10)), ("test-tab-2", identitycomp("str"))),
    Component[int | str],
)
