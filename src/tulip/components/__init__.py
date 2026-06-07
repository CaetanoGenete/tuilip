from dataclasses import dataclass
from itertools import repeat
from more_itertools import interleave, intersperse

from functools import partial, wraps
from typing import Callable, Literal, Never, Unpack, overload
from collections.abc import Mapping, Sequence

from tulip.components.types import (
    Component,
    ComponentGen,
    Renderable,
)
from tulip.render.types import Signal, Text, TextLike
from tulip.components.utils import pollinput, pollrefresh
from tulip.math import divup
from tulip.string import Justify, just
from tulip.views import MapView, ShelfView


type ComponentFactory[**P, R] = Callable[P, Component[R]]
type ComponentGenFactory[**P, R] = Callable[P, ComponentGen[R]]


@overload
def component[**P, R](
    fn: Literal[None] = ...,
    *,
    stateless: Literal[False],
    debug_name: str = ...,
    indent: int = ...,
) -> Callable[[ComponentGenFactory[P, R]], ComponentFactory[P, R]]: ...


@overload
def component[**P, R](
    fn: Literal[None] = ...,
    *,
    stateless: Literal[True],
    debug_name: str = ...,
    indent: int = ...,
) -> Callable[[ComponentGenFactory[P, R]], ComponentFactory[P, Never]]: ...


@overload
def component[**P, R](
    fn: ComponentGenFactory[P, R],
    *,
    stateless: bool = ...,
    debug_name: str = ...,
    indent: int = ...,
) -> ComponentFactory[P, R]: ...


def component[**P, R](
    fn: ComponentGenFactory[P, R] | None = None,
    *,
    stateless: bool = False,
    debug_name: str = "",
    indent: int = 0,
) -> (
    ComponentFactory[P, R]
    | Callable[[ComponentGenFactory[P, R]], ComponentFactory[P, R]]
):
    if fn is None:
        return partial(
            component,
            stateless=stateless,
            debug_name=debug_name,
            indent=indent,
        )

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Component[R]:
        return Component(
            stateless=stateless,
            debug_name=debug_name or fn.__name__,
            gen=fn(*args, **kwargs),
            indent=indent,
        )

    return wrapper


type StandardCommandsMap[C, *A] = Mapping[str, Callable[[C, Unpack[A]], bool | None]]


@component(stateless=True, debug_name="noprop")
def _noprop[R](comp: Component[R]) -> ComponentGen[R]:
    yield Signal.NOPROP
    yield comp


def noprop[R](comp: Component[R], noprop: bool = True):
    """Prevents 'key' from being passed down to components wrapped by this
    function.

    Args:
        comp: A valid component
        noprop: If `false`, this is a no-op.

    Returns:
        A component.
    """
    if noprop:
        return _noprop(comp)

    return comp


def padding[R](
    *comps: Renderable[R],
    indent: int,
    start: bool = False,
) -> Component[R]:
    @component(stateless=True, debug_name="padding", indent=indent)
    def result() -> ComponentGen[R | None]:
        if comps and start:
            yield " " * indent
        for comp in comps:
            yield comp
        yield

    return result()


type Tabs[R] = Sequence[tuple[TextLike, Renderable[R]]]


@dataclass(slots=True)
class TabController:
    tab: int
    refresh: bool = False

    def next[R](self, tabs: Tabs[R]) -> None:
        if self.tab + 1 < len(tabs):
            self.tab += 1
            self.refresh = True

    def prev[R](self, _: Tabs[R]) -> None:
        if self.tab > 0:
            self.tab -= 1
            self.refresh = True


DEFAULT_TABS_PER_PAGE = 3


type TabviewFormatter = Callable[[Sequence[TextLike], int], TextLike]


def tabview_compact(
    tabs_per_page: int = DEFAULT_TABS_PER_PAGE,
    sep: TextLike = " ",
) -> TabviewFormatter:
    """Shows `tabs_per_page` tab titles, separated by spaces

    Args:
        tabs_per_page: Number of tab titles to show per page.

    Returns:
        Tabview formatter function.
    """

    def _heading(tabs: Sequence[TextLike], tab_idx: int) -> Text:
        tab_name = tabs[tab_idx]
        tab_page = tab_idx // tabs_per_page
        npages = divup(len(tabs), tabs_per_page)

        return Text(
            " ",
            Text(
                "<",
                style="tabview.arrow-enabled"
                if tab_page > 0
                else "tabview.arrow-disabled",
            ),
            *(
                Text(sep, Text(tab, style="tabview.unselected"))
                for tab in tabs[tab_page * tabs_per_page : tab_idx]
            ),
            sep,
            Text(tab_name, style="tabview.selected"),
            *(
                Text(sep, Text(tab, style="tabview.unselected"))
                for tab in tabs[tab_idx + 1 : (tab_page + 1) * tabs_per_page]
            ),
            sep,
            Text(
                ">",
                style="tabview.arrow-enabled"
                if tab_page + 1 < npages
                else "tabview.arrow-disabled",
            ),
            "\n",
        )

    return _heading


DEFAULT_TABVIEW_FIXED_WIDTH = 40


