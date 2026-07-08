import asyncio

from tuilip.components import aloading
from tuilip.render.std import aloop
from tuilip.render.types import Text


async def process() -> str:
    await asyncio.sleep(3)
    return "finished!!!"


async def main() -> None:
    await aloop(
        Text("Header:\n"),
        aloading(
            process(),
            placeholder="waiting...",
            exit_on_complete=True,
        ),
    )


asyncio.run(main())
