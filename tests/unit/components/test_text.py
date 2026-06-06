import pytest

from dataclasses import dataclass
from tulip.components._types import Span, Text


@dataclass
class _TestCase:
    actual: Text
    index: slice
    spans: list[Span]


@pytest.mark.parametrize(
    "test_case",
    [
        _TestCase(
            actual=Text("abcdef", style="s1"),
            index=slice(2, 5),
            spans=[
                Span("cde", style="s1", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(2, 4),
            spans=[
                Span("c", style="s1", indent=0),
                Span("d", style="s2", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(1, 4, 2),
            spans=[
                Span("b", style="s1", indent=0),
                Span("d", style="s2", indent=0),
            ],
        ),
        _TestCase(
            actual=(
                Text("abc", style="s1")
                + Text("defg", style="s2")
                + Text("hij", style="s3")
            ),
            index=slice(1, 20, 2),
            spans=[
                Span("b", style="s1", indent=0),
                Span("df", style="s2", indent=0),
                Span("hj", style="s3", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1")
            + Text("defg", style="s2")
            + Text("hij", style="s3"),
            index=slice(2, 20, 5),
            spans=[
                Span("c", style="s1", indent=0),
                Span("h", style="s3", indent=0),
            ],
        ),
    ],
)
def test_slice(test_case: _TestCase) -> None:
    actual = test_case.actual[test_case.index]

    assert actual.spans() == test_case.spans
