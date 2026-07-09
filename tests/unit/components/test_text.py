from dataclasses import dataclass

import pytest

from tuilip.render.text import Span, Text


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
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(None, None, None),
            spans=[
                Span("abc", style="s1", indent=0),
                Span("de", style="s2", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(1, None, None),
            spans=[
                Span("bc", style="s1", indent=0),
                Span("de", style="s2", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(None, 2, None),
            spans=[
                Span("ab", style="s1", indent=0),
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
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(0, 0, 1),
            spans=[],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(None, None, -1),
            spans=[
                Span("ed", style="s2", indent=0),
                Span("cba", style="s1", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(2, None, -1),
            spans=[
                Span("cba", style="s1", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(3, 0, -1),
            spans=[
                Span("d", style="s2", indent=0),
                Span("cb", style="s1", indent=0),
            ],
        ),
        _TestCase(
            actual=Text("abc", style="s1") + Text("de", style="s2"),
            index=slice(0, 0, -1),
            spans=[],
        ),
    ],
)
def test_slice(test_case: _TestCase) -> None:
    actual = test_case.actual[test_case.index]

    assert actual.spans() == test_case.spans
    assert len(actual) == sum(len(span.value) for span in actual.spans())
