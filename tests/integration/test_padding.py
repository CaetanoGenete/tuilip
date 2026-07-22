from typing import assert_type, cast

from tests.utils import identitycomp
from tuilip.components import padding
from tuilip.components.types import Component, Renderable


assert_type(
    padding("test", indent=0),
    str,
)

assert_type(
    padding(identitycomp("test"), indent=0),
    Component[str],
)

assert_type(
    padding(identitycomp(10), indent=0),
    Component[int],
)

assert_type(
    padding(cast(Renderable[str], identitycomp("test")), indent=0),
    Renderable[str],
)
