from contextlib import nullcontext
import msvcrt
from typing import ContextManager, final

from tulip.input.types import InputHandler
from tulip.input.keys import Key


@final
class Win32InputHandler(InputHandler):
    def read(self) -> int:
        ch = msvcrt.getch()

        # parse special multi character keys
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
                    return Key.DEL
                case _:
                    return 0

        return int.from_bytes(ch)

    def raw(self) -> ContextManager[None]:
        return nullcontext()
