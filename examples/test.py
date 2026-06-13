from typing import assert_type

from tulip.components import echo_key, prompt, select, tabview, tabview_fixed
from tulip.render.rich import loop
from tulip.render.types import Text
from tulip.string import Justify
from tulip.views import LazySeq

try:
    result = loop(
        Text("Header:\n"),
        tabview(
            [
                ("tab1", Text("tab1")),
                ("tab 2", prompt()),
                ("tab3", echo_key()),
                ("tab4", select(LazySeq(200, lambda i: f"item - {i}"))),
                (
                    "tab5",
                    select(
                        [
                            Text("item - a"),
                            select(LazySeq(3, lambda i: f"item - {i}")),
                            Text("item - b"),
                            Text("item - c"),
                            Text("item - d"),
                        ]
                    ),
                ),
            ],
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
    print(f"selected: {result}")
