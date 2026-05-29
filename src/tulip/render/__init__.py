import inspect

from typing import Callable, cast

from tulip.components._types import CompNode, Component, Signal, Text


def render[R](
    *components: Component[R] | Text,
    onrefresh: Callable[[list[Text], list[CompNode[R]]], str],
) -> R:
    nodes = list(map(CompNode, reversed(components)))

    key = ""
    while True:
        screen: list[Text] = []

        stack = nodes.copy()
        while stack:
            curr = stack.pop()
            comp = curr.comp

            if isinstance(comp, Text):
                screen.append(comp)
                continue

            created = inspect.getgeneratorstate(comp.gen) != "GEN_CREATED"
            if comp.stateless and created:
                assert comp.cache, "Component generator ran outside of loop!"
                stack.extend(reversed(comp.cache.children))
                continue

            new_children: list[CompNode[R]] = []
            while True:
                try:
                    if created:
                        child = comp.gen.send(key)
                    else:
                        child = next(comp.gen)
                        created = True

                except StopIteration as e:
                    if comp.stateless:
                        break
                    return cast(R, e.value)

                match child:
                    case Signal.NO_CHANGE:
                        assert comp.cache, "Component generator ran outside of loop!"
                        new_children = comp.cache.children
                        break
                    case None:
                        break
                    case _:
                        # QOL: allow users to provide _raw_ strings.
                        if isinstance(child, str):
                            child = Text(child)

                        new_children.append(CompNode(child))

            comp.cache = curr
            curr.children = new_children
            stack.extend(reversed(curr.children))

        key = onrefresh(screen, nodes)
