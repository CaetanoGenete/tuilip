from typing import Any, Callable


def rpadfn[*Ts, R](fn: Callable[[*Ts], R]) -> Callable[[*tuple[*Ts, Any]], R]:
    """Adds an additional positional argument to the end of a callable, with no effect.

    Args:
        fn: The function to mutate.
    """

    def wrapper(*args: *tuple[*Ts, Any]) -> R:
        return fn(*args[:-1])

    return wrapper
