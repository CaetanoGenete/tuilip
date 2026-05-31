try:
    from rich.text import Text as RichText
    from rich.live import Live
except ImportError as e:
    raise Exception("Cannot use Rich backend; rich is not installed!") from e

from rich.console import Console
from rich.theme import Theme
from tulip.components._types import CompNode, Component, Text
from tulip.render import render
from readchar import readchar

DEFAULT_THEME = Theme(
    {
        "tabview.selected": "red",
        "tabview.unselected": "blue",
        "tabview.arrow-enabled": "",
        "tabview.arrow-disabled": "dim",
        "select.selected": "green",
    }
)


def loop[R](*components: Component[R] | Text, console: Console | None = None) -> R:
    if console is None:
        console = Console(theme=DEFAULT_THEME)

    with Live(console=console, auto_refresh=False, transient=False) as live:

        def onrefresh(screen: list[Text], _: list[CompNode[R]]) -> str:
            rendered = RichText.assemble(
                *(
                    RichText.from_markup(span.value, style=span.style, end="")
                    for text in screen
                    for span in text.spans()
                ),
                end="",
            )
            live.update(rendered, refresh=True)

            key = readchar()
            if key == "\x03":
                raise KeyboardInterrupt()
            return key

        return render(*components, onrefresh=onrefresh)
