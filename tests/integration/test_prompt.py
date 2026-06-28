from dataclasses import dataclass
from pathlib import Path
import pytest

from tuilip.components import PromptController, prompt
from tuilip.input.keys import Key
from tuilip.tester import ComponentTester


def _wrap_cursor(cursor: int, promptlen: int) -> int:
    if cursor >= 0:
        return cursor

    return promptlen + 1 + cursor


@pytest.mark.parametrize(
    "pos",
    [1, 10, -2, -1]
)
def test_set_cursor(snapshot_path: Path, pos: int) -> None:
    init_prompt = "A test string or something..."

    controller = PromptController(init_prompt)
    tester = ComponentTester(prompt(controller=controller))

    with tester.record(snapshot_path, compare=True):
        controller.cursor = _wrap_cursor(pos, len(init_prompt))
        tester.next(Key.NULL)


@dataclass
class _DeleteWordTestCase:
    name: str
    init_prompt: str
    final_prompt: str
    init_cursor: int
    final_cursor: int


@pytest.mark.parametrize(
    "test_case",
    [
        # First word tests
        _DeleteWordTestCase(
            name="No change on delete first word from start",
            init_prompt="Some test string",
            final_prompt="Some test string",
            init_cursor=0,
            final_cursor=0,
        ),
        _DeleteWordTestCase(
            name="Delete first word from in-between",
            init_prompt="Some test string",
            final_prompt="me test string",
            init_cursor=2,
            final_cursor=0,
        ),
        _DeleteWordTestCase(
            name="Delete first word from in-between, with single space prefix",
            init_prompt=" Some test string",
            final_prompt=" me test string",
            init_cursor=3,
            final_cursor=1,
        ),
        _DeleteWordTestCase(
            name="Delete first word from in-between, with double space prefix",
            init_prompt="  Some test string",
            final_prompt="  me test string",
            init_cursor=4,
            final_cursor=2,
        ),
        _DeleteWordTestCase(
            name="Delete first word from end",
            init_prompt="Some test string",
            final_prompt=" test string",
            init_cursor=4,
            final_cursor=0,
        ),
        _DeleteWordTestCase(
            name="Delete first word from start of next word",
            init_prompt="Some test string",
            final_prompt="test string",
            init_cursor=5,
            final_cursor=0,
        ),
        # In-between word tests
        _DeleteWordTestCase(
            name="Delete second word from in-between",
            init_prompt="Some test string",
            final_prompt="Some st string",
            init_cursor=7,
            final_cursor=5,
        ),
        _DeleteWordTestCase(
            name="Delete second word from end",
            init_prompt="Some test string",
            final_prompt="Some  string",
            init_cursor=9,
            final_cursor=5,
        ),
        _DeleteWordTestCase(
            name="Delete second word from start of next word",
            init_prompt="Some test string",
            final_prompt="Some string",
            init_cursor=10,
            final_cursor=5,
        ),
        _DeleteWordTestCase(
            name="Delete second word from start of next word, with double space",
            init_prompt="Some test  string",
            final_prompt="Some string",
            init_cursor=11,
            final_cursor=5,
        ),
        # misc:
        _DeleteWordTestCase(
            name="Delete empty from start",
            init_prompt="",
            final_prompt="",
            init_cursor=0,
            final_cursor=0,
        ),
    ],
    ids=lambda x: x.name,
)
def test_delete_word(test_case: _DeleteWordTestCase) -> None:
    controller = PromptController(test_case.init_prompt, test_case.init_cursor)
    tester = ComponentTester(
        prompt(controller=controller, commands={Key.LF: PromptController.select})
    )

    controller.delword()
    tester.next(Key.LF)

    assert controller.cursor == test_case.final_cursor
    assert tester.ret == test_case.final_prompt


@dataclass
class _TestDeleteCharTestCase:
    name: str
    init_prompt: str
    final_prompt: str
    init_cursor: int
    final_cursor: int


@pytest.mark.parametrize(
    "test_case",
    [
        _TestDeleteCharTestCase(
            name="Delete from start",
            init_prompt="Some test string",
            final_prompt="Some test string",
            init_cursor=0,
            final_cursor=0,
        ),
        _TestDeleteCharTestCase(
            name="Delete from center",
            init_prompt="Some test string",
            final_prompt="Some est string",
            init_cursor=6,
            final_cursor=5,
        ),
        _TestDeleteCharTestCase(
            name="Delete from end",
            init_prompt="Some test string",
            final_prompt="Some test strin",
            init_cursor=-1,
            final_cursor=-1,
        ),
    ],
    ids=lambda x: x.name,
)
def test_delete_char(test_case: _TestDeleteCharTestCase) -> None:
    controller = PromptController(
        test_case.init_prompt,
        _wrap_cursor(test_case.init_cursor, len(test_case.init_prompt)),
    )
    tester = ComponentTester(
        prompt(
            controller=controller,
            commands={Key.LF: PromptController.select},
        )
    )

    controller.delchar()
    tester.next(Key.LF)

    assert tester.ret == test_case.final_prompt
    assert controller.cursor == _wrap_cursor(
        test_case.final_cursor,
        len(controller.prompt),
    )
