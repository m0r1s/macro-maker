"""
MORIS UNIVERSAL LICENSE (MUL) - Version 1.0
Copyright (c) moris

This software is licensed under the MORIS UNIVERSAL LICENSE (MUL).
By downloading, copying, or running this software, you agree to accept all terms and conditions
of the MUL license, which are included in the accompanying LICENSE.md file.

KEY TERMS:
- Personal use only (non-commercial)
- Attribution to original author is REQUIRED
- Commercial use is strictly prohibited
- Redistribution without license and attribution is prohibited
- Personal modifications allowed, but derivatives must retain original credit
- NO WARRANTY - use at your own risk

Full license text: See LICENSE.md
For support: https://discord.gg/2fraBuhe3m
"""

"""Windows-platform ctypes structures and helper functions.

No Qt imports here — pure ctypes / stdlib only.
"""

import ctypes
import ctypes.wintypes

from .constants import (
    INPUT_MOUSE,
    MOUSEEVENTF_ABSOLUTE,
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
    MOUSEEVENTF_MIDDLEDOWN,
    MOUSEEVENTF_MIDDLEUP,
    MOUSEEVENTF_MOVE,
    MOUSEEVENTF_RIGHTDOWN,
    MOUSEEVENTF_RIGHTUP,
    MOUSEEVENTF_VIRTUALDESK,
)


# ---------------------------------------------------------------------------
# ctypes structures
# ---------------------------------------------------------------------------

class MOUSEINPUT(ctypes.Structure):
    """Mirrors the Win32 MOUSEINPUT structure."""

    _fields_ = [
        ("dx",          ctypes.c_long),
        ("dy",          ctypes.c_long),
        ("mouseData",   ctypes.c_ulong),
        ("dwFlags",     ctypes.c_ulong),
        ("time",        ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    """Mirrors the Win32 INPUT structure (mouse variant)."""

    class _INPUTunion(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("_input",)
    _fields_    = [("type", ctypes.c_ulong), ("_input", _INPUTunion)]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def send_mouse_move(x: int, y: int) -> None:
    """Move the mouse cursor to absolute screen coordinates (x, y).

    Args:
        x: Target X coordinate in screen pixels.
        y: Target Y coordinate in screen pixels.
    """
    user32 = ctypes.windll.user32
    sw = user32.GetSystemMetrics(78)
    sh = user32.GetSystemMetrics(79)
    ox = user32.GetSystemMetrics(76)
    oy = user32.GetSystemMetrics(77)
    ax = int((x - ox) * 65535 / sw)
    ay = int((y - oy) * 65535 / sh)
    inp = (INPUT * 1)(INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(
            dx=ax, dy=ay,
            dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
        ),
    ))
    user32.SendInput(1, inp, ctypes.sizeof(INPUT))


def send_mouse_input(x: int, y: int, button: str, pressed: bool) -> None:
    """Send a mouse button event at absolute coordinates.

    Moves to (x, y) first, then fires the press/release flag.

    Args:
        x: Target X coordinate in screen pixels.
        y: Target Y coordinate in screen pixels.
        button: One of ``"left"``, ``"right"``, or ``"middle"``.
        pressed: ``True`` for a down event, ``False`` for an up event.
    """
    user32 = ctypes.windll.user32
    sw = user32.GetSystemMetrics(78)
    sh = user32.GetSystemMetrics(79)
    ox = user32.GetSystemMetrics(76)
    oy = user32.GetSystemMetrics(77)
    ax = int((x - ox) * 65535 / sw)
    ay = int((y - oy) * 65535 / sh)

    if button == "right":
        btn_flag = MOUSEEVENTF_RIGHTDOWN if pressed else MOUSEEVENTF_RIGHTUP
    elif button == "middle":
        btn_flag = MOUSEEVENTF_MIDDLEDOWN if pressed else MOUSEEVENTF_MIDDLEUP
    else:
        btn_flag = MOUSEEVENTF_LEFTDOWN if pressed else MOUSEEVENTF_LEFTUP

    move_inp = (INPUT * 1)(INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(
            dx=ax, dy=ay,
            dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
        ),
    ))
    user32.SendInput(1, move_inp, ctypes.sizeof(INPUT))

    btn_inp = (INPUT * 1)(INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(
            dx=ax, dy=ay,
            dwFlags=btn_flag | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
        ),
    ))
    user32.SendInput(1, btn_inp, ctypes.sizeof(INPUT))


def set_window_topmost(hwnd_int: int, topmost: bool) -> None:
    """Set or clear the TOPMOST flag for a window.

    Args:
        hwnd_int: Integer representation of the window handle.
        topmost: ``True`` to pin on top, ``False`` to remove.
    """
    user32 = ctypes.windll.user32
    hwnd = ctypes.wintypes.HWND(hwnd_int)
    user32.SetWindowPos.restype  = ctypes.wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        ctypes.wintypes.HWND, ctypes.wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.wintypes.UINT,
    ]
    HWND_TOPMOST   = ctypes.wintypes.HWND(-1)
    HWND_NOTOPMOST = ctypes.wintypes.HWND(-2)
    SWP_NOSIZE     = 0x0001
    SWP_NOMOVE     = 0x0002
    SWP_NOACTIVATE = 0x0010
    user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST if topmost else HWND_NOTOPMOST,
        0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
    )
