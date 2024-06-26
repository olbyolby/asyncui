"""
Defines an Enumeration for ModifierKeys and Keys.

Enums:
    ModifierKeys: Enumeration of every modifier key
    Keys: Enumeration of every Key with names
"""
import pygame
import logging
from enum import Enum, Flag
from typing import Any

logger = logging.getLogger(__name__)

class ModifierKeys(Flag):
    """
    An enumeration containing named constants for every modifier key
    """
    Empty = pygame.KMOD_MODE
    LeftShift = pygame.KMOD_LSHIFT
    RightShift = pygame.KMOD_RSHIFT
    Shift = pygame.KMOD_SHIFT
    LeftControl = pygame.KMOD_LCTRL
    RightControl = pygame.KMOD_RCTRL
    Control = pygame.KMOD_CTRL
    LeftAlt = pygame.KMOD_LALT
    RightAlt = pygame.KMOD_RALT
    Alt = pygame.KMOD_ALT
    Meta = pygame.KMOD_META
    LeftMeta = pygame.KMOD_LMETA
    RightMeta = pygame.KMOD_RMETA
    CapsLock = pygame.KMOD_CAPS
    NumLock = pygame.KMOD_NUM
    AltGr = pygame.KMOD_MODE  # Wtf is AltGr?


class Keys(Enum):
    """
    An enumeration containing named constants for every pygame key, each has type "Key"
    """
    Backspace = pygame.K_BACKSPACE
    Tab = pygame.K_TAB
    Clear = pygame.K_CLEAR
    Return = pygame.K_RETURN
    Pause = pygame.K_PAUSE
    Escape = pygame.K_ESCAPE
    Space = pygame.K_SPACE
    Exclaim = pygame.K_EXCLAIM
    Quotedbl = pygame.K_QUOTEDBL
    Hash = pygame.K_HASH
    Dollar = pygame.K_DOLLAR
    Ampersand = pygame.K_AMPERSAND
    Quote = pygame.K_QUOTE
    LeftParen = pygame.K_LEFTPAREN
    RightParen = pygame.K_RIGHTPAREN
    Asterisk = pygame.K_ASTERISK
    Plus = pygame.K_PLUS
    Comma = pygame.K_COMMA
    Minus = pygame.K_MINUS
    Period = pygame.K_PERIOD
    Slash = pygame.K_SLASH
    Zero = pygame.K_0
    One = pygame.K_1
    Two = pygame.K_2
    Three = pygame.K_3
    Four = pygame.K_4
    Five = pygame.K_5
    Six = pygame.K_6
    Seven = pygame.K_7
    Eight = pygame.K_8
    Nine = pygame.K_9
    Colon = pygame.K_COLON
    Semicolon = pygame.K_SEMICOLON
    Less = pygame.K_LESS
    Equals = pygame.K_EQUALS
    Greater = pygame.K_GREATER
    Question = pygame.K_QUESTION
    At = pygame.K_AT
    LeftBracket = pygame.K_LEFTBRACKET
    Backslash = pygame.K_BACKSLASH
    RightBracket = pygame.K_RIGHTBRACKET
    Caret = pygame.K_CARET
    Underscore = pygame.K_UNDERSCORE
    Backquote = pygame.K_BACKQUOTE
    A = pygame.K_a
    B = pygame.K_b
    C = pygame.K_c
    D = pygame.K_d
    E = pygame.K_e
    F = pygame.K_f
    G = pygame.K_g
    H = pygame.K_h
    I = pygame.K_i  # noqa: E741
    J = pygame.K_j
    K = pygame.K_k
    L = pygame.K_l
    M = pygame.K_m
    N = pygame.K_n
    O = pygame.K_o  # noqa: E741
    P = pygame.K_p
    Q = pygame.K_q
    R = pygame.K_r
    S = pygame.K_s
    T = pygame.K_t
    U = pygame.K_u
    V = pygame.K_v
    W = pygame.K_w
    X = pygame.K_x
    Y = pygame.K_y
    Z = pygame.K_z
    Delete = pygame.K_DELETE
    KP0 = pygame.K_KP0
    KP1 = pygame.K_KP1
    KP2 = pygame.K_KP2
    KP3 = pygame.K_KP3
    KP4 = pygame.K_KP4
    KP5 = pygame.K_KP5
    KP6 = pygame.K_KP6
    KP7 = pygame.K_KP7
    KP8 = pygame.K_KP8
    KP9 = pygame.K_KP9
    KPPeriod = pygame.K_KP_PERIOD
    KPDivide = pygame.K_KP_DIVIDE
    KPMultiply = pygame.K_KP_MULTIPLY
    KPMinus = pygame.K_KP_MINUS
    KPPlus = pygame.K_KP_PLUS
    KPEnter = pygame.K_KP_ENTER
    KPEquals = pygame.K_KP_EQUALS
    Up = pygame.K_UP
    Down = pygame.K_DOWN
    Right = pygame.K_RIGHT
    Left = pygame.K_LEFT
    Insert = pygame.K_INSERT
    Home = pygame.K_HOME
    End = pygame.K_END
    PageUp = pygame.K_PAGEUP
    PageDown = pygame.K_PAGEDOWN
    F1 = pygame.K_F1
    F2 = pygame.K_F2
    F3 = pygame.K_F3
    F4 = pygame.K_F4
    F5 = pygame.K_F5
    F6 = pygame.K_F6
    F7 = pygame.K_F7
    F8 = pygame.K_F8
    F9 = pygame.K_F9
    F10 = pygame.K_F10
    F11 = pygame.K_F11
    F12 = pygame.K_F12
    F13 = pygame.K_F13
    F14 = pygame.K_F14
    F15 = pygame.K_F15
    Numlock = pygame.K_NUMLOCK
    Capslock = pygame.K_CAPSLOCK
    Scrollock = pygame.K_SCROLLOCK
    RShift = pygame.K_RSHIFT
    LShift = pygame.K_LSHIFT
    RCtrl = pygame.K_RCTRL
    LCtrl = pygame.K_LCTRL
    RAlt = pygame.K_RALT
    LAlt = pygame.K_LALT
    RMeta = pygame.K_RMETA
    LMeta = pygame.K_LMETA
    LSuper = pygame.K_LSUPER
    RSuper = pygame.K_RSUPER
    Mode = pygame.K_MODE
    Help = pygame.K_HELP
    Print = pygame.K_PRINT
    SysReq = pygame.K_SYSREQ
    Break = pygame.K_BREAK
    Menu = pygame.K_MENU
    Power = pygame.K_POWER
    Euro = pygame.K_EURO
    AcBack = pygame.K_AC_BACK

    ErrorKey = -1 # You should not see this, if you do, something has gone horribly wrong.
    @classmethod
    def _missing_(cls, value: object) -> int | Any:
        if isinstance(value, int):
            logger.warn(f"Unknown key with code {value} was recived, returning ErrorKey")
            return cls.ErrorKey
        return super()._missing_(value)
    
