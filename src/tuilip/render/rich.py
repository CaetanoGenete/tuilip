try:
    from rich.live import Live
    from rich.text import Text as RichText
except ImportError as e:
    raise Exception("Cannot use Rich backend; rich is not installed!") from e

from rich.console import Console
from rich.theme import Theme

from tuilip.components.types import Component
from tuilip.input.types import InputHandler
from tuilip.input import DefaultInputHandler
from tuilip.render import TextView, render, resolve_indent
from tuilip.render.types import Text

DEFAULT_THEME = Theme(
    {
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
        "prompt.cursor": "black on white",
    }
)


def loop[R](
    *components: Component[R] | Text,
    console: Console | None = None,
    input_handler: InputHandler = DefaultInputHandler(),
) -> R:
    if console is None:
        console = Console(theme=DEFAULT_THEME)

    def onrefresh(screen: list[TextView]) -> int:
        result = RichText.assemble(
            *((span.value, span.style) for span in resolve_indent(screen))
        )

        live.update(result, refresh=True)

        key = input_handler.read()
        if key == 0x03:
            raise KeyboardInterrupt()
        return key

    with (
        Live(console=console, auto_refresh=False, transient=False) as live,
        input_handler.raw(),
    ):
        return render(*components, onrefresh=onrefresh)
