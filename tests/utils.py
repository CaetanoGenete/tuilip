from typing import assert_type

from tuilip.components import component
from tuilip.components.types import Component, ComponentGen


@component
def identitycomp[T](value: T) -> ComponentGen[T]:
    yield None
    return value


assert_type(identitycomp(1), Component[int])
assert_type(identitycomp("test"), Component[str])
