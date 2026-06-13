from enum import IntEnum
from typing import Mapping


class Key(IntEnum):
    CTRL_A = 1
    CTRL_B = 2
    CTRL_C = 3
    CTRL_D = 4
    CTRL_E = 5
    CTRL_F = 6
    CTRL_G = 7
    BACKSPACE = 8
    TAB = 9
    LF = 10
    CTRL_K = 11
    CTRL_L = 12
    CR = 13
    CTRL_N = 14
    CTRL_O = 15
    CTRL_P = 16
    CTRL_Q = 17
    CTRL_R = 18
    CTRL_S = 19
    CTRL_T = 20
    CTRL_U = 21
    CTRL_V = 22
    CTRL_W = 23
    CTRL_X = 24
    CTRL_Y = 25
    CTRL_Z = 26

    ESCAPE = 27

    UP = 0x100 + 0
    DOWN = 0x100 + 1
    LEFT = 0x100 + 2
    RIGHT = 0x100 + 3
    DEL = 0x100 + 4
    HOME = 0x100 + 5
    PAGE_UP = 0x100 + 6
    PAGE_DOWN = 0x100 + 7
    END = 0x100 + 8


type EscapeMap = dict[int, EscapeMap | int]


def escape_code_map(escape_codes: Mapping[bytes, int | Key]) -> EscapeMap:
    """Converts flat `escape-sequence -> Key` to a tree structure.

    Unlike vim sequences, escape codes must NOT be prefixes of other sequences.

    Args:
        escape_codes: Mapping of escape sequences to key codes.

    Returns:
        Trie, indexed by character ordinals.
    """
    result: EscapeMap = {}

    for code, mapping in escape_codes.items():
        curr = result
        for chr in code[:-1]:
            curr = curr.setdefault(chr, {})
            assert isinstance(curr, dict), f"Overlapping escape codes! {code}"

        last = code[-1]
        assert last not in curr, f"Overlapping escape codes! {code}"
        curr[last] = mapping

    return result
