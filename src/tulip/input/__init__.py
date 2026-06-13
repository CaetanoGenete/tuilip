import sys

from tulip.input.types import InputHandler

if sys.platform == "win32":
    from tulip.input.win32 import Win32InputHandler as DefaultInputHandler
else:
    from tulip.input.posix import PosixInputHandler as DefaultInputHandler

__all__ = [
    "DefaultInputHandler",
    "InputHandler",
]
