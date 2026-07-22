from concurrent.futures import ThreadPoolExecutor
from time import sleep

from tuilip.components import FutureBehaviour, futurecomp
from tuilip.functional import identity
from tuilip.render.std import render
from tuilip.render.text import Text


def process() -> str:
    sleep(3)
    return "finished!!!"


with ThreadPoolExecutor(3) as tpe:
    render(
        Text("Header:\n"),
        futurecomp(
            tpe.submit(process),
            on_success=identity,
            on_pending="waiting...",
            behaviour=FutureBehaviour.RETURN_RESULT,
        ),
    )
