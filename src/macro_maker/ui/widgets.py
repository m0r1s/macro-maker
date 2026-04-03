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
from typing import Optional

from PySide6.QtCore import (
    Property,
    QElapsedTimer,
    QEvent,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QRegularExpression,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QIntValidator,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
    QPolygon,
    QRegularExpressionValidator,
    QTextOption,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QStyle,
    QStyleOptionButton,
    QVBoxLayout,
    QWidget,
)

from ..utils.constants import (
    FONT,
    KNOB_D,
    KNOB_OFF,
    KNOB_TRAV,
    KNOB_Y,
    SW_H,
    SW_W,
    TRACK_H,
    TRACK_OFF,
    TRACK_ON,
    TRACK_Y,
)
from ..utils.serialization import _norm_key

try:
    from pynput import keyboard as _kb
    _OK = True
except ImportError:
    _OK = False

_QT_KEY_SPECIAL: dict = {
    Qt.Key_Escape:    ("Key.esc",       "Esc"),
    Qt.Key_Tab:       ("Key.tab",       "Tab"),
    Qt.Key_Return:    ("Key.enter",     "Enter"),
    Qt.Key_Enter:     ("Key.enter",     "Enter"),
    Qt.Key_Backspace: ("Key.backspace", "Backspace"),
    Qt.Key_Delete:    ("Key.delete",    "Delete"),
    Qt.Key_Home:      ("Key.home",      "Home"),
    Qt.Key_End:       ("Key.end",       "End"),
    Qt.Key_Left:      ("Key.left",      "Left"),
    Qt.Key_Right:     ("Key.right",     "Right"),
    Qt.Key_Up:        ("Key.up",        "Up"),
    Qt.Key_Down:      ("Key.down",      "Down"),
    Qt.Key_Insert:    ("Key.insert",    "Insert"),
    Qt.Key_PageUp:    ("Key.page_up",   "PgUp"),
    Qt.Key_PageDown:  ("Key.page_down", "PgDn"),
    Qt.Key_Space:     ("Key.space",     "Space"),
    Qt.Key_Shift:     ("Key.shift",     "Shift"),
    Qt.Key_Control:   ("Key.ctrl",      "Ctrl"),
    Qt.Key_Alt:       ("Key.alt",       "Alt"),
    Qt.Key_Meta:      ("Key.cmd",       "Win"),
    Qt.Key_Super_L:   ("Key.cmd",       "Win"),
    Qt.Key_Super_R:   ("Key.cmd_r",     "Win R"),
    Qt.Key_Menu:      ("Key.menu",      "Menu"),
}
for _fi in range(1, 24):
    _k = getattr(Qt, f"Key_F{_fi}", None)
    if _k:
        _QT_KEY_SPECIAL[_k] = (f"Key.f{_fi}", f"F{_fi}")

_SPECIAL_DISPLAY: dict = {canon: lbl for canon, lbl in _QT_KEY_SPECIAL.values()}


def _svg_icon(svg_bytes: bytes, size: int = 16, color: str = "#52596b") -> QIcon:
    colored = svg_bytes.replace(b"currentColor", color.encode())
    pix = QPixmap()
    pix.loadFromData(colored, "SVG")
    return QIcon(pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))


def _ev_label(ev: dict) -> str:
    tp = ev.get("type", "")
    if tp == "mouse_move":
        dur = ev.get("move_duration", 0)
        mode = ev.get("move_mode", "Linear")
        if dur:
            return f"Move  ({int(ev['x'])}, {int(ev['y'])})  {mode}  {dur}ms"
        return f"Move  ({int(ev['x'])}, {int(ev['y'])})"
    if tp == "mouse_click":
        act = "Press" if ev.get("pressed") else "Release"
        return f"Click {ev.get('button','left').title()} {act}  ({int(ev['x'])}, {int(ev['y'])})"
    if tp == "mouse_scroll":
        return f"Scroll  ({int(ev['x'])}, {int(ev['y'])})  dx={ev['dx']:.1f} dy={ev['dy']:.1f}"
    if tp == "key_press":
        k  = ev.get("key", {})
        ch = _SPECIAL_DISPLAY.get(k.get("special", "")) or k.get("char") or "?"
        return f"Key Press  {ch}"
    if tp == "key_release":
        k  = ev.get("key", {})
        ch = _SPECIAL_DISPLAY.get(k.get("special", "")) or k.get("char") or "?"
        return f"Key Release  {ch}"
    if tp == "wait":
        ms = ev.get("duration", 1.0) * 1000
        return f"Wait  {ms:.0f} ms"
    if tp == "webhook":
        msg   = ev.get("message", "")
        short = msg[:24] + "\u2026" if len(msg) > 24 else msg
        return f"Webhook  {short}" if short else "Webhook"
    if tp == "loop_above":
        count = ev.get("count", 1)
        return f"Loop Above  {count}\u00d7"
    if tp == "mouse_drag_right":
        n = len(ev.get("deltas", []))
        return f"Right Drag  {n} steps"
    return tp


