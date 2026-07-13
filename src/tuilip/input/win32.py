import asyncio
from contextlib import nullcontext
import subprocess
import ctypes
import msvcrt
from typing import ContextManager, final, override

from tuilip.input.types import TIMEOUT, AsyncInputHandler, BlockingInputHandler
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


INFINITE_TIMEOUT = 0xFFFFFFFF


@final
class Win32InputHandler(BlockingInputHandler):
    def __init__(self) -> None:
        self.h_ev = _k32.CreateEventW(None, False, False, None)
        self.h_con = _k32.GetStdHandle(subprocess.STD_INPUT_HANDLE)
        self.poll_arr = (ctypes.c_void_p * 2)(self.h_con, self.h_ev)

    def _read(self, timeout: int) -> int:
        while True:
            match _k32.WaitForMultipleObjects(2, self.poll_arr, False, timeout):
                case 0:
                    pass
                case 1:
                    return Key.NULL
                case 0x102:
                    return TIMEOUT
                case resp:
                    raise RuntimeError(
                        f"win32 unexpected WaitForMultipleObjects response: {resp}"
                    )

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
    def read(self, timeout: float) -> int:
        return self._read(int(timeout * 1000))

    @override
    def raw(self) -> ContextManager[None]:
        return nullcontext()

    @override
    def interrupt(self) -> None:
        _k32.SetEvent(self.h_ev)

    def __del__(self) -> None:
        _k32.CloseHandle(self.h_ev)


@final
class AsyncWin32InputHandler(AsyncInputHandler):
    def __init__(self) -> None:
        self.sync_handle = Win32InputHandler()

    @override
    async def read(self) -> int:
        # Cannot find clean way to wait for input using asyncio
        return await asyncio.get_running_loop().run_in_executor(
            None,
            self.sync_handle._read,
            0xFFFFFFFF,
        )

    @override
    def raw(self) -> ContextManager[None]:
        return self.sync_handle.raw()

    @override
    def interrupt(self) -> None:
        return self.sync_handle.interrupt()
