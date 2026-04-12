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

import json
import os
import struct
import sys
from typing import Any

from .constants import (
    APPDATA_SUBDIR,
    AUTOSAVE_FILENAME,
    EvtCode,
    MMR_MAGIC,
    REGISTRY_KEY,
)


def _btn_byte(s: str) -> int:
    return 1 if s == "right" else (2 if s == "middle" else 0)


def _btn_str(b: int) -> str:
    return ["left", "right", "middle"][b]


def _norm_button(b: Any) -> str:
    bs = str(b).lower()
    return "right" if "right" in bs else ("middle" if "middle" in bs else "left")


def _norm_key(k: Any) -> dict:
    if isinstance(k, dict):
        return k
    try:
        from pynput.keyboard import Key as _Key, KeyCode as _KC
        if isinstance(k, _Key):
            return {"special": str(k)}
        if isinstance(k, _KC):
            return {"char": k.char, "vk": k.vk}
    except Exception:
        pass
    s = str(k)
    if s.startswith("Key."):
        return {"special": s}
    if len(s) == 1:
        return {"char": s, "vk": None}
    return {"special": s}


def _mmr_encode_key(k: Any) -> bytes:
    if isinstance(k, dict):
        if k.get("special"):
            s = k["special"].encode("utf-8")[:63]
            return struct.pack("BB", 0, len(s)) + s
        if k.get("char") is not None:
            c = (k["char"] or "").encode("utf-8")[:4]
            return struct.pack("BB", 1, len(c)) + c
        if k.get("vk"):
            return struct.pack("BBI", 2, 4, k["vk"])
    s = str(k).encode("utf-8")[:63]
    return struct.pack("BB", 0, len(s)) + s


def _mmr_decode_key(data: bytes, pos: int) -> tuple[dict, int]:
    kind = data[pos]
    ln   = data[pos + 1]
    pos += 2
    raw  = data[pos:pos + ln]
    pos += ln
    if kind == 0:
        return {"special": raw.decode("utf-8")}, pos
    if kind == 1:
        return {"char": raw.decode("utf-8"), "vk": None}, pos
    vk = struct.unpack_from("<I", raw)[0]
    return {"vk": vk, "char": None}, pos


def ser_key(key: Any) -> dict:
    try:
        from pynput.keyboard import Key, KeyCode
        if isinstance(key, Key):
            return {"special": str(key)}
        if isinstance(key, KeyCode):
            return {"char": key.char, "vk": key.vk}
    except Exception:
        pass
    return {"char": None, "vk": None}


def ser_key_to_canon(k: Any) -> str | None:
    if isinstance(k, dict):
        if k.get("special"):
            return k["special"]
        if k.get("char"):
            return k["char"].lower()
        if k.get("vk"):
            return f"vk:{k['vk']}"
    s = str(k)
    if s.startswith("Key.") or len(s) == 1:
        return s.lower() if len(s) == 1 else s
    return None


def parse_key(k: Any) -> Any:
    try:
        from pynput.keyboard import Key, KeyCode
        if isinstance(k, dict):
            if k.get("special"):
                attr = k["special"].replace("Key.", "")
                return getattr(Key, attr, None)
            if k.get("vk") is not None:
                return KeyCode.from_vk(k["vk"])
            if k.get("char") is not None:
                return KeyCode.from_char(k["char"])
            return None
        s = str(k)
        if s.startswith("Key."):
            attr = s.replace("Key.", "")
            return getattr(Key, attr, None)
        if len(s) == 1:
            return KeyCode.from_char(s)
    except Exception:
        pass
    return None


def str_to_canon(s: str) -> str | None:
    s = s.strip()
    if s.upper().startswith("F") and s[1:].isdigit():
        return f"Key.f{s[1:]}"
    named = {
        "Escape":    "Key.esc",
        "Tab":       "Key.tab",
        "Return":    "Key.enter",
        "Space":     "Key.space",
        "Backspace": "Key.backspace",
        "Delete":    "Key.delete",
        "Home":      "Key.home",
        "End":       "Key.end",
        "Up":        "Key.up",
        "Down":      "Key.down",
        "Left":      "Key.left",
        "Right":     "Key.right",
    }
    if s in named:
        return named[s]
    if len(s) == 1:
        return s.lower()
    return None