class StyledSpinBox(QDoubleSpinBox):
    def paintEvent(self, e: object) -> None:
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        btn_w = 18
        cx = self.width() - btn_w // 2
        h  = self.height()
        pen = QPen(QColor("#7a8299"), 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        uc = h // 4
        p.drawLine(cx - 3, uc + 2, cx, uc - 1)
        p.drawLine(cx, uc - 1, cx + 3, uc + 2)
        dc = h * 3 // 4
        p.drawLine(cx - 3, dc - 2, cx, dc + 1)
        p.drawLine(cx, dc + 1, cx + 3, dc - 2)
        p.end()


class EditButton(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("btnEdit")
        self._arrow_angle:  float = 0.0
        self._arrow_target: float = 0.0
        self._arrow_start:  float = 0.0
        self._animating:    bool  = False
        self._elapsed: Optional[QElapsedTimer] = None
        self._duration: float = 200.0
        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_expanded(self, v: bool) -> None:
        self._arrow_start  = self._arrow_angle
        self._arrow_target = 90.0 if v else 0.0
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._animating = True
        self.update()

    def paintEvent(self, _e: object) -> None:
        if self._animating and self._elapsed is not None:
            ms = self._elapsed.elapsed()
            t  = min(1.0, ms / self._duration)
            if t < 0.5:
                ease = 16.0 * t ** 5
            else:
                ease = 1.0 - (-2.0 * t + 2.0) ** 5 / 2.0
            self._arrow_angle = (
                self._arrow_start
                + (self._arrow_target - self._arrow_start) * ease
            )
            if t >= 1.0:
                self._arrow_angle = self._arrow_target
                self._animating   = False

        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        enabled = self.isEnabled()
        hover   = bool(opt.state & QStyle.State_MouseOver)
        pressed = self.isDown()

        if not enabled:
            bg     = QColor(255, 255, 255, int(0.02 * 255))
            border = QColor(255, 255, 255, int(0.05 * 255))
            fg     = QColor(0x2A, 0x2D, 0x3A)
        elif pressed:
            bg     = QColor(255, 255, 255, int(0.09 * 255))
            border = QColor(255, 255, 255, int(0.13 * 255))
            fg     = QColor(0xC8, 0xCF, 0xDF)
        elif hover:
            bg     = QColor(255, 255, 255, int(0.06 * 255))
            border = QColor(255, 255, 255, int(0.10 * 255))
            fg     = QColor(0xC8, 0xCF, 0xDF)
        else:
            bg     = QColor(255, 255, 255, int(0.03 * 255))
            border = QColor(255, 255, 255, int(0.06 * 255))
            fg     = QColor(0x9A, 0xA3, 0xB8)

        r = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(r, 7, 7)

        label   = "Edit Events"
        font    = self.font()
        font.setPixelSize(11)
        font.setBold(True)
        p.setFont(font)
        fm      = p.fontMetrics()
        tw      = fm.horizontalAdvance(label)
        arrow_w = 6
        gap     = 5
        ox      = 10
        cy      = self.height() // 2

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(fg))

        rad   = math.radians(self._arrow_angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        cx_a  = ox + arrow_w / 2.0
        base_pts = [(-arrow_w / 2, -3), (-arrow_w / 2, 3), (arrow_w / 2, 0)]
        pts_f: list = []
        for bx, by in base_pts:
            rx = bx * cos_a - by * sin_a
            ry = bx * sin_a + by * cos_a
            pts_f.append((cx_a + rx, cy + ry))

        path = QPainterPath()
        path.moveTo(pts_f[0][0], pts_f[0][1])
        path.lineTo(pts_f[1][0], pts_f[1][1])
        path.lineTo(pts_f[2][0], pts_f[2][1])
        path.closeSubpath()
        p.drawPath(path)

        p.setPen(fg)
        p.drawText(
            QRect(ox + arrow_w + gap, 0, tw + 2, self.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            label,
        )
        p.end()

        if self._animating:
            self.update()


class InlineEditButton(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Edit", parent)
        self.setObjectName("btnInlineEdit")
        self.setFixedHeight(16)
        self.setFixedWidth(32)


class PlayButton(QPushButton):
    def __init__(self, key_text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("btnPlay")
        self._key_text = key_text
        self._playing  = False
        self.setFixedHeight(32)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_key(self, key_text: str) -> None:
        self._key_text = key_text
        self.update()

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(130, 32)

    def minimumSizeHint(self) -> QSize:
        return QSize(80, 32)

    def paintEvent(self, _e: object) -> None:
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        enabled = self.isEnabled()
        a       = 1.0 if enabled else 0.28

        if self._playing:
            cr, cg, cb_v = 255, 170, 50
        else:
            cr, cg, cb_v = 50, 230, 140

        if self.isDown():
            bg     = QColor(cr, cg, cb_v, int(0.29 * 255 * a))
            border = QColor(cr, cg, cb_v, int(0.80 * 255 * a))
        elif opt.state & QStyle.State_MouseOver:
            bg     = QColor(cr, cg, cb_v, int(0.19 * 255 * a))
            border = QColor(cr, cg, cb_v, int(0.55 * 255 * a))
        else:
            bg     = QColor(cr, cg, cb_v, int(0.09 * 255 * a))
            border = QColor(cr, cg, cb_v, int(0.30 * 255 * a))

        r2 = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(r2, 7, 7)

        icon_col = QColor(cr, cg, cb_v, int(255 * a))
        label = (
            f"Stop  [{self._key_text}]"
            if self._playing
            else f"Play  [{self._key_text}]"
        )
        font = self.font()
        font.setPixelSize(11)
        font.setBold(True)
        p.setFont(font)
        fm    = p.fontMetrics()
        tw    = fm.horizontalAdvance(label)
        tri_w = 9
        gap   = 6
        total = tri_w + gap + tw
        ox    = (self.width() - total) // 2
        cy    = self.height() // 2
        ts    = 5

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(icon_col))
        if self._playing:
            sq = 9
            p.drawRect(ox, cy - sq // 2, sq, sq)
        else:
            tri = QPolygon([
                QPoint(ox,         cy - ts),
                QPoint(ox,         cy + ts),
                QPoint(ox + tri_w, cy),
            ])
            p.drawPolygon(tri)

        p.setPen(icon_col)
        p.drawText(
            QRect(ox + tri_w + gap, 0, tw + 2, self.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            label,
        )
        p.end()


class RecButton(QPushButton):
    _COL_NORMAL = (255, 75, 105)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("btnRecord")
        self._paused = False

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self.update()

    def paintEvent(self, _e: object) -> None:
        from PySide6.QtWidgets import QStyleOptionButton, QStyle
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        enabled = self.isEnabled()
        a       = 1.0 if enabled else 0.28
        cr, cg, cb_v = self._COL_NORMAL

        if self.isDown():
            bg     = QColor(cr, cg, cb_v, int(0.29 * 255 * a))
            border = QColor(cr, cg, cb_v, int(0.80 * 255 * a))
        elif opt.state & QStyle.State_MouseOver:
            bg     = QColor(cr, cg, cb_v, int(0.19 * 255 * a))
            border = QColor(cr, cg, cb_v, int(0.52 * 255 * a))
        else:
            bg     = QColor(cr, cg, cb_v, int(0.09 * 255 * a))
            border = QColor(cr, cg, cb_v, int(0.30 * 255 * a))

        r2 = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(r2, 10, 10)

        icon_col = QColor(cr, cg, cb_v, int(255 * a))
        label    = self.text()

        font = self.font()
        font.setPixelSize(11)
        font.setBold(True)
        p.setFont(font)
        fm  = p.fontMetrics()
        tw  = fm.horizontalAdvance(label)
        cy  = self.height() // 2

        if self._paused:
            bar_w, bar_h, gap = 3, 9, 3
            icon_w = bar_w + gap + bar_w
            total  = icon_w + 6 + tw
            ox     = (self.width() - total) // 2

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(icon_col))
            p.drawRoundedRect(ox,              cy - bar_h // 2, bar_w, bar_h, 1, 1)
            p.drawRoundedRect(ox + bar_w + gap, cy - bar_h // 2, bar_w, bar_h, 1, 1)

            p.setPen(icon_col)
            p.drawText(
                QRect(ox + icon_w + 6, 0, tw + 2, self.height()),
                Qt.AlignVCenter | Qt.AlignLeft,
                label,
            )
        else:
            total = tw
            ox    = (self.width() - total) // 2
            p.setPen(icon_col)
            p.drawText(
                QRect(ox, 0, tw + 2, self.height()),
                Qt.AlignVCenter | Qt.AlignLeft,
                label,
            )
        p.end()


class KeyCapture(QLineEdit):
    key_changed = Signal(str)

    _MOUSE_NAMES = {
        Qt.MiddleButton: "Middle",
        Qt.XButton1:     "XButton1",
        Qt.XButton2:     "XButton2",
    }

    def __init__(self, key: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("keyInput")
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(42, 26)
        self._key = key
        self.setText(key)

    def key(self) -> str:
        return self._key

    def _commit_capture(self, name: str) -> None:
        self._key = name
        self.setText(name)
        self.key_changed.emit(name)
        self.releaseMouse()
        self.clearFocus()

    def _cancel_capture(self) -> None:
        self.setText(self._key)
        self.releaseMouse()
        self.clearFocus()

    def mousePressEvent(self, e: object) -> None:
        btn = e.button()
        if self.text() == "\u2026":
            name = self._MOUSE_NAMES.get(btn)
            if name:
                self._commit_capture(name)
            elif btn not in (Qt.LeftButton, Qt.RightButton):
                pass
            else:
                self._cancel_capture()
        else:
            self.setFocus()
            self.setText("\u2026")
            self.grabMouse()

    def keyPressEvent(self, e: object) -> None:
        k = e.key()
        if k in (Qt.Key_Return, Qt.Key_Escape):
            self._cancel_capture()
            return
        seq = QKeySequence(k).toString()
        if seq:
            self._commit_capture(seq)
        else:
            self._cancel_capture()

    def focusOutEvent(self, e: object) -> None:
        if self.text() == "\u2026":
            self.releaseMouse()
            self.setText(self._key)
        super().focusOutEvent(e)


class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(
        self, checked: bool = False, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._on        = checked
        self._anim_pos  = 1.0 if checked else 0.0
        self.setFixedSize(SW_W, SW_H)
        self.setCursor(Qt.PointingHandCursor)
        self._timer = QTimer(self)
        self._timer.setInterval(12)
        self._timer.timeout.connect(self._step)

    def _step(self) -> None:
        target = 1.0 if self._on else 0.0
        diff   = target - self._anim_pos
        if abs(diff) < 0.03:
            self._anim_pos = target
            self._timer.stop()
        else:
            self._anim_pos += diff * 0.22
        self.update()

    def isChecked(self) -> bool:
        return self._on

    def setChecked(self, v: bool, animate: bool = True) -> None:
        if v == self._on:
            return
        self._on = v
        if animate:
            self._timer.start()
        else:
            self._anim_pos = 1.0 if v else 0.0
            self.update()
        self.toggled.emit(v)

    def mousePressEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton:
            self.setChecked(not self._on)

    def paintEvent(self, _: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        a = self._anim_pos

        c_off, c_on = TRACK_OFF, TRACK_ON
        rv = int(c_off[0] + (c_on[0] - c_off[0]) * a)
        gv = int(c_off[1] + (c_on[1] - c_off[1]) * a)
        bv = int(c_off[2] + (c_on[2] - c_off[2]) * a)

        knob_off_cx = KNOB_OFF + KNOB_D / 2
        knob_on_cx  = KNOB_OFF + KNOB_TRAV + KNOB_D / 2
        track_x     = knob_off_cx - TRACK_H / 2
        track_w     = (knob_on_cx + TRACK_H / 2) - track_x
        track_rect  = QRectF(track_x, TRACK_Y, track_w, TRACK_H)
        radius      = TRACK_H / 2

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(rv, gv, bv)))
        p.drawRoundedRect(track_rect, radius, radius)

        knob_x    = KNOB_OFF + self._anim_pos * KNOB_TRAV
        knob_rect = QRectF(knob_x, KNOB_Y, KNOB_D, KNOB_D)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(knob_rect)

        p.setPen(QPen(QColor(0, 0, 0, 130), 1.8))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(knob_rect.adjusted(0.9, 0.9, -0.9, -0.9))
        p.end()


class MinimizeBtn(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("btnMin")
        self.setFixedSize(22, 22)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False

    def enterEvent(self, e: object) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e: object) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, _: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self._hovered:
            p.setBrush(QBrush(QColor(255, 255, 255, 18)))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(0, 0, 22, 22, 5, 5)
        cx, cy = 11, 11
        color = QColor("#eef0f5") if self._hovered else QColor("#52596b")
        pen   = QPen(color, 1.8, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(cx - 5, cy + 2), QPointF(cx + 5, cy + 2))
        p.end()


class RowExpandButton(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("btnRowExpand")
        self._expanded = False

    def set_expanded(self, v: bool) -> None:
        self._expanded = v
        self.update()

    def paintEvent(self, _e: object) -> None:
        p   = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        hover = bool(opt.state & QStyle.State_MouseOver)
        fg    = QColor(0xC8, 0xCF, 0xDF) if hover else QColor(0x52, 0x59, 0x6B)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(fg))
        cx = self.width()  // 2
        cy = self.height() // 2
        if self._expanded:
            pts = QPolygon([
                QPoint(cx - 3, cy - 1),
                QPoint(cx + 3, cy - 1),
                QPoint(cx,     cy + 3),
            ])
        else:
            pts = QPolygon([
                QPoint(cx - 2, cy - 3),
                QPoint(cx - 2, cy + 3),
                QPoint(cx + 3, cy),
            ])
        p.drawPolygon(pts)
        p.end()


class _KeyGrabber(QWidget):
    def __init__(
        self,
        on_captured: callable,
        on_cancel: callable,
    ) -> None:
        super().__init__(
            None,
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._on_captured = on_captured
        self._on_cancel   = on_cancel
        self._done        = False
        self.setFixedSize(1, 1)
        self.move(-100, -100)

    def keyPressEvent(self, e: object) -> None:
        if self._done:
            return
        k  = e.key()
        sp = _QT_KEY_SPECIAL.get(k)
        if sp:
            k_dict  = {"special": sp[0]}
            display = sp[1]
        else:
            text = e.text()
            if text and text.isprintable() and len(text) == 1:
                k_dict  = {"char": text, "vk": None}
                display = text
            else:
                seq = QKeySequence(k).toString()
                if not seq:
                    return
                k_dict  = {"special": seq.lower(), "vk": None}
                display = seq
        self._done = True
        self.close()
        self._on_captured(k_dict, display)

    def focusOutEvent(self, e: object) -> None:
        super().focusOutEvent(e)
        if not self._done:
            self._done = True
            QTimer.singleShot(0, self._on_cancel)


class _PosHUD(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        lo = QHBoxLayout(self)
        lo.setContentsMargins(8, 4, 8, 4)
        self._lbl = QLabel("X: 0   Y: 0")
        self._lbl.setStyleSheet(
            f"color:#eef0f5; font-family:{FONT}; font-size:11px; font-weight:700;")
        lo.addWidget(self._lbl)
        self.setStyleSheet(
            "QWidget { background: rgba(18,22,34,210); border-radius: 5px; }")
        self.adjustSize()

    def update_pos(self, x: int, y: int) -> None:
        self._lbl.setText(f"X: {x}   Y: {y}")
        self.adjustSize()
        screen = QGuiApplication.screenAt(QPoint(x, y))
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        sg = screen.geometry()
        nx = x + 18
        ny = y - self.height() - 8
        nx = min(nx, sg.right() - self.width())
        ny = max(ny, sg.top())
        self.move(nx, ny)


class _PosGrabOverlay(QWidget):
    captured  = Signal(int, int)
    cancelled = Signal()

    def __init__(self) -> None:
        import sys
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.setMouseTracking(True)
        if sys.platform == "darwin":
            self.setAttribute(Qt.WA_TranslucentBackground)
        else:
            self.setWindowOpacity(0.01)

        vg = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(vg)

        self._hud = _PosHUD()
        self._hud.show()

    def showEvent(self, e: object) -> None:
        import sys
        super().showEvent(e)
        if sys.platform == "darwin":
            QTimer.singleShot(0, self.grabMouse)
            self.setFocus()

    def mouseMoveEvent(self, e: object) -> None:
        p = e.globalPosition().toPoint()
        self._hud.update_pos(p.x(), p.y())

    def mousePressEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton:
            p = e.globalPosition().toPoint()
            self._finish()
            self.captured.emit(p.x(), p.y())
        elif e.button() == Qt.RightButton:
            self._finish()
            self.cancelled.emit()

    def keyPressEvent(self, e: object) -> None:
        if e.key() == Qt.Key_Escape:
            self._finish()
            self.cancelled.emit()

    def _finish(self) -> None:
        import sys
        if sys.platform == "darwin":
            self.releaseMouse()
        self._hud.close()
        self.close()


class _GripHandle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 18)
        self._active = False
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def set_active(self, on: bool) -> None:
        self._active = on
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = QColor("#78c8ff") if self._active else QColor("#4a5068")
        p.setBrush(color)
        p.setPen(Qt.NoPen)
        r = 1.0
        cols = [6.0, 10.0]
        rows = [5.5, 9.0, 12.5]
        for x in cols:
            for y in rows:
                p.drawEllipse(QPointF(x, y), r, r)
        p.end()


class EventRow(QWidget):
    deleted    = Signal(int)
    changed    = Signal(int, dict)
    drag_start = Signal(int, object)
    row_clicked = Signal(int, int)

    def __init__(
        self, idx: int, ev: dict, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._idx       = idx
        self._ev        = dict(ev)
        self._expanded  = False
        self._selected  = False
        self._capturing = False
        self._kb_listener  = None
        self._key_grabber  = None
        self.setObjectName("seqRow")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(8, 4, 8, 4)
        self._outer.setSpacing(0)

        hdr = QHBoxLayout()
        hdr.setSpacing(4)
        hdr.setContentsMargins(0, 0, 0, 0)

        self._idx_lbl = QLabel(f"{idx+1:>3}.")
        self._idx_lbl.setFixedWidth(28)
        self._idx_lbl.setStyleSheet("color:#52596b; font-size:10px;")
        hdr.addWidget(self._idx_lbl)

        self._summary = QLabel(_ev_label(ev))
        self._summary.setStyleSheet("color:#eef0f5; font-size:11px;")
        self._summary.setMinimumWidth(0)
        self._summary.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        hdr.addWidget(self._summary, 1)

        self._t_lbl = QLabel(f"{ev.get('time', 0):.3f}s")
        self._t_lbl.setStyleSheet("color:#52596b; font-size:10px;")
        self._t_lbl.setFixedWidth(62)
        self._t_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if ev.get("type") in ("webhook", "loop_above", "wait"):
            self._t_lbl.setVisible(False)
        hdr.addWidget(self._t_lbl)

        self._drag_handle = _GripHandle()
        self._drag_handle.setCursor(Qt.OpenHandCursor)
        self._drag_handle.installEventFilter(self)
        hdr.addWidget(self._drag_handle)

        self._exp_btn = RowExpandButton()
        self._exp_btn.setFixedSize(18, 18)
        self._exp_btn.clicked.connect(self._toggle_expand)
        hdr.addWidget(self._exp_btn)

        del_btn = QLabel("\u2715")
        del_btn.setObjectName("btnRowDel")
        del_btn.setFixedSize(14, 18)
        del_btn.setAlignment(Qt.AlignCenter)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setAttribute(Qt.WA_Hover, True)
        del_btn.mousePressEvent = lambda e: self.deleted.emit(self._idx)
        hdr.addWidget(del_btn)

        self._outer.addLayout(hdr)

        self._detail = QWidget()
        self._detail.setVisible(False)
        dl = QVBoxLayout(self._detail)
        dl.setContentsMargins(24, 2, 6, 2)
        dl.setSpacing(2)

        self._fields_w = QWidget()
        self._fields_l = QVBoxLayout(self._fields_w)
        self._fields_l.setContentsMargins(0, 0, 0, 0)
        self._fields_l.setSpacing(1)
        dl.addWidget(self._fields_w)

        self._outer.addWidget(self._detail)
        self._build_fields()

    def _field_row(self, label: str, widget: QWidget) -> QHBoxLayout:
        r = QHBoxLayout()
        r.setSpacing(6)
        r.setContentsMargins(0, 0, 0, 0)
        r.setAlignment(Qt.AlignVCenter)
        lbl = QLabel(label)
        lbl.setFixedWidth(52)
        lbl.setFixedHeight(16)
        lbl.setStyleSheet("color:#7a8299; font-size:10px;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        r.addWidget(lbl, 0, Qt.AlignVCenter)
        r.addWidget(widget, 0, Qt.AlignVCenter)
        r.addStretch()
        return r

    def _make_edit(self, val: object, numbers_only: bool = False) -> QLineEdit:
        e = QLineEdit(str(val))
        e.setObjectName("seqEdit")
        e.setFixedWidth(90)
        e.setFixedHeight(16)
        if numbers_only:
            e.setValidator(QIntValidator(-999999, 999999))
        return e

    def _inline_row(self, label_text: str) -> QHBoxLayout:
        r = QHBoxLayout()
        r.setSpacing(6)
        r.setContentsMargins(0, 0, 0, 0)
        r.setAlignment(Qt.AlignVCenter)
        lbl = QLabel(label_text)
        lbl.setFixedWidth(52)
        lbl.setFixedHeight(16)
        lbl.setStyleSheet("color:#7a8299; font-size:10px;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        r.addWidget(lbl, 0, Qt.AlignVCenter)
        return r

    def _inline_edit_row(
        self, key: str, label_text: str, val: object, numbers_only: bool = False
    ) -> QHBoxLayout:
        return self._build_single_row(
            self._make_inline_widgets(key, label_text, val, numbers_only)
        )

    def _inline_label_row(
        self, label_text: str, val: str, options: list, key: str
    ) -> QHBoxLayout:
        r    = self._inline_row(label_text)
        disp = QLabel(val)
        disp.setStyleSheet(
            "color:#78c8ff; font-size:11px; font-weight:700; min-width:20px;")
        btn_edit = InlineEditButton()
        btn_edit.setFixedHeight(16)
        btn_edit.setFixedWidth(32)

        def cycle() -> None:
            cur  = disp.text()
            opts = list(options)
            nxt  = (
                opts[(opts.index(cur) + 1) % len(opts)]
                if cur in opts
                else opts[0]
            )
            disp.setText(nxt)
            if key == "action_pressed":
                self._ev["pressed"] = (nxt == "Press")
            else:
                self._ev[key] = nxt
            self._summary.setText(_ev_label(self._ev))
            self.changed.emit(self._idx, dict(self._ev))

        btn_edit.clicked.connect(cycle)
        r.addWidget(disp, 0, Qt.AlignVCenter)
        r.addWidget(btn_edit, 0, Qt.AlignVCenter)
        r.addStretch()
        return r

    def _make_inline_widgets(
        self, key: str, label_text: str, val: object,
        numbers_only: bool = False, on_commit=None
    ) -> tuple:
        H = 16
        lbl = QLabel(label_text)
        lbl.setFixedWidth(52)
        lbl.setFixedHeight(H)
        lbl.setStyleSheet("color:#7a8299; font-size:10px;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        val_stack = QStackedWidget()
        val_stack.setFixedSize(35, H)
        val_stack.setContentsMargins(0, 0, 0, 0)

        disp = QLabel(str(val))
        disp.setFixedSize(35, H)
        disp.setContentsMargins(0, 0, 0, 0)
        disp.setStyleSheet(
            "color:#78c8ff; font-size:10px; font-weight:700;"
            " background: transparent; padding: 0; margin: 0;")
        disp.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        val_stack.addWidget(disp)

        edit = QLineEdit(str(val))
        edit.setFixedSize(35, H)
        edit.setContentsMargins(0, 0, 0, 0)
        edit.setStyleSheet(
            "QLineEdit { background: transparent; border: none; outline: none;"
            " color: #78c8ff; font-size: 10px; font-weight: 700; padding: 0; margin: 0; }")
        edit.setTextMargins(-2, 0, 0, 0)
        edit.setFrame(False)
        if numbers_only:
            edit.setValidator(QIntValidator(-999999, 999999))
        val_stack.addWidget(edit)

        btn_stack = QStackedWidget()
        btn_stack.setFixedSize(36, H)
        btn_stack.setContentsMargins(0, 0, 0, 0)

        btn_edit = InlineEditButton()
        btn_edit.setFixedSize(36, H)
        btn_stack.addWidget(btn_edit)

        btn_done = QLabel("Close")
        btn_done.setObjectName("btnSeqClose")
        btn_done.setFixedSize(36, H)
        btn_done.setAlignment(Qt.AlignCenter)
        btn_done.setCursor(Qt.PointingHandCursor)
        btn_done.setAttribute(Qt.WA_Hover, True)
        btn_stack.addWidget(btn_done)

        def start() -> None:
            edit.setText(disp.text())
            val_stack.setCurrentIndex(1)
            btn_stack.setCurrentIndex(1)
            edit.setFocus()

        def commit() -> None:
            edit.deselect()
            v = edit.text()
            try:
                if on_commit is not None:
                    display = on_commit(v)
                    disp.setText(display)
                else:
                    stored = int(v) if numbers_only else v
                    self._ev[key] = stored
                    disp.setText(str(stored))
                    self._summary.setText(_ev_label(self._ev))
                    self.changed.emit(self._idx, dict(self._ev))
            except Exception:
                pass
            val_stack.setCurrentIndex(0)
            btn_stack.setCurrentIndex(0)
            self.setFocus()

        btn_edit.clicked.connect(start)
        btn_done.mousePressEvent = lambda e: commit()
        edit.returnPressed.connect(commit)
        edit.focusOutEvent = lambda e: (QLineEdit.focusOutEvent(edit, e), commit())

        return lbl, val_stack, btn_stack

    def _build_combined_row(self, left: tuple, right: tuple) -> QHBoxLayout:
        l_lbl, l_val, l_btn = left
        r_lbl, r_val, r_btn = right
        fm = l_lbl.fontMetrics()
        bw = fm.horizontalAdvance("Edit") + 6

        label_w = fm.horizontalAdvance("Dur") + 2
        std_val_w = fm.horizontalAdvance("0.000s") + 4

        l_lbl.setFixedWidth(label_w)
        r_lbl.setFixedWidth(label_w)

        for stack, fallback_w in ((l_val, std_val_w), (r_val, std_val_w)):
            w = max(stack.minimumWidth(), fallback_w)
            stack.setFixedWidth(w)
            for i in range(stack.count()):
                stack.widget(i).setFixedWidth(w)

        for stack in (l_btn, r_btn):
            stack.setFixedWidth(bw)
            for i in range(stack.count()):
                stack.widget(i).setFixedWidth(bw)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(l_lbl, 0, Qt.AlignVCenter)
        row.addWidget(l_val, 0, Qt.AlignVCenter)
        row.addWidget(l_btn, 0, Qt.AlignVCenter)
        sep = QFrame()
        sep.setFixedSize(1, 14)
        sep.setStyleSheet("background: rgba(255,255,255,0.35);")
        row.addWidget(sep, 0, Qt.AlignVCenter)
        row.addWidget(r_lbl, 0, Qt.AlignVCenter)
        row.addWidget(r_val, 0, Qt.AlignVCenter)
        row.addWidget(r_btn, 0, Qt.AlignVCenter)
        row.addStretch()
        return row

    def _build_single_row(self, widgets: tuple) -> QHBoxLayout:
        lbl, val_stack, btn_stack = widgets
        fm = lbl.fontMetrics()
        bw    = fm.horizontalAdvance("Edit") + 6
        val_w = max(val_stack.minimumWidth(), fm.horizontalAdvance("0.000s") + 4)
        lbl.setFixedWidth(fm.horizontalAdvance("Dur") + 2)
        val_stack.setFixedWidth(val_w)
        for i in range(val_stack.count()):
            val_stack.widget(i).setFixedWidth(val_w)
        btn_stack.setFixedWidth(bw)
        for i in range(btn_stack.count()):
            btn_stack.widget(i).setFixedWidth(bw)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(lbl, 0, Qt.AlignVCenter)
        row.addWidget(val_stack, 0, Qt.AlignVCenter)
        row.addWidget(btn_stack, 0, Qt.AlignVCenter)
        row.addStretch()
        return row

    def _webhook_message_row(self, key: str) -> QHBoxLayout:
        H = 16

        _vfont = QFont()
        _vfont.setPixelSize(11)
        _vfont.setBold(True)
        _fm = QFontMetrics(_vfont)

        def _text_w(text: str) -> int:
            return max(30, _fm.horizontalAdvance(text) + 6)

        val = str(self._ev.get(key, ""))

        row_l = self._inline_row("Message")
        row_l.setSpacing(3)
        _row_lbl = row_l.itemAt(0).widget()
        if _row_lbl:
            row_l.setAlignment(_row_lbl, Qt.AlignTop)

        disp = QLabel(val)
        disp.setWordWrap(True)
        disp.setFixedWidth(max(44, _text_w(val)))
        disp.setStyleSheet(
            "color:#78c8ff; font-size:11px; font-weight:700;"
            " background:transparent; padding:0; margin:0;")
        disp.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        row_l.addWidget(disp, 0, Qt.AlignTop)

        edit = QPlainTextEdit(val)
        edit.setFixedHeight(H + 2)
        edit.setFrameShape(QFrame.NoFrame)
        edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        edit.setWordWrapMode(QTextOption.WrapAnywhere)
        edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        edit.document().setDocumentMargin(0)
        edit.setStyleSheet(
            "QPlainTextEdit { background:transparent; border:none; outline:none;"
            " color:#78c8ff; font-size:11px; font-weight:700; padding:0; margin:0; }")
        _vp_pal = edit.viewport().palette()
        _vp_pal.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0, 0))
        edit.viewport().setPalette(_vp_pal)
        edit.viewport().setAutoFillBackground(False)
        btn_edit = InlineEditButton()
        btn_edit.setFixedSize(36, H)
        row_l.addWidget(btn_edit, 0, Qt.AlignTop)

        edit.hide()
        row_l.addWidget(edit, 0, Qt.AlignTop)

        btn_done = QLabel("Close")
        btn_done.setObjectName("btnSeqClose")
        btn_done.setFixedSize(36, H)
        btn_done.setAlignment(Qt.AlignCenter)
        btn_done.setCursor(Qt.PointingHandCursor)
        btn_done.setAttribute(Qt.WA_Hover, True)
        btn_done.hide()
        row_l.addWidget(btn_done, 0, Qt.AlignTop)

        row_l.addStretch()

        _editing = [False]

        def _update_disp_size() -> None:
            avail_w = max(44, self._fields_w.width() - 94)
            text = disp.text()
            tw = _text_w(text)
            if tw <= avail_w:
                disp.setFixedWidth(tw)
                disp.setFixedHeight(H + 2)
            else:
                disp.setFixedWidth(avail_w)
                rect = disp.fontMetrics().boundingRect(
                    QRect(0, 0, avail_w, 10000),
                    Qt.TextWordWrap | Qt.AlignLeft, text)
                disp.setFixedHeight(max(H + 2, rect.height() + 2))
            row_l.activate()
            self._fields_l.invalidate()
            self._fields_w.updateGeometry()

        def _update_edit_size() -> None:
            if not _editing[0]:
                return
            avail_w = max(44, self._fields_w.width() - 94)
            text = edit.toPlainText()
            tw   = _text_w(text)
            if tw <= avail_w and "\n" not in text:
                edit.document().setTextWidth(-1)
                edit.setFixedWidth(tw)
                edit.setFixedHeight(H + 2)
                row_l.activate()
                self._fields_l.invalidate()
                self._fields_w.updateGeometry()
            else:
                edit.setFixedWidth(avail_w)
                edit.document().setTextWidth(avail_w)
                def _apply_height() -> None:
                    if not _editing[0]:
                        return
                    line_h = _fm.lineSpacing()
                    paragraphs = edit.toPlainText().split('\n')
                    total_lines = 0
                    for para in paragraphs:
                        if not para:
                            total_lines += 1
                        else:
                            rect = _fm.boundingRect(
                                QRect(0, 0, avail_w, 10000),
                                Qt.TextWrapAnywhere, para)
                            total_lines += max(1, (rect.height() + line_h - 1) // line_h)
                    doc_h = total_lines * line_h
                    h = max(H + 2, doc_h + 4)
                    edit.setFixedHeight(h)
                    row_l.activate()
                    self._fields_l.invalidate()
                    self._fields_w.updateGeometry()
                QTimer.singleShot(0, _apply_height)

        def start() -> None:
            _editing[0] = True
            edit.setFixedWidth(disp.width())
            edit.setFixedHeight(disp.height())
            disp.hide()
            btn_edit.hide()
            edit.show()
            btn_done.show()
            edit.blockSignals(True)
            edit.setPlainText(str(self._ev.get(key, "")))
            edit.blockSignals(False)
            edit.setFocus()
            QTimer.singleShot(0, _update_edit_size)

        def commit() -> None:
            if not _editing[0]:
                return
            _editing[0] = False
            v = edit.toPlainText()
            self._ev[key] = v
            disp.setText(v)
            edit.hide()
            btn_done.hide()
            disp.show()
            btn_edit.show()
            _update_disp_size()
            self._summary.setText(_ev_label(self._ev))
            self.changed.emit(self._idx, dict(self._ev))
            self.setFocus()

        def _on_key_press(e: object) -> None:
            if e.key() in (Qt.Key_Return, Qt.Key_Enter):
                if e.modifiers() & Qt.ShiftModifier:
                    QPlainTextEdit.keyPressEvent(edit, e)
                else:
                    commit()
            else:
                QPlainTextEdit.keyPressEvent(edit, e)

        def _on_focus_out(e: object) -> None:
            QPlainTextEdit.focusOutEvent(edit, e)
            QTimer.singleShot(0, lambda: commit() if not edit.hasFocus() else None)

        edit.textChanged.connect(_update_edit_size)
        edit.keyPressEvent = _on_key_press
        edit.focusOutEvent = _on_focus_out
        btn_edit.clicked.connect(start)
        btn_done.mousePressEvent = lambda e: commit()
        QTimer.singleShot(0, _update_disp_size)
        return row_l

    def _build_fields(self) -> None:
        while self._fields_l.count():
            item = self._fields_l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        if self._kb_listener:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
            self._kb_listener = None
        self._capturing = False

        tp = self._ev.get("type", "mouse_click")
        self._field_widgets: dict = {}
        _row_q: list = []

        def enqueue(key: str, label: str, val: object,
                    numbers_only: bool = False, on_commit=None) -> None:
            widgets = self._make_inline_widgets(key, label, val, numbers_only, on_commit)
            if _row_q:
                self._fields_l.addLayout(self._build_combined_row(_row_q.pop(), widgets))
            else:
                _row_q.append(widgets)

        def flush() -> None:
            while _row_q:
                self._fields_l.addLayout(self._build_single_row(_row_q.pop()))

        if tp == "mouse_move" and not self._ev.get("recorded"):
            for key, label in (("x", "X"), ("y", "Y")):
                val = int(self._ev.get(key, 0))
                enqueue(key, label, str(val), numbers_only=True)

            xy_row = self._fields_l.itemAt(self._fields_l.count() - 1).layout()
            stretch_idx = xy_row.count() - 1

            vsep = QFrame()
            vsep.setFixedSize(1, 14)
            vsep.setStyleSheet("background: rgba(255,255,255,0.35);")
            xy_row.insertWidget(stretch_idx, vsep, 0, Qt.AlignVCenter)
            stretch_idx += 1

            set_pos_btn = InlineEditButton()
            set_pos_btn.setText("Set Pos")
            set_pos_btn.setFixedHeight(16)

            def _start_pos_grab() -> None:
                self._pos_overlay = _PosGrabOverlay()

                def _on_captured(cx: int, cy: int) -> None:
                    self._ev["x"] = cx
                    self._ev["y"] = cy
                    self._summary.setText(_ev_label(self._ev))
                    self.changed.emit(self._idx, dict(self._ev))
                    self._build_fields()

                self._pos_overlay.captured.connect(_on_captured)
                self._pos_overlay.show()
                self._pos_overlay.activateWindow()

            set_pos_btn.clicked.connect(_start_pos_grab)
            xy_row.insertWidget(stretch_idx, set_pos_btn, 0, Qt.AlignVCenter)

        if tp in ("mouse_click", "mouse_scroll"):
            for key, label in (("x", "X"), ("y", "Y")):
                val = int(self._ev.get(key, 0))
                enqueue(key, label, str(val), numbers_only=True)

        if tp == "mouse_click":
            xy_row = self._fields_l.itemAt(self._fields_l.count() - 1).layout()
            stretch_idx = xy_row.count() - 1

            vsep = QFrame()
            vsep.setFixedSize(1, 14)
            vsep.setStyleSheet("background: rgba(255,255,255,0.35);")
            xy_row.insertWidget(stretch_idx, vsep, 0, Qt.AlignVCenter)
            stretch_idx += 1

            set_pos_btn = InlineEditButton()
            set_pos_btn.setText("Set Pos")
            set_pos_btn.setFixedHeight(16)

            def _start_click_pos_grab() -> None:
                self._click_pos_overlay = _PosGrabOverlay()

                def _on_click_captured(cx: int, cy: int) -> None:
                    self._ev["x"] = cx
                    self._ev["y"] = cy
                    self._summary.setText(_ev_label(self._ev))
                    self.changed.emit(self._idx, dict(self._ev))
                    self._build_fields()

                self._click_pos_overlay.captured.connect(_on_click_captured)
                self._click_pos_overlay.show()
                self._click_pos_overlay.activateWindow()

            set_pos_btn.clicked.connect(_start_click_pos_grab)
            xy_row.insertWidget(stretch_idx, set_pos_btn, 0, Qt.AlignVCenter)

        if tp == "mouse_scroll":
            for key, label in (("dx", "dX"), ("dy", "dY")):
                val = self._ev.get(key, 0)
                enqueue(key, label, str(val), numbers_only=True)

        if tp in ("key_press", "key_release"):
            k   = self._ev.get("key", {})
            cur = _SPECIAL_DISPLAY.get(k.get("special", "")) or k.get("char") or "?"

            key_val_stack = QStackedWidget()
            key_val_stack.setFixedSize(35, 16)
            key_val_stack.setContentsMargins(0, 0, 0, 0)
            self._key_lbl = QLabel(cur)
            self._key_lbl.setFixedSize(35, 16)
            self._key_lbl.setContentsMargins(0, 0, 0, 0)
            self._key_lbl.setStyleSheet(
                "color:#78c8ff; font-size:10px; font-weight:700;"
                " background: transparent; padding: 0; margin: 0;")
            self._key_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            key_val_stack.addWidget(self._key_lbl)
            self._key_capturing_lbl = QLabel("Press\u2026")
            self._key_capturing_lbl.setFixedSize(35, 16)
            self._key_capturing_lbl.setContentsMargins(0, 0, 0, 0)
            self._key_capturing_lbl.setStyleSheet(
                "color:#52596b; font-size:10px; background: transparent;"
                " padding: 0; margin: 0;")
            self._key_capturing_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            key_val_stack.addWidget(self._key_capturing_lbl)
            self._key_val_stack = key_val_stack

            key_btn_stack = QStackedWidget()
            key_btn_stack.setFixedSize(36, 16)
            key_btn_stack.setContentsMargins(0, 0, 0, 0)
            self._cap_btn = InlineEditButton()
            self._cap_btn.setFixedSize(36, 16)
            self._cap_btn.clicked.connect(self._start_capture)
            key_btn_stack.addWidget(self._cap_btn)
            self._cancel_btn = QLabel("Close")
            self._cancel_btn.setObjectName("btnSeqClose")
            self._cancel_btn.setFixedSize(36, 16)
            self._cancel_btn.setAlignment(Qt.AlignCenter)
            self._cancel_btn.setCursor(Qt.PointingHandCursor)
            self._cancel_btn.setAttribute(Qt.WA_Hover, True)
            self._cancel_btn.mousePressEvent = lambda e: self._cancel_capture()
            key_btn_stack.addWidget(self._cancel_btn)
            self._key_btn_stack = key_btn_stack

            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel("Key")
            lbl.setFixedWidth(52)
            lbl.setFixedHeight(16)
            lbl.setStyleSheet("color:#7a8299; font-size:10px;")
            lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            _row_q.append((lbl, key_val_stack, key_btn_stack))

        if tp == "wait":
            def _dur_commit(v: str) -> str:
                dur = max(0.0, float(v))
                self._ev["duration"] = dur
                self._summary.setText(_ev_label(self._ev))
                self.changed.emit(self._idx, dict(self._ev))
                return f"{dur:.3f}"
            enqueue("duration", "Dur",
                    f"{self._ev.get('duration', 1.0):.3f}", on_commit=_dur_commit)

        if tp == "wait":
            flush()
            return

        if tp == "webhook":
            self._fields_l.addLayout(self._webhook_message_row("message"))
            return

        if tp == "loop_above":
            def _count_commit(v: str) -> str:
                try:
                    count = max(1, int(float(v)))
                except ValueError:
                    count = 1
                self._ev["count"] = count
                self._summary.setText(_ev_label(self._ev))
                self.changed.emit(self._idx, dict(self._ev))
                return str(count)
            enqueue("count", "Times", str(self._ev.get("count", 1)),
                    numbers_only=True, on_commit=_count_commit)
            flush()
            return

        if tp == "mouse_move" and not self._ev.get("recorded"):
            def _dur_ms_commit(v: str) -> str:
                try:
                    ms = max(0, int(float(v)))
                except ValueError:
                    ms = 0
                self._ev["move_duration"] = ms
                self._summary.setText(_ev_label(self._ev))
                self.changed.emit(self._idx, dict(self._ev))
                return str(ms)

            dur_widgets = self._make_inline_widgets(
                "move_duration", "Dur",
                str(self._ev.get("move_duration", 0)),
                numbers_only=True, on_commit=_dur_ms_commit)

            _modes = ("Linear", "Human")
            mode_lbl = QLabel("Mode")
            mode_lbl.setFixedHeight(16)
            mode_lbl.setStyleSheet("color:#7a8299; font-size:10px;")
            mode_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            mode_val_stack = QStackedWidget()
            mode_val_stack.setContentsMargins(0, 0, 0, 0)
            self._mode_val_lbl = QLabel(self._ev.get("move_mode", "Linear"))
            self._mode_val_lbl.setFixedHeight(16)
            self._mode_val_lbl.setContentsMargins(0, 0, 0, 0)
            self._mode_val_lbl.setStyleSheet(
                "color:#78c8ff; font-size:10px; font-weight:700;"
                " background:transparent; padding:0; margin:0;")
            self._mode_val_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            mode_val_stack.addWidget(self._mode_val_lbl)

            mode_btn_stack = QStackedWidget()
            mode_btn_stack.setFixedSize(18, 16)
            mode_btn_stack.setContentsMargins(0, 0, 0, 0)
            mode_cycle_btn = QPushButton("\u203a")
            mode_cycle_btn.setObjectName("btnExpand")
            mode_cycle_btn.setFixedSize(18, 16)
            mode_cycle_btn.setCursor(Qt.PointingHandCursor)

            def _cycle_mode() -> None:
                cur = self._mode_val_lbl.text()
                nxt = _modes[((_modes.index(cur) if cur in _modes else 0) + 1) % len(_modes)]
                self._mode_val_lbl.setText(nxt)
                self._ev["move_mode"] = nxt
                self._summary.setText(_ev_label(self._ev))
                self.changed.emit(self._idx, dict(self._ev))

            mode_cycle_btn.clicked.connect(_cycle_mode)
            mode_btn_stack.addWidget(mode_cycle_btn)

            self._fields_l.addLayout(
                self._build_combined_row(dur_widgets, (mode_lbl, mode_val_stack, mode_btn_stack)))

        t_val_stack = QStackedWidget()
        t_val_stack.setFixedSize(35, 16)
        t_val_stack.setContentsMargins(0, 0, 0, 0)
        self._time_disp_lbl = QLabel(f"{self._ev.get('time', 0.0):.3f}s")
        self._time_disp_lbl.setFixedSize(35, 16)
        self._time_disp_lbl.setContentsMargins(0, 0, 0, 0)
        self._time_disp_lbl.setStyleSheet(
            "color:#78c8ff; font-size:10px; font-weight:700;"
            " background: transparent; padding: 0; margin: 0;")
        self._time_disp_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        t_val_stack.addWidget(self._time_disp_lbl)
        self._time_edit_field = QLineEdit(f"{self._ev.get('time', 0.0):.3f}")
        self._time_edit_field.setFixedSize(35, 16)
        self._time_edit_field.setContentsMargins(0, 0, 0, 0)
        self._time_edit_field.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]*")))
        self._time_edit_field.setStyleSheet(
            "QLineEdit { background: transparent; border: none; outline: none;"
            " color: #78c8ff; font-size: 11px; font-weight: 700;"
            " padding: 0; margin: 0; }")
        self._time_edit_field.setTextMargins(-2, 0, 0, 0)
        self._time_edit_field.setFrame(False)
        self._time_edit_field.returnPressed.connect(self._commit_time_edit)
        self._time_edit_field.focusOutEvent = lambda e: (
            QLineEdit.focusOutEvent(self._time_edit_field, e),
            self._commit_time_edit(),
        )
        t_val_stack.addWidget(self._time_edit_field)

        t_btn_stack = QStackedWidget()
        t_btn_stack.setFixedSize(36, 16)
        t_btn_stack.setContentsMargins(0, 0, 0, 0)
        self._time_edit_btn = InlineEditButton()
        self._time_edit_btn.setFixedSize(36, 16)
        self._time_edit_btn.clicked.connect(self._start_time_edit)
        t_btn_stack.addWidget(self._time_edit_btn)
        self._time_done_btn = QLabel("Close")
        self._time_done_btn.setObjectName("btnSeqClose")
        self._time_done_btn.setFixedSize(36, 16)
        self._time_done_btn.setAlignment(Qt.AlignCenter)
        self._time_done_btn.setCursor(Qt.PointingHandCursor)
        self._time_done_btn.setAttribute(Qt.WA_Hover, True)
        self._time_done_btn.mousePressEvent = lambda e: self._commit_time_edit()
        t_btn_stack.addWidget(self._time_done_btn)
        self._t_val_stack = t_val_stack
        self._t_btn_stack = t_btn_stack

        t_widgets = (QLabel("Time"), t_val_stack, t_btn_stack)
        t_widgets[0].setFixedWidth(52)
        t_widgets[0].setFixedHeight(16)
        t_widgets[0].setStyleSheet("color:#7a8299; font-size:10px;")
        t_widgets[0].setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        if _row_q:
            self._fields_l.addLayout(self._build_combined_row(_row_q.pop(), t_widgets))
        else:
            self._fields_l.addLayout(self._build_single_row(t_widgets))

    def _start_time_edit(self) -> None:
        self._time_edit_field.setText(f"{self._ev.get('time', 0.0):.3f}")
        self._t_val_stack.setCurrentIndex(1)
        self._t_btn_stack.setCurrentIndex(1)
        self._time_edit_field.setFocus()

    def _commit_time_edit(self) -> None:
        self._time_edit_field.deselect()
        try:
            val = float(self._time_edit_field.text())
            self._ev["time"] = max(0.0, val)
        except ValueError:
            pass
        self._time_disp_lbl.setText(f"{self._ev.get('time', 0.0):.3f}s")
        self._t_val_stack.setCurrentIndex(0)
        self._t_btn_stack.setCurrentIndex(0)
        self._t_lbl.setText(f"{self._ev['time']:.3f}s")
        self.changed.emit(self._idx, dict(self._ev))
        self.setFocus()

    def _start_capture(self) -> None:
        if self._capturing:
            return
        self._capturing = True
        self._key_val_stack.setCurrentIndex(1)
        self._key_btn_stack.setCurrentIndex(1)
        self._cap_btn.setEnabled(False)
        self._key_grabber = _KeyGrabber(self._on_key_grabbed, self._cancel_capture)
        self._key_grabber.show()
        self._key_grabber.activateWindow()
        self._key_grabber.setFocus()

    def _on_key_grabbed(self, k_dict: dict, display: str) -> None:
        if not self._capturing:
            return
        self._ev["key"] = k_dict
        self._capture_done(display)

    def _cancel_capture(self) -> None:
        self._capturing = False
        if self._key_grabber:
            try:
                self._key_grabber.close()
            except Exception:
                pass
            self._key_grabber = None
        if self._kb_listener:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
            self._kb_listener = None
        self._key_val_stack.setCurrentIndex(0)
        self._key_btn_stack.setCurrentIndex(0)
        self._cap_btn.setEnabled(True)
        self.setFocus()

    def _capture_done(self, display: str) -> None:
        self._capturing = False
        if self._key_grabber:
            try:
                self._key_grabber.close()
            except Exception:
                pass
            self._key_grabber = None
        if self._kb_listener:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
            self._kb_listener = None
        self._key_lbl.setText(display)
        self._key_val_stack.setCurrentIndex(0)
        self._key_btn_stack.setCurrentIndex(0)
        self._cap_btn.setEnabled(True)
        self._summary.setText(_ev_label(self._ev))
        self.changed.emit(self._idx, dict(self._ev))
        self.setFocus()

    def _ms_changed(self, v: str) -> None:
        try:
            self._ev["duration"] = max(0, float(v)) / 1000.0
            self._summary.setText(_ev_label(self._ev))
            self.changed.emit(self._idx, dict(self._ev))
        except Exception:
            pass

    def _field_changed(self, key: str) -> None:
        try:
            val = self._field_widgets[key].text()
            if key in ("x", "y", "dx", "dy"):
                self._ev[key] = float(val)
            self._summary.setText(_ev_label(self._ev))
            self.changed.emit(self._idx, dict(self._ev))
        except Exception:
            pass

    def _refresh_style(self) -> None:
        if self._expanded:
            name = "seqRowSelected"
        elif self._selected:
            name = "seqRowSel"
        else:
            name = "seqRow"
        self.setObjectName(name)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._refresh_style()

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._detail.setVisible(self._expanded)
        self._exp_btn.set_expanded(self._expanded)
        self._refresh_style()

    def mousePressEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton:
            self.row_clicked.emit(self._idx, e.modifiers().value)

    def eventFilter(self, obj: object, e: object) -> bool:
        if obj is self._drag_handle and e.type() == QEvent.MouseButtonPress:
            if e.button() == Qt.LeftButton:
                self._drag_handle.set_active(True)
                self._drag_handle.setCursor(Qt.ClosedHandCursor)
                self.drag_start.emit(self._idx, e.globalPosition().toPoint())
                return True
        if obj is self._drag_handle and e.type() == QEvent.MouseButtonRelease:
            self._drag_handle.setCursor(Qt.OpenHandCursor)
        return super().eventFilter(obj, e)

    def set_dragging(self, on: bool) -> None:
        self._drag_handle.set_active(on)
        self._drag_handle.setCursor(
            Qt.ClosedHandCursor if on else Qt.OpenHandCursor)

    def update_index(self, idx: int) -> None:
        self._idx = idx
        self._idx_lbl.setText(f"{idx+1:>3}.")


class _ResizeHandle(QWidget):
    resize_press   = Signal(object)
    resize_move    = Signal(object)
    resize_release = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(8)
        self.setCursor(Qt.SizeVerCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self._dragging = False

    def paintEvent(self, e: object) -> None:
        p  = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = self.width()  // 2
        cy = self.height() // 2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 40))
        for i in range(-2, 3):
            p.drawEllipse(cx + i * 5 - 1, cy - 1, 3, 3)
        p.end()

    def mousePressEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton:
            self._dragging = True
            self.resize_press.emit(e.globalPosition().toPoint())
            e.accept()

    def mouseMoveEvent(self, e: object) -> None:
        if self._dragging and e.buttons() == Qt.LeftButton:
            self.resize_move.emit(e.globalPosition().toPoint())
            e.accept()

    def mouseReleaseEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton:
            self._dragging = False
            self.resize_release.emit()
            e.accept()
