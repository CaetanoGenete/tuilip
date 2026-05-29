from dataclasses import dataclass

from functools import partial, wraps
from typing import Callable, Literal, Never, Unpack, overload
from collections.abc import Mapping, Sequence

from tulip.components._types import NO_STYLE, Component, ComponentGen, Text, TextLike
from tulip.components.utils import pollinput


type ComponentFactory[**P, R] = Callable[P, Component[R]]
type ComponentGenFactory[**P, R] = Callable[P, ComponentGen[R]]


@overload
def component[**P, R](
    fn: Literal[None] = ...,
    *,
    stateless: Literal[False],
) -> Callable[[ComponentGenFactory[P, R]], ComponentFactory[P, R]]: ...


@overload
def component[**P, R](
    fn: Literal[None] = ...,
    *,
    stateless: Literal[True],
) -> Callable[[ComponentGenFactory[P, R]], ComponentFactory[P, Never]]: ...


@overload
def component[**P, R](
    fn: ComponentGenFactory[P, R],
    *,
    stateless: bool = ...,
) -> ComponentFactory[P, R]: ...


def component[**P, R](
    fn: ComponentGenFactory[P, R] | None = None,
    *,
    stateless: bool = False,
) -> (
    ComponentFactory[P, R]
    | Callable[[ComponentGenFactory[P, R]], ComponentFactory[P, R]]
):
    if fn is None:
        return partial(component, stateless=stateless)

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Component[R]:
        return Component(
            stateless=stateless,
            debug_name=fn.__name__,
            gen=fn(*args, **kwargs),
        )

    return wrapper


type StandardCommandsMap[C, *A] = Mapping[str, Callable[[C, Unpack[A]], bool | None]]


@component(stateless=True)
def text(*values: TextLike, style: str = NO_STYLE):
    yield Text(*values, style=style)


type Tabs[R] = Sequence[tuple[str, Component[R] | Text]]


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

    while True:
        tab_idx = controller.tab
        tab_page = tab_idx // tabs_per_page
        npages = len(tabs) // tabs_per_page

        tab_name, tab_comp = tabs[tab_idx]

        yield Text(
            " ",
            Text("<" if tab_page > 0 else " ", style="tabview.arrow"),
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
            Text(" >" if tab_page < npages else "", style="tabview.arrow"),
            "\n",
        )
        yield tab_comp

        yield from pollinput(commands, controller, tabs)


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
def select(
    values: Sequence[str],
    *,
    separator: str = "\n",
    cursor: str | Text | None = None,
    controller: SelectController | None = None,
    commands: StandardCommandsMap[
        SelectController, Sequence[str]
    ] = DEFAULT_SELECT_COMMANDS,
) -> ComponentGen[int]:
    controller = controller or SelectController(index=0)

    if cursor is None:
        cursor = "> "

    if isinstance(cursor, str):
        cursor = Text(cursor, style="select.selected")

    indent = " " * len(cursor)
    while True:
        yield Text.ass(
            Text(indent, value, separator) for value in values[: controller.index]
        )
        yield Text(cursor, values[controller.index], separator)
        yield Text.ass(
            Text(indent, value, separator) for value in values[controller.index + 1 :]
        )

        done, _ = yield from pollinput(commands, controller, values)
        if done:
            return controller.index
