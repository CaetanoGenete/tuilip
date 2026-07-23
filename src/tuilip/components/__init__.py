from collections.abc import Mapping, Sequence
import asyncio
from concurrent.futures import Future
from dataclasses import dataclass
from enum import IntEnum
from functools import partial, wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Generator,
    Iterable,
    TypeVar,
    Literal,
    Never,
    Unpack,
    overload,
)
from tuilip.components.types import (
    Component,
    ComponentGen,
    ComponentYieldT,
    Renderable,
    TOrNever,
)
from tuilip.components.utils import pollrefresh
from tuilip.functional import rpadfn
from tuilip.input.keys import Key
from tuilip.math import divup
from tuilip.render.types import RendererContext, Loop
from tuilip.render.text import Text, TextLike
from tuilip.string import Justify, just
from tuilip.views import MapView, ShelfView

type ComponentFactory[**P, R] = Callable[P, Component[R]]
type ComponentGen2[Y, R] = Generator[ComponentYieldT[Y], int, R]
type ComponentGenFactory[**P, Y, R] = Callable[P, ComponentGen2[Y, R]]


@overload
def component[**P, Y, R](
    fn: None = ...,
    *,
    noreturn: Literal[False],
    debug_name: str = ...,
    indent: int = ...,
) -> Callable[[ComponentGenFactory[P, Y, R]], ComponentFactory[P, Y | R]]: ...


@overload
def component[**P, Y, R](
    fn: None = ...,
    *,
    noreturn: Literal[True],
    debug_name: str = ...,
    indent: int = ...,
) -> Callable[[ComponentGenFactory[P, Y, R]], ComponentFactory[P, Y]]: ...


@overload
def component[**P](
    fn: ComponentGenFactory[P, Never, Never],
    *,
    noreturn: bool = ...,
    debug_name: str = ...,
    indent: int = ...,
) -> ComponentFactory[P, Never]: ...


@overload
def component[**P, Y, R](
    fn: ComponentGenFactory[P, Y, R],
    *,
    noreturn: bool = ...,
    debug_name: str = ...,
    indent: int = ...,
) -> ComponentFactory[P, Y | R]: ...


def component[**P, R](
    fn: ComponentGenFactory[P, R, R] | None = None,
    *,
    noreturn: bool = False,
    debug_name: str = "",
    indent: int = 0,
) -> Any:
    """Converts a generator into a tuilip Component.

    Args:
        fn: The build function
        noreturn: If true, last build is re-used once generator closes.
        debug_name: The name of the component as it appears in logs and error messages. Defaults to the function name.
        indent: Offsets (to the right) the component by `indent`. See `tuilip.components:padding` for more details.

    Returns:
        A Tuilip component.
    """
    if fn is None:
        return partial(
            component,
            noreturn=noreturn,
            debug_name=debug_name,
            indent=indent,
        )

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Component[R]:
        return Component(
            noreturn=noreturn,
            debug_name=debug_name or fn.__name__,
            gen=fn(*args, **kwargs),
            indent=indent,
        )

    return wrapper


type StdCommandsMap[C, *A] = Mapping[int | Key, Callable[[C, Unpack[A]], bool | None]]


@component(noreturn=True)
def noprop(comp: Renderable[TOrNever], *, n: int = 0) -> ComponentGen2[TOrNever, None]:
    """Prevents 'key' from being passed down to components wrapped by this function.

    Args:
        comp: A valid component
        n: Prevent propogation for `n` builds, if `n == 0` prevent indefinitely,
    """
    assert n >= 0, "n must be non-negative"

    for _ in range(n):
        yield Loop.NOPROP
        yield comp
        yield Loop.POLLINPUT

    if n == 0:
        yield Loop.NOPROP

    yield comp


def padding[T: Renderable[Any]](comp: T, indent: int) -> T:
    """Indents child component by `indent` units.

    This is a right translation of the entire component (and its descendants), relative
    to its parent.

    Indent may be negative, in which case the translation becomes `-indent` units to the
    left, relative to the parent. However, note that _total indent_ (i.e. the sum of all
    ancestor indents) is restricted to be non-negative (i.e. >= 0).

    Args:
        comp: The component to indent.
        indent: An integer (may be negative).
    """

    if indent == 0:
        return comp

    @component(
        noreturn=True,
        debug_name="padding",
        indent=indent,
    )
    def result() -> ComponentGen2[Any, None]:
        yield comp

    return result()  # type: ignore


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

    def prev(self) -> None:
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
def tabview(
    tabs: Sequence[Tab[TOrNever]],
    *,
    heading: TabviewFormatter = DEFAULT_TABVIEW_HEADING,
    controller: TabController | None = None,
    commands: TabviewCommandsMap[TOrNever] | None = None,
) -> ComponentGen[TOrNever]:
    """Shows one component (from `tabs`) at a time.

    Args:
        tabs: Sequence of (tab_name, component) tuples.
        heading: Optional heading.
        controller: Controller for this component.
        commands: Optional key-action mapping.
    """

    controller = controller or TabController(tab=0)
    commands = commands or DEFAULT_TABVIEW_COMMANDS

    last_tab = controller.tab
    while True:
        tab_idx = controller.tab

        yield heading(ShelfView(tabs, 0), tab_idx)

        tab_comp = tabs[tab_idx][1]
        yield (
            noprop(tab_comp, n=1)
            if last_tab != tab_idx and isinstance(tab_comp, Component)
            else tab_comp
        )
        yield from pollrefresh(commands, controller, tabs)

        last_tab = tab_idx


