from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import partial
from typing import Callable, Generator, Sequence

from tuilip.render.text import Text

type AnimatedGen = Generator[Text | str, None, None]


@dataclass(slots=True)
class AnimatedText:
    text_gen: AnimatedGen
    period: int = 1
    cache: Text | None = field(default=None, init=False)
    next_frame: int = field(default=-1, init=False)

    def at_period(self, period: int) -> AnimatedText:
        return replace(self, period=period)


def animated_text[**P](
    text_gen: Callable[P, Generator[Text | str, None, None]],
) -> Callable[P, AnimatedText]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> AnimatedText:
        return AnimatedText(text_gen=text_gen(*args, **kwargs))

    return wrapper


@animated_text
def animframes(
    frames: Sequence[str | Text],
    repeat: bool = False,
) -> AnimatedGen:
    curr_frame = 0
    nframes = len(frames)

    while True:
        yield frames[curr_frame]

        curr_frame += 1
        if curr_frame >= nframes:
            if not repeat:
                break

            curr_frame = 0


loading_spinner_1 = partial(
    animframes,
    frames=["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    repeat=True,
)
