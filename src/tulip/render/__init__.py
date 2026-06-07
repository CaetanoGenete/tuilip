from dataclasses import dataclass
import inspect
from typing import Callable, cast

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
    onrefresh: Callable[[list[TextView]], str],
) -> R:
    nodes = list(map(CompNode, reversed(components)))

    key = ""
    while True:
        screen: list[TextView] = []

        noprop_idx = 1 << 31
        indent_stack = [(0, 0)]

        stack = nodes.copy()
        while stack:
            curr = stack.pop()
            comp = curr.comp

            stacklen = len(stack)
            if not curr.propkey:
                noprop_idx = min(noprop_idx, stacklen)

            indent_idx, indent = indent_stack[-1]
            while stacklen < indent_idx:
                _ = indent_stack.pop()
                indent_idx, indent = indent_stack[-1]

            if isinstance(comp, Text):
                screen.append(TextView(comp, indent))
                continue

            if comp.indent:
                indent_stack.append((stacklen, indent + comp.indent))

            created = inspect.getgeneratorstate(comp.gen) != "GEN_CREATED"
            if comp.stateless and created:
                assert comp.cache, "Component generator ran outside of loop!"
                stack.extend(reversed(comp.cache.children))
                continue

            if stacklen >= noprop_idx:
                effective_key = ""
            else:
                effective_key = key
                noprop_idx = 1 << 31

            new_children: list[CompNode[R]] = []
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
                        cached_text.clear()
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
