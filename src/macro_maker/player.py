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

import math
import random
import sys
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal

from .utils.platform_helpers import (
    get_mouse_pos, send_mouse_move, send_mouse_input,
    send_mouse_move_relative, set_timer_resolution_ms, reset_timer_resolution_ms,
)
from .utils.serialization import parse_key, send_webhook, ser_key_to_canon

try:
    from pynput.keyboard import Controller as KbCtrl
    from pynput.mouse import Button as MsBtn, Controller as MsCtrl
    _OK = True
except ImportError:
    _OK = False


def _expand_loops(events: list) -> list:
    result: list = []
    segment_start: int = 0
    for ev in events:
        if ev.get("type") == "loop_above":
            count = max(1, int(ev.get("count", 1)))
            segment = result[segment_start:]
            if segment and count > 1:
                t0       = segment[0]["time"]
                t_last   = segment[-1]["time"]
                span     = t_last - t0
                last_end = t_last
                for _ in range(count - 1):
                    for seg_ev in segment:
                        new_ev = dict(seg_ev)
                        if span > 0:
                            new_ev["time"] = last_end + (seg_ev["time"] - t0)
                        result.append(new_ev)
                    last_end += span
            segment_start = len(result)
        else:
            result.append(ev)
    return result


def _release_all(
    kb: Optional[object],
    pressed_keys: set,
    ms: Optional[object],
    pressed_btns: set,
) -> None:
    if kb:
        for k in list(pressed_keys):
            try:
                kb.release(k)
            except Exception:
                pass
    if ms:
        for b in list(pressed_btns):
            try:
                ms.release(b)
            except Exception:
                pass