def key_to_canon(k: Any) -> str | None:
    try:
        from pynput.keyboard import Key, KeyCode
        if isinstance(k, Key):
            return str(k)
        if isinstance(k, KeyCode):
            if k.char:
                return k.char.lower()
            if k.vk:
                return f"vk:{k.vk}"
    except Exception:
        pass
    return None


def mmr_save(events: list[dict], path: str) -> None:
    buf = bytearray()
    buf += MMR_MAGIC
    buf += struct.pack("<I", len(events))
    for ev in events:
        tp = ev["type"]
        try:
            t = float(ev["time"])
            if tp == "mouse_move":
                dur_ms = int(ev.get("move_duration", 0))
                mode   = ev.get("move_mode", "Linear")
                if dur_ms > 0 or mode != "Linear":
                    mode_b = 1 if mode == "Human" else 0
                    buf += struct.pack("<BdddIB", EvtCode.MOVE_EX, t,
                                       float(ev["x"]), float(ev["y"]),
                                       dur_ms, mode_b)
                elif ev.get("recorded"):
                    buf += struct.pack("<Bddd", EvtCode.MOVE_REC, t,
                                       float(ev["x"]), float(ev["y"]))
                else:
                    buf += struct.pack("<Bddd", EvtCode.MOVE, t,
                                       float(ev["x"]), float(ev["y"]))
            elif tp == "mouse_click":
                buf += struct.pack("<Bddd", EvtCode.CLICK, t,
                                   float(ev["x"]), float(ev["y"]))
                buf += struct.pack("BB",
                                   _btn_byte(_norm_button(ev["button"])),
                                   1 if ev["pressed"] else 0)
            elif tp == "mouse_scroll":
                buf += struct.pack("<Bddddd", EvtCode.SCROLL, t,
                                   float(ev["x"]), float(ev["y"]),
                                   float(ev["dx"]), float(ev["dy"]))
            elif tp in ("key_press", "key_release"):
                code = EvtCode.KPRESS if tp == "key_press" else EvtCode.KREL
                kb   = _mmr_encode_key(_norm_key(ev["key"]))
                buf += struct.pack("<Bd", code, t) + kb
            elif tp == "loop_above":
                count = max(1, int(ev.get("count", 1)))
                buf += struct.pack("<BdI", EvtCode.LOOP_ABOVE, t, count)
            elif tp == "mouse_drag_right":
                deltas = ev.get("deltas", [])
                buf += struct.pack("<BdI", EvtCode.DRAG_RIGHT, t, len(deltas))
                for ddx, ddy, dt in deltas:
                    buf += struct.pack("<iid", int(ddx), int(ddy), float(dt))
            elif tp == "wait":
                dur = float(ev.get("duration", 1.0))
                buf += struct.pack("<Bdd", EvtCode.WAIT, t, dur)
            elif tp == "webhook":
                url_b  = ev.get("url", "").encode("utf-8")[:65535]
                uid_b  = ev.get("user_id", "").encode("utf-8")[:65535]
                msg_b  = ev.get("message", "").encode("utf-8")[:65535]
                buf += struct.pack("<Bd", EvtCode.WEBHOOK, t)
                buf += struct.pack("<H", len(url_b)) + url_b
                buf += struct.pack("<H", len(uid_b)) + uid_b
                buf += struct.pack("<H", len(msg_b)) + msg_b
        except Exception:
            pass
    with open(path, "wb") as f:
        f.write(buf)


