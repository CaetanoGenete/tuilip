from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import partial, wraps
from typing import Any, Callable, Iterable, Literal, Never, Unpack, overload

from tulip.components.types import (
    Component,
    ComponentGen,
    Renderable,
)
from tulip.components.utils import pollcond, pollrefresh
from tulip.functional import rpadfn
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
        indent: Offsets (to the right) the component by `indent`. See `tulip.components:padding` for more details.

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
    """Indents child component by `indent` units.

    This is a right translation of the entire component (and its descendants), relative
    to its parent.

    Indent may be negative, in which case the translation is now `-indent` units to the
    left, relative to the parent. However note that _total_ (i.e. the sum of all
    ancestor indents) is restricted to be non-negative (i.e. >= 0).

    Args:
        comp: The component to indent.
        indent: An integer (may be negative).
    """

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


type Tab[R] = tuple[TextLike, Renderable[R]]


@dataclass(slots=True)
class TabController:
    tab: int
    refresh: bool = False

    def next[R](self, tabs: Sequence[Tab[R]]) -> None:
        """Select the next tab.

        On overflow, remains at the last tab.

        Args:
            tabs: The list of available tabs
        """

        if self.tab + 1 < len(tabs):
            self.tab += 1
            self.refresh = True

    def prev[R](self) -> None:
        """Select the previous tab.

        On overflow, remains at the first tab.
        """

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
        sep: Separator between tabs (includes ends).

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
            sep,
            *(
                Text(Text(tab, style="tabview.unselected"), sep)
                for tab in tabs[tab_page * tabs_per_page : tab_idx]
            ),
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
            sep,
            *(
                Text(Text(tab, style="tabview.unselected"), sep)
                for tab in tabs[tab_page * tabs_per_page : tab_idx]
            ),
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


type TabviewCommandsMap[R] = StdCommandsMap[TabController, Sequence[Tab[R]]]


DEFAULT_TABVIEW_COMMANDS: TabviewCommandsMap[Any] = {
    Key.LEFT: rpadfn(TabController.prev),
    Key.RIGHT: TabController.next,
}
DEFAULT_TABVIEW_HEADING = tabview_compact(3)


@component
def tabview[R](
    tabs: Sequence[Tab[R]],
    *,
    heading: TabviewFormatter = DEFAULT_TABVIEW_HEADING,
    controller: TabController | None = None,
    commands: TabviewCommandsMap[R] = DEFAULT_TABVIEW_COMMANDS,
) -> ComponentGen[R]:
    """Shows one component (from `tabs`) at a time.

    Args:
        tabs: Sequence of (tab_name, component) tuples.
        heading: Optional heading.
        controller: Controller for this component.
        commands: Optional key-action mapping.
    """

    controller = controller or TabController(tab=0)

    last_tab = controller.tab

    def _poll(*_: Any) -> bool:
        nonlocal last_tab

        tab_idx = controller.tab
        refresh = controller.refresh and last_tab != tab_idx

        last_tab = tab_idx
        controller.refresh = False

        return refresh

    while True:
        tab_idx = controller.tab

        yield heading(ShelfView(tabs, 0), tab_idx)

        if last_tab != tab_idx:
            yield Signal.NOPROP

        yield tabs[tab_idx][1]
        yield from pollcond(commands, _poll, controller, tabs)


def tabviewn[R](
    *tabs: Tab[R],
    heading: TabviewFormatter = DEFAULT_TABVIEW_HEADING,
    controller: TabController | None = None,
    commands: TabviewCommandsMap[R] = DEFAULT_TABVIEW_COMMANDS,
) -> Component[R]:
    """Variadic interface for `tabview`.

    Args:
        tabs: (tab_name, component) tuples.
        heading: Optional heading.
        controller: Controller for this component.
        commands: Optional key-action mapping.
    """

    return tabview(tabs, heading=heading, controller=controller, commands=commands)


@component(stateless=True)
def seq[R](
    comps: Iterable[Renderable[R]],
    sep: Renderable[R] = "",
) -> ComponentGen[R | None]:
    """Lays out components sequentially, with an optional `separator` between.

    Args:
        comps: The components to layout.
        sep: Optional Component to interleave between `comps`.
    """

    if not sep:
        for value in comps:
            yield value
        return

    it = iter(comps)
    try:
        yield next(it)
    except StopIteration:
        return

    for value in it:
        yield sep
        yield value


def seqn[R](
    *comps: Renderable[R],
    sep: Renderable[R] = "",
) -> Component[R]:
    return seq(comps, sep=sep)


@dataclass
class SelectController:
    index: int
    refresh: bool = False

    def next(self, items: Sequence[Any]) -> None:
        """Moves cursor to the next item, wrapping around if at the end.

        Always refreshes.

        Args:
            items: The list of available items.
        """

        self.index = (self.index + 1) % len(items)
        self.refresh = True

    def prev(self, items: Sequence[Any]) -> None:
        """Moves cursor to the previous item, wrapping around if at the start.

        Always refreshes.

        Args:
            items: The list of available items.
        """

        self.index = (self.index - 1) % len(items)
        self.refresh = True

    def first(self) -> None:
        """Moves cursor to the first item.

        Refreshes if index has changed.
        """

        if self.index != 0:
            self.index = 0
            self.refresh = True

    def last(self, items: Sequence[Any]) -> None:
        """Moves cursor to the last item.

        Refreshes if index has changed.

        Args:
            items: The list of available items.
        """

        lasti = len(items) - 1
        if self.index != lasti:
            self.index = lasti
            self.refresh = True

    def select(self) -> bool:
        """Select current element pointed at by cursor."""

        return True


