from typing import Never, assert_type

from tuilip.components import (
    component,
    prompt,
    select,
    selectn,
    tabview_fixed,
    tabviewn,
)
from tuilip.components.types import ComponentGen
from tuilip.render.std import render
from tuilip.render.types import Signal
from tuilip.render.text import Text
from tuilip.string import Justify
from tuilip.views import LazySeq


@component
def echo_key() -> ComponentGen[Never]:
    yield "Key: "
    while True:
        yield f"Key: {(yield Signal.POLLINPUT)}"


try:
    result = render(
        Text("Header:\n"),
        tabviewn(
            ("tab1", Text("tab1")),
            ("tab 2", prompt()),
            ("tab3", echo_key()),
            ("tab4", select(LazySeq(200, lambda i: f"item - {i}"))),
            (
                "tab5",
                selectn(
                    Text("item - a"),
                    select(LazySeq(3, lambda i: f"item - {i}")),
                    Text("item - b"),
                    Text("item - c"),
                    Text("item - d"),
                ),
            ),
            heading=tabview_fixed(
                width=10,
                # sep="[dim]~[/dim]",
                # fill="[dim]~[/dim]",
                justify=Justify.CENTER,
            ),
        ),
    )
    assert_type(result, str | int)

except KeyboardInterrupt:
    pass
else:
    print(f"\nselected: {result}")
