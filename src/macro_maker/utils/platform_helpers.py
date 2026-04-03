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
import threading

_WINDOWS = sys.platform == "win32"
_MACOS   = sys.platform == "darwin"

if _WINDOWS:
    import ctypes
    import ctypes.wintypes

if _MACOS:
    import ctypes as _ct

    _kCGSessionEventTap          = 1
    _kCGHeadInsertEventTap       = 0
    _kCGEventTapOptionListenOnly = 1
    _kCGEventRightMouseDragged   = 7
    _kCGMouseButtonRight         = 1
    _kCGMouseEventDeltaX         = 4
    _kCGMouseEventDeltaY         = 5

    class _CGPoint(_ct.Structure):
        _fields_ = [("x", _ct.c_double), ("y", _ct.c_double)]

    _CGEventTapCallBack = _ct.CFUNCTYPE(
        _ct.c_void_p,
        _ct.c_void_p,
        _ct.c_uint32,
        _ct.c_void_p,
        _ct.c_void_p,
    )

    try:
        _cg = _ct.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        _cf = _ct.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")

        _cg.CGEventCreate.restype              = _ct.c_void_p
        _cg.CGEventCreate.argtypes             = [_ct.c_void_p]
        _cg.CGEventGetLocation.restype         = _CGPoint
        _cg.CGEventGetLocation.argtypes        = [_ct.c_void_p]
        _cg.CGEventCreateMouseEvent.restype    = _ct.c_void_p
        _cg.CGEventCreateMouseEvent.argtypes   = [
            _ct.c_void_p, _ct.c_uint32, _CGPoint, _ct.c_uint32]
        _cg.CGEventSetIntegerValueField.argtypes = [
            _ct.c_void_p, _ct.c_uint32, _ct.c_int64]
        _cg.CGEventPost.argtypes               = [_ct.c_uint32, _ct.c_void_p]
        _cg.CGEventGetIntegerValueField.restype  = _ct.c_int64
        _cg.CGEventGetIntegerValueField.argtypes = [_ct.c_void_p, _ct.c_uint32]
        _cg.CGEventTapCreate.restype   = _ct.c_void_p
        _cg.CGEventTapCreate.argtypes  = [
            _ct.c_uint32, _ct.c_uint32, _ct.c_uint32,
            _ct.c_uint64, _CGEventTapCallBack, _ct.c_void_p,
        ]
        _cg.CGEventTapEnable.argtypes  = [_ct.c_void_p, _ct.c_bool]

        _cf.CFMachPortCreateRunLoopSource.restype  = _ct.c_void_p
        _cf.CFMachPortCreateRunLoopSource.argtypes = [
            _ct.c_void_p, _ct.c_void_p, _ct.c_long]
        _cf.CFRunLoopGetCurrent.restype  = _ct.c_void_p
        _cf.CFRunLoopGetCurrent.argtypes = []
        _cf.CFRunLoopAddSource.argtypes  = [
            _ct.c_void_p, _ct.c_void_p, _ct.c_void_p]
        _cf.CFRunLoopRunInMode.restype   = _ct.c_int32
        _cf.CFRunLoopRunInMode.argtypes  = [
            _ct.c_void_p, _ct.c_double, _ct.c_bool]
        _cf.CFRunLoopRemoveSource.argtypes = [
            _ct.c_void_p, _ct.c_void_p, _ct.c_void_p]
        _cf.CFRelease.argtypes = [_ct.c_void_p]

        _kCFRunLoopDefaultMode = _ct.c_void_p.in_dll(
            _cf, "kCFRunLoopDefaultMode").value
        _MACOS_CG_OK = True
    except Exception:
        _MACOS_CG_OK = False

