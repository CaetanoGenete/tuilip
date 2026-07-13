from tuilip.input.keys import Key
from tuilip.render.anim import loading_spinner_1
from tuilip.components import ComponentGen
from tuilip.components import component
from tuilip.components.utils import pollcond
import asyncio

from tuilip.render.std import arender


@component
def exit_on_interrupt() -> ComponentGen[None]:
    yield from pollcond(
        {Key.CTRL_C: lambda: True},
        lambda: False,
    )
    return None


async def main() -> None:
    await arender(
        loading_spinner_1(),
        exit_on_interrupt(),
        animation_period=1 / 10,
    )


asyncio.run(main())
