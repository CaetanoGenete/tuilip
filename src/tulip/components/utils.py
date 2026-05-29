from typing import Callable, Concatenate, Protocol
from collections.abc import Generator, Mapping
from tulip.components._types import Signal


class RefreshableController(Protocol):
    refresh: bool


def pollinput[**P, C: RefreshableController](
    commands: Mapping[str, Callable[Concatenate[C, P], bool | None]],
    controller: C,
    *args: P.args,
    **kwargs: P.kwargs,
) -> Generator[Signal | None, str, tuple[bool, str]]:
    """Component snippet for polling for application input.

    Typical tulip polling loop.

    Args:
        commands: Upon receiving an input `code`, invokes `commands[code]`.
        controller: A controller object.
        args: Additional positional args to pass to commands callable.
        kwargs: Addtional keyword args to pass to commands callable.

    Yields:
        NO_CHANGE signals, until controller.refresh = true.
    """
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
