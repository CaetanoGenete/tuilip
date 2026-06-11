from tulip.components import select, tabview, tabview_fixed
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
                ("tab 2", Text("tab2")),
                ("tab3", select(LazySeq(200, lambda i: f"item - {i}"))),
                (
                    "tab4",
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
except KeyboardInterrupt:
    pass
else:
    print(f"selected: {result}")
