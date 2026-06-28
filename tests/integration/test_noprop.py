import pytest
from more_itertools import take
from tuilip.components import noprop
from tuilip.input.keys import Key
from tuilip.tester import ComponentTester, MockCompState, mockcomp


@pytest.mark.parametrize("n", range(1, 10))
def test_noprop_twice(n: int) -> None:
    mockstate = MockCompState()

    tester = ComponentTester(noprop(mockcomp(mockstate), n=n))

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

    tester = ComponentTester(noprop(mockcomp(mockstate), n=0))

    for key in Key:
        tester.next(key)
        assert mockstate.key == Key.NULL

    assert not tester.done
