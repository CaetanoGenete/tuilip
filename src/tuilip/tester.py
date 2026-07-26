from contextlib import contextmanager, nullcontext
from tuilip.input import BlockingInputHandler
from dataclasses import asdict, dataclass, field
from collections import deque
import os
from pathlib import Path
import random
import re
from typing import Any, Generator, Generic, Iterator, Never, cast, final, ContextManager
from xml.etree.ElementTree import Element
from xml.etree.ElementPath import iterfind

from tuilip.components import component
from tuilip.components.types import CompCacheChild, Component, TOrNever, ComponentGen
from tuilip.input.keys import Key
from tuilip.render import BuildOutput, build_it, render_animations, resolve_indent
from tuilip.render.anim import AnimatedText
from tuilip.render.std import DEFAULT_THEME, apply_styles
from tuilip.render.types import Loop, RendererContext
from tuilip.render.text import Text


class NoMoreFramesError(Exception): ...


@dataclass(slots=True)
class TestFrame:
    key: Key | None
    rendered: str


@final
@dataclass
class TesterInputHandler[T](BlockingInputHandler):
    """Input handler for ComponentTester.

    This handler inverts the typical UI flow of the _build_ waiting for input. Instead,
    input drives the build.
    """

    render_it: Generator[tuple[BuildOutput, bool], int, T]
    anim_frame: int = 0
    keys: deque[Key] = field(default_factory=deque[Key])

    frames: list[TestFrame] = field(default_factory=list[TestFrame], init=False)
    ret: T | None = field(default=None, init=False)
    done: bool = field(default=False, init=False)

    def flush(self) -> int:
        """Processes stored keys.

        Returns:
            Number of builds.
        """

        nbuilds = 0
        while self.keys:
            key = self.keys.popleft()

            try:
                screen, poll = self.render_it.send(key)
            except StopIteration as e:
                self.ret = cast(T, e.value)
                self.done = True
                continue

            nbuilds += 1
            if not poll:
                self.keys.append(Key.NULL)

            rendered = render_animations(screen, self.anim_frame)
            rendered = resolve_indent(rendered)
            rendered = apply_styles(rendered, DEFAULT_THEME)
            self.frames.append(TestFrame(key=key, rendered=rendered))

        return nbuilds

    def read(self, timeout: float) -> int:
        del timeout
        return Key.NULL

    def interrupt(self) -> None:
        self.keys.appendleft(Key.NULL)
        self.flush()

    def raw(self) -> ContextManager[None]:
        return nullcontext()


@dataclass(slots=True)
class ComponentQueryResult:
    debug_name: str
    indent: int
    noreturn: bool
    rebuilt: bool


SNAPSHOT_FRAME_DELIM = "\n\n;;; key: %s ;;;\n\n"
SNAPSHOT_PATTERN = re.compile(SNAPSHOT_FRAME_DELIM % "[a-zA-Z_]+")


def _iter_snapshot(snapshots: str) -> Iterator[str]:
    """Helper function, extracts individual snapshots from snapshot file."""

    last = 0
    for value in re.finditer(SNAPSHOT_PATTERN, snapshots):
        yield snapshots[last : value.start()]
        last = value.end()

    yield snapshots[last:]


@dataclass
class ComponentTester(Generic[TOrNever]):
    """Suite of testing utilities for components.

    **IMPORTANT**: prefer creating with `component_tester` function!
    """

    comp: Component[TOrNever]
    ihandler: TesterInputHandler[TOrNever]

    def __post_init__(self) -> None:
        self.__build_idx = 0
        self.next(None)  # type: ignore

    def next(self, *keys: Key) -> None:
        """Render the next frame of the component.

        `keys` are fed to the renderer in order; this may trigger a render per key.

        Raises:
            NoMoreFrameError: If called after the component has returned.
        """

        self.ihandler.keys.extend(keys)
        self.__build_idx += self.ihandler.flush()

    @property
    def done(self) -> bool:
        """True when the component has returned.

        Invoking `next` after this returns `true` will raise a `NoMoreFrameError`.

        Returns:
            A boolean value.
        """
        return self.ihandler.done

    @property
    def ret(self) -> TOrNever | None:
        """The returned value of the component, or `None`.

        The `done` attribute indicates whether there is a return value or not.
        """
        return self.ihandler.ret

    def find(self, xpath: str) -> Iterator[ComponentQueryResult]:
        """Returns all components matching the `xpath` expression.

        Args:
            xpath: XPath query string.

        Yields:
            A matching component proxy object.
        """
        root = Element("root")

        stack: list[tuple[Element, CompCacheChild[Any]]] = [(root, self.comp)]

        last = root
        while stack:
            parent, curr = stack.pop()

            if isinstance(curr, Text):
                last.tail = str(curr)
                continue

            if isinstance(curr, AnimatedText):
                parent.append(
                    Element(
                        "animatedtext",
                        attrib={
                            "period": str(curr.period),
                            "next": str(curr.next_frame),
                        },
                    )
                )
                continue

            last = Element(
                curr.debug_name,
                attrib={
                    "noreturn": str(curr.noreturn).lower(),
                    "indent": str(curr.indent).lower(),
                    "rebuilt": str(self.__build_idx == curr.cache.build_index),
                },
            )
            parent.append(last)

            children = curr.cache.children
            if children and isinstance(child := children[0], Text):
                last.text = str(child)
                children = children[1:]

            stack.extend([(last, comp) for comp in reversed(children)])

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

        frame_start = len(self.ihandler.frames) - 1
        try:
            yield

            if compare and os.path.isfile(out):
                with open(out, "rt", encoding="utf-8") as f:
                    expected = f.read()

                for actual, expected in zip(
                    (x.rendered for x in self.ihandler.frames[frame_start:]),
                    _iter_snapshot(expected),
                    strict=True,
                ):
                    assert actual == expected

        finally:
            with open(out, "wt", encoding="utf-8") as f:
                f.write(self.ihandler.frames[0].rendered)

                for frame in self.ihandler.frames[1:]:
                    key = frame.key
                    assert key is not None

                    f.write(SNAPSHOT_FRAME_DELIM % key.name)
                    f.write(frame.rendered)


@contextmanager
def component_tester(
    comp: Component[TOrNever],
    *,
    snapshot_path: str | Path | None = None,
    compare: bool = False,
) -> Generator[ComponentTester[TOrNever], None, None]:
    assert not (compare and snapshot_path is None), (
        "snapshot_path is required if compare=True"
    )

    render_it = build_it([comp])
    ihandler = TesterInputHandler(render_it)
    context = RendererContext(ihandler)

    with context.context():
        tester = ComponentTester(comp, ihandler)

        with (
            tester.record(snapshot_path, compare=compare)
            if snapshot_path is not None
            else nullcontext()
        ):
            yield tester


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
