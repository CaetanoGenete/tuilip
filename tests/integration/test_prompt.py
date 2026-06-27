from pathlib import Path
import pytest

from tuilip.components import PromptController, prompt
from tuilip.input.keys import Key
from tuilip.tester import ComponentTester


_TEST_MOVE_CURSOR_PROMPT = "A test string or something..."


@pytest.mark.parametrize(
    "pos",
    [
        1,
        10,
        len(_TEST_MOVE_CURSOR_PROMPT) - 1,
        len(_TEST_MOVE_CURSOR_PROMPT),
    ],
)
def test_move_cursor(snapshot_path: Path, pos: int) -> None:
    controller = PromptController(_TEST_MOVE_CURSOR_PROMPT)
    tester = ComponentTester(prompt(controller=controller))

    with tester.record(snapshot_path, compare=True):
        controller.cursor = pos
        tester.next(Key.NULL)
