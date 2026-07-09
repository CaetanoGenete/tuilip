from contextvars import ContextVar
from dataclasses import dataclass
from enum import IntEnum

from tuilip.input.types import InputHandlerBase


class Signal(IntEnum):
    POLLINPUT = 1
    NOCHANGE = 2
    NOPOLL = 3
    PROP = 4
    NOPROP = 5


@dataclass(slots=True)
class RendererContext:
    input_handler: InputHandlerBase


RENDERER_CONTEXT = ContextVar[RendererContext]("tuilip_renderer_context")
