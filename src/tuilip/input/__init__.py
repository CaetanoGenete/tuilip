import sys

from tuilip.input.types import InputHandler

if sys.platform == "win32":
    from tuilip.input.win32 import Win32InputHandler as DefaultInputHandler
else:
    from tuilip.input.posix import PosixInputHandler as DefaultInputHandler

__all__ = [
    "DefaultInputHandler",
    "InputHandler",
]
