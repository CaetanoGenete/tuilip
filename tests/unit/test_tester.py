from tuilip.tester import component_tester, mockcomp
from more_itertools import one


def test_rebuilt() -> None:
    with component_tester(mockcomp()) as tester:
        assert one(tester.find("./mockcomp")).changed
