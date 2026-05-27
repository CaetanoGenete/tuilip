from typing import Callable, Concatenate, Protocol
from collections.abc import Generator, Mapping
from tulip.components._types import Signal


class RefreshableController(Protocol):
    refresh: bool


def poll[**P, C: RefreshableController](
    commands: Mapping[str, Callable[Concatenate[C, P], bool | None]],
    controller: C,
    *args: P.args,
    **kwargs: P.kwargs,
) -> Generator[Signal | None, str, tuple[bool, str]]:
    returned = False

    key = yield
    while True:
        if key in commands and commands[key](controller, *args, **kwargs):
            returned = True
            break

        if controller.refresh:
            break

        key = yield Signal.NO_CHANGE

    controller.refresh = False
    return returned, key
