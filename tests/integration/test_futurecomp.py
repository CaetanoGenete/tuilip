from typing import Never, assert_type

from tuilip.components import FutureBehaviour, futurecomp
from tuilip.components.types import Component
from tests.utils import identitycomp


async def identity_coro[R](value: R) -> R:
    return value


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
