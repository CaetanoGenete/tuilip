from collections.abc import Generator, Mapping
from typing import Callable, Concatenate, NamedTuple, Protocol

from tulip.render.types import Signal


class PollResult(NamedTuple):
    done: bool
    key: int


def pollcond[**P](
    commands: Mapping[int, Callable[P, bool | None]],
    poll: Callable[P, bool],
    *args: P.args,
    **kwargs: P.kwargs,
) -> Generator[Signal | None, int, PollResult]:
    """Component snippet for input polling.

    Polls until `poll` return `True` or truthy return from `commands`.

    Args:
        commands: Upon receiving an input `code`, invokes `commands[code]`.
        poll: Polling condition, return `True` to stop.
        args: Additional positional args to pass to commands callable.
        kwargs: Addtional keyword args to pass to commands callable.

    Yields:
        NO_CHANGE signals, until conditions are satisfied.
    """

    returned = False

    key = yield Signal.POLLINPUT
    while True:
        if key in commands and commands[key](*args, **kwargs):
            returned = True
            break

        if poll(*args, **kwargs):
            break

        key = yield Signal.NOCHANGE

    return PollResult(returned, key)


class RefreshableController(Protocol):
    refresh: bool


def _pollrefresh[**P](
    controller: RefreshableController,
    *args: P.args,
    **kwargs: P.kwargs,
) -> bool:
    del args
    del kwargs
    return controller.refresh


def pollrefresh[**P, C: RefreshableController](
    commands: Mapping[int, Callable[Concatenate[C, P], bool | None]],
    controller: C,
    *args: P.args,
    **kwargs: P.kwargs,
) -> Generator[Signal | None, int, PollResult]:
    """Component snippet for typical tulip polling.

    Polls for condition `controller.refresh = True` and truthy return from `commands`.

    Args:
        commands: Upon receiving an input `code`, invokes `commands[code]`.
        controller: A controller object.
        args: Additional positional args to pass to commands callable.
        kwargs: Addtional keyword args to pass to commands callable.

    Yields:
        NO_CHANGE signals, until conditions are satisfied.
    """

    result = yield from pollcond(
        commands,
        _pollrefresh,
        controller,
        *args,
        **kwargs,
    )
    controller.refresh = False

    return result
