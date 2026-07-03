from contextlib import nullcontext
import subprocess
import ctypes
import msvcrt
from typing import ContextManager, final, override

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

_k32 = ctypes.windll.kernel32


@final
class Win32InputHandler(InputHandler):
    def __init__(self) -> None:
        self.h_ev = _k32.CreateEventW(None, False, False, None)
        self.h_con = _k32.GetStdHandle(subprocess.STD_INPUT_HANDLE)
        self.poll_arr = (ctypes.c_void_p * 2)(self.h_con, self.h_ev)

    @override
    def read(self) -> int:
        while True:
            if _k32.WaitForMultipleObjects(2, self.poll_arr, False, 0xFFFFFFFF) == 1:
                return Key.NULL

            if msvcrt.kbhit():
                break

            _k32.FlushConsoleInputBuffer(self.h_con)

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

    @override
    def raw(self) -> ContextManager[None]:
        return nullcontext()

    @override
    def interrupt(self) -> None:
        _k32.SetEvent(self.h_ev)

    def __del__(self) -> None:
        _k32.CloseHandle(self.h_ev)
