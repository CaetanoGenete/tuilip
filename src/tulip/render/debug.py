from functools import partial
from tulip.components._types import CompNode, Text
from tulip.render import render
from readchar import readchar


def _onrefresh[R](_: list[Text], nodes: list[CompNode[R]]) -> str:
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
