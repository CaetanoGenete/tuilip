from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Generator, Self


if TYPE_CHECKING:
    from tuilip.input.types import InputHandlerBase


class Loop(IntEnum):
    POLLINPUT = 1
    NOCHANGE = 2
    NOPOLL = 3
    PROP = 4
    NOPROP = 5


_RENDERER_CONTEXT = ContextVar["RendererContext"]("tuilip_renderer_context")


@dataclass(slots=True)
class RendererContext:
    input_handler: InputHandlerBase

    @contextmanager
    def context(self) -> Generator[Self, None, None]:
        token = _RENDERER_CONTEXT.set(self)
        try:
            yield self
        finally:
            _RENDERER_CONTEXT.reset(token)

    @staticmethod
    def get() -> "RendererContext":
        return _RENDERER_CONTEXT.get()
