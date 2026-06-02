from dataclasses import dataclass
from itertools import repeat
from more_itertools import interleave, intersperse

from functools import partial, wraps
from typing import Callable, Literal, Never, Unpack, overload
from collections.abc import Mapping, Sequence

from tulip.components._types import (
    NO_STYLE,
    Component,
    ComponentGen,
    Renderable,
    Signal,
    Text,
    TextLike,
)
from tulip.components.utils import pollinput, pollrefresh


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


@component(stateless=True)
def text(*values: TextLike, style: str = NO_STYLE):
    yield Text(*values, style=style)


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


type Tabs[R] = Sequence[tuple[str, Renderable[R]]]


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
DEFAULT_TABVIEW_COMMANDS = {
    "a": TabController.prev,
    "d": TabController.next,
}


@component
def tabview[R](
    tabs: Tabs[R],
    *,
    tabs_per_page: int = DEFAULT_TABS_PER_PAGE,
    controller: TabController | None = None,
    commands: StandardCommandsMap[TabController, Tabs[R]] = DEFAULT_TABVIEW_COMMANDS,
) -> ComponentGen[R]:
    controller = controller or TabController(tab=0)

    last_tab = controller.tab
    while True:
        tab_idx = controller.tab
        tab_page = tab_idx // tabs_per_page
        npages = len(tabs) // tabs_per_page

        tab_name, tab_comp = tabs[tab_idx]

        yield Text(
            " ",
            Text(
                "<",
                style="tabview.arrow-enabled"
                if tab_page > 0
                else "tabview.arrow-disabled",
            ),
            *(
                Text(" ", Text(tab, style="tabview.unselected"))
                for tab, _ in tabs[tab_page * tabs_per_page : tab_idx]
            ),
            " ",
            Text(tab_name, style="tabview.selected"),
            *(
                Text(" ", Text(tab, style="tabview.unselected"))
                for tab, _ in tabs[tab_idx + 1 : (tab_page + 1) * tabs_per_page]
            ),
            Text(
                " >",
                style="tabview.arrow-enabled"
                if tab_page < npages
                else "tabview.arrow-disabled",
            ),
            "\n",
        )

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


@component
def select[R](
    values: Sequence[Renderable[R]],
    *,
    separator: TextLike = "\n",
    cursor: TextLike | None = None,
    controller: SelectController | None = None,
    commands: StandardCommandsMap[
        SelectController,
        Sequence[Renderable[R]]
    ] = DEFAULT_SELECT_COMMANDS,
) -> ComponentGen[R | int]:
    controller = controller or SelectController(index=0)

    if cursor is None:
        cursor = "> "

    if isinstance(cursor, str):
        cursor = Text(cursor, style="select.selected")

    if isinstance(separator, str):
        separator = Text(separator)

    indent = len(cursor)
    while True:
        yield padding(
            *intersperse(
                separator,
                values[: controller.index],
            ),
            start=True,
            indent=indent,
        )

        yield Text("\n", cursor) if controller.index > 0 else cursor
        yield values[controller.index]

        yield padding(
            *interleave(
                repeat(separator),
                values[controller.index + 1 :],
            ),
            indent=indent,
        )

        if (yield from pollrefresh(commands, controller, values)).done:
            return controller.index
