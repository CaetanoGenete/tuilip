from __future__ import annotations

from dataclasses import dataclass, field
import sys
from typing import IO, TYPE_CHECKING, Iterable, Mapping, Self

from tuilip.components.types import TOrNever
from tuilip.input import DefaultAsyncInputHandler, DefaultInputHandler
from tuilip.render import BuildOutput, aloop, loop, resolve_indent, render_animations

if TYPE_CHECKING:
    from tuilip.components.types import Renderable
    from tuilip.render.text import Span
    from tuilip.input.types import AsyncInputHandler, BlockingInputHandler
    from types import TracebackType


ANSI_MAP = {
    # --- Styles & Formatting ---
    "reset": "0",
    "bold": "1",
    "dim": "2",
    "italic": "3",
    "underline": "4",
    "blink_slow": "5",
    "blink_rapid": "6",
    "reverse": "7",
    "hidden": "8",
    "strikethrough": "9",
    # --- Standard Foreground Colors ---
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    # --- Standard Background Colors ---
    "bblack": "40",
    "bred": "41",
    "bgreen": "42",
    "byellow": "43",
    "bblue": "44",
    "bmagenta": "45",
    "bcyan": "46",
    "bwhite": "47",
    # --- Bright/High-Intensity Foreground Colors ---
    "bright_black": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
    # --- Bright/High-Intensity Background Colors ---
    "bbright_black": "100",
    "bbright_red": "101",
    "bbright_green": "102",
    "bbright_yellow": "103",
    "bbright_blue": "104",
    "bbright_magenta": "105",
    "bbright_cyan": "106",
    "bbright_white": "107",
}

DEFAULT_THEME = {
    # tabview
    "tabview.selected": "red",
    "tabview.unselected": "blue",
    "tabview.arrow-enabled": "",
    "tabview.arrow-disabled": "dim",
    # select
    "select.selected": "green",
    "select.bullets": "dim",
    "select.pager": "dim",
    # Prompt:
    "prompt.cursor": "black bwhite",
}


def apply_styles(spanit: Iterable[Span], theme: Mapping[str, str]) -> str:
    return "".join(
        [
            f"\x1b[{
                ';'.join(
                    ANSI_MAP[style]
                    for style in theme.get(span.style, span.style).split(' ')
                    if style
                )
            }m{span.value}\x1b[0m"
            if span.style
            else span.value
            for span in spanit
        ]
    )


CURSOR_HIDE = "\x1b[?25l"
CURSOR_SHOW = "\x1b[?25h"


def _clear_lines(nlines: int) -> str:
    if nlines == 0:
        return "\r\x1b[J"
    return f"\x1b[{nlines}F\x1b[J"


@dataclass(slots=True)
class Painter:
    theme: Mapping[str, str]
    auto_flush: bool
    out: IO[str]
    transient: bool
    nlines: int = field(default=0, init=False)

    def draw(self, screen: BuildOutput, frame: int) -> None:
        rendered = render_animations(screen, frame)
        rendered = resolve_indent(rendered)
        rendered = apply_styles(rendered, self.theme)

        self.out.write(_clear_lines(self.nlines))
        self.out.write(rendered)

        self.nlines = rendered.count("\n")

        if self.auto_flush:
            self.out.flush()

    def __enter__(self) -> Self:
        self.out.write(CURSOR_HIDE)
        return self

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.out.write(CURSOR_SHOW)
        if self.transient:
            self.out.write(_clear_lines(self.nlines))


DEFAULT_ANIMATION_PERIOD = 1 / 10


def render(
    *components: Renderable[TOrNever],
    input_handler: BlockingInputHandler | None = None,
    theme: Mapping[str, str] = DEFAULT_THEME,
    out: IO[str] = sys.stdout,
    auto_flush: bool = True,
    transient: bool = False,
    animation_period: float = DEFAULT_ANIMATION_PERIOD,
) -> TOrNever:
    input_handler = input_handler or DefaultInputHandler()

    with (
        Painter(
            theme=theme,
            out=out,
            auto_flush=auto_flush,
            transient=transient,
        ) as painter,
        input_handler.raw(),
    ):
        return loop(
            *components,
            input_handler=input_handler,
            draw=painter.draw,
            animation_period=animation_period,
        )


async def arender(
    *components: Renderable[TOrNever],
    input_handler: AsyncInputHandler | None = None,
    theme: Mapping[str, str] = DEFAULT_THEME,
    out: IO[str] = sys.stdout,
    auto_flush: bool = True,
    transient: bool = False,
    animation_period: float = DEFAULT_ANIMATION_PERIOD,
) -> TOrNever:
    input_handler = input_handler or DefaultAsyncInputHandler()

    with (
        Painter(
            theme=theme,
            out=out,
            auto_flush=auto_flush,
            transient=transient,
        ) as painter,
        input_handler.raw(),
    ):
        return await aloop(
            *components,
            input_handler=input_handler,
            draw=painter.draw,
            animation_period=animation_period,
        )
