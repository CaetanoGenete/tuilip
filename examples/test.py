from typing import assert_type

from tuilip.components import echo_key, prompt, select, selectn, tabview_fixed, tabviewn
from tuilip.render.std import loop
from tuilip.render.types import Text
from tuilip.string import Justify
from tuilip.views import LazySeq

try:
    result = loop(
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