def mmr_load(path: str) -> list[dict]:
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(MMR_MAGIC):
        raise ValueError("not an MMR file")
    pos = len(MMR_MAGIC)
    (n,) = struct.unpack_from("<I", data, pos)
    pos += 4
    events: list[dict] = []
    for _ in range(n):
        if pos >= len(data):
            break
        code = data[pos]
        pos += 1
        (t,) = struct.unpack_from("<d", data, pos)
        pos += 8
        if code == EvtCode.MOVE:
            x, y = struct.unpack_from("<dd", data, pos)
            pos += 16
            events.append({"type": "mouse_move", "x": x, "y": y, "time": t})
        elif code == EvtCode.MOVE_REC:
            x, y = struct.unpack_from("<dd", data, pos)
            pos += 16
            events.append({"type": "mouse_move", "x": x, "y": y, "time": t,
                           "recorded": True})
        elif code == EvtCode.MOVE_EX:
            x, y = struct.unpack_from("<dd", data, pos)
            pos += 16
            (dur_ms,) = struct.unpack_from("<I", data, pos)
            pos += 4
            mode_b = data[pos]
            pos += 1
            mode = "Human" if mode_b == 1 else "Linear"
            events.append({"type": "mouse_move", "x": x, "y": y, "time": t,
                           "move_duration": int(dur_ms), "move_mode": mode})
        elif code == EvtCode.CLICK:
            x, y = struct.unpack_from("<dd", data, pos)
            pos += 16
            btn = data[pos]
            pressed = bool(data[pos + 1])
            pos += 2
            events.append({"type": "mouse_click", "x": x, "y": y,
                           "button": _btn_str(btn), "pressed": pressed, "time": t})
        elif code == EvtCode.SCROLL:
            x, y, dx, dy = struct.unpack_from("<dddd", data, pos)
            pos += 32
            events.append({"type": "mouse_scroll", "x": x, "y": y,
                           "dx": dx, "dy": dy, "time": t})
        elif code in (EvtCode.KPRESS, EvtCode.KREL):
            key, pos = _mmr_decode_key(data, pos)
            tp = "key_press" if code == EvtCode.KPRESS else "key_release"
            events.append({"type": tp, "key": key, "time": t})
        elif code == EvtCode.LOOP_ABOVE:
            (count,) = struct.unpack_from("<I", data, pos)
            pos += 4
            events.append({"type": "loop_above", "count": int(count), "time": t})
        elif code == EvtCode.DRAG_RIGHT:
            (n_deltas,) = struct.unpack_from("<I", data, pos)
            pos += 4
            deltas = []
            for _ in range(n_deltas):
                ddx, ddy = struct.unpack_from("<ii", data, pos)
                pos += 8
                (dt,) = struct.unpack_from("<d", data, pos)
                pos += 8
                deltas.append([ddx, ddy, dt])
            events.append({"type": "mouse_drag_right", "time": t, "deltas": deltas})
        elif code == EvtCode.WAIT:
            (dur,) = struct.unpack_from("<d", data, pos)
            pos += 8
            events.append({"type": "wait", "duration": dur, "time": t})
        elif code == EvtCode.WEBHOOK:
            (url_len,) = struct.unpack_from("<H", data, pos); pos += 2
            url = data[pos:pos + url_len].decode("utf-8"); pos += url_len
            (uid_len,) = struct.unpack_from("<H", data, pos); pos += 2
            uid = data[pos:pos + uid_len].decode("utf-8"); pos += uid_len
            (msg_len,) = struct.unpack_from("<H", data, pos); pos += 2
            msg = data[pos:pos + msg_len].decode("utf-8"); pos += msg_len
            events.append({"type": "webhook", "url": url, "user_id": uid,
                           "message": msg, "time": t})
    return events


def _app_data_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(
            os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(base, APPDATA_SUBDIR)
    os.makedirs(d, exist_ok=True)
    return d


def _settings_path() -> str:
    return os.path.join(_app_data_dir(), "settings.json")


def reg_save(d: dict) -> None:
    if sys.platform == "win32":
        try:
            import winreg
            k = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE)
            for n, v in d.items():
                winreg.SetValueEx(k, n, 0, winreg.REG_SZ, str(v))
            winreg.CloseKey(k)
        except Exception:
            pass
    else:
        try:
            with open(_settings_path(), "w", encoding="utf-8") as f:
                json.dump({n: str(v) for n, v in d.items()}, f, indent=2)
        except Exception:
            pass


