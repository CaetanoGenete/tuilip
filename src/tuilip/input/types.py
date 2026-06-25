from abc import abstractmethod
from typing import ContextManager, Protocol


class InputHandler(Protocol):
    @abstractmethod
    def read(self) -> int:
        """Reads a single tuilip key.

        The implementation may choose the source arbitrarily, or mock if needed.

        Returns:
            A tuilip key-code. See tuilip.input.keys
        """

    @abstractmethod
    def raw(self) -> ContextManager[None]:
        """Places the InputHandler in `raw` mode."""
