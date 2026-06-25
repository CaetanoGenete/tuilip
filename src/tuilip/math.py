def divup(num: int, denom: int) -> int:
    """Integer division rounded up to the nearest integer.

    Args:
        num: The numerator.
        denom: The denomiator.

    Returns:
        An integer.
    """
    return (num + denom - 1) // denom