def reg_load() -> dict:
    if sys.platform == "win32":
        try:
            import winreg
            k = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_READ)
            out: dict = {}
            i = 0
            while True:
                try:
                    n, v, _ = winreg.EnumValue(k, i)
                    out[n] = v
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(k)
            return out
        except Exception:
            return {}
    else:
        try:
            with open(_settings_path(), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def autosave_path() -> str:
    return os.path.join(_app_data_dir(), AUTOSAVE_FILENAME)


def autosave(events: list[dict]) -> None:
    try:
        mmr_save(events, autosave_path())
    except Exception:
        pass


def autoload() -> list[dict]:
    try:
        p = autosave_path()
        if os.path.exists(p):
            with open(p, "rb") as f:
                if f.read(4) == MMR_MAGIC:
                    return mmr_load(p)
    except Exception:
        pass
    return []


def ensure_mmr_icon(ico_b64: str) -> None:
    if sys.platform != "win32":
        return
    try:
        import base64
        import winreg
        import ctypes as _ctypes

        ico_dir = _app_data_dir()
        ico_path = os.path.join(ico_dir, "filetype_mmr.ico")
        ico_data = base64.b64decode(ico_b64)
        with open(ico_path, "wb") as f:
            f.write(ico_data)

        def _set(hive: Any, path: str, name: str, val: str) -> None:
            k = winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, val)
            winreg.CloseKey(k)

        _set(winreg.HKEY_CURRENT_USER, r"Software\Classes\.mmr",
             "", "MorisMacroFile")
        _set(winreg.HKEY_CURRENT_USER, r"Software\Classes\MorisMacroFile",
             "", "Moris Macro Recording")
        _set(winreg.HKEY_CURRENT_USER,
             r"Software\Classes\MorisMacroFile\DefaultIcon",
             "", f"{ico_path},0")

        _ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception:
        pass


def send_webhook(
    url: str,
    user_id: str,
    message: str,
    elapsed: float = 0.0,
    show_elapsed: bool = True,
    show_cycles: bool = True,
    cycle_count: int = 0,
) -> None:
    try:
        import urllib.request
        import urllib.error
        import datetime

        url = url.strip().rstrip("/")
        if not url or "discord.com/api/webhooks/" not in url:
            return

        fields: list[dict] = []
        if show_elapsed:
            h = int(elapsed) // 3600
            m = (int(elapsed) % 3600) // 60
            s = int(elapsed) % 60
            fields.append({
                "name":   "Time Elapsed",
                "value":  f"{h:02d}:{m:02d}:{s:02d}",
                "inline": True,
            })
        if show_cycles:
            fields.append({
                "name":   "Cycles",
                "value":  str(cycle_count),
                "inline": True,
            })

        embed: dict = {
            "title":       "moris macro maker - m\u00b3",
            "description": message or "\u200b",
            "color":       0x4DB8FF,
            "footer":      {"text": "v1.2.2"},
            "timestamp":   datetime.datetime.utcnow().strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
        }
        if fields:
            embed["fields"] = fields

        mention = f"<@{user_id}>" if user_id else None
        payload: dict = {
            "username": "moris macro maker - m\u00b3",
            "embeds":   [embed],
        }
        if mention:
            payload["content"] = mention

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent":   "DiscordBot (moris-macro-maker, 1.0)",
            },
            method="POST",
        )
        import ssl
        ctx = ssl.create_default_context()
        if sys.platform == "darwin" and os.path.exists("/etc/ssl/cert.pem"):
            ctx.load_verify_locations("/etc/ssl/cert.pem")
        try:
            urllib.request.urlopen(req, timeout=8, context=ctx)
        except urllib.error.HTTPError:
            pass
    except Exception:
        pass
