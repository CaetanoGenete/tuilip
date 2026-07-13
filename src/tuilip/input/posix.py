import asyncio
import fcntl
from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from select import select
import sys
from typing import Any, ContextManager, Iterator, final, override, Protocol
import termios

from tuilip.input.types import TIMEOUT, AsyncInputHandler, BlockingInputHandler
from tuilip.input.keys import Key, escape_code_map

C_IFLAG = 0
C_LFLAG = 3
C_CC = 6


class HasFileNo(Protocol):
    def fileno(self) -> int: ...


type FDLike = int | HasFileNo


@contextmanager
def tcrecover(fd: FDLike) -> Iterator[list[Any]]:
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
def tcraw(fd: FDLike = sys.stdin) -> Iterator[list[Any]]:
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
    b"[2~": Key.INSERT,
    b"[3~": Key.SDEL,
    b"[4~": Key.END,
    b"[5~": Key.PAGE_UP,
    b"[6~": Key.PAGE_DOWN,
    b"[7~": Key.HOME,
    b"[8~": Key.END,
    # Meta (alt) + arrow keys
    b"[1;3A": Key.META_UP,
    b"[1;3B": Key.META_DOWN,
    b"[1;3C": Key.META_RIGHT,
    b"[1;3D": Key.META_LEFT,
    # ctrl + arrow keys
    b"[1;5A": Key.CTRL_UP,
    b"[1;5B": Key.CTRL_DOWN,
    b"[1;5C": Key.CTRL_RIGHT,
    b"[1;5D": Key.CTRL_LEFT,
    # SS3
    b"OA": Key.UP,
    b"OB": Key.DOWN,
    b"OC": Key.RIGHT,
    b"OD": Key.LEFT,
    b"OF": Key.END,
    b"OH": Key.HOME,
}
ESCAPE_MAP = escape_code_map(ESCAPE_CODES)


class FileLike[R](HasFileNo, Protocol):
    def read(self, n: int, /) -> R: ...


def read_key(file: FileLike[bytes]) -> int:
    flags = termios.tcgetattr(file)
    old_cc = flags[C_CC].copy()

    try:
        if (key := file.read(1)) != b"\x1b":
            return key[0]

        cc = flags[C_CC]
        cc[termios.VMIN] = 0
        cc[termios.VTIME] = 1
        termios.tcsetattr(file, termios.TCSANOW, flags)

        curr = ESCAPE_MAP
        while not isinstance(curr, int):
            key = file.read(1)
            if key == b"":
                # TODO: Perhaps buffer keys instead???
                return Key.ESCAPE

            key = key[0]
            if key not in curr:
                # TODO: Perhaps buffer keys instead???
                return Key.ESCAPE

            curr = curr[key]

        return curr

    finally:
        flags[C_CC] = old_cc
        termios.tcsetattr(file, termios.TCSANOW, flags)


@final
@dataclass(slots=True)
class PosixInputHandler(BlockingInputHandler):
    source: FileLike[bytes] = sys.stdin.buffer

    def __post_init__(self) -> None:
        self.event_fd = os.eventfd(0, os.O_NONBLOCK)

    @override
    def read(self, timeout: float) -> int:
        ready = select((self.source, self.event_fd), (), (), timeout)[0]
        if not ready:
            return TIMEOUT

        if self.event_fd in ready:
            # Read to reset event
            os.eventfd_read(self.event_fd)

        if self.source not in ready:
            return Key.NULL

        return read_key(self.source)

    @override
    def raw(self) -> ContextManager[Any]:
        return tcraw(self.source)

    @override
    def interrupt(self) -> None:
        os.eventfd_write(self.event_fd, 1)

    def __del__(self) -> None:
        os.close(self.event_fd)


@dataclass(slots=True)
class CachedFile:
    file: FileLike[bytes]
    cache: bytes = field(default=b"", init=False)

    def prefetch(self, n: int) -> None:
        self.cache += self.file.read(n)

    def read(self, n: int) -> bytes:
        result = self.cache[:n]
        self.cache = self.cache[n:]

        if (remaining := n - len(result)) > 0:
            result += self.file.read(remaining)

        return result

    def fileno(self) -> int:
        return self.file.fileno()


@final
class AsyncPosixInputHandler(AsyncInputHandler):
    __slots__ = "source", "read_event", "interrupt_event"

    def __init__(self, source: FileLike[bytes] = sys.stdin.buffer) -> None:
        # Note: something (perhaps python buffers stdin?) is seeking to the end of
        # `source` after asyncio notifies it is 'ready' for reading, but before
        # `read_event.wait()` is run by the event loop, causing `source.read` to block.
        # Solution: prefetch and cache reads immediately upon being notified.
        self.source = CachedFile(source)

        fl = fcntl.fcntl(source, fcntl.F_GETFL)
        fcntl.fcntl(source, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.read_event = asyncio.Event()
        self.interrupt_event = asyncio.Event()

        asyncio.get_running_loop().add_reader(
            self.source,
            self._on_read_ready,
        )

    def _on_read_ready(self) -> None:
        self.source.prefetch(4096)
        self.read_event.set()

    @override
    async def read(self) -> int:
        if self.source.cache:
            return read_key(self.source)

        await asyncio.wait(
            (
                asyncio.create_task(self.read_event.wait()),
                asyncio.create_task(self.interrupt_event.wait()),
            ),
            return_when=asyncio.FIRST_COMPLETED,
        )

        self.interrupt_event.clear()
        if self.read_event.is_set():
            self.read_event.clear()
            return read_key(self.source)

        return Key.NULL

    @override
    def raw(self) -> ContextManager[None]:
        return tcraw(self.source)  # type: ignore

    @override
    def interrupt(self) -> None:
        self.interrupt_event.set()
