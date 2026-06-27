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
    "reset": "\x1b[0m",
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "italic": "\x1b[3m",
    "underline": "\x1b[4m",
    "blink_slow": "\x1b[5m",
    "blink_rapid": "\x1b[6m",
    "reverse": "\x1b[7m",
    "hidden": "\x1b[8m",
    "strikethrough": "\x1b[9m",
    # --- Standard Foreground Colors ---
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    # --- Standard Background Colors ---
    "bblack": "\x1b[40m",
    "bred": "\x1b[41m",
    "bgreen": "\x1b[42m",
    "byellow": "\x1b[43m",
    "bblue": "\x1b[44m",
    "bmagenta": "\x1b[45m",
    "bcyan": "\x1b[46m",
    "bwhite": "\x1b[47m",
    # --- Bright/High-Intensity Foreground Colors ---
    "bright_black": "\x1b[90m",
    "bright_red": "\x1b[91m",
    "bright_green": "\x1b[92m",
    "bright_yellow": "\x1b[93m",
    "bright_blue": "\x1b[94m",
    "bright_magenta": "\x1b[95m",
    "bright_cyan": "\x1b[96m",
    "bright_white": "\x1b[97m",
    # --- Bright/High-Intensity Background Colors ---
    "bbright_black": "\x1b[100m",
    "bbright_red": "\x1b[101m",
    "bbright_green": "\x1b[102m",
    "bbright_yellow": "\x1b[103m",
    "bbright_blue": "\x1b[104m",
    "bbright_magenta": "\x1b[105m",
    "bbright_cyan": "\x1b[106m",
    "bbright_white": "\x1b[107m",
}


def render_styles(spanit: Iterable[Span], theme: Mapping[str, str]) -> str:
    result = ""
    for span in spanit:
        result += "".join(
            ANSI_MAP[style]
            for style in theme.get(span.style, span.style).split(" ")
            if style
        )
        result += f"{span.value}\x1b[0m"

    return result


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
