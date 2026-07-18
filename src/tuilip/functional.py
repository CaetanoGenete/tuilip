from typing import Any, Callable, Iterator


def rpadfn[*Ts, R](fn: Callable[[*Ts], R]) -> Callable[[*tuple[*Ts, Any]], R]:
    """Adds an additional positional argument to the end of a callable, with no effect.

    Args:
        fn: The function to mutate.
    """

    def wrapper(*args: *tuple[*Ts, Any]) -> R:
        return fn(*args[:-1])

    return wrapper


def atend(iterator: Iterator[Any]) -> bool:
    """Checks iterator is at end. Advances iterator.

    Args:
        iterator: An iterator

    Returns:
        True if at end, otherwise False.
    """
    try:
        next(iterator)
        return False
    except StopIteration:
        return True


def identity[T](x: T) -> T:
    return x