class PlayWorker(QObject):
    finished = Signal()

    def __init__(
        self,
        events: list,
        speed: float,
        listener: Optional[object] = None,
        loop_count: int = 0,
        wh_show_elapsed: bool = True,
        wh_show_cycles: bool  = True,
        global_wall_start: Optional[float] = None,
    ) -> None:
        super().__init__()
        self._ev                 = events
        self._speed              = speed
        self._listener           = listener
        self._stop_evt           = threading.Event()
        self._kb: Optional[object] = KbCtrl() if _OK else None
        self._ms: Optional[object] = MsCtrl() if _OK else None
        self._pkeys: set           = set()
        self._pbtns: set           = set()
        self._held_btn: str        = ""
        self._loop_count         = loop_count
        self._wh_show_elapsed    = wh_show_elapsed
        self._wh_show_cycles     = wh_show_cycles
        self._global_wall_start  = global_wall_start

    @staticmethod
    def _check_accessibility() -> None:
        if sys.platform != "darwin":
            return
        try:
            import ctypes
            _lib = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework"
                "/ApplicationServices"
            )
            _lib.AXIsProcessTrusted.restype  = ctypes.c_bool
            _lib.AXIsProcessTrusted.argtypes = []
            if not _lib.AXIsProcessTrusted():
                print(
                    "\n[MacroPlayer] *** ACCESSIBILITY PERMISSION MISSING ***\n"
                    "  Keyboard and mouse-click playback requires Accessibility.\n"
                    "  Open:  System Settings → Privacy & Security → Accessibility\n"
                    "  Add your terminal app (Terminal.app / iTerm2) OR Python.\n"
                    "  Then quit and relaunch the app.\n"
                )
        except Exception:
            pass

    def run(self) -> None:
        self._check_accessibility()
        if not _OK or not self._ev:
            self.finished.emit()
            return

        events = _expand_loops(self._ev)
        if not events:
            self.finished.emit()
            return

        kb = self._kb
        ms = self._ms

        t_offset   = events[0]["time"]
        wall_start = time.perf_counter()

        for ev in events:
            if self._stop_evt.is_set():
                break

            target = (ev["time"] - t_offset) / self._speed
            now    = time.perf_counter() - wall_start
            delay  = target - now
            if delay > 0.001:
                self._stop_evt.wait(timeout=delay)
                if self._stop_evt.is_set():
                    break

            tp = ev["type"]
            try:
                if tp == "mouse_move":
                    tx, ty = int(ev["x"]), int(ev["y"])
                    dur_ms = float(ev.get("move_duration", 0))
                    mode   = ev.get("move_mode", "Linear")
                    held = self._held_btn or None
                    if dur_ms <= 0:
                        send_mouse_move(tx, ty, held)
                    else:
                        sx, sy  = get_mouse_pos()
                        dur_s   = dur_ms / 1000.0 / self._speed
                        steps   = max(2, int(dur_s * 120))
                        dx, dy  = tx - sx, ty - sy
                        dist    = math.hypot(dx, dy)

                        if mode == "Human" and dist > 0:
                            perp_x = -dy / dist
                            perp_y =  dx / dist
                            side   = random.choice([-1, 1])
                            arc    = dist * random.uniform(0.04, 0.12) * side
                            cp1x = sx + dx * 0.3 + perp_x * arc
                            cp1y = sy + dy * 0.3 + perp_y * arc
                            cp2x = sx + dx * 0.7 + perp_x * arc * 0.6
                            cp2y = sy + dy * 0.7 + perp_y * arc * 0.6
                        else:
                            cp1x = cp1y = cp2x = cp2y = 0.0

                        move_start = time.perf_counter()
                        for i in range(1, steps + 1):
                            if self._stop_evt.is_set():
                                break
                            t = i / steps
                            if mode == "Human" and dist > 0:
                                te = t * t * (3.0 - 2.0 * t)
                                mt = 1.0 - te
                                bx = mt**3*sx + 3*mt**2*te*cp1x + 3*mt*te**2*cp2x + te**3*tx
                                by = mt**3*sy + 3*mt**2*te*cp1y + 3*mt*te**2*cp2y + te**3*ty
                            else:
                                bx = sx + t * dx
                                by = sy + t * dy
                            send_mouse_move(int(bx), int(by), held)
                            sleep_d = move_start + dur_s * t - time.perf_counter()
                            if sleep_d > 0.001:
                                self._stop_evt.wait(timeout=sleep_d)

                elif tp == "mouse_click":
                    btn_str = str(ev["button"]).lower()
                    if "right" in btn_str:
                        btn = "right"
                    elif "middle" in btn_str:
                        btn = "middle"
                    else:
                        btn = "left"
                    pressed = bool(ev["pressed"])
                    if self._listener:
                        self._listener.mark_replayed_click()
                    send_mouse_input(int(ev["x"]), int(ev["y"]), btn, pressed)
                    if _OK:
                        _btn_map = {
                            "left":   MsBtn.left,
                            "right":  MsBtn.right,
                            "middle": MsBtn.middle,
                        }
                        btn_obj = _btn_map.get(btn)
                        if btn_obj is not None:
                            if pressed:
                                self._pbtns.add(btn_obj)
                                self._held_btn = btn
                            else:
                                self._pbtns.discard(btn_obj)
                                if self._held_btn == btn:
                                    self._held_btn = ""

                elif tp == "mouse_scroll":
                    ms.position = (int(ev["x"]), int(ev["y"]))
                    ms.scroll(int(ev["dx"]), int(ev["dy"]))

                elif tp == "mouse_drag_right":
                    deltas = ev.get("deltas", [])
                    if deltas:
                        set_timer_resolution_ms(1)
                        try:
                            drag_wall = time.perf_counter()
                            for ddx, ddy, dt in deltas:
                                if self._stop_evt.is_set():
                                    break
                                target_t = dt / self._speed
                                slp = target_t - (time.perf_counter() - drag_wall)
                                if slp > 0.0015:
                                    self._stop_evt.wait(timeout=slp - 0.0005)
                                while (time.perf_counter() - drag_wall) < target_t:
                                    if self._stop_evt.is_set():
                                        break
                                if self._stop_evt.is_set():
                                    break
                                send_mouse_move_relative(int(ddx), int(ddy))
                        finally:
                            reset_timer_resolution_ms(1)

                elif tp == "key_press":
                    k     = ev["key"]
                    canon = ser_key_to_canon(k)
                    if canon and self._listener:
                        self._listener.mark_replayed(canon)
                    obj = parse_key(k)
                    if obj is not None:
                        kb.press(obj)
                        self._pkeys.add(obj)

                elif tp == "key_release":
                    obj = parse_key(ev["key"])
                    if obj is not None:
                        kb.release(obj)
                        self._pkeys.discard(obj)

                elif tp == "wait":
                    dur = float(ev.get("duration", 1.0)) / self._speed
                    self._stop_evt.wait(timeout=dur)
                    wall_start = (
                        time.perf_counter()
                        - (ev["time"] - t_offset) / self._speed
                    )

                elif tp == "webhook":
                    ref = (
                        self._global_wall_start
                        if self._global_wall_start is not None
                        else wall_start
                    )
                    elapsed = time.perf_counter() - ref
                    threading.Thread(
                        target=send_webhook,
                        args=(
                            ev.get("url", ""),
                            ev.get("user_id", ""),
                            ev.get("message", ""),
                            elapsed,
                            self._wh_show_elapsed,
                            self._wh_show_cycles,
                            self._loop_count,
                        ),
                        daemon=True,
                    ).start()

            except Exception as exc:
                print(f"[PlayWorker] ERROR on {tp}: {exc}")

        _release_all(kb, self._pkeys, ms, self._pbtns)
        self.finished.emit()

    def stop(self) -> None:
        self._stop_evt.set()
        _release_all(self._kb, self._pkeys, self._ms, self._pbtns)
