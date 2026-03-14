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

"""Custom Qt widget classes for the Moris Macro Maker UI."""

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
    QIcon,
    QIntValidator,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygon,
    QRegularExpressionValidator,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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

# Qt key → (pynput canon, display label) mapping
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


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _svg_icon(svg_bytes: bytes, size: int = 16, color: str = "#52596b") -> QIcon:
    """Create a QIcon from SVG bytes with a given stroke colour.

    Args:
        svg_bytes: Raw SVG data; ``currentColor`` is replaced by *color*.
        size:      Square icon size in pixels.
        color:     CSS colour string to substitute.

    Returns:
        A :class:`QIcon` at the requested size.
    """
    colored = svg_bytes.replace(b"currentColor", color.encode())
    pix = QPixmap()
    pix.loadFromData(colored, "SVG")
    return QIcon(pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))


def _ev_label(ev: dict) -> str:
    """Return a short human-readable description of an event dict.

    Args:
        ev: Event dict.

    Returns:
        Descriptive string.
    """
    tp = ev.get("type", "")
    if tp == "mouse_move":
        return f"Move  ({int(ev['x'])}, {int(ev['y'])})"
    if tp == "mouse_click":
        act = "Press" if ev.get("pressed") else "Release"
        return f"Click {ev.get('button','left').title()} {act}  ({int(ev['x'])}, {int(ev['y'])})"
    if tp == "mouse_scroll":
        return f"Scroll  ({int(ev['x'])}, {int(ev['y'])})  dx={ev['dx']:.1f} dy={ev['dy']:.1f}"
    if tp == "key_press":
        k  = ev.get("key", {})
        ch = k.get("special") or k.get("char") or "?"
        return f"Key Press  {ch}"
    if tp == "key_release":
        k  = ev.get("key", {})
        ch = k.get("special") or k.get("char") or "?"
        return f"Key Release  {ch}"
    if tp == "wait":
        ms = ev.get("duration", 1.0) * 1000
        return f"Wait  {ms:.0f} ms"
    if tp == "webhook":
        msg   = ev.get("message", "")
        short = msg[:24] + "\u2026" if len(msg) > 24 else msg
        return f"Webhook  {short}" if short else "Webhook"
    return tp


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class StyledSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox with custom up/down arrow painting."""

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
    """Expandable "Edit Events" button with animated arrow."""

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
        """Animate the arrow to point right (expanded) or down (collapsed).

        Args:
            v: ``True`` to expand, ``False`` to collapse.
        """
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
    """Small "Edit" button used inside sequence rows."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Edit", parent)
        self.setObjectName("btnInlineEdit")
        self.setFixedHeight(16)
        self.setFixedWidth(32)