if _WINDOWS:
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

    _WM_INPUT       = 0x00FF
    _RIM_TYPEMOUSE  = 0
    _RIDEV_INPUTSINK = 0x00000100
    _RIDEV_REMOVE   = 0x00000001
    _RID_INPUT      = 0x10000003
    _PM_REMOVE      = 0x0001

    class _RAWINPUTDEVICE(ctypes.Structure):
        _fields_ = [
            ("usUsagePage", ctypes.c_ushort),
            ("usUsage",     ctypes.c_ushort),
            ("dwFlags",     ctypes.c_ulong),
            ("hwndTarget",  ctypes.wintypes.HWND),
        ]

    class _RAWINPUTHEADER(ctypes.Structure):
        _fields_ = [
            ("dwType",  ctypes.c_ulong),
            ("dwSize",  ctypes.c_ulong),
            ("hDevice", ctypes.wintypes.HANDLE),
            ("wParam",  ctypes.wintypes.WPARAM),
        ]

    class _RAWMOUSE_BTN_STRUCT(ctypes.Structure):
        _fields_ = [
            ("usButtonFlags", ctypes.c_ushort),
            ("usButtonData",  ctypes.c_ushort),
        ]

    class _RAWMOUSE_BTN_UNION(ctypes.Union):
        _fields_ = [
            ("ulButtons", ctypes.c_ulong),
            ("_s",        _RAWMOUSE_BTN_STRUCT),
        ]

    class _RAWMOUSE(ctypes.Structure):
        _anonymous_ = ("_u",)
        _fields_ = [
            ("usFlags",            ctypes.c_ushort),
            ("_u",                 _RAWMOUSE_BTN_UNION),
            ("ulRawButtons",       ctypes.c_ulong),
            ("lLastX",             ctypes.c_long),
            ("lLastY",             ctypes.c_long),
            ("ulExtraInformation", ctypes.c_ulong),
        ]

    class _RAWINPUT_UNION(ctypes.Union):
        _fields_ = [("mouse", _RAWMOUSE)]

    class _RAWINPUT(ctypes.Structure):
        _fields_ = [
            ("header", _RAWINPUTHEADER),
            ("data",   _RAWINPUT_UNION),
        ]

    class _RI_MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd",    ctypes.wintypes.HWND),
            ("message", ctypes.c_uint),
            ("wParam",  ctypes.wintypes.WPARAM),
            ("lParam",  ctypes.wintypes.LPARAM),
            ("time",    ctypes.c_ulong),
            ("pt",      ctypes.wintypes.POINT),
        ]

    _WNDPROC_T = ctypes.WINFUNCTYPE(
        ctypes.c_ssize_t,
        ctypes.wintypes.HWND,
        ctypes.c_uint,
        ctypes.wintypes.WPARAM,
        ctypes.wintypes.LPARAM,
    )

    class _WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize",        ctypes.c_uint),
            ("style",         ctypes.c_uint),
            ("lpfnWndProc",   _WNDPROC_T),
            ("cbClsExtra",    ctypes.c_int),
            ("cbWndExtra",    ctypes.c_int),
            ("hInstance",     ctypes.wintypes.HANDLE),
            ("hIcon",         ctypes.wintypes.HANDLE),
            ("hCursor",       ctypes.wintypes.HANDLE),
            ("hbrBackground", ctypes.wintypes.HANDLE),
            ("lpszMenuName",  ctypes.c_wchar_p),
            ("lpszClassName", ctypes.c_wchar_p),
            ("hIconSm",       ctypes.wintypes.HANDLE),
        ]


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


def send_mouse_move(x: int, y: int, held_button: str = None) -> None:
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
            if held_button == "right":
                evt_type = Quartz.kCGEventRightMouseDragged
                btn_num  = Quartz.kCGMouseButtonRight
            elif held_button == "left":
                evt_type = Quartz.kCGEventLeftMouseDragged
                btn_num  = Quartz.kCGMouseButtonLeft
            else:
                evt_type = Quartz.kCGEventMouseMoved
                btn_num  = 0
            ev = Quartz.CGEventCreateMouseEvent(
                None, evt_type, (float(x), float(y)), btn_num)
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


def set_timer_resolution_ms(period: int = 1) -> None:
    if _WINDOWS:
        ctypes.windll.winmm.timeBeginPeriod(period)


def reset_timer_resolution_ms(period: int = 1) -> None:
    if _WINDOWS:
        ctypes.windll.winmm.timeEndPeriod(period)


def send_mouse_move_relative(dx: int, dy: int) -> None:
    if _WINDOWS:
        user32 = ctypes.windll.user32
        inp = (INPUT * 1)(INPUT(
            type=INPUT_MOUSE,
            mi=MOUSEINPUT(
                dx=dx, dy=dy,
                dwFlags=MOUSEEVENTF_MOVE,
            ),
        ))
        user32.SendInput(1, inp, ctypes.sizeof(INPUT))
    elif _MACOS and _MACOS_CG_OK:
        try:
            ev_src = _cg.CGEventCreate(None)
            loc    = _cg.CGEventGetLocation(ev_src)
            new_x  = loc.x + dx
            new_y  = loc.y + dy
            ev = _cg.CGEventCreateMouseEvent(
                None, _kCGEventRightMouseDragged,
                _CGPoint(new_x, new_y), _kCGMouseButtonRight,
            )
            _cg.CGEventSetIntegerValueField(ev, _kCGMouseEventDeltaX, int(dx))
            _cg.CGEventSetIntegerValueField(ev, _kCGMouseEventDeltaY, int(dy))
            _cg.CGEventPost(_kCGSessionEventTap, ev)
        except Exception:
            pass


