import os
import sys
from tuilip.input.keys import Key
from tuilip.render.text import Text
from tuilip.render.std import render
from tuilip import components
from tuilip.render.text import NO_STYLE
from tuilip.views import MapView


TTY = "CONIN$" if sys.platform == "win32" else "/dev/tty"


def select(options: list[str]) -> int:
    if not os.isatty(sys.stdin.fileno()):
        options += sys.stdin.read().splitlines()

        try:
            fd = os.open(TTY, os.O_RDWR)
            os.dup2(fd, 0)
            os.close(fd)
            sys.stdin = open(0, "r")
        except OSError as e:
            print(f"Failed to reopen terminal handle:", e, file=sys.stderr)

    controller = components.SelectController(0)
    result = render(
        components.select(
            MapView(
                tuple(enumerate(options)),
                mapfn=lambda item: Text(
                    item[1],
                    style="select.selected"
                    if item[0] == controller.index
                    else NO_STYLE,
                ),
            ),
            controller=controller,
        ),
        components.onkey(
            dict.fromkeys((Key.CTRL_C, Key.ESCAPE), lambda: -1),
        ),
    )

    if result == -1:
        return 0

    sys.stdout.write("\n")
    sys.stdout.write(options[result])

    return 0
