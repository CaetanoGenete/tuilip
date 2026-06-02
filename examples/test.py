from tulip.components._types import Text
from tulip.render.rich import loop
from tulip.components import select
from tulip.components import tabview

try:
    inner_select = select(["a", "b", "c"])

    result = loop(
        Text("Header:\n"),
        tabview(
            [
                ("tab1", Text("tab1")),
                ("tab2", Text("tab2")),
                ("tab3", select([f"item - {i}" for i in range(200)])),
                ("tab4", Text("tab4")),
            ]
        ),
    )
except KeyboardInterrupt:
    pass
else:
    print(f"selected: {result}")
