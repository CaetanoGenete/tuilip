from tulip.render.rich import loop
from tulip.components import select, text
from tulip.components import tabview

try:
    result = loop(
        text("Header:\n"),
        tabview(
            [
                ("tab1", text("tab1")),
                ("tab2", text("[red]tab2[/red]")),
                ("tab3", select([f"test - {i}" for i in range(10)])),
                ("tab4", text("tab4")),
            ]
        ),
    )
except KeyboardInterrupt:
    pass
else:
    print(f"selected: {result}")
