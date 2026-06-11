try:
    from rich.live import Live
    from rich.text import Text as RichText
except ImportError as e:
    raise Exception("Cannot use Rich backend; rich is not installed!") from e

from readchar import readchar
from rich.console import Console
from rich.theme import Theme

from tulip.components.types import Component
from tulip.render import TextView, render
from tulip.render.types import Text

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
    }
)


def loop[R](*components: Component[R] | Text, console: Console | None = None) -> R:
    if console is None:
        console = Console(theme=DEFAULT_THEME)

    with Live(console=console, auto_refresh=False, transient=False) as live:

        def onrefresh(screen: list[TextView]) -> str:
            result = RichText()

            last_indent = 0
            for view in screen:
                view_indent = view.indent

                for span in view.text.spans():
                    indent = view_indent + span.indent
                    parsed_str = span.value

                    if indent > 0:
                        if (diff := indent - last_indent) > 0:
                            parsed_str = f"\x1b[{diff}C{parsed_str}"
                        elif diff < 0:
                            parsed_str = f"\x1b[{-diff}D{parsed_str}"

                        last_char = parsed_str[-1]
                        parsed_str = f"{parsed_str[:-1].replace('\n', f'\n\x1b[{indent}C')}{last_char}"

                        if last_char == "\n":
                            indent = 0

                    last_indent = indent

                    result.append(
                        RichText.from_markup(
                            parsed_str,
                            style=span.style,
                        ),
                    )

            live.update(result, refresh=True)

            key = readchar()
            if key == "\x03":
                raise KeyboardInterrupt()
            return key

        return render(*components, onrefresh=onrefresh)
