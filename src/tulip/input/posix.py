from contextlib import contextmanager
from dataclasses import dataclass
import sys
from typing import IO, Any, ContextManager, Generator, final, override
import termios

from tulip.input.types import InputHandler
from tulip.input.keys import Key, escape_code_map

C_IFLAG = 0
C_LFLAG = 3
C_CC = 6


@contextmanager
def tcrecover(fd: IO[Any]) -> Generator[list[Any]]:
    """Restores any tty attribute changes upon exiting context manager.

    Args:
        fd: The file descritor to track.

    Yields:
        The current tty attributes of `fd`, as returned by `tcgetattr`.
    """

    old_settings = termios.tcgetattr(fd)
    # Note: cc is a list, hence need to copy here.
    old_cc = old_settings[C_CC].copy()

    try:
        yield old_settings.copy()
    finally:
        old_settings[C_CC] = old_cc
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


@contextmanager
def tcraw(fd: IO[Any] = sys.stdin) -> Generator[list[Any]]:
    """Places `fd` in a `raw` like terminal mode.

    Args:
        fd: The file descritor to alter.

    Yields:
        The current tty attributes of `fd`, as returned by `tcgetattr`.
    """

    with tcrecover(fd) as flags:
        flags[C_IFLAG] &= ~(
            termios.IGNBRK
            | termios.BRKINT
            | termios.INLCR
            | termios.IGNCR
            | termios.ICRNL
            | termios.IXON
        )
        flags[C_LFLAG] &= ~(termios.ECHO | termios.ICANON | termios.ISIG)
        termios.tcsetattr(fd, termios.TCSAFLUSH, flags)

        yield flags


ESCAPE_CODES = {
    # CSI
    b"[A": Key.UP,
    b"[B": Key.DOWN,
    b"[C": Key.RIGHT,
    b"[D": Key.LEFT,
    b"[F": Key.END,
    b"[H": Key.HOME,
    b"[1~": Key.HOME,
    b"[3~": Key.DEL,
    b"[4~": Key.END,
    b"[5~": Key.PAGE_UP,
    b"[6~": Key.PAGE_DOWN,
    b"[7~": Key.END,
    # SS3
    b"OA": Key.UP,
    b"OB": Key.DOWN,
    b"OC": Key.RIGHT,
    b"OD": Key.LEFT,
    b"OF": Key.END,
    b"OH": Key.HOME,
}
ESCAPE_MAP = escape_code_map(ESCAPE_CODES)


@final
@dataclass(slots=True)
class PosixInputHandler(InputHandler):
    fd: IO[bytes] = sys.stdin.buffer

    @override
    def read(self) -> int:
        flags = termios.tcgetattr(self.fd)
        old_cc = flags[C_CC].copy()

        try:
            match self.fd.read(1):
                case b"":
                    return 0
                case b"\x1b":
                    pass
                case key:
                    return key[0]

            cc = flags[C_CC]
            cc[termios.VMIN] = 0
            cc[termios.VTIME] = 1
            termios.tcsetattr(self.fd, termios.TCSANOW, flags)

            curr = ESCAPE_MAP
            while not isinstance(curr, int):
                key = self.fd.read(1)
                if key == b"":
                    # TODO: Perhaps buffer keys instead???
                    return Key.ESCAPE

                chr = key[0]
                if chr not in curr:
                    # TODO: Perhaps buffer keys instead???
                    return Key.ESCAPE

                curr = curr[chr]

            return curr

        finally:
            flags[C_CC] = old_cc
            termios.tcsetattr(self.fd, termios.TCSANOW, flags)

    @override
    def raw(self) -> ContextManager[None]:
        return tcraw(self.fd)  # type: ignore
