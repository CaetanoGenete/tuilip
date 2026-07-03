from dataclasses import dataclass
from inspect import GEN_CLOSED, GEN_CREATED, getgeneratorstate
from typing import Generator, Iterable, Iterator, Reversible, cast

from collections.abc import Callable

from tuilip.components.types import Component
from tuilip.input import InputHandler
from tuilip.render.exceptions import TooManyChildrenException
from tuilip.render.types import RENDERER_CONTEXT, RendererContext, Signal, Span, Text


@dataclass(slots=True)
class TextView:
    text: Text
    indent: int


MAX_COMPONENT_CHILDREN = 1000


def render_it[R](
    components: Reversible[Component[R] | Text],
) -> Generator[list[TextView], int, R]:
    key = 0
    while True:
        screen: list[TextView] = []

        noprop_idx = 1 << 31
        # stores (indent, stack_ptr) flattened tuples.
        indent_stack = [0, 0]

        stack = list(reversed(components))
        while stack:
            comp = stack.pop()
            stacklen = len(stack)

            while stacklen < indent_stack[-1]:
                del indent_stack[-2:]
            indent = indent_stack[-2]

            if isinstance(comp, Text):
                screen.append(TextView(comp, indent))
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

            new_children: list[Component[R] | Text] = []
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

                child.cache.propkey = propkey
                new_children.append(child)
            else:
                raise TooManyChildrenException(comp)

            if cached_text:
                new_children.append(cached_text)

            comp.cache.children = new_children
            stack.extend(reversed(new_children))

        key = yield screen


def render[R](
    *components: Component[R] | Text,
    input_handler: InputHandler,
    draw: Callable[[list[TextView]], None],
) -> R:
    token = RENDERER_CONTEXT.set(RendererContext(input_handler))
    try:
        renderer = render_it(components)

        try:
            screen = next(renderer)
        except StopIteration as e:
            return e.value

        while True:
            draw(screen)
            try:
                screen = renderer.send(input_handler.read())
            except StopIteration as e:
                return e.value
    finally:
        RENDERER_CONTEXT.reset(token)


def resolve_indent(screen: Iterable[TextView]) -> Iterator[Span]:
    last_indent = 0
    for view in screen:
        view_indent = view.indent

        for span in view.text.spans():
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
