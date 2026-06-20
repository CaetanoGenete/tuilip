from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any, Generator, Iterator
from xml.etree.ElementTree import Element, ElementTree

from tulip.components.types import Component
from tulip.input.keys import Key
from tulip.render import render_it, resolve_indent
from tulip.render.types import Text


def _to_xml_element(comp: Component[Any]) -> Element:
    parent = Element(
        comp.debug_name,
        {
            "stateless": str(comp.stateless),
            "indent": str(comp.indent),
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
                last = _to_xml_element(child_comp)
                parent.append(last)

    return parent


SNAPSHOT_PATTERN = re.compile(r"\n\n^;;; key: [a-zA-Z_]+ ;;;$\n\n", re.MULTILINE)


def _iter_snapshot(snapshots: str) -> Iterator[str]:
    """Helper function, extracts individual snapshots from snapshot file."""

    last = 0
    for value in re.finditer(SNAPSHOT_PATTERN, snapshots):
        yield snapshots[last : value.start()]
        last = value.end()

    yield snapshots[last:]


class NoMoreFrameError(Exception): ...


@dataclass
class TestFrame:
    key: Key | None
    rendered: str


@dataclass
class ComponentTester[R]:
    comp: Component[R]
    ret: R | None = field(default=None, init=False)
    done: bool = field(default=False, init=False)
    frames: list[TestFrame] = field(default_factory=list[TestFrame], init=False)

    def __post_init__(self) -> None:
        self.render_it = render_it([self.comp])
        self.next(None)  # type: ignore

    def next(self, *keys: Key) -> None:
        """Render the next frame of the component.

        `keys` are fed to the renderer in order.

        Raises:
            NoMoreFrameError: If this function is called after the component has returned.
        """
        for key in keys:
            if self.done:
                raise NoMoreFrameError()

            try:
                screen = self.render_it.send(key)
            except StopIteration as e:
                self.ret = e.value
                self.done = True
            else:
                frame = TestFrame(
                    key=key,
                    rendered="".join(span.value for span in resolve_indent(screen)),
                )
                self.frames.append(frame)

    def find(self, xpath: str) -> Element | None:
        root = Element("root")
        root.append(_to_xml_element(self.comp))

        return ElementTree(root).find(xpath)

    @contextmanager
    def record(self, out: str | Path, *, compare: bool) -> Generator[None, None, None]:
        """Within the context manager, writes all rendered frames to `out`.

        Args:
            out: A path like object to a file.
            compare: If true, compares existing frames in `out`, erring if any differ.
        """

        frame_start = len(self.frames) - 1
        try:
            yield

            if compare and os.path.isfile(out):
                with open(out, "rt") as f:
                    expected = f.read()

                for actual, expected in zip(
                    (x.rendered for x in self.frames[frame_start:]),
                    _iter_snapshot(expected),
                    strict=True,
                ):
                    assert actual == expected

        finally:
            with open(out, "wt") as f:
                f.write(self.frames[0].rendered)

                for frame in self.frames[1:]:
                    key = frame.key
                    assert key

                    f.write(f"\n\n;;; key: {key.name} ;;;\n\n{frame.rendered}")
