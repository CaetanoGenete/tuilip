try:
    from rich.text import Text as RichText
    from rich.live import Live
except ImportError as e:
    raise Exception("Cannot use Rich backend. Rich is not installed!") from e

from tulip.components._types import Component
from tulip.render import render
from typing import Any
from readchar import readchar


def loop[R](*components: Component[R]) -> R:
    with Live(auto_refresh=False, transient=False) as live:

        def onrefresh(screen: list[str], _: Any) -> str:
            live.update(
                RichText().join(map(RichText.from_markup, screen)),
                refresh=True,
            )

            key = readchar()
            if key == "\x03":
                raise KeyboardInterrupt()
            return key

        return render(*components, onrefresh=onrefresh)
