from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import partial, wraps
from typing import Any, Callable, Iterable, Literal, Never, Unpack, overload

from tulip.components.types import (
    Component,
    ComponentGen,
    Renderable,
)
from tulip.components.utils import pollinput, pollrefresh
from tulip.input.keys import Key
from tulip.math import divup
from tulip.render.types import Signal, Text, TextLike
from tulip.string import Justify, just
from tulip.views import MapView, ShelfView

type ComponentFactory[**P, R] = Callable[P, Component[R]]
type ComponentGenFactory[**P, R] = Callable[P, ComponentGen[R]]


@overload
def component[**P, R](
    fn: None = ...,
    *,
    stateless: Literal[False],
    debug_name: str = ...,
    indent: int = ...,
) -> Callable[[ComponentGenFactory[P, R]], ComponentFactory[P, R]]: ...


@overload
def component[**P, R](
    fn: None = ...,
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
    """Converts a generator into a tulip Component.

    Args:
        fn: The build function
        stateless: If true, component is only built once.
        debug_name: The name of the component as it appears in logs and error messages. Defaults to the function name.
        indent: Offsets (to the right) the component by `indent`.

    Returns:
        A Tuilip component.
    """
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


type StdCommandsMap[C, *A] = Mapping[int | Key, Callable[[C, Unpack[A]], bool | None]]


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


@overload
def padding(
    comp: str | Text,
    indent: int,
) -> Component[Never]: ...


@overload
def padding[R](
    comp: Component[R],
    indent: int,
) -> Component[R]: ...


def padding[R](
    comp: Renderable[R],
    indent: int,
) -> Renderable[R]:
    if indent == 0:
        return comp

    @component(
        stateless=True,
        debug_name="padding",
        indent=indent,
    )
    def result() -> ComponentGen[R | None]:
        yield comp

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

    def prev[R](self) -> None:
        if self.tab > 0:
            self.tab -= 1
            self.refresh = True


DEFAULT_TABS_PER_PAGE = 3
DEFAULT_TABVIEW_SEP = " "


type TabviewFormatter = Callable[[Sequence[TextLike], int], TextLike]


def tabview_compact(
    tabs_per_page: int = DEFAULT_TABS_PER_PAGE,
    sep: TextLike = DEFAULT_TABVIEW_SEP,
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
    sep: TextLike = DEFAULT_TABVIEW_SEP,
    justify: Justify = Justify.LEFT,
    fill: str = DEFAULT_TABVIEW_SEP,
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


type TabviewCommandsMap[R] = StdCommandsMap[TabController, Tabs[R]]


DEFAULT_TABVIEW_COMMANDS: TabviewCommandsMap[Any] = {
    Key.LEFT: lambda c, _: c.prev(),
    Key.RIGHT: TabController.next,
}
DEFAULT_TABVIEW_HEADING = tabview_compact(3)


@component
def tabview[R](
    tabs: Tabs[R],
    *,
    heading: TabviewFormatter = DEFAULT_TABVIEW_HEADING,
    controller: TabController | None = None,
    commands: TabviewCommandsMap[R] = DEFAULT_TABVIEW_COMMANDS,
) -> ComponentGen[R]:
    controller = controller or TabController(tab=0)

    last_tab = controller.tab
    while True:
        tab_idx = controller.tab

        yield heading(ShelfView(tabs, 0), tab_idx)

        if last_tab != tab_idx:
            yield Signal.NOPROP

        yield tabs[tab_idx][1]

        yield from pollinput(
            commands,
            lambda c, _: c.refresh or last_tab != tab_idx,
            controller,
            tabs,
        )

        controller.refresh = False
        last_tab = tab_idx


@component(stateless=True)
def seq[R](
    comps: Iterable[Renderable[R]],
    separator: Renderable[R] = "",
) -> ComponentGen[R | None]:
    if not separator:
        for value in comps:
            yield value
        return

    it = iter(comps)
    try:
        yield next(it)
    except StopIteration:
        return

    for value in it:
        yield separator
        yield value


def seqn[R](
    *comps: Renderable[R],
    separator: Renderable[R] = "",
) -> Component[R]:
    return seq(comps, separator=separator)


@dataclass
class SelectController:
    index: int
    refresh: bool = False

    def next(self, items: Sequence[Any]) -> None:
        self.index = (self.index + 1) % len(items)
        self.refresh = True

    def prev(self, items: Sequence[Any]) -> None:
        self.index = (self.index - 1) % len(items)
        self.refresh = True

    def first(self) -> None:
        if self.index != 0:
            self.index = 0
            self.refresh = True

    def last(self, items: Sequence[Any]) -> None:
        lasti = max(0, len(items) - 1)
        if self.index != lasti:
            self.index = lasti
            self.refresh = True

    def select(self) -> bool:
        return True


type SelectCommandsMap[R] = StdCommandsMap[SelectController, Sequence[Renderable[R]]]


DEFAULT_SELECT_COMMANDS: dict[int, Callable[[SelectController, Any], Any]] = {
    Key.UP: SelectController.prev,
    Key.DOWN: SelectController.next,
    Key.G_LOWER: lambda c, _: c.first(),
    Key.G: SelectController.last,
    Key.CR: lambda c, _: c.select(),
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
    commands: SelectCommandsMap[R] = DEFAULT_SELECT_COMMANDS,
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
    cursorcomp = padding(
        # TODO: This is currently a little bit of a hack... make possible with engine.
        Text(cursor, f"\x1b[{indent}D"),
        indent=-indent,
    )

    while True:
        idx = controller.index
        page = idx // items_per_page

        yield padding(
            seqn(
                *values[page * items_per_page : idx],
                seqn(cursorcomp, values[idx]),
                *values[idx + 1 : (page + 1) * items_per_page],
                separator=separator,
            ),
            indent=indent,
        )

        if (nitems := len(values)) > items_per_page:
            npages = (nitems + items_per_page - 1) // items_per_page

            yield "\n\n"
            yield padding(
                Text(
                    ("○" * page) + "●" + ("○" * (npages - page - 1)),
                    style="select.bullets",
                )
                if npages <= SELECT_MAX_BULLETS
                else Text(
                    f"[{page + 1}|{npages}]",
                    style="select.pager",
                ),
                indent=2,
            )

        if (yield from pollrefresh(commands, controller, values)).done:
            return controller.index


@dataclass
class PromptController:
    prompt: str = ""
    cursor: int = 0

    def prevchar(self) -> None:
        self.cursor = max(0, self.cursor - 1)

    def nextchar(self) -> None:
        self.cursor = min(len(self.prompt), self.cursor + 1)

    def prevword(self) -> None:
        self.cursor = self.prompt.rfind(" ", 0, max(0, self.cursor - 1)) + 1

    def nextword(self) -> None:
        wstart = self.prompt.find(" ", self.cursor)
        if wstart == -1:
            wstart = len(self.prompt)

        self.cursor = wstart + 1

    def delchar(self) -> None:
        self.prompt = self.prompt[: self.cursor - 1] + self.prompt[self.cursor :]
        self.prevchar()

    def delword(self) -> None:
        wstart = self.prompt.rfind(" ", 0, max(0, self.cursor - 1)) + 1

        self.prompt = self.prompt[:wstart] + self.prompt[self.cursor :]
        self.cursor = wstart

    def insert(self, key: int) -> None:
        # For now, only support printable ascii range
        if 32 <= key <= 126:
            self.prompt = (
                f"{self.prompt[: self.cursor]}{chr(key)}{self.prompt[self.cursor :]}"
            )
            self.nextchar()

    def select(self) -> bool:
        return True


type PromptCommandsMap = StdCommandsMap[PromptController]


DEFAULT_PROMPT_COMMANDS: PromptCommandsMap = {
    Key.DEL: PromptController.delchar,
    Key.BACKSPACE: PromptController.delword,
    Key.LF: PromptController.select,
    Key.CR: PromptController.select,
    Key.LEFT: PromptController.prevchar,
    Key.RIGHT: PromptController.nextchar,
    Key.CTRL_LEFT: PromptController.prevword,
    Key.CTRL_RIGHT: PromptController.nextword,
    Key.META_LEFT: PromptController.prevword,
    Key.META_RIGHT: PromptController.nextword,
}


@component
def prompt(
    *,
    controller: PromptController | None = None,
    commands: PromptCommandsMap = DEFAULT_PROMPT_COMMANDS,
) -> ComponentGen[str]:
    controller = controller or PromptController()

    while True:
        yield Text(
            controller.prompt[: controller.cursor],
            Text(
                controller.prompt[controller.cursor]
                if controller.cursor < len(controller.prompt)
                else " ",
                style="prompt.cursor",
            ),
            controller.prompt[controller.cursor + 1 :],
        )

        if (key := (yield)) in commands:
            if commands[key](controller):
                return controller.prompt
        else:
            controller.insert(key)


@component
def echo_key() -> ComponentGen[Never]:
    yield "Key: "
    while True:
        yield f"Key: {(yield)}"
