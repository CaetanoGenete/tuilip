from contextlib import nullcontext
import msvcrt
from typing import ContextManager, final

from tuilip.input.types import InputHandler
from tuilip.input.keys import Key

SPECIAL_KEY_MAP = {
    71: Key.HOME,
    72: Key.UP,
    73: Key.PAGE_UP,
    75: Key.LEFT,
    77: Key.RIGHT,
    79: Key.END,
    80: Key.DOWN,
    81: Key.PAGE_DOWN,
    83: Key.SDEL,
    115: Key.CTRL_LEFT,
    116: Key.CTRL_RIGHT,
    141: Key.CTRL_UP,
    145: Key.CTRL_DOWN,
    155: Key.META_LEFT,
    157: Key.META_RIGHT,
    152: Key.META_UP,
    160: Key.META_DOWN,
}


@final
class Win32InputHandler(InputHandler):
    def read(self) -> int:
        ch = msvcrt.getch()

        # Parse special multi character keys
        # https://learn.microsoft.com/cpp/c-runtime-library/reference/getch-getwch#remarks
        if ch in b"\x00\xe0":
            return SPECIAL_KEY_MAP.get(msvcrt.getch()[0], Key.NULL)

        # Weird discrepency between Windows and Unix, backspace and del are swapped...
        # Choosing Unix standard:
        if ch == b"\x08":
            return Key.DEL

        if ch == b"\x7f":
            return Key.BACKSPACE

        return int.from_bytes(ch)

    def raw(self) -> ContextManager[None]:
        return nullcontext()
