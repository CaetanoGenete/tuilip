from typing import Callable, Never, assert_type
import time
import pytest
import asyncio

from tuilip.components import FutureBehaviour, futurecomp
from tuilip.components.types import Component
from tests.utils import identitycomp
from tuilip.tester import component_tester


class _TestCoroException(Exception): ...


async def identity_coro[R](
    value: R,
    *,
    sleep: float = 0,
    error: bool = False,
) -> R:
    if sleep > 0:
        await asyncio.sleep(sleep)

    if error:
        raise _TestCoroException()

    return value


async def poll(
    init_wait: float, cond: Callable[[], bool], max_wait: float, interval: float = 0.02
) -> None:
    start = time.monotonic()
    await asyncio.sleep(init_wait)

    while cond() == False and (time.monotonic() - start) < max_wait:
        await asyncio.sleep(interval)


@pytest.mark.asyncio
async def test_coro_completes_on_success():
    expected = "test_coro_completes results"

    comp = futurecomp(
        identity_coro(expected, sleep=0.1),
        behaviour=FutureBehaviour.RETURN_RESULT,
    )

    with component_tester(comp) as tester:
        await poll(0.1, lambda: tester.done, 0.2)
        assert tester.done
        assert tester.ret == expected


@pytest.mark.asyncio
async def test_coro_completes_on_error():
    comp = futurecomp(
        identity_coro("test_coro_completes results", sleep=0.1, error=True),
        behaviour=FutureBehaviour.RETURN_RESULT,
    )

    with component_tester(comp) as tester:
        await poll(0.1, lambda: tester.done, 0.2)
        assert tester.done
        assert isinstance(tester.ret, _TestCoroException)


# type checks

## defaults

assert_type(
    futurecomp(identity_coro(10)),
    Component[Never],
)

## RETURN_NEVER

assert_type(
    futurecomp(
        identity_coro(10),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[Never],
)

assert_type(
    futurecomp(
        identity_coro(10),
        on_success=lambda _: identitycomp(10.0),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[float],
)
assert_type(
    futurecomp(
        identity_coro(10),
        on_success=lambda _: "test",
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[Never],
)

assert_type(
    futurecomp(
        identity_coro(10),
        on_error=lambda _: identitycomp(10.0),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[float],
)
assert_type(
    futurecomp(
        identity_coro(10),
        on_error=lambda _: "test",
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[Never],
)

assert_type(
    futurecomp(
        identity_coro(10),
        on_pending=identitycomp(10.0),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[float],
)
assert_type(
    futurecomp(
        identity_coro(10),
        on_pending="test",
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[Never],
)


assert_type(
    futurecomp(
        identity_coro(10),
        on_success=lambda _: identitycomp(10.0),
        on_error=lambda _: identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[float | str],
)
assert_type(
    futurecomp(
        identity_coro(10),
        on_success=lambda _: identitycomp(10.0),
        on_pending=identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[float | str],
)
assert_type(
    futurecomp(
        identity_coro(10),
        on_error=lambda _: identitycomp(10.2),
        on_pending=identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[float | str],
)

assert_type(
    futurecomp(
        identity_coro([32]),
        on_success=lambda v: identitycomp(v),
        on_error=lambda _: identitycomp(10.2),
        on_pending=identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_NEVER,
    ),
    Component[float | str | list[int]],
)

## RETURN_RESULT

assert_type(
    futurecomp(
        identity_coro(10),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[int | BaseException],
)

assert_type(
    futurecomp(
        identity_coro([21]),
        on_success=lambda _: identitycomp(10.0),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[float | list[int] | BaseException],
)
assert_type(
    futurecomp(
        identity_coro([21]),
        on_success=lambda _: "test",
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[Never | list[int] | BaseException],
)

assert_type(
    futurecomp(
        identity_coro([21]),
        on_error=lambda _: identitycomp(10.0),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[float | list[int] | BaseException],
)
assert_type(
    futurecomp(
        identity_coro([21]),
        on_error=lambda _: "test",
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[Never | list[int] | BaseException],
)

assert_type(
    futurecomp(
        identity_coro([21]),
        on_pending=identitycomp(10.0),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[float | list[int] | BaseException],
)
assert_type(
    futurecomp(
        identity_coro([21]),
        on_pending="test",
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[Never | list[int] | BaseException],
)


assert_type(
    futurecomp(
        identity_coro([21]),
        on_success=lambda _: identitycomp(10.0),
        on_error=lambda _: identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[float | str | list[int] | BaseException],
)
assert_type(
    futurecomp(
        identity_coro([21]),
        on_success=lambda _: identitycomp(10.0),
        on_pending=identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[float | str | list[int] | BaseException],
)
assert_type(
    futurecomp(
        identity_coro([21]),
        on_error=lambda _: identitycomp(10.2),
        on_pending=identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[float | str | list[int] | BaseException],
)

assert_type(
    futurecomp(
        identity_coro([32]),
        on_success=lambda v: identitycomp(v),
        on_error=lambda _: identitycomp(10.2),
        on_pending=identitycomp("test"),
        behaviour=FutureBehaviour.RETURN_RESULT,
    ),
    Component[float | str | list[int] | BaseException],
)
