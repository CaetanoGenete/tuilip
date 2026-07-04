import sys

from tuilip.input.types import BlockingInputHandler, AsyncInputHandler

if sys.platform == "win32":
    from tuilip.input.win32 import Win32InputHandler as DefaultInputHandler
    from tuilip.input.win32 import AsyncWin32InputHandler as DefaultAsyncInputHandler
else:
    from tuilip.input.posix import PosixInputHandler as DefaultInputHandler
    from tuilip.input.posix import AsyncPosixInputHandler as DefaultAsyncInputHandler

__all__ = [
    "DefaultInputHandler",
    "DefaultAsyncInputHandler",
    "BlockingInputHandler",
    "AsyncInputHandler",
]