class PlayButton(QPushButton):
    """Play/Stop button with dynamic label and custom painting."""

    def __init__(self, key_text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("btnPlay")
        self._key_text = key_text
        self._playing  = False
        self.setFixedHeight(32)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_key(self, key_text: str) -> None:
        """Update the hotkey label text.

        Args:
            key_text: New key label to display.
        """
        self._key_text = key_text
        self.update()

    def set_playing(self, playing: bool) -> None:
        """Switch the button between Play and Stop appearance.

        Args:
            playing: ``True`` when playback is active.
        """
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


class KeyCapture(QLineEdit):
    """Read-only line edit that captures the next key press on click."""

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
        """Return the currently captured key string."""
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
                pass  # unknown button, stay in capture mode
            # LMB/RMB while capturing: cancel
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
    """Animated on/off toggle widget."""

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
        """Return whether the switch is on."""
        return self._on

    def setChecked(self, v: bool, animate: bool = True) -> None:
        """Set the switch state.

        Args:
            v:       New state.
            animate: Whether to animate the transition.
        """
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
    """Custom minimise button with hover painting."""

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
    """Tiny triangle button used to expand/collapse sequence rows."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("btnRowExpand")
        self._expanded = False

    def set_expanded(self, v: bool) -> None:
        """Update arrow direction.

        Args:
            v: ``True`` if the row is expanded.
        """
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
    """Invisible floating widget that captures exactly one key press."""

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


class EventRow(QWidget):
    """Single row in the sequence editor representing one event."""

    deleted    = Signal(int)
    changed    = Signal(int, dict)
    drag_start = Signal(int, object)

    def __init__(
        self, idx: int, ev: dict, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._idx       = idx
        self._ev        = dict(ev)
        self._expanded  = False
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
        if ev.get("type") == "webhook":
            self._t_lbl.setVisible(False)
        hdr.addWidget(self._t_lbl)

        self._drag_handle = QLabel("::")
        self._drag_handle.setFixedSize(16, 18)
        self._drag_handle.setAlignment(Qt.AlignCenter)
        self._drag_handle.setStyleSheet("color:#3a3f52; font-size:10px;")
        self._drag_handle.setCursor(Qt.OpenHandCursor)
        self._drag_handle.installEventFilter(self)
        hdr.addWidget(self._drag_handle)

        self._exp_btn = RowExpandButton()
        self._exp_btn.setFixedSize(18, 18)
        self._exp_btn.clicked.connect(self._toggle_expand)
        hdr.addWidget(self._exp_btn)

        del_btn = QPushButton("\u2715")
        del_btn.setObjectName("btnSeqDel")
        del_btn.setFixedSize(18, 18)
        del_btn.clicked.connect(lambda: self.deleted.emit(self._idx))
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
        if self._ev.get("type") == "mouse_move":
            self._exp_btn.setEnabled(False)
            sp = self._exp_btn.sizePolicy()
            sp.setRetainSizeWhenHidden(True)
            self._exp_btn.setSizePolicy(sp)
            self._exp_btn.setVisible(False)

    # ------------------------------------------------------------------

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
        r = self._inline_row(label_text)
        W, H = 76, 16

        val_stack = QStackedWidget()
        val_stack.setFixedSize(W, H)
        val_stack.setContentsMargins(0, 0, 0, 0)

        disp = QLabel(str(val))
        disp.setFixedSize(W, H)
        disp.setContentsMargins(0, 0, 0, 0)
        disp.setStyleSheet(
            "color:#78c8ff; font-size:11px; font-weight:700;"
            " background: transparent; padding: 0; margin: 0;")
        disp.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        val_stack.addWidget(disp)

        edit = QLineEdit(str(val))
        edit.setFixedSize(W, H)
        edit.setContentsMargins(0, 0, 0, 0)
        edit.setStyleSheet(
            "QLineEdit { background: transparent; border: none; outline: none;"
            " color: #78c8ff; font-size: 11px; font-weight: 700; padding: 0; margin: 0; }")
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
        r.addWidget(val_stack, 0, Qt.AlignVCenter)
        r.addWidget(btn_stack, 0, Qt.AlignVCenter)
        r.addStretch()
        return r

    def _inline_label_row(
        self, label_text: str, val: str, options: list, key: str
    ) -> QHBoxLayout:
        r    = self._inline_row(label_text)
        disp = QLabel(val)
        disp.setStyleSheet(
            "color:#78c8ff; font-size:11px; font-weight:700; min-width:60px;")
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

        def add(key: str, label: str, val: object, numbers_only: bool = False) -> None:
            e = self._make_edit(val, numbers_only=numbers_only)
            self._field_widgets[key] = e
            self._fields_l.addLayout(self._field_row(label, e))
            e.textChanged.connect(lambda _, k=key: self._field_changed(k))

        if tp in ("mouse_click", "mouse_scroll"):
            for key, label in (("x", "X"), ("y", "Y")):
                val = int(self._ev.get(key, 0))
                self._fields_l.addLayout(
                    self._inline_edit_row(key, label, str(val), numbers_only=True))

        if tp == "mouse_scroll":
            for key, label in (("dx", "dX"), ("dy", "dY")):
                val = self._ev.get(key, 0)
                self._fields_l.addLayout(
                    self._inline_edit_row(key, label, str(val), numbers_only=True))

        if tp in ("key_press", "key_release"):
            k   = self._ev.get("key", {})
            cur = k.get("special") or k.get("char") or "?"

            key_val_stack = QStackedWidget()
            key_val_stack.setFixedSize(76, 16)
            key_val_stack.setContentsMargins(0, 0, 0, 0)
            self._key_lbl = QLabel(cur)
            self._key_lbl.setFixedSize(76, 16)
            self._key_lbl.setContentsMargins(0, 0, 0, 0)
            self._key_lbl.setStyleSheet(
                "color:#78c8ff; font-size:11px; font-weight:700;"
                " background: transparent; padding: 0; margin: 0;")
            self._key_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            key_val_stack.addWidget(self._key_lbl)
            self._key_capturing_lbl = QLabel("Press a key\u2026")
            self._key_capturing_lbl.setFixedSize(76, 16)
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
            row.addWidget(lbl, 0, Qt.AlignVCenter)
            row.addWidget(key_val_stack, 0, Qt.AlignVCenter)
            row.addWidget(key_btn_stack, 0, Qt.AlignVCenter)
            row.addStretch()
            self._fields_l.addLayout(row)

        if tp == "wait":
            ms = self._ev.get("duration", 1.0) * 1000
            add("duration_ms", "Duration", int(ms), numbers_only=True)
            self._field_widgets["duration_ms"].textChanged.connect(
                lambda v: self._ms_changed(v))

        if tp == "webhook":
            self._fields_l.addLayout(
                self._inline_edit_row(
                    "message", "Message",
                    self._ev.get("message", ""), numbers_only=False))

        if tp == "webhook":
            return

        t_val_stack = QStackedWidget()
        t_val_stack.setFixedSize(76, 16)
        t_val_stack.setContentsMargins(0, 0, 0, 0)
        self._time_disp_lbl = QLabel(f"{self._ev.get('time', 0.0):.3f}s")
        self._time_disp_lbl.setFixedSize(76, 16)
        self._time_disp_lbl.setContentsMargins(0, 0, 0, 0)
        self._time_disp_lbl.setStyleSheet(
            "color:#78c8ff; font-size:11px; font-weight:700;"
            " background: transparent; padding: 0; margin: 0;")
        self._time_disp_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        t_val_stack.addWidget(self._time_disp_lbl)
        self._time_edit_field = QLineEdit(f"{self._ev.get('time', 0.0):.3f}")
        self._time_edit_field.setFixedSize(76, 16)
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

        t_row = QHBoxLayout()
        t_row.setSpacing(6)
        t_lbl = QLabel("Time")
        t_lbl.setFixedWidth(52)
        t_lbl.setFixedHeight(16)
        t_lbl.setStyleSheet("color:#7a8299; font-size:10px;")
        t_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        t_row.addWidget(t_lbl, 0, Qt.AlignVCenter)
        t_row.addWidget(t_val_stack, 0, Qt.AlignVCenter)
        t_row.addWidget(t_btn_stack, 0, Qt.AlignVCenter)
        t_row.addStretch()
        self._fields_l.addLayout(t_row)

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

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._detail.setVisible(self._expanded)
        self._exp_btn.set_expanded(self._expanded)
        self.setObjectName("seqRowSel" if self._expanded else "seqRow")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton and self._ev.get("type") != "mouse_move":
            self._toggle_expand()

    def eventFilter(self, obj: object, e: object) -> bool:
        if obj is self._drag_handle and e.type() == QEvent.MouseButtonPress:
            if e.button() == Qt.LeftButton:
                self._drag_handle.setStyleSheet(
                    "color:#78c8ff; font-size:10px;")
                self._drag_handle.setCursor(Qt.ClosedHandCursor)
                self.drag_start.emit(self._idx, e.globalPosition().toPoint())
                return True
        if obj is self._drag_handle and e.type() == QEvent.MouseButtonRelease:
            self._drag_handle.setCursor(Qt.OpenHandCursor)
        return super().eventFilter(obj, e)

    def set_dragging(self, on: bool) -> None:
        """Toggle drag-handle highlight.

        Args:
            on: ``True`` while dragging.
        """
        self._drag_handle.setStyleSheet(
            "color:#78c8ff; font-size:10px;"
            if on else "color:#3a3f52; font-size:10px;")
        self._drag_handle.setCursor(
            Qt.ClosedHandCursor if on else Qt.OpenHandCursor)

    def update_index(self, idx: int) -> None:
        """Update the displayed row number.

        Args:
            idx: Zero-based event index.
        """
        self._idx = idx
        self._idx_lbl.setText(f"{idx+1:>3}.")


class _ResizeHandle(QWidget):
    """Draggable resize handle painted as a row of dots."""

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
