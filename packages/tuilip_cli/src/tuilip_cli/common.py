from tuilip.components import component
from tuilip.components.types import ComponentGen
from tuilip.components.utils import pollcond
from tuilip.input.keys import Key


@component
def exit_on_interrupt() -> ComponentGen[None]:
    yield from pollcond(
        {Key.CTRL_C: lambda: True},
        lambda: False,
    )
    return None