class RawMouseInputListener:

    def __init__(self, callback) -> None:
        self._callback  = callback
        self._stop_evt  = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not (_WINDOWS or _MACOS):
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="MMR-RawInput")
        self._thread.start()

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        if _WINDOWS:
            self._run_windows()
        elif _MACOS:
            self._run_macos()

    def _run_macos(self) -> None:
        if not _MACOS_CG_OK:
            return
        try:
            cb       = self._callback
            stop_evt = self._stop_evt

            def _tap_cb(proxy, type_, event, _refcon):
                if type_ == _kCGEventRightMouseDragged:
                    dx = int(_cg.CGEventGetIntegerValueField(
                        event, _kCGMouseEventDeltaX))
                    dy = int(_cg.CGEventGetIntegerValueField(
                        event, _kCGMouseEventDeltaY))
                    if dx != 0 or dy != 0:
                        cb(dx, dy)
                return event

            tap_cb = _CGEventTapCallBack(_tap_cb)
            self._macos_tap_cb = tap_cb

            mask = _ct.c_uint64(1 << _kCGEventRightMouseDragged)
            tap  = _cg.CGEventTapCreate(
                _kCGSessionEventTap,
                _kCGHeadInsertEventTap,
                _kCGEventTapOptionListenOnly,
                mask,
                tap_cb,
                None,
            )
            if not tap:
                return

            rl_source = _cf.CFMachPortCreateRunLoopSource(None, tap, 0)
            run_loop  = _cf.CFRunLoopGetCurrent()
            _cf.CFRunLoopAddSource(run_loop, rl_source, _kCFRunLoopDefaultMode)
            _cg.CGEventTapEnable(tap, True)

            while not stop_evt.is_set():
                _cf.CFRunLoopRunInMode(_kCFRunLoopDefaultMode, 0.01, False)

            _cg.CGEventTapEnable(tap, False)
            _cf.CFRunLoopRemoveSource(run_loop, rl_source, _kCFRunLoopDefaultMode)
            _cf.CFRelease(rl_source)
            _cf.CFRelease(tap)
        except Exception:
            pass

    def _run_windows(self) -> None:
        user32   = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        cb       = self._callback
        stop_evt = self._stop_evt

        user32.DefWindowProcW.restype  = ctypes.c_ssize_t
        user32.DefWindowProcW.argtypes = [
            ctypes.wintypes.HWND,
            ctypes.c_uint,
            ctypes.wintypes.WPARAM,
            ctypes.wintypes.LPARAM,
        ]

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == _WM_INPUT:
                sz = ctypes.c_uint(0)
                user32.GetRawInputData(
                    ctypes.wintypes.HANDLE(lparam), _RID_INPUT,
                    None, ctypes.byref(sz), ctypes.sizeof(_RAWINPUTHEADER),
                )
                if sz.value > 0:
                    buf = (ctypes.c_byte * sz.value)()
                    user32.GetRawInputData(
                        ctypes.wintypes.HANDLE(lparam), _RID_INPUT,
                        buf, ctypes.byref(sz), ctypes.sizeof(_RAWINPUTHEADER),
                    )
                    raw = ctypes.cast(buf, ctypes.POINTER(_RAWINPUT)).contents
                    if raw.header.dwType == _RIM_TYPEMOUSE:
                        dx = raw.data.mouse.lLastX
                        dy = raw.data.mouse.lLastY
                        if dx != 0 or dy != 0:
                            cb(dx, dy)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        proc_cb     = _WNDPROC_T(wnd_proc)
        hinstance   = kernel32.GetModuleHandleW(None)
        class_name  = "MMR_RawMouseInput_v1"

        wc              = _WNDCLASSEXW()
        wc.cbSize       = ctypes.sizeof(_WNDCLASSEXW)
        wc.lpfnWndProc  = proc_cb
        wc.hInstance    = hinstance
        wc.lpszClassName = class_name
        user32.RegisterClassExW(ctypes.byref(wc))

        hwnd = user32.CreateWindowExW(
            0, class_name, None, 0,
            0, 0, 0, 0,
            ctypes.wintypes.HWND(-3),
            None, hinstance, None,
        )

        rid             = _RAWINPUTDEVICE()
        rid.usUsagePage = 0x01
        rid.usUsage     = 0x02
        rid.dwFlags     = _RIDEV_INPUTSINK
        rid.hwndTarget  = hwnd
        user32.RegisterRawInputDevices(
            ctypes.byref(rid), 1, ctypes.sizeof(_RAWINPUTDEVICE))

        msg = _RI_MSG()
        while not stop_evt.is_set():
            while user32.PeekMessageW(
                    ctypes.byref(msg), None, 0, 0, _PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            stop_evt.wait(timeout=0.001)

        rid2             = _RAWINPUTDEVICE()
        rid2.usUsagePage = 0x01
        rid2.usUsage     = 0x02
        rid2.dwFlags     = _RIDEV_REMOVE
        rid2.hwndTarget  = None
        user32.RegisterRawInputDevices(
            ctypes.byref(rid2), 1, ctypes.sizeof(_RAWINPUTDEVICE))
        user32.DestroyWindow(hwnd)
        user32.UnregisterClassW(class_name, hinstance)


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
