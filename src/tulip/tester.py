from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
import random
import re
from typing import Any, Generator, Iterator, Never
from xml.etree.ElementTree import Element
from xml.etree.ElementPath import iterfind

from tulip.components import component
from tulip.components.types import Component, ComponentGen
from tulip.input.keys import Key
from tulip.render import render_it, resolve_indent
from tulip.render.types import Signal, Text


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
    stateless: bool
    indent: int
    rebuilt: bool


@dataclass
class ComponentTester[R]:
    comp: Component[R]
    ret: R | None = field(default=None, init=False)
    done: bool = field(default=False, init=False)
    frames: list[TestFrame] = field(default_factory=list[TestFrame], init=False)

    def __post_init__(self) -> None:
        self.__render_it = render_it([self.comp])
        self.__build_id: dict[int, int] = {}

        self.next(None)  # type: ignore

    def next(self, *keys: Key) -> None:
        """Render the next frame of the component.

        `keys` are fed to the renderer in order; this may trigger a render per key.

        Raises:
            NoMoreFrameError: If called after the component has returned.
        """
        for i, key in enumerate(keys):
            if self.done:
                raise NoMoreFramesError()

            if i == len(keys) - 1:
                self.__build_id = {}

                stack = [self.comp]
                while stack:
                    curr = stack.pop()

                    if (cache := curr.cache) is not None:
                        # On rebuild, children list is always recreated
                        self.__build_id[id(curr)] = id(cache.children)
                        stack.extend(
                            node.comp
                            for node in reversed(cache.children)
                            if not isinstance(node.comp, Text)
                        )

            try:
                screen = self.__render_it.send(key)
            except StopIteration as e:
                self.ret = e.value
                self.done = True
            else:
                frame = TestFrame(
                    key=key,
                    rendered="".join(span.value for span in resolve_indent(screen)),
                )
                self.frames.append(frame)

    def _to_xml_element(self, comp: Component[Any]) -> Element:
        prev_id = self.__build_id.get(id(comp))
        curr_id = None if comp.cache is None else id(comp.cache.children)

        parent = Element(
            comp.debug_name,
            attrib={
                "stateless": str(comp.stateless).lower(),
                "indent": str(comp.indent).lower(),
                "rebuilt": str(curr_id != prev_id),
            },
        )

        if comp.cache:
            last: Element | None = None
            for child_node in comp.cache.children:
                child_comp = child_node.comp

                if isinstance(child_comp, Text):
                    if last is None:
                        parent.text = str(child_comp)
                    else:
                        last.tail = str(child_comp)
                else:
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
                stateless=child.attrib["stateless"] == "true",
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

                    f.write(f"{SNAPSHOT_FRAME_DELIM % key.name}{frame.rendered}")


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

        Stores

        Args:
            state: State struct.
            template: f-string template for component to render, args are `state`'s fields.
            id: Optional state.id override
    e"""
    state = state or MockCompState()
    state.id = id or state.id

    while True:
        yield template.format(**asdict(state))
        state.key = Key((yield Signal.POLLINPUT))
        state.builds += 1
