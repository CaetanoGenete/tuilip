from tuilip.input.keys import Key
from tuilip.components import ComponentGen
from tuilip.components import component
from tuilip.components.utils import pollcond
from tuilip.functional import identity
from tuilip.components import seq
import asyncio
import random

from tuilip.components import futurecomp
from tuilip.render.std import arender
from tuilip.render.text import Text


async def process() -> str:
    await asyncio.sleep(2 + random.random() * 3)
    return "finished!!!"


@component
def exit_on_interrupt() -> ComponentGen[None]:
    yield from pollcond(
        {Key.CTRL_C: lambda: True},
        lambda: False,
    )
    return None


async def main() -> None:
    await arender(
        Text("Header:\n"),
        seq(
            [
                futurecomp(
                    process(),
                    on_success=identity,
                    on_pending="waiting...",
                )
                for _ in range(10)
            ],
            sep="\n",
        ),
        exit_on_interrupt(),
    )


asyncio.run(main())
