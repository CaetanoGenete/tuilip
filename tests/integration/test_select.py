from pathlib import Path
import pytest
from typing import Any, assert_type

from more_itertools import one

from tuilip.input.keys import Key
from tuilip.tester import component_tester
from tuilip.components import SELECT_MAX_BULLETS, SelectController, select, selectn
from tuilip.components.types import Component
from tests.utils import identitycomp


@pytest.mark.parametrize("nitems", [1, 5, 10, 11, 21])
def test_navigate(snapshot_path: Path, nitems: int) -> None:
    """Tests navigation of select using the arrow keys.

    1. Test navigation from 1,2,3...n,1 wraps
    2. Test navigation from 1,n,n-1,...1 wraps
    """

    comp = select(
        [f"item - {i}" for i in range(nitems)],
        items_per_page=10,
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        for _ in range(nitems):
            tester.next(Key.DOWN)

        for _ in range(nitems):
            tester.next(Key.UP)


def test_no_rebuild(snapshot_path: Path) -> None:
    """Tests select doesn't rebuild if pressed key is not in commands."""

    comp = select([f"item - {i}" for i in range(4)])

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        tester.next(Key.L)
        assert not one(tester.find("./select")).changed

        tester.next(Key.DOWN)

        tester.next(Key.U)
        assert not one(tester.find("./select")).changed


def test_controller(snapshot_path: Path) -> None:
    """Tests select controller.

    1. Selected item can be changed with just the controller.
    2. Selected item only changes if refresh=True.
    """

    items_per_page = 4

    controller = SelectController(1)
    comp = select(
        [f"item - {i}" for i in range(5)],
        controller=controller,
        items_per_page=items_per_page,
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        for index in (2, 0, items_per_page):
            controller.index = index
            controller.refresh = True
            tester.next(Key.NULL)

        # Index change should have no effect unless refresh = True
        controller.index = 3
        tester.next(Key.NULL)
        assert not one(tester.find("./select")).changed

        tester.next(Key.UP)


_TEST_PAGER_MAX_ITEMS = 3


@pytest.mark.parametrize(
    "nitems",
    [
        pytest.param(
            _TEST_PAGER_MAX_ITEMS - 1,
            id="No page indicator",
        ),
        pytest.param(
            _TEST_PAGER_MAX_ITEMS * SELECT_MAX_BULLETS,
            id="Bullets page indicator",
        ),
        pytest.param(
            _TEST_PAGER_MAX_ITEMS * SELECT_MAX_BULLETS + 1, id="Numbered page indicator"
        ),
    ],
)
def test_page_indicator(snapshot_path: Path, nitems: int) -> None:
    """Tests page indicator.

    1. Don't show if too few items
    1. Show bullets up to `SELECT_MAX_BULLETS`
    1. Show number above
    """

    controller = SelectController(0)
    comp = select(
        [f"item - {i}" for i in range(nitems)],
        items_per_page=_TEST_PAGER_MAX_ITEMS,
        controller=controller,
    )

    with component_tester(comp, snapshot_path=snapshot_path, compare=True) as tester:
        # Check at end of first page
        controller.index = min(_TEST_PAGER_MAX_ITEMS - 1, nitems - 1)
        controller.refresh = True
        tester.next(Key.NULL)

        # Check at start of second page
        controller.index = min(_TEST_PAGER_MAX_ITEMS, nitems - 1)
        controller.refresh = True
        tester.next(Key.NULL)

        # Check at the end of last page
        controller.index = nitems - 1
        controller.refresh = True
        tester.next(Key.NULL)


@pytest.mark.parametrize(
    "index",
    [0, 4, 9, 10],
)
def test_enter_select_item(index: int) -> None:
    """Test select given index on <ENTER>."""

    controller = SelectController(0)
    comp = select(
        [f"item - {i}" for i in range(11)],
        items_per_page=10,
        controller=controller,
    )

    with component_tester(comp) as tester:
        controller.index = index
        tester.next(Key.NULL)
        tester.next(Key.CR)

    assert tester.done and tester.ret == index


def test_command_select_item() -> None:
    """Test select given index on command return True."""

    index = 3

    def _select(controller: SelectController, *_: Any) -> bool:
        controller.index = index
        return True

    comp = select(
        [f"item - {i}" for i in range(11)],
        items_per_page=10,
        commands={Key.ASTERISK: _select},
    )

    with component_tester(comp) as tester:
        tester.next(Key.ASTERISK)
        assert tester.done and tester.ret == index


# Type checks

assert_type(
    selectn("test"),
    Component[int],
)
assert_type(
    select(["test"]),
    Component[int],
)
assert_type(
    selectn("test1", "test2"),
    Component[int],
)
assert_type(
    select(["test1", "test2"]),
    Component[int],
)

assert_type(
    selectn(identitycomp("test")),
    Component[str | int],
)
assert_type(
    select([identitycomp("test")]),
    Component[str | int],
)

assert_type(
    selectn(identitycomp("test"), "other"),
    Component[str | int],
)
assert_type(
    select([identitycomp("test"), "other"]),
    Component[str | int],
)

assert_type(
    selectn(identitycomp("test"), sep=identitycomp(0.1)),
    Component[str | int | float],
)
assert_type(
    select([identitycomp("test")], sep=identitycomp(0.1)),
    Component[str | int | float],
)
