try:
    from rich.live import Live
    from rich.text import Text as RichText
    from rich.console import Console
    from rich.theme import Theme
except ImportError as e:
    raise Exception("Cannot use Rich backend; rich is not installed!") from e

from tuilip.components.types import Component
from tuilip.input.types import BlockingInputHandler
from tuilip.input import DefaultInputHandler
from tuilip.render import BuildOutput, loop, render_animations, resolve_indent
from tuilip.render.text import Text

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


def render[R](
    *components: Component[R] | Text,
    console: Console | None = None,
    input_handler: BlockingInputHandler = DefaultInputHandler(),
    animation_period: float = 1 / 10,
) -> R:
    if console is None:
        console = Console(theme=DEFAULT_THEME)

    def draw(screen: BuildOutput, frame: int) -> None:
        rendered = render_animations(screen, frame)
        rendered = resolve_indent(rendered)

        result = RichText.assemble(*((span.value, span.style) for span in rendered))
        live.update(result, refresh=True)

    with (
        Live(console=console, auto_refresh=False, transient=False) as live,
        input_handler.raw(),
    ):
        return loop(
            *components,
            input_handler=input_handler,
            draw=draw,
            animation_period=animation_period,
        )
