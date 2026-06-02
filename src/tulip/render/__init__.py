from dataclasses import dataclass
import inspect

from typing import Callable, cast

from tulip.components._types import CompNode, Component, Signal, Text


@dataclass(slots=True)
class TextView:
    text: Text
    indent: int


def render[R](
    *components: Component[R] | Text,
    onrefresh: Callable[[list[TextView], list[CompNode[R]]], str],
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

            new_children: list[CompNode[R]] = []
            # Keeps track of whether the previous child was textual.
            was_text: bool = False
            # Whether child nodes should propogate 'key'
            propkey = True

            if stacklen >= noprop_idx:
                effective_key = ""
            else:
                effective_key = key
                noprop_idx = 1 << 31

            while True:
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

                # QOL: allow users to provide _raw_ strings.
                if isinstance(child, str):
                    child = Text(child)

                # Optimisation: squash contiguous text nodes, to reduce node count.
                if isinstance(child, Text):
                    if was_text:
                        new_children[-1].comp = (
                            cast(Text, new_children[-1].comp) + child
                        )
                        continue

                    was_text = True
                else:
                    was_text = False

                new_children.append(CompNode(child, propkey=propkey))

            comp.cache = curr
            curr.children = new_children
            stack.extend(reversed(curr.children))

        key = onrefresh(screen, nodes)
