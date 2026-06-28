import sys
from typing import IO, Iterable, Mapping

from tuilip.components.types import Component
from tuilip.input.types import InputHandler
from tuilip.input import DefaultInputHandler
from tuilip.render import TextView, render, resolve_indent
from tuilip.render.types import Span, Text

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


def render_styles(spanit: Iterable[Span], theme: Mapping[str, str]) -> str:
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


def clear_lines(nlines: int) -> str:
    return f"\x1b[{nlines}F\x1b[J"


def loop[R](
    *components: Component[R] | Text,
    input_handler: InputHandler = DefaultInputHandler(),
    theme: Mapping[str, str] = DEFAULT_THEME,
    out: IO[str] = sys.stdout,
    auto_flush: bool = True,
    transient: bool = False,
) -> R:
    nlines = 0

    def onrefresh(screen: list[TextView]) -> int:
        nonlocal nlines

        if nlines:
            out.write(clear_lines(nlines))

        rendered = render_styles(resolve_indent(screen), theme)
        out.write(rendered)
        nlines = rendered.count("\n")

        if auto_flush:
            out.flush()

        key = input_handler.read()
        if key == 0x03:
            raise KeyboardInterrupt()
        return key

    try:
        out.write("\x1b[?25l")
        with input_handler.raw():
            return render(*components, onrefresh=onrefresh)
    finally:
        out.write("\x1b[?25h")
        if transient:
            out.write(clear_lines(nlines))
