from contextlib import nullcontext
import msvcrt
from typing import ContextManager, final

from tuilip.input.types import InputHandler
from tuilip.input.keys import Key


@final
class Win32InputHandler(InputHandler):
    def read(self) -> int:
        ch = msvcrt.getch()

        # Parse special multi character keys
        # https://learn.microsoft.com/cpp/c-runtime-library/reference/getch-getwch#remarks
        if ch in b"\x00\xe0":
            match msvcrt.getch()[0]:
                case 71:
                    return Key.HOME
                case 72:
                    return Key.UP
                case 73:
                    return Key.PAGE_UP
                case 75:
                    return Key.LEFT
                case 77:
                    return Key.RIGHT
                case 79:
                    return Key.END
                case 80:
                    return Key.DOWN
                case 81:
                    return Key.PAGE_DOWN
                case 83:
                    return Key.SDEL
                case 115:
                    return Key.CTRL_LEFT
                case 116:
                    return Key.CTRL_RIGHT
                case 141:
                    return Key.CTRL_UP
                case 145:
                    return Key.CTRL_DOWN
                case 155:
                    return Key.META_LEFT
                case 157:
                    return Key.META_RIGHT
                case 152:
                    return Key.META_UP
                case 160:
                    return Key.META_DOWN
                case _:
                    return 0

        # Weird discrepency between Windows and Unix, backspace and del are swapped...
        # Choosing Unix standard:
        if ch == b"\x08":
            return Key.DEL

        if ch == b"\x7f":
            return Key.BACKSPACE

        return int.from_bytes(ch)

    def raw(self) -> ContextManager[None]:
        return nullcontext()