def tabview_fixed(
    width: int = DEFAULT_TABVIEW_FIXED_WIDTH,
    *,
    tabs_per_page: int = DEFAULT_TABS_PER_PAGE,
    sep: TextLike = " ",
    justify: Justify = Justify.LEFT,
    fill: str = " ",
) -> TabviewFormatter:
    """Shows `tabs_per_page` tab titles, displayed in fixed width columns.

    Args:
        tabs_per_page: Number of tab titles to show per page.
        width: Width per tab title.

    Returns:
        Tabview formatter function.
    """

    def _heading(tabs: Sequence[TextLike], tab_idx: int) -> Text:
        tab_page = tab_idx // tabs_per_page
        npages = divup(len(tabs), tabs_per_page)

        tabs = MapView(
            tabs,
            lambda tab: just(tab, width, justify, lfill=fill, rfill=fill),
        )
        tab_name = tabs[tab_idx]

        return Text(
            " ",
            Text(
                "<",
                style="tabview.arrow-enabled"
                if tab_page > 0
                else "tabview.arrow-disabled",
            ),
            *(
                Text(sep, Text(tab, style="tabview.unselected"))
                for tab in tabs[tab_page * tabs_per_page : tab_idx]
            ),
            sep,
            Text(tab_name, style="tabview.selected"),
            *(
                Text(sep, Text(tab, style="tabview.unselected"))
                for tab in tabs[tab_idx + 1 : (tab_page + 1) * tabs_per_page]
            ),
            *(
                Text(sep, Text(fill * width, style="tabview.unselected"))
                for _ in range(len(tabs), (tab_page + 1) * tabs_per_page)
            ),
            sep,
            Text(
                ">",
                style="tabview.arrow-enabled"
                if tab_page + 1 < npages
                else "tabview.arrow-disabled",
            ),
            "\n",
        )

    return _heading


DEFAULT_TABVIEW_COMMANDS = {
    "a": TabController.prev,
    "d": TabController.next,
}
DEFAULT_TABVIEW_HEADING = tabview_compact(3)


@component
def tabview[R](
    tabs: Tabs[R],
    *,
    heading: TabviewFormatter = DEFAULT_TABVIEW_HEADING,
    controller: TabController | None = None,
    commands: StandardCommandsMap[TabController, Tabs[R]] = DEFAULT_TABVIEW_COMMANDS,
) -> ComponentGen[R]:
    controller = controller or TabController(tab=0)

    last_tab = controller.tab
    while True:
        tab_idx = controller.tab
        _, tab_comp = tabs[tab_idx]

        yield heading(ShelfView(tabs, 0), tab_idx)

        if last_tab != tab_idx:
            yield Signal.NOPROP

        yield tab_comp
        yield from pollinput(
            commands,
            lambda c, _: c.refresh or last_tab != tab_idx,
            controller,
            tabs,
        )

        controller.refresh = False
        last_tab = tab_idx


@dataclass
class SelectController:
    index: int
    refresh: bool = False

    def next[R](self, items: Sequence[R]) -> None:
        self.index = (self.index + 1) % len(items)
        self.refresh = True

    def prev[R](self, items: Sequence[R]) -> None:
        self.index = (self.index - 1) % len(items)
        self.refresh = True

    def select[R](self, _: Sequence[R]) -> bool:
        return True


DEFAULT_SELECT_COMMANDS = {
    "w": SelectController.prev,
    "s": SelectController.next,
    "\r": SelectController.select,
}
DEFAULT_ITEMS_PER_PAGE = 10
SELECT_MAX_BULLETS = 10


@component
def select[R](
    values: Sequence[Renderable[R]],
    *,
    separator: TextLike = "\n",
    cursor: TextLike | None = None,
    items_per_page: int = DEFAULT_ITEMS_PER_PAGE,
    controller: SelectController | None = None,
    commands: StandardCommandsMap[
        SelectController,
        Sequence[Renderable[R]],
    ] = DEFAULT_SELECT_COMMANDS,
) -> ComponentGen[R | int]:
    assert items_per_page > 0, "must be positive"

    controller = controller or SelectController(index=0)

    if cursor is None:
        cursor = "> "

    if isinstance(cursor, str):
        cursor = Text(cursor, style="select.selected")

    if isinstance(separator, str):
        separator = Text(separator)

    indent = len(cursor)
    while True:
        page, page_idx = divmod(controller.index, items_per_page)

        yield padding(
            *intersperse(
                separator,
                values[page * items_per_page : controller.index],
            ),
            start=True,
            indent=indent,
        )

        yield Text("\n", cursor) if page_idx > 0 else cursor

        yield padding(
            values[controller.index],
            *interleave(
                repeat(separator),
                values[controller.index + 1 : (page + 1) * items_per_page],
            ),
            indent=indent,
        )

        if (nitems := len(values)) > items_per_page:
            npages = (nitems + items_per_page - 1) // items_per_page

            yield "\n\n" + " " * indent
            if npages <= SELECT_MAX_BULLETS:
                yield Text(
                    ("○" * page) + "●" + ("○" * (npages - page - 1)),
                    style="select.bullets",
                )
            else:
                yield Text(
                    f"[{page + 1}|{npages}]",
                    style="select.pager",
                )

        if (yield from pollrefresh(commands, controller, values)).done:
            return controller.index
