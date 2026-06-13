from enum import IntEnum, auto
from typing import Mapping

SPECIAL_KEY_START = 0x110000


class Key(IntEnum):
    # Control characters (1 - 31)
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

    # Printable characters (32-126)
    SPACE = 32
    EXCLAMATION = 33
    DOUBLE_QUOTE = 34
    POUND = 35
    DOLLAR = 36
    PERCENT = 37
    AMPERSAND = 38
    SINGLE_QUOTE = 39
    OPEN_PAREN = 40
    CLOSING_PAREN = 41
    ASTERISK = 42
    PLUS = 43
    COMMA = 44
    MINUS = 45
    DOT = 46
    SLASH = 47

    ## Digits
    ZERO = 48
    ONE = 49
    TWO = 50
    THREE = 51
    FOUR = 52
    FIVE = 53
    SIX = 54
    SEVEN = 55
    EIGHT = 56
    NINE = 57

    COLON = 58
    SEMICOLON = 59
    LESS_THAN = 60
    EQUAL = 61
    GREATER_THAN = 62
    QUESTION = 63
    AT = 64

    ## Uppercase Alphabet (65 - 90)
    A = 65
    B = 66
    C = 67
    D = 68
    E = 69
    F = 70
    G = 71
    H = 72
    I = 73
    J = 74
    K = 75
    L = 76
    M = 77
    N = 78
    O = 79
    P = 80
    Q = 81
    R = 82
    S = 83
    T = 84
    U = 85
    V = 86
    W = 87
    X = 88
    Y = 89
    Z = 90

    OPEN_BRACKET = 91
    BACKSLASH = 92
    CLOSING_BRACKET = 93
    CARET = 94
    UNDERSCORE = 95
    BACKTICK = 96

    ## Lowercase Alphabet (97 - 122)
    A_LOWER = 97
    B_LOWER = 98
    C_LOWER = 99
    D_LOWER = 100
    E_LOWER = 101
    F_LOWER = 102
    G_LOWER = 103
    H_LOWER = 104
    I_LOWER = 105
    J_LOWER = 106
    K_LOWER = 107
    L_LOWER = 108
    M_LOWER = 109
    N_LOWER = 110
    O_LOWER = 111
    P_LOWER = 112
    Q_LOWER = 113
    R_LOWER = 114
    S_LOWER = 115
    T_LOWER = 116
    U_LOWER = 117
    V_LOWER = 118
    W_LOWER = 119
    X_LOWER = 120
    Y_LOWER = 121
    Z_LOWER = 122

    OPEN_BRACE = 123
    PIPE = 124
    CLOSING_BRACE = 125
    TILDE = 126

    DEL = 127

    # Special characters

    ## Arrow keys
    UP = SPECIAL_KEY_START
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    META_UP = auto()
    META_DOWN = auto()
    META_LEFT = auto()
    META_RIGHT = auto()
    CTRL_UP = auto()
    CTRL_DOWN = auto()
    CTRL_LEFT = auto()
    CTRL_RIGHT = auto()

    SDEL = auto()
    HOME = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    END = auto()


type EscapeMap = dict[int, EscapeMap | int]


def escape_code_map(escape_codes: Mapping[bytes, int | Key]) -> EscapeMap:
    """Converts flat `escape-sequence -> Key` mapping to a tree structure.

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