type SelectCommandsMap[R] = StdCommandsMap[SelectController, Sequence[Renderable[R]]]


DEFAULT_ITEMS_PER_PAGE = 10
DEFAULT_SELECT_COMMANDS: dict[int, Callable[[SelectController, Any], Any]] = {
    Key.UP: SelectController.prev,
    Key.DOWN: SelectController.next,
    Key.G_LOWER: rpadfn(SelectController.first),
    Key.HOME: rpadfn(SelectController.first),
    Key.G: SelectController.last,
    Key.END: SelectController.last,
    Key.CR: rpadfn(SelectController.select),
}
SELECT_MAX_BULLETS = 10


@component
def select[R](
    comps: Sequence[Renderable[R]],
    *,
    sep: TextLike = "\n",
    cursor: TextLike | None = None,
    items_per_page: int = DEFAULT_ITEMS_PER_PAGE,
    controller: SelectController | None = None,
    commands: SelectCommandsMap[R] = DEFAULT_SELECT_COMMANDS,
) -> ComponentGen[R | int]:
    """Selects between 'comps'. Analogous to html <select>.

    Args:
        values: Components to select between.
        sep: Optional separator componenet between `values`.
        cursor: Cursor character (or string).
        items_per_page: Number of items to show per page.
        controller: Controller for this select component.
        commands: Optional key-action mapping.

    Returns:
        Index of the selected component
    """

    assert items_per_page > 0, "must be positive"

    controller = controller or SelectController(index=0)

    if cursor is None:
        cursor = "> "

    if isinstance(cursor, str):
        cursor = Text(cursor, style="select.selected")

    if isinstance(sep, str):
        sep = Text(sep)

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
                *comps[page * items_per_page : idx],
                seqn(cursorcomp, comps[idx]),
                *comps[idx + 1 : (page + 1) * items_per_page],
                sep=sep,
            ),
            indent=indent,
        )

        if (nitems := len(comps)) > items_per_page:
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

        if (yield from pollrefresh(commands, controller, comps)).done:
            return controller.index


@dataclass
class PromptController:
    prompt: str = ""
    cursor: int = 0

    def prevchar(self) -> None:
        """Moves cursor to the previous character (if not at the start)."""

        self.cursor = max(0, self.cursor - 1)

    def nextchar(self) -> None:
        """Moves cursor to the next character (if not at the end)."""

        self.cursor = min(len(self.prompt), self.cursor + 1)

    def prevword(self) -> None:
        """Moves cursor to the previous word.

        A word is defined as a non-space character, separated by spaces.
        """

        cursor = self.cursor
        prompt = self.prompt

        while True:
            cursor = prompt.rfind(" ", 0, max(0, cursor - 1)) + 1
            if (
                prompt[cursor - 1 : cursor] in ("", " ")
                and prompt[cursor : cursor + 1] != " "
            ):
                break

        self.cursor = cursor

    def nextword(self) -> None:
        """Moves cursor to the next word.

        A word is defined as a non-space character, separated by spaces.
        """

        cursor = self.cursor
        prompt = self.prompt

        while True:
            cursor = self.prompt.find(" ", cursor) + 1
            if cursor == 0:
                cursor = len(self.prompt)
                break

            if (
                prompt[cursor - 1 : cursor] in ("", " ")
                and prompt[cursor : cursor + 1] != " "
            ):
                break

        self.cursor = cursor

    def start(self) -> None:
        """Places the cursor at the start of the prompt."""

        self.cursor = 0

    def end(self) -> None:
        """Places the cursor at the end of the prompt."""

        self.cursor = len(self.prompt)

    def delchar(self) -> None:
        """Deletes the character immediately before the cursor."""

        self.prompt = (
            self.prompt[: max(0, self.cursor - 1)] + self.prompt[self.cursor :]
        )
        self.prevchar()

    def delword(self) -> None:
        """Deletes up to the start of the word at or before the cursor."""

        prev_cursor = self.cursor

        self.prevword()
        self.prompt = self.prompt[: self.cursor] + self.prompt[prev_cursor:]

    def insert(self, key: int) -> None:
        """Insert the given key at the cursor, if it's printable.

        Args:
            key: Keycode to insert.
        """

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
    Key.HOME: PromptController.start,
    Key.END: PromptController.end,
}


@component
def prompt(
    *,
    controller: PromptController | None = None,
    commands: PromptCommandsMap = DEFAULT_PROMPT_COMMANDS,
) -> ComponentGen[str]:
    """Text prompt.

    Args:
        controller: Controller for this prompt component.
        commands: Optional key-action mapping.

    Returns:
        The entered prompt.
    """
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

        if (key := (yield Signal.POLLINPUT)) in commands:
            if commands[key](controller):
                return controller.prompt
        else:
            controller.insert(key)


@component
def echo_key() -> ComponentGen[Never]:
    yield "Key: "
    while True:
        yield f"Key: {(yield Signal.POLLINPUT)}"
