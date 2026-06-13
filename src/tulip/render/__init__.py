from dataclasses import dataclass
from inspect import GEN_CREATED, getgeneratorstate
from typing import cast

from collections.abc import Callable
from tulip.components.types import Component
from tulip.render.exceptions import TooManyChildrenException
from tulip.render.types import CompNode, Signal, Text


@dataclass(slots=True)
class TextView:
    text: Text
    indent: int


MAX_COMPONENT_CHILDREN = 1000


def render[R](
    *components: Component[R] | Text,
    onrefresh: Callable[[list[TextView]], int],
) -> R:
    nodes = list(map(CompNode, reversed(components)))

    key = 0
    while True:
        screen: list[TextView] = []

        noprop_idx = 1 << 31
        # stores (indent, stack_ptr) flattened tuples.
        indent_stack = [0, 0]

        stack = nodes.copy()
        while stack:
            curr = stack.pop()
            comp = curr.comp

            stacklen = len(stack)

            if not curr.propkey:
                noprop_idx = min(noprop_idx, stacklen)

            while stacklen < indent_stack[-1]:
                del indent_stack[-2:]
            indent = indent_stack[-2]

            if isinstance(comp, Text):
                screen.append(TextView(comp, indent))
                continue

            if comp.indent:
                indent_stack.extend((indent + comp.indent, stacklen))

            created = getgeneratorstate(comp.gen) is not GEN_CREATED
            if comp.stateless and created:
                assert comp.cache, "Component generator ran outside of loop!"
                stack.extend(reversed(comp.cache.children))
                continue

            if stacklen >= noprop_idx:
                effective_key = 0
            else:
                effective_key = key
                noprop_idx = 1 << 31

            new_children: list[CompNode[R]] = []
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
                    if comp.stateless:
                        break
                    return cast(R, e.value)

                match child:
                    case Signal.NOCHANGE:
                        assert comp.cache, "Component generator ran outside of loop!"
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
                        break
                    case _:
                        pass

                # Optimisation: squash contiguous text nodes, to reduce node count.
                if isinstance(child, (str, Text)):
                    cached_text += child
                    continue

                if cached_text:
                    new_children.append(CompNode(cached_text, propkey=propkey))
                    cached_text = Text()

                new_children.append(CompNode(child, propkey=propkey))
            else:
                raise TooManyChildrenException(comp)

            if cached_text:
                new_children.append(CompNode(cached_text, propkey=propkey))

            comp.cache = curr
            curr.children = new_children
            stack.extend(reversed(curr.children))

        key = onrefresh(screen)
