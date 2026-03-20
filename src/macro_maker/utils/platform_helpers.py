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

import sys

_WINDOWS = sys.platform == "win32"
_MACOS   = sys.platform == "darwin"

if _WINDOWS:
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

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx",          ctypes.c_long),
            ("dy",          ctypes.c_long),
            ("mouseData",   ctypes.c_ulong),
            ("dwFlags",     ctypes.c_ulong),
            ("time",        ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _INPUTunion(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT)]

        _anonymous_ = ("_input",)
        _fields_    = [("type", ctypes.c_ulong), ("_input", _INPUTunion)]

    def _win_to_abs(x: int, y: int) -> tuple:
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(78)
        sh = user32.GetSystemMetrics(79)
        ox = user32.GetSystemMetrics(76)
        oy = user32.GetSystemMetrics(77)
        return int((x - ox) * 65535 / sw), int((y - oy) * 65535 / sh)


def get_mouse_pos() -> tuple:
    if _WINDOWS:
        class _POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = _POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    try:
        from pynput.mouse import Controller as _MC
        return _MC().position
    except Exception:
        return 0, 0


def send_mouse_move(x: int, y: int) -> None:
    if _WINDOWS:
        ax, ay = _win_to_abs(x, y)
        user32 = ctypes.windll.user32
        inp = (INPUT * 1)(INPUT(
            type=INPUT_MOUSE,
            mi=MOUSEINPUT(
                dx=ax, dy=ay,
                dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
            ),
        ))
        user32.SendInput(1, inp, ctypes.sizeof(INPUT))
    elif _MACOS:
        try:
            import Quartz
            ev = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventMouseMoved, (float(x), float(y)), 0)
            Quartz.CGEventPost(Quartz.kCGSessionEventTap, ev)
        except Exception:
            from pynput.mouse import Controller as _MC
            _MC().position = (x, y)


def send_mouse_input(x: int, y: int, button: str, pressed: bool) -> None:
    if _WINDOWS:
        ax, ay = _win_to_abs(x, y)
        user32 = ctypes.windll.user32

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
    else:
        from pynput.mouse import Controller as _MC, Button as _Btn
        mc = _MC()
        mc.position = (x, y)
        if button == "right":
            btn = _Btn.right
        elif button == "middle":
            btn = _Btn.middle
        else:
            btn = _Btn.left
        if pressed:
            mc.press(btn)
        else:
            mc.release(btn)


def set_window_topmost(hwnd_int: int, topmost: bool) -> None:
    import ctypes
    import ctypes.util

    if _MACOS:
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))

        libobjc.sel_registerName.restype  = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        libobjc.objc_msgSend.restype  = ctypes.c_void_p
        libobjc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        sel_window   = libobjc.sel_registerName(b"window")
        sel_setLevel = libobjc.sel_registerName(b"setLevel:")

        ns_view   = ctypes.c_void_p(hwnd_int)
        ns_window = libobjc.objc_msgSend(ns_view, sel_window)

        NSFloatingWindowLevel = 3
        NSNormalWindowLevel   = 0
        level = NSFloatingWindowLevel if topmost else NSNormalWindowLevel

        libobjc.objc_msgSend.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long,
        ]
        libobjc.objc_msgSend(ns_window, sel_setLevel, level)
        return

    if not _WINDOWS:
        return

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
