from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Awaitable, Generator, Iterable

from tuilip.input.keys import Key
from tuilip.components import ComponentGen, ComponentGen2, seqn, seq
from tuilip.components import component
from tuilip.components.types import Component
from tuilip.render.anim import loading_spinner_1
from tuilip.components.utils import pollcond
import asyncio
import random

from tuilip.components import loading
from tuilip.render.anim import animated_text
from tuilip.render.std import arender
from tuilip.render.text import Text
from tuilip.render.types import Loop


@component
def exit_on_interrupt() -> ComponentGen[None]:
    yield from pollcond(
        {Key.CTRL_C: lambda: True},
        lambda: False,
    )
    return None


@dataclass
class LoadingController:
    init_message: str | Text

    def __post_init__(self) -> None:
        self.__context = ContextVar(
            "controller_context",
            default=self.init_message,
        )

    @property
    def message(self) -> str | Text:
        return self.__context.get()

    @message.setter
    def message(self, value: str | Text, /) -> None:
        self.__context.set(value)

    def from_task(self, task: asyncio.Task[Any]) -> str | Text:
        return task.get_context().get(
            self.__context,
            self.init_message,
        )


cont = LoadingController("starting...")


async def process(i: int) -> str:
    await asyncio.sleep(2 + random.random() * 3)
    cont.message = "still loading..."
    await asyncio.sleep(1 + random.random() * 2)
    cont.message = "done!"
    return f"result {i}"


@animated_text
def _aloadinglist_text(
    task: asyncio.Task[Any],
    controller: LoadingController,
) -> Generator[str | Text, None, None]:
    while True:
        yield controller.from_task(task)


@component
def _aloadinglist_completed[R](values: list[R]) -> ComponentGen[list[R]]:
    yield Loop.NOPOLL
    return values


@component(noreturn=True)
def aloadinglist[R](
    futs: Iterable[Awaitable[R]],
    controller: LoadingController | None = None,
) -> ComponentGen2[list[R], None]:
    controller = controller or LoadingController("loading...")

    tasks = list(map(asyncio.ensure_future, futs))
    yield seqn(
        *(
            loading(
                future=task,
                on_complete=lambda _, c=controller, f=task: Text("✓ ", c.from_task(f)),
                placeholder=seq(
                    [
                        loading_spinner_1(),
                        _aloadinglist_text(task, controller),
                    ],
                    sep=" ",
                ),
            )
            for task in tasks
        ),
        loading(
            asyncio.gather(*tasks),
            on_complete=_aloadinglist_completed,
        ),
        sep="\n",
    )


def aloadinglistn[R](
    *futs: Awaitable[R],
    controller: LoadingController | None = None,
) -> Component[list[R]]:
    return aloadinglist(futs, controller=controller)


async def main() -> None:
    result = await arender(
        Text("Header:\n"),
        aloadinglistn(
            process(0),
            process(1),
            process(2),
            controller=cont,
        ),
        exit_on_interrupt(),
    )

    print(result)


asyncio.run(main())
