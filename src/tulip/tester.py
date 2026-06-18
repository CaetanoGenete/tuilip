from contextlib import suppress
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
from typing import IO, Any, Callable, Iterable, Iterator
from xml.etree.ElementTree import Element, ElementTree

from tulip.components.types import Component
from tulip.input.keys import Key
from tulip.render import TextView, render, resolve_indent
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


@dataclass
class ComponentTester:
    comp: Component[Any]

    def find(self, xpath: str) -> Element | None:
        root = Element("root")
        root.append(_to_xml_element(self.comp))

        return ElementTree(root).find(xpath)


type ComponentTestFn = Callable[[ComponentTester], Iterable[Key]]


class StopSnapshotError(Exception): ...


def test_loop[R](
    comp: Component[R],
    keys: Iterable[Key],
    out: IO[bytes],
) -> R | None:
    keys = iter(keys)

    def onrefresh(screen: list[TextView]) -> int:
        rendered = "".join(span.value for span in resolve_indent(screen))

        try:
            key = next(keys)
        except StopIteration:
            raise StopSnapshotError()
        else:
            rendered += f"\n\n;;; key: {key.name} ;;;\n\n"
            return key
        finally:
            out.write(rendered.encode())

    with suppress(StopSnapshotError):
        return render(comp, onrefresh=onrefresh)


SNAPSHOT_PATTERN = re.compile(rb"^;;; key: [a-zA-Z_]+ ;;;$", re.MULTILINE)


def _iter_snapshot(snapshots: bytes) -> Iterator[bytes]:
    """Helper function, extracts individual snapshots from snapshot file."""

    last = 0
    for value in re.finditer(SNAPSHOT_PATTERN, snapshots):
        yield snapshots[last : value.start()]
        last = value.end()

    yield snapshots[last:]


def component_test[R](
    comp: Component[R],
    snapshots: bool = False,
) -> Callable[[ComponentTestFn], Callable[[], None]]:

    def decorator(test_fn: ComponentTestFn) -> Callable[[], None]:
        tester = ComponentTester(comp)

        outpath = Path("tests/fixtures", test_fn.__module__, test_fn.__name__)

        def wrapper() -> None:
            outpath.parent.mkdir(exist_ok=True, parents=True)

            out = BytesIO()
            test_loop(comp, test_fn(tester), out)
            out.seek(0)

            actual = out.read()

            if snapshots:
                if outpath.is_file():
                    for actual, expected in zip(
                        _iter_snapshot(actual),
                        _iter_snapshot(outpath.read_bytes()),
                        strict=True,
                    ):
                        assert actual == expected
                else:
                    outpath.write_bytes(actual)

        return wrapper

    return decorator
