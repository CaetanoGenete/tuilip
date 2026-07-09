from concurrent.futures import ThreadPoolExecutor
from time import sleep

from tuilip.components import loading
from tuilip.render.std import render
from tuilip.render.types import Text


def process() -> str:
    sleep(3)
    return "finished!!!"


with ThreadPoolExecutor(3) as tpe:
    render(
        Text("Header:\n"),
        loading(
            tpe.submit(process),
            placeholder="waiting...",
            exit_on_complete=True,
        ),
    )
