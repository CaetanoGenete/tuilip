from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
import random
import re
from typing import Any, Generator, Iterator, Never
from xml.etree.ElementTree import Element
from xml.etree.ElementPath import iterfind

from tuilip.components import component
from tuilip.components.types import Component, ComponentGen
from tuilip.input.keys import Key
from tuilip.render import render_animations, build_it, resolve_indent
from tuilip.render.anim import AnimatedText
from tuilip.render.std import DEFAULT_THEME, apply_styles
from tuilip.render.types import Loop
from tuilip.render.text import Text


SNAPSHOT_FRAME_DELIM = "\n\n;;; key: %s ;;;\n\n"
SNAPSHOT_PATTERN = re.compile(SNAPSHOT_FRAME_DELIM % "[a-zA-Z_]+")


def _iter_snapshot(snapshots: str) -> Iterator[str]:
    """Helper function, extracts individual snapshots from snapshot file."""

    last = 0
    for value in re.finditer(SNAPSHOT_PATTERN, snapshots):
        yield snapshots[last : value.start()]
        last = value.end()

    yield snapshots[last:]


class NoMoreFramesError(Exception): ...


@dataclass(slots=True)
class TestFrame:
    key: Key | None
    rendered: str


@dataclass(slots=True)
class ComponentQueryResult:
    debug_name: str
    noreturn: bool
    indent: int
    rebuilt: bool


@dataclass
class ComponentTester[R]:
    comp: Component[R]
    anim_frame: int = 0

    frames: list[TestFrame] = field(default_factory=list[TestFrame], init=False)

    ret: R | None = field(default=None, init=False)
    done: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.__render_it = build_it([self.comp])
        self.__build_id: dict[int, int] = {}

        self.next(None)  # type: ignore

    def next(self, *keys: Key) -> None:
        """Render the next frame of the component.

        `keys` are fed to the renderer in order; this may trigger a render per key.

        Raises:
            NoMoreFrameError: If called after the component has returned.
        """

        key_stack = list(reversed(keys))
        while key_stack:
            if self.done:
                raise NoMoreFramesError()

            key = key_stack.pop()

            if not key_stack:
                self.__build_id = {}

                stack = [self.comp]
                while stack:
                    curr = stack.pop()
                    cache = curr.cache

                    # On rebuild, children list is always recreated
                    self.__build_id[id(curr)] = id(cache.children)
                    stack.extend(
                        child
                        for child in reversed(cache.children)
                        if not isinstance(child, (Text, AnimatedText))
                    )

            try:
                screen, poll = self.__render_it.send(key)
            except StopIteration as e:
                self.ret = e.value
                self.done = True
                continue

            if not poll:
                key_stack.append(Key.NULL)

            rendered = render_animations(screen, self.anim_frame)
            rendered = resolve_indent(rendered)
            rendered = apply_styles(rendered, DEFAULT_THEME)

            self.frames.append(TestFrame(key=key, rendered=rendered))

    def _to_xml_element(self, comp: Component[Any]) -> Element:
        prev_id = self.__build_id.get(id(comp))
        curr_id = id(comp.cache.children)

        parent = Element(
            comp.debug_name,
            attrib={
                "noreturn": str(comp.noreturn).lower(),
                "indent": str(comp.indent).lower(),
                "rebuilt": str(curr_id != prev_id),
            },
        )

        if comp.cache:
            last: Element | None = None
            for child_comp in comp.cache.children:
                match child_comp:
                    case Text():
                        if last is None:
                            parent.text = str(child_comp)
                        else:
                            last.tail = str(child_comp)
                    case AnimatedText():
                        last = Element(
                            "animatedtext",
                            attrib={
                                "period": str(child_comp.period),
                                "next": str(child_comp.next_frame),
                            },
                        )
                        parent.append(last)
                    case Component():
                        last = self._to_xml_element(child_comp)
                        parent.append(last)

        return parent

    def find(self, xpath: str) -> Iterator[ComponentQueryResult]:
        root = Element("root")
        root.append(self._to_xml_element(self.comp))

        for child in iterfind(root, xpath):
            yield ComponentQueryResult(
                debug_name=child.tag,
                indent=int(child.attrib["indent"]),
                noreturn=child.attrib["noreturn"] == "true",
                rebuilt=child.attrib["rebuilt"] == "true",
            )

    @contextmanager
    def record(self, out: str | Path, *, compare: bool) -> Generator[None, None, None]:
        """Within the context manager, writes all rendered frames to `out` (including
        the currently visible frame).

        Args:
            out: A path like object to a file.
            compare: If true, compares existing frames in `out`, erring if any differ.
        """

        frame_start = len(self.frames) - 1
        try:
            yield

            if compare and os.path.isfile(out):
                with open(out, "rt", encoding="utf-8") as f:
                    expected = f.read()

                for actual, expected in zip(
                    (x.rendered for x in self.frames[frame_start:]),
                    _iter_snapshot(expected),
                    strict=True,
                ):
                    assert actual == expected

        finally:
            with open(out, "wt", encoding="utf-8") as f:
                f.write(self.frames[0].rendered)

                for frame in self.frames[1:]:
                    key = frame.key
                    assert key is not None

                    f.write(SNAPSHOT_FRAME_DELIM % key.name)
                    f.write(frame.rendered)


@dataclass(slots=True)
class MockCompState:
    id: str = field(default_factory=lambda: str(random.randint(0, (1 << 63) - 1)))
    builds: int = 0
    key: Key = Key.NULL


DEFAULT_MOCK_TEMPLATE = """\
id: {id}
buildno: {builds}
key: {key.name}"""


@component
def mockcomp(
    state: MockCompState | None = None,
    *,
    template: str = DEFAULT_MOCK_TEMPLATE,
    id: str = "",
) -> ComponentGen[Never]:
    """Measured component object.

    Args:
        state: State struct.
        template: f-string template for component to render, args are `state`'s fields.
        id: Optional state.id override
    """
    state = state or MockCompState()
    state.id = id or state.id

    while True:
        yield template.format(**asdict(state))
        state.key = Key((yield Loop.POLLINPUT))
        state.builds += 1
