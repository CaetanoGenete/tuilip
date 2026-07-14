from abc import abstractmethod
from typing import ContextManager, Protocol

TIMEOUT = -1
"""Return value when `BlockingInputHandler` times out."""


class InputHandlerBase(Protocol):
    @abstractmethod
    def raw(self) -> ContextManager[None]:
        """Places the InputHandler in `raw` mode."""

    @abstractmethod
    def interrupt(self) -> None:
        """Interrupt `read`, typically returning Key.NULL"""


class BlockingInputHandler(InputHandlerBase, Protocol):
    @abstractmethod
    def read(self, timeout: float) -> int:
        """Reads a single tuilip key.

        The implementation may choose the source arbitrarily, or mock if needed.

        Returns:
            A tuilip key-code. See tuilip.input.keys
        """


class AsyncInputHandler(InputHandlerBase, Protocol):
    @abstractmethod
    async def read(self) -> int:
        """Reads a single tuilip key.

        The implementation may choose the source arbitrarily, or mock if needed.

        Returns:
            A tuilip key-code. See tuilip.input.keys
        """
