from __future__ import annotations

import asyncio

from tuilip.input.keys import Key
from dataclasses import dataclass
from inspect import GEN_CLOSED, GEN_CREATED, getgeneratorstate
from typing import TYPE_CHECKING, Generator, Iterable, Iterator, cast
from collections.abc import Callable

from tuilip.render.exceptions import TooManyChildrenException
from tuilip.render.types import RendererContext, Signal
from tuilip.render.text import Span, Text
from tuilip.synchronisation import Clock
from tuilip.components.types import CompCacheChild, Component, Renderable, ComponentGen
from tuilip.render.anim import AnimatedText

if TYPE_CHECKING:
    from tuilip.input.types import AsyncInputHandler, BlockingInputHandler


@dataclass(slots=True)
class Offset[T]:
    value: T
    indent: int


type BuildOutput = list[Offset[Text | AnimatedText]]


MAX_COMPONENT_CHILDREN = 1000
"""Maximum number of child component.

If exceeded, `build_it` raises a TooManyChildrenException.
"""


def _root_it[R](children: Iterable[Renderable[R]]) -> ComponentGen[R]:
    for child in children:
        yield child


def build_it[R](
    components: Iterable[Renderable[R]],
) -> Generator[tuple[BuildOutput, bool], int, R]:
    root = Component(
        noreturn=True,
        debug_name="root",
        gen=_root_it(components),
    )

    key = 0
    while True:
        screen: BuildOutput = []

        noprop_idx = 1 << 31
        # stores (indent, stack_ptr) flattened tuples.
        indent_stack = [0, 0]

        poll = True

        stack: list[CompCacheChild[R]] = [root]
        while stack:
            comp = stack.pop()
            stacklen = len(stack)

            while stacklen < indent_stack[-1]:
                del indent_stack[-2:]
            indent = indent_stack[-2]

            if not isinstance(comp, Component):
                screen.append(Offset(comp, indent))
                continue

            if comp.indent:
                indent_stack.extend((indent + comp.indent, stacklen))

            if not comp.cache.propkey:
                noprop_idx = min(noprop_idx, stacklen)

            genstate = getgeneratorstate(comp.gen)
            created = genstate is not GEN_CREATED

            if comp.noreturn and genstate is GEN_CLOSED:
                stack.extend(reversed(comp.cache.children))
                continue

            if stacklen >= noprop_idx:
                effective_key = 0
            else:
                effective_key = key
                noprop_idx = 1 << 31

            new_children: list[CompCacheChild[R]] = []
            # Cache of contiguous text nodes.
            cached_text = Text()
            # Whether child nodes should propogate 'key'
            propkey = True

            for _ in range(MAX_COMPONENT_CHILDREN):
                try:
                    if created:
                        child = comp.gen.send(effective_key)
                    else:
                        child = next(comp.gen)
                        created = True

                except StopIteration as e:
                    if comp.noreturn:
                        break
                    return cast(R, e.value)

                match child:
                    case Signal.POLLINPUT:
                        break
                    case Signal.NOCHANGE:
                        new_children = comp.cache.children
                        cached_text = Text()
                        break
                    case Signal.NOPOLL:
                        poll = False
                        break
                    case Signal.PROP:
                        propkey = True
                        continue
                    case Signal.NOPROP:
                        propkey = False
                        continue
                    case None:
                        continue
                    case _:
                        pass

                # Optimisation: squash contiguous text nodes, to reduce node count.
                if isinstance(child, (str, Text)):
                    cached_text += child
                    continue

                if cached_text:
                    new_children.append(cached_text)
                    cached_text = Text()

                if isinstance(child, Component):
                    child.cache.propkey = propkey

                new_children.append(child)
            else:
                raise TooManyChildrenException(comp)

            if cached_text:
                new_children.append(cached_text)

            comp.cache.children = new_children
            stack.extend(reversed(new_children))

        key = yield screen, poll


def loop[R](
    *components: Renderable[R],
    input_handler: BlockingInputHandler,
    draw: Callable[[BuildOutput, int], None],
    animation_period: float,
) -> R:
    clock = Clock(animation_period)
    frame: int = 0

    with RendererContext(input_handler).context():
        renderer = build_it(components)

        key: int = None  # type: ignore
        while True:
            try:
                screen, poll = renderer.send(key)
            except StopIteration as e:
                return cast(R, e.value)

            # TODO: if clock delta is close enough, increase frame
            draw(screen, frame)

            if not poll:
                key = Key.NULL
                continue

            # Handle animation + key-input

            while True:
                if (key := input_handler.read(clock.delta())) != -1:
                    break

                frame += 1
                draw(screen, frame)


async def aloop[R](
    *components: Renderable[R],
    input_handler: AsyncInputHandler,
    draw: Callable[[BuildOutput, int], None],
    animation_period: float,
) -> R:
    clock = Clock(animation_period)
    frame: int = 0

    with RendererContext(input_handler).context():
        renderer = build_it(components)

        key: int = None  # type: ignore
        while True:
            try:
                screen, poll = renderer.send(key)
            except StopIteration as e:
                return cast(R, e.value)

            # TODO: if clock delta is close enough, increase frame
            draw(screen, frame)

            if not poll:
                key = Key.NULL
                continue

            # Handle animation + key-input

            key_task = asyncio.create_task(input_handler.read())
            while True:
                done, _ = await asyncio.wait(
                    (asyncio.create_task(clock.synca()), key_task),
                    return_when="FIRST_COMPLETED",
                )
                if key_task in done:
                    key = key_task.result()
                    break

                frame += 1
                draw(screen, frame)


def render_animations(
    screen: Iterable[Offset[Text | AnimatedText]],
    frame: int,
) -> Iterator[Offset[Text]]:
    for drawable in screen:
        anim = drawable.value
        if isinstance(anim, AnimatedText):
            if anim.next_frame <= frame:
                text = next(anim.text_gen, anim.cache) or ""
                anim.next_frame += anim.period - (anim.next_frame % anim.period)
            else:
                text = anim.cache or ""

            if isinstance(text, str):
                text = Text(text)

            anim.cache = text
            anim = text

        yield Offset(value=anim, indent=drawable.indent)


def resolve_indent(screen: Iterable[Offset[Text]]) -> Iterator[Span]:
    last_indent = 0
    for view in screen:
        view_indent = view.indent

        for span in view.value.spans():
            indent = view_indent + span.indent
            parsed_str = span.value

            if indent > 0:
                if (diff := indent - last_indent) > 0:
                    parsed_str = f"\x1b[{diff}C{parsed_str}"
                elif diff < 0:
                    parsed_str = f"\x1b[{-diff}D{parsed_str}"

                last_char = parsed_str[-1]
                parsed_str = (
                    f"{parsed_str[:-1].replace('\n', f'\n\x1b[{indent}C')}{last_char}"
                )

                if last_char == "\n":
                    indent = 0

            last_indent = indent

            yield Span(
                value=parsed_str,
                style=span.style,
                indent=0,
            )