def tabviewn(
    *tabs: Tab[TOrNever],
    heading: TabviewFormatter = DEFAULT_TABVIEW_HEADING,
    controller: TabController | None = None,
    commands: TabviewCommandsMap[TOrNever] | None = None,
) -> Component[TOrNever]:
    """Variadic interface for `tabview`.

    Args:
        tabs: (tab_name, component) tuples.
        heading: Optional heading.
        controller: Controller for this component.
        commands: Optional key-action mapping.
    """

    return tabview(tabs, heading=heading, controller=controller, commands=commands)


@component(noreturn=True)
def seq(
    comps: Iterable[Renderable[TOrNever]],
    sep: Renderable[TOrNever] = "",
) -> ComponentGen2[TOrNever, None]:
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


def seqn(
    *comps: Renderable[TOrNever],
    sep: Renderable[TOrNever] = "",
) -> Component[TOrNever]:
    """Variadic interface for `seq`.

    Args:
        comps: The components to layout.
        sep: Optional Component to interleave between `comps`.
    """
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
DEFAULT_SELECT_COMMANDS: SelectCommandsMap[Any] = {
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
def select(
    comps: Sequence[Renderable[TOrNever]],
    *,
    sep: Renderable[TOrNever] = "\n",
    cursor: TextLike | None = None,
    items_per_page: int = DEFAULT_ITEMS_PER_PAGE,
    controller: SelectController | None = None,
    commands: SelectCommandsMap[TOrNever] | None = None,
) -> ComponentGen2[TOrNever, int]:
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
    commands = commands or DEFAULT_SELECT_COMMANDS

    if cursor is None:
        cursor = "> "

    if isinstance(cursor, str):
        cursor = Text(cursor, style="select.selected")

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


def selectn(
    *comps: Renderable[TOrNever],
    sep: Renderable[TOrNever] = "\n",
    cursor: TextLike | None = None,
    items_per_page: int = DEFAULT_ITEMS_PER_PAGE,
    controller: SelectController | None = None,
    commands: SelectCommandsMap[TOrNever] | None = None,
) -> Component[TOrNever | int]:
    """Variadic interface for `select`.

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
    return select(
        comps,
        sep=sep,
        cursor=cursor,
        items_per_page=items_per_page,
        controller=controller,
        commands=commands,
    )


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
        """Select the current prompt.

        NOTE: Has no effect unless invoked as part of a `command`.
        """
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

        if (key := (yield Loop.POLLINPUT)) in commands:
            if commands[key](controller):
                return controller.prompt
        else:
            controller.insert(key)


class FutureBehaviour(IntEnum):
    RETURN_NEVER = 0
    RETURN_RESULT = 1


def _future_comp_impl[T, R](
    fut: Future[T] | asyncio.Task[T],
    *,
    on_success: Callable[[T], Renderable[R] | None] | None = None,
    on_error: Callable[[BaseException], Renderable[R] | None] | None,
    on_pending: Renderable[R] | None,
    behaviour: FutureBehaviour,
) -> ComponentGen2[R, T | BaseException | None]:
    context = RendererContext.get()
    fut.add_done_callback(lambda _: context.input_handler.interrupt())

    yield on_pending
    yield Loop.POLLINPUT

    while not fut.done():
        yield Loop.NOCHANGE

    try:
        result = fut.result()
    except BaseException as e:
        result = e
        if on_error is not None:
            yield on_error(e)
    else:
        if on_success is not None:
            yield on_success(result)

    if behaviour == FutureBehaviour.RETURN_RESULT:
        yield Loop.NOPOLL
        return result


type FutureType[R] = Future[R] | Awaitable[R]
U = TypeVar("U")


@overload
def futurecomp(
    future: FutureType[U],
    *,
    on_success: Callable[[U], Renderable[TOrNever] | None] | None = None,
    on_error: Callable[[BaseException], Renderable[TOrNever] | None] | None = ...,
    on_pending: Renderable[TOrNever] | None = ...,
    behaviour: Literal[FutureBehaviour.RETURN_NEVER] = ...,
) -> Component[TOrNever]: ...


@overload
def futurecomp(
    future: FutureType[U],
    *,
    on_success: Callable[[U], Renderable[TOrNever] | None] | None = None,
    on_error: Callable[[BaseException], Renderable[TOrNever] | None] | None = ...,
    on_pending: Renderable[TOrNever] | None = ...,
    behaviour: Literal[FutureBehaviour.RETURN_RESULT] = ...,
) -> Component[TOrNever | BaseException | U]: ...


def futurecomp(
    future: FutureType[Any],
    *,
    on_success: Callable[[Any], Renderable[Any] | None] | None = None,
    on_error: Callable[[BaseException], Renderable[Any] | None] | None = None,
    on_pending: Renderable[Any] | None = None,
    behaviour: FutureBehaviour = FutureBehaviour.RETURN_NEVER,
) -> Component[Any]:
    """Component dependent on lifecycle of a future value.

    The return value of this component can be changed by the `behaviour` parameter:
    - RETURN_NEVER: marks this component as `noreturn`.
    - RETURN_RESULT: Returns the result of the future or an Exception.

    Supports both concurrent Futures and asyncio Tasks, if a coroutine is provided, it
    is automatically wrapped in a Task.

    Args:
        future: An asyncio Awaitable or a concurrent Future.
        on_success: Renderable to yield on successfull `future` completion. If None, yields nothing.
        on_error: Renderable to yield on erroneous `future` completion. If None, yields nothing.
        on_pending: Renderable to yield before `future` has completed. If None, yields nothing.
        behaviour: Behaviour of component upon `future` completion.

    Returns:
        A component.
    """
    if not isinstance(future, Future):
        future = asyncio.ensure_future(future)

    return component(
        _future_comp_impl,
        noreturn=behaviour == FutureBehaviour.RETURN_NEVER,
    )(
        future,
        on_success=on_success,
        on_error=on_error,
        on_pending=on_pending,
        behaviour=behaviour,
    )
