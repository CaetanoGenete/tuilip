import pytest
from dataclasses import dataclass
from typing import Callable

from tuilip.components import PromptController


@dataclass
class _MoveCursorTestCase:
    name: str
    movefn: Callable[[PromptController], None]
    prompt: str
    init_cursor: int
    final_cursor: int


def _wrap_cursor(cursor: int, promptlen: int) -> int:
    if cursor >= 0:
        return cursor

    return promptlen + 1 + cursor


@pytest.mark.parametrize(
    "test_case",
    [
        # nextchar
        _MoveCursorTestCase(
            name="nextchar from end",
            movefn=PromptController.nextchar,
            prompt="Some test string",
            init_cursor=-1,
            final_cursor=-1,
        ),
        _MoveCursorTestCase(
            name="nextchar from one-before-end",
            movefn=PromptController.nextchar,
            prompt="Some test string",
            init_cursor=-2,
            final_cursor=-1,
        ),
        _MoveCursorTestCase(
            name="nextchar from center",
            movefn=PromptController.nextchar,
            prompt="Some test string",
            init_cursor=6,
            final_cursor=7,
        ),
        # prevchar
        _MoveCursorTestCase(
            name="nextchar from start",
            movefn=PromptController.prevchar,
            prompt="Some test string",
            init_cursor=0,
            final_cursor=0,
        ),
        _MoveCursorTestCase(
            name="nextchar from one-after-start",
            movefn=PromptController.prevchar,
            prompt="Some test string",
            init_cursor=1,
            final_cursor=0,
        ),
        _MoveCursorTestCase(
            name="prevchar from center",
            movefn=PromptController.prevchar,
            prompt="Some test string",
            init_cursor=6,
            final_cursor=5,
        ),
        # next word
        _MoveCursorTestCase(
            name="nextword from end",
            movefn=PromptController.nextword,
            prompt="Some test string",
            init_cursor=-1,
            final_cursor=-1,
        ),
        _MoveCursorTestCase(
            name="nextword from middle of last word",
            movefn=PromptController.nextword,
            prompt="Some test string",
            init_cursor=-4,
            final_cursor=-1,
        ),
        _MoveCursorTestCase(
            name="nextword from middle of penultimate word",
            movefn=PromptController.nextword,
            prompt="Some test string",
            init_cursor=6,
            final_cursor=10,
        ),
        _MoveCursorTestCase(
            name="nextword from middle of penultimate word, with double space",
            movefn=PromptController.nextword,
            prompt="Some test  string",
            init_cursor=6,
            final_cursor=11,
        ),
        _MoveCursorTestCase(
            name="nextword from start of penultimate word",
            movefn=PromptController.nextword,
            prompt="Some test string",
            init_cursor=5,
            final_cursor=10,
        ),
        _MoveCursorTestCase(
            name="nextword from end of penultimate word",
            movefn=PromptController.nextword,
            prompt="Some test string",
            init_cursor=8,
            final_cursor=10,
        ),
        # prev word
        _MoveCursorTestCase(
            name="prevword from start",
            movefn=PromptController.prevword,
            prompt="Some test string",
            init_cursor=0,
            final_cursor=0,
        ),
        _MoveCursorTestCase(
            name="prevword from middle of first word",
            movefn=PromptController.prevword,
            prompt="Some test string",
            init_cursor=2,
            final_cursor=0,
        ),
        _MoveCursorTestCase(
            name="prevword from end of first word",
            movefn=PromptController.prevword,
            prompt="Some test string",
            init_cursor=4,
            final_cursor=0,
        ),
        _MoveCursorTestCase(
            name="prevword from start of second word",
            movefn=PromptController.prevword,
            prompt="Some test string",
            init_cursor=5,
            final_cursor=0,
        ),
        _MoveCursorTestCase(
            name="prevword from start of second word, with double space",
            movefn=PromptController.prevword,
            prompt="Some  test string",
            init_cursor=6,
            final_cursor=0,
        ),
        _MoveCursorTestCase(
            name="prevword from middle of second word",
            movefn=PromptController.prevword,
            prompt="Some test string",
            init_cursor=6,
            final_cursor=5,
        ),
    ],
    ids=lambda x: x.name,
)
def test_move_cursor(test_case: _MoveCursorTestCase) -> None:
    init_cursor = _wrap_cursor(test_case.init_cursor, len(test_case.prompt))
    final_cursor = _wrap_cursor(test_case.final_cursor, len(test_case.prompt))

    controller = PromptController(test_case.prompt, init_cursor)
    test_case.movefn(controller)

    assert controller.cursor == final_cursor
