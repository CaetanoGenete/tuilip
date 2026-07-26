from typing import Never, assert_type

import pytest
from more_itertools import take
from tuilip.components import noprop
from tuilip.components.types import Component
from tuilip.input.keys import Key
from tuilip.tester import MockCompState, component_tester, mockcomp
from tests.utils import identitycomp


@pytest.mark.parametrize("n", range(1, 10))
def test_noprop_n(n: int) -> None:
    mockstate = MockCompState()
    comp = noprop(mockcomp(mockstate), n=n)

    with component_tester(comp) as tester:
        keyit = iter(Key)
        for key in take(n - 1, keyit):
            tester.next(key)
            assert mockstate.key == Key.NULL

        key = next(keyit)
        tester.next(key)
        assert mockstate.key == key

        assert not tester.done


def test_noprop_indefinitely() -> None:
    mockstate = MockCompState()
    comp = noprop(mockcomp(mockstate), n=0)

    with component_tester(comp) as tester:
        for key in Key:
            tester.next(key)
            assert mockstate.key == Key.NULL

        assert not tester.done


# type checks

assert_type(
    noprop("test"),
    Component[Never],
)

assert_type(
    noprop(identitycomp(10)),
    Component[int],
)

assert_type(
    noprop(identitycomp(31.2)),
    Component[float],
)
