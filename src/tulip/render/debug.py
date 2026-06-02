from functools import partial
from tulip.components._types import CompNode
from tulip.render import TextView, render
from readchar import readchar


def _onrefresh[R](_: list[TextView], nodes: list[CompNode[R]]) -> str:
    for node in reversed(nodes):
        print(node)

    print("---")

    key = readchar()
    print("Key pressed: ", str(key.encode("charmap")))
    print("---")

    if key == "\x03":
        raise KeyboardInterrupt()
    return key


loop = partial(render, onrefresh=_onrefresh)
