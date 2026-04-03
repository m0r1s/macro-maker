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

import base64
import os
import sys
from typing import Optional

from PySide6.QtCore import (
    QByteArray,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QThread,
    QTimer,
    QUrl,
    Signal,
)
from PySide6.QtGui import QColor, QDesktopServices, QPixmap, QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..player import PlayWorker
from ..recorder import MacroRecorder
from ..utils.constants import (
    DEFAULT_LOOP,
    DEFAULT_LOOP_COUNT,
    DEFAULT_LOOP_INTERVAL,
    DEFAULT_LOOP_TIMER,
    DEFAULT_PLAY_KEY,
    DEFAULT_REC_KEY,
    DEFAULT_SPEED,
    FONT,
    LOGO_B64,
    MMR_ICO_B64,
    SEQ_MIN_H,
    SVG_COG,
    SVG_PIN,
    SVG_PIN_ON,
)
from ..utils.serialization import (
    MMR_MAGIC,
    autosave,
    autoload,
    ensure_mmr_icon,
    mmr_load,
    mmr_save,
    reg_load,
    reg_save,
)
from .widgets import (
    EditButton,
    EventRow,
    KeyCapture,
    MinimizeBtn,
    PlayButton,
    RecButton,
    _ResizeHandle,
    _ev_label,
    _norm_key,
    _svg_icon,
    ToggleSwitch,
    RowExpandButton,
    _KeyGrabber,
)

try:
    from pynput import keyboard as _kb
    _OK = True
except ImportError:
    _OK = False


class _TypeDropdown(QWidget):
    changed = Signal(int)

    _LABELS = [
        "Key Press", "Mouse Click",
        "Mouse Move", "Mouse Scroll", "Webhook",
        "Loop Above",
    ]

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._idx = -1
        lo = QHBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)
        self._btn = QPushButton("Select type  \u25be")
        self._btn.setObjectName("btnTypeDropdown")
        self._btn.setFixedHeight(26)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self._open_popup)
        lo.addWidget(self._btn)

    def currentIndex(self) -> int:
        return self._idx

    def _open_popup(self) -> None:
        popup = QWidget(None, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        popup.setAttribute(Qt.WA_TranslucentBackground, True)
        outer_lo = QVBoxLayout(popup)
        outer_lo.setContentsMargins(0, 0, 0, 0)

        inner = QFrame()
        inner.setObjectName("typePopupInner")
        inner.setAttribute(Qt.WA_StyledBackground, True)
        ilo = QVBoxLayout(inner)
        ilo.setContentsMargins(5, 5, 5, 5)
        ilo.setSpacing(2)

        for i, label in enumerate(self._LABELS):
            opt = QPushButton(label)
            opt.setObjectName(
                "btnTypeOptionSel" if i == self._idx else "btnTypeOption")
            opt.setFixedHeight(26)
            opt.setCursor(Qt.PointingHandCursor)
            opt.clicked.connect(
                lambda _=None, idx=i: (self._select(idx), popup.close()))
            ilo.addWidget(opt)

        outer_lo.addWidget(inner)
        gpos = self._btn.mapToGlobal(QPoint(0, self._btn.height() + 3))
        popup.move(gpos)
        popup.show()
        popup.adjustSize()

    def _select(self, idx: int) -> None:
        self._idx = idx
        self._btn.setText(f"{self._LABELS[idx]}  \u25be")
        self.changed.emit(idx)


_QT_TO_PYNPUT: dict = {
    "Return": "Key.enter", "Enter": "Key.enter",
    "Space": "Key.space", "Backspace": "Key.backspace",
    "Tab": "Key.tab", "Escape": "Key.esc",
    "Delete": "Key.delete", "Insert": "Key.insert",
    "Home": "Key.home", "End": "Key.end",
    "PgUp": "Key.page_up", "PgDown": "Key.page_down",
    "Up": "Key.up", "Down": "Key.down",
    "Left": "Key.left", "Right": "Key.right",
    "Shift": "Key.shift", "Ctrl": "Key.ctrl", "Alt": "Key.alt",
    "Meta": "Key.cmd", "CapsLock": "Key.caps_lock",
    **{f"F{i}": f"Key.f{i}" for i in range(1, 13)},
}


def _qt_key_to_norm(s: str) -> dict:
    if s in _QT_TO_PYNPUT:
        return {"special": _QT_TO_PYNPUT[s]}
    if len(s) == 1:
        return {"char": s.lower(), "vk": None}
    return {"special": s}


class AddInputDialog(QDialog):
    pos_preview = Signal(int)

    def __init__(self, parent: QWidget, n_events: int = 0) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag: Optional[object] = None
        self._n_events = n_events
        self.result_event: Optional[dict] = None
        self.result_pos: int = n_events

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 18)

        container = QWidget()
        container.setObjectName("mainContainer")
        container.setAttribute(Qt.WA_StyledBackground, True)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(40)
        sh.setColor(QColor(0, 0, 0, 200))
        sh.setOffset(0, 10)
        container.setGraphicsEffect(sh)
        outer.addWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tb = QWidget()
        tb.setObjectName("titleBar")
        tb.setAttribute(Qt.WA_StyledBackground, True)
        tb.setFixedHeight(34)
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(12, 0, 8, 0)
        tbl.setSpacing(4)
        _ico_data = base64.b64decode(LOGO_B64)
        _pix = QPixmap()
        _pix.loadFromData(_ico_data)
        logo_lbl = QLabel()
        logo_lbl.setPixmap(
            _pix.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_lbl.setFixedSize(16, 16)
        tbl.addWidget(logo_lbl)
        tbl.addSpacing(5)
        ttl = QLabel("Add Input")
        ttl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; font-weight:700; color:#eef0f5;")
        tbl.addWidget(ttl)
        tbl.addStretch()
        xb = QPushButton("\u2715")
        xb.setObjectName("btnClose")
        xb.setFixedSize(22, 22)
        xb.clicked.connect(self._on_cancel)
        tbl.addWidget(xb)

        def _tb_press(e: object) -> None:
            if e.button() == Qt.LeftButton:
                self._drag = (
                    e.globalPosition().toPoint() - self.frameGeometry().topLeft())

        def _tb_move(e: object) -> None:
            if self._drag and e.buttons() == Qt.LeftButton:
                self.move(e.globalPosition().toPoint() - self._drag)

        def _tb_release(e: object) -> None:
            self._drag = None

        tb.mousePressEvent   = _tb_press
        tb.mouseMoveEvent    = _tb_move
        tb.mouseReleaseEvent = _tb_release
        root.addWidget(tb)

        sep0 = QFrame()
        sep0.setObjectName("sep")
        sep0.setFixedHeight(1)
        root.addWidget(sep0)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 12, 14, 14)
        bl.setSpacing(8)
        root.addWidget(body)

        type_card = QWidget()
        type_card.setObjectName("settingsCard")
        type_card.setAttribute(Qt.WA_StyledBackground, True)
        tc = QHBoxLayout(type_card)
        tc.setContentsMargins(12, 8, 12, 8)
        tc.setSpacing(0)
        type_lbl = QLabel("Type")
        type_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; color:#7a8299;")
        tc.addWidget(type_lbl)
        tc.addStretch()
        self._type_combo = _TypeDropdown()
        self._type_combo.changed.connect(self._rebuild_fields)
        tc.addWidget(self._type_combo)
        bl.addWidget(type_card)

        self._fields_card = QWidget()
        self._fields_card.setObjectName("settingsCard")
        self._fields_card.setAttribute(Qt.WA_StyledBackground, True)
        self._fields_card.setVisible(False)
        self._fields_layout = QVBoxLayout(self._fields_card)
        self._fields_layout.setContentsMargins(12, 10, 12, 10)
        self._fields_layout.setSpacing(8)
        bl.addWidget(self._fields_card)

        ins_card = QWidget()
        ins_card.setObjectName("settingsCard")
        ins_card.setAttribute(Qt.WA_StyledBackground, True)
        ic = QHBoxLayout(ins_card)
        ic.setContentsMargins(12, 8, 12, 8)
        ic.setSpacing(0)
        ins_lbl = QLabel("Insert after")
        ins_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; color:#7a8299;")
        ic.addWidget(ins_lbl)
        ic.addStretch()
        self._pos_edit = QLineEdit(str(n_events))
        self._pos_edit.setObjectName("keyInput")
        self._pos_edit.setFixedSize(50, 24)
        self._pos_edit.setAlignment(Qt.AlignCenter)
        self._pos_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[0-9]*")))
        self._pos_edit.textChanged.connect(self._emit_pos_preview)
        ic.addWidget(self._pos_edit)
        self._ins_card = ins_card
        self._ins_card.setVisible(False)
        bl.addWidget(ins_card)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("btnRecord")
        cancel.setFixedHeight(28)
        cancel.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel)
        self._ok_btn = QPushButton("Add")
        self._ok_btn.setObjectName("btnImport")
        self._ok_btn.setFixedHeight(28)
        self._ok_btn.setVisible(False)
        self._ok_btn.clicked.connect(self._on_ok)
        btn_row.addWidget(self._ok_btn)
        bl.addLayout(btn_row)

    def _row(self, label_text: str, *widgets: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel(label_text)
        lbl.setFixedWidth(68)
        lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; color:#7a8299;")
        row.addWidget(lbl)
        row.addStretch()
        for w in widgets:
            row.addWidget(w)
        return row

    def _plain_edit(self, val: str = "0", numeric: bool = False) -> QLineEdit:
        e = QLineEdit(val)
        e.setObjectName("keyInput")
        e.setFixedSize(70, 24)
        e.setAlignment(Qt.AlignCenter)
        if numeric:
            e.setValidator(
                QRegularExpressionValidator(
                    QRegularExpression(r"[0-9]*\.?[0-9]*")))
        return e

    def _cycle_btn(self, options: list, key_attr: str) -> tuple:
        lbl = QLabel(options[0])
        lbl.setStyleSheet(
            f"font-family:{FONT}; color:#78c8ff; font-size:11px; font-weight:700;")
        btn = QPushButton("\u203a")
        btn.setObjectName("btnExpand")
        btn.setFixedSize(18, 18)

        def cycle() -> None:
            cur = lbl.text()
            nxt = (
                options[(options.index(cur) + 1) % len(options)]
                if cur in options else options[0]
            )
            lbl.setText(nxt)
            setattr(self, key_attr, nxt)

        btn.clicked.connect(cycle)
        setattr(self, key_attr, options[0])
        return lbl, btn

    def _clear_fields(self) -> None:
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().setParent(None)
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().hide()
                        sub.widget().setParent(None)

    def _rebuild_fields(self, idx: int = -1) -> None:
        self._clear_fields()

        if idx == -1:
            self._fields_card.setVisible(False)
            self._ins_card.setVisible(False)
            self._ok_btn.setVisible(False)
            QTimer.singleShot(0, lambda: self.resize(self.minimumSizeHint()))
            return

        self._fields_card.setVisible(True)
        self._ins_card.setVisible(True)
        self._ok_btn.setVisible(True)
        self._emit_pos_preview(self._pos_edit.text())

        if idx == 0:
            self._key_capture = KeyCapture()
            self._key_capture.setFixedSize(70, 26)
            act_lbl, act_cycle = self._cycle_btn(
                ["Press", "Release"], "_key_act_val")
            self._fields_layout.addLayout(self._row("Key", self._key_capture))
            self._fields_layout.addLayout(self._row("Action", act_lbl, act_cycle))

        elif idx == 1:
            self._click_x = self._plain_edit("0", numeric=True)
            self._click_y = self._plain_edit("0", numeric=True)
            self._fields_layout.addLayout(self._row("X", self._click_x))
            self._fields_layout.addLayout(self._row("Y", self._click_y))
            btn_lbl, btn_cycle = self._cycle_btn(
                ["Left", "Right", "Middle"], "_click_btn_val")
            act_lbl, act_cycle = self._cycle_btn(
                ["Press", "Release"], "_click_act_val")
            self._fields_layout.addLayout(self._row("Button", btn_lbl, btn_cycle))
            self._fields_layout.addLayout(self._row("Action", act_lbl, act_cycle))

        elif idx == 2:
            self._move_x = self._plain_edit("0", numeric=True)
            self._move_y = self._plain_edit("0", numeric=True)
            self._fields_layout.addLayout(self._row("X", self._move_x))
            self._fields_layout.addLayout(self._row("Y", self._move_y))

        elif idx == 3:
            self._scroll_x  = self._plain_edit("0", numeric=True)
            self._scroll_y  = self._plain_edit("0", numeric=True)
            self._scroll_dx = self._plain_edit("0", numeric=True)
            self._scroll_dy = self._plain_edit("0", numeric=True)
            self._fields_layout.addLayout(self._row("X",  self._scroll_x))
            self._fields_layout.addLayout(self._row("Y",  self._scroll_y))
            self._fields_layout.addLayout(self._row("dX", self._scroll_dx))
            self._fields_layout.addLayout(self._row("dY", self._scroll_dy))

        elif idx == 4:
            self._wh_stored_url = ""
            try:
                cfg = reg_load()
                self._wh_stored_url = cfg.get("webhook_url", "")
            except Exception:
                pass
            self._wh_msg_edit = QLineEdit()
            self._wh_msg_edit.setObjectName("keyInput")
            self._wh_msg_edit.setFixedHeight(24)
            self._wh_msg_edit.setFixedWidth(140)
            self._fields_layout.addLayout(
                self._row("Message", self._wh_msg_edit))

        elif idx == 5:
            self._loop_count_edit = self._plain_edit("1", numeric=True)
            self._fields_layout.addLayout(self._row("Times", self._loop_count_edit))

        if idx not in (4, 5):
            self._time_edit = self._plain_edit("0.000", numeric=True)
            self._fields_layout.addLayout(self._row("Time (s)", self._time_edit))

        QTimer.singleShot(0, lambda: self.resize(self.minimumSizeHint()))

    def _emit_pos_preview(self, text: str = "") -> None:
        try:
            pos = max(0, min(self._n_events, int(text or "0")))
        except ValueError:
            pos = self._n_events
        self.pos_preview.emit(pos)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_ok(self) -> None:
        idx = self._type_combo.currentIndex()
        if idx == -1:
            return
        try:
            t = float(self._time_edit.text()) if idx not in (4, 5) else 0.0
        except Exception:
            t = 0.0

        if idx == 0:
            key_str = getattr(self, "_key_capture", None)
            if not key_str or not key_str.key():
                return
            action = getattr(self, "_key_act_val", "Press")
            tp = "key_press" if action == "Press" else "key_release"
            self.result_event = {
                "type": tp,
                "key":  _qt_key_to_norm(key_str.key()),
                "time": t,
            }

        elif idx == 1:
            try:
                x = int(self._click_x.text())
                y = int(self._click_y.text())
            except ValueError:
                return
            btn     = getattr(self, "_click_btn_val", "Left").lower()
            pressed = getattr(self, "_click_act_val", "Press") == "Press"
            self.result_event = {
                "type": "mouse_click", "x": x, "y": y,
                "button": btn, "pressed": pressed, "time": t,
            }

        elif idx == 2:
            try:
                x = int(self._move_x.text())
                y = int(self._move_y.text())
            except ValueError:
                return
            self.result_event = {"type": "mouse_move", "x": x, "y": y, "time": t}

        elif idx == 3:
            try:
                x  = int(self._scroll_x.text())
                y  = int(self._scroll_y.text())
                dx = float(self._scroll_dx.text())
                dy = float(self._scroll_dy.text())
            except ValueError:
                return
            self.result_event = {
                "type": "mouse_scroll", "x": x, "y": y,
                "dx": dx, "dy": dy, "time": t,
            }

        elif idx == 4:
            url_val = getattr(self, "_wh_stored_url", "")
            if not url_val:
                return
            msg = getattr(self, "_wh_msg_edit", None)
            self.result_event = {
                "type":    "webhook",
                "url":     url_val,
                "user_id": "",
                "message": msg.text().strip() if msg else "",
                "time":    0.0,
            }

        elif idx == 5:
            try:
                count = max(1, int(float(
                    getattr(self, "_loop_count_edit", None).text() or "1")))
            except Exception:
                count = 1
            self.result_event = {"type": "loop_above", "count": count, "time": 0.0}

        try:
            self.result_pos = max(
                0, min(self._n_events, int(self._pos_edit.text() or "0")))
        except ValueError:
            self.result_pos = self._n_events
        self.accept()

    def closeEvent(self, e: object) -> None:
        super().closeEvent(e)

    def mousePressEvent(self, e: object) -> None:
        focused = self.focusWidget()
        if focused and isinstance(focused, QLineEdit):
            focused.clearFocus()
            self.setFocus()

    def mouseMoveEvent(self, e: object) -> None:
        pass

    def mouseReleaseEvent(self, e: object) -> None:
        pass


class WaitDialog(QDialog):
    def __init__(self, parent: QWidget, n_events: int = 0) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag: Optional[object] = None
        self._n_events = n_events
        self.result_ms: Optional[float] = None
        self.result_pos: int = n_events

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        frame = QFrame()
        frame.setObjectName("dlgFrame")
        frame.setAttribute(Qt.WA_StyledBackground, True)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(30)
        sh.setColor(QColor(0, 0, 0, 180))
        sh.setOffset(0, 8)
        frame.setGraphicsEffect(sh)
        outer.addWidget(frame)

        fl = QVBoxLayout(frame)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setSpacing(0)

        title = QLabel("Add Wait")
        title.setStyleSheet("font-size:12px; font-weight:700; color:#eef0f5;")
        fl.addWidget(title)
        fl.addSpacing(10)

        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFixedHeight(1)
        fl.addWidget(sep)
        fl.addSpacing(10)

        ms_row = QHBoxLayout()
        ms_row.setSpacing(0)
        ms_lbl = QLabel("Duration")
        ms_lbl.setFixedWidth(76)
        ms_lbl.setStyleSheet("color:#7a8299; font-size:11px;")
        ms_row.addWidget(ms_lbl)
        self._ms_edit = QLineEdit("1000")
        self._ms_edit.setStyleSheet(
            "QLineEdit { background: transparent; border: none;"
            " border-bottom: 1px solid rgba(255,255,255,0.13);"
            " color: #eef0f5; font-size: 11px; padding: 1px 2px; }")
        self._ms_edit.setFixedWidth(70)
        self._ms_edit.setFixedHeight(18)
        self._ms_edit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"[0-9]*\.?[0-9]*")))
        ms_row.addWidget(self._ms_edit)
        ms_unit = QLabel("ms")
        ms_unit.setStyleSheet("color:#52596b; font-size:11px;")
        ms_row.addSpacing(6)
        ms_row.addWidget(ms_unit)
        ms_row.addStretch()
        fl.addLayout(ms_row)

        fl.addSpacing(8)
        sep2 = QFrame()
        sep2.setObjectName("sep")
        sep2.setFixedHeight(1)
        fl.addWidget(sep2)
        fl.addSpacing(10)

        ins_row = QHBoxLayout()
        ins_row.setSpacing(0)
        ins_lbl = QLabel("Insert after")
        ins_lbl.setFixedWidth(76)
        ins_lbl.setStyleSheet("color:#7a8299; font-size:11px;")
        ins_row.addWidget(ins_lbl)
        self._pos_edit = QLineEdit(str(n_events))
        self._pos_edit.setStyleSheet(
            "QLineEdit { background: transparent; border: none;"
            " border-bottom: 1px solid rgba(255,255,255,0.13);"
            " color: #eef0f5; font-size: 11px; padding: 1px 2px; }")
        self._pos_edit.setFixedWidth(50)
        self._pos_edit.setFixedHeight(18)
        self._pos_edit.setAlignment(Qt.AlignCenter)
        self._pos_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[0-9]*")))
        ins_row.addWidget(self._pos_edit)
        ins_row.addStretch()
        fl.addLayout(ins_row)

        fl.addSpacing(8)
        sep3 = QFrame()
        sep3.setObjectName("sep")
        sep3.setFixedHeight(1)
        fl.addWidget(sep3)
        fl.addSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("btnImport")
        cancel.setFixedHeight(26)
        cancel.setFixedWidth(70)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addSpacing(6)
        ok = QPushButton("Add")
        ok.setObjectName("btnRecord")
        ok.setFixedHeight(26)
        ok.setFixedWidth(70)
        ok.clicked.connect(self._on_ok)
        btn_row.addWidget(ok)
        btn_row.addStretch()
        fl.addLayout(btn_row)

    def _on_ok(self) -> None:
        try:
            self.result_ms = max(0, float(self._ms_edit.text() or "0"))
            try:
                self.result_pos = max(
                    0, min(self._n_events, int(self._pos_edit.text() or "0")))
            except ValueError:
                self.result_pos = self._n_events
            self.accept()
        except ValueError:
            pass

    def mousePressEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton:
            self._drag = (
                e.globalPosition().toPoint() - self.frameGeometry().topLeft())
            focused = self.focusWidget()
            if focused and isinstance(focused, QLineEdit):
                focused.clearFocus()
                self.setFocus()

    def mouseMoveEvent(self, e: object) -> None:
        if self._drag and e.buttons() == Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e: object) -> None:
        self._drag = None


class SettingsDlg(QDialog):
    setting_changed = Signal(str, object)

    def __init__(
        self,
        parent: QWidget,
        speed: float,
        loop: bool,
        loop_t: bool,
        loop_int: int,
        loop_n: int,
        loop_count_enabled: bool,
        rec_key: str,
        play_key: str,
        parent_cfg: Optional[dict] = None,
    ) -> None:
        if parent_cfg is None:
            parent_cfg = {}
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag: Optional[object] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 18)

        container = QWidget()
        container.setObjectName("mainContainer")
        container.setAttribute(Qt.WA_StyledBackground, True)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(40)
        sh.setColor(QColor(0, 0, 0, 200))
        sh.setOffset(0, 10)
        container.setGraphicsEffect(sh)
        outer.addWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tb = QWidget()
        tb.setObjectName("titleBar")
        tb.setAttribute(Qt.WA_StyledBackground, True)
        tb.setFixedHeight(34)
        self._tb = tb
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(12, 0, 8, 0)
        tbl.setSpacing(4)
        _ico_data = base64.b64decode(LOGO_B64)
        _pix2     = QPixmap()
        _pix2.loadFromData(_ico_data)
        logo_lbl = QLabel()
        logo_lbl.setPixmap(
            _pix2.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_lbl.setFixedSize(16, 16)
        tbl.addWidget(logo_lbl)
        tbl.addSpacing(5)
        ttl = QLabel("Settings")
        ttl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; font-weight:700; color:#eef0f5;")
        tbl.addWidget(ttl)
        tbl.addStretch()
        xb = QPushButton("\u2715")
        xb.setObjectName("btnClose")
        xb.setFixedSize(22, 22)
        xb.clicked.connect(self.accept)
        tbl.addWidget(xb)

        def _tb_press(e: object) -> None:
            if e.button() == Qt.LeftButton:
                self._drag = (
                    e.globalPosition().toPoint() - self.frameGeometry().topLeft())

        def _tb_move(e: object) -> None:
            if self._drag and e.buttons() == Qt.LeftButton:
                self.move(e.globalPosition().toPoint() - self._drag)

        def _tb_release(e: object) -> None:
            self._drag = None

        tb.mousePressEvent   = _tb_press
        tb.mouseMoveEvent    = _tb_move
        tb.mouseReleaseEvent = _tb_release
        root.addWidget(tb)

        sep0 = QFrame()
        sep0.setObjectName("sep")
        sep0.setFixedHeight(1)
        root.addWidget(sep0)

        body = QWidget()
        body.setObjectName("settingsBody")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 12, 14, 2)
        bl.setSpacing(8)
        root.addWidget(body)

        spd_card = self._card()
        sc = QVBoxLayout(spd_card)
        sc.setContentsMargins(12, 10, 12, 10)
        sc.setSpacing(8)
        sc.addWidget(self._cap("PLAYBACK SPEED"))
        sr = QHBoxLayout()
        sr.setSpacing(0)
        hint = QLabel("Playback speed")
        hint.setStyleSheet(
            f"font-family:{FONT}; font-size:12px; color:#eef0f5;")
        sr.addWidget(hint)
        sr.addSpacing(10)
        for _spd_val, _spd_lbl in ((1.0, "1×"), (2.0, "2×"), (3.0, "3×")):
            _btn = QPushButton(_spd_lbl)
            _btn.setObjectName("btnSpeedPreset")
            _btn.setFixedSize(28, 26)
            _btn.setCursor(Qt.PointingHandCursor)
            _btn.clicked.connect(
                lambda _=False, v=_spd_val: (
                    self.speed.setText(f"{v:.1f}"),
                    self.setting_changed.emit("speed", v),
                ))
            sr.addWidget(_btn)
            sr.addSpacing(4)
        sr.addStretch()
        self.speed = QLineEdit(f"{speed:.1f}")
        self.speed.setObjectName("keyInput")
        self.speed.setFixedSize(42, 26)
        self.speed.setAlignment(Qt.AlignCenter)
        self.speed.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"[0-9]*\.?[0-9]*")))

        def _speed_changed(v: str) -> None:
            try:
                self.setting_changed.emit("speed", float(v))
            except ValueError:
                pass

        self.speed.textChanged.connect(_speed_changed)
        sr.addWidget(self.speed)
        sc.addLayout(sr)
        bl.addWidget(spd_card)

        loop_card = self._card()
        lc = QVBoxLayout(loop_card)
        lc.setContentsMargins(12, 10, 12, 10)
        lc.setSpacing(7)
        lc.addWidget(self._cap("LOOP OPTIONS"))

        loop_row = QHBoxLayout()
        loop_row.setSpacing(0)
        loop_row.setContentsMargins(0, 0, 0, 0)
        loop_row.setAlignment(Qt.AlignVCenter)
        self.loop_cb = ToggleSwitch(checked=loop)
        self.loop_cb.toggled.connect(lambda v: self.setting_changed.emit("loop", v))
        loop_row.addWidget(self.loop_cb, 0, Qt.AlignVCenter)
        loop_row.addSpacing(10)
        loop_lbl = QLabel("Loop continuously")
        loop_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:12px; font-weight:400; color:#eef0f5;")
        loop_row.addWidget(loop_lbl, 0, Qt.AlignVCenter)
        loop_row.addStretch()
        lc.addLayout(loop_row)

        ln_row = QHBoxLayout()
        ln_row.setSpacing(0)
        ln_row.setContentsMargins(0, 0, 0, 0)
        ln_row.setAlignment(Qt.AlignVCenter)
        self.loop_count_cb = ToggleSwitch(checked=loop_count_enabled)
        self.loop_count_cb.toggled.connect(
            lambda v: self.setting_changed.emit("loop_count_enabled", v))
        ln_row.addWidget(self.loop_count_cb, 0, Qt.AlignVCenter)
        ln_row.addSpacing(10)
        ln_lbl = QLabel("Loop count")
        ln_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:12px; font-weight:400; color:#eef0f5;")
        ln_row.addWidget(ln_lbl, 0, Qt.AlignVCenter)
        ln_row.addStretch()
        self.loop_n_edit = QLineEdit(str(loop_n))
        self.loop_n_edit.setObjectName("keyInput")
        self.loop_n_edit.setFixedSize(42, 26)
        self.loop_n_edit.setAlignment(Qt.AlignCenter)
        self.loop_n_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[0-9]*")))
        self.loop_n_edit.setEnabled(loop_count_enabled)
        self.loop_count_cb.toggled.connect(self.loop_n_edit.setEnabled)

        def _on_loop_n_change(txt: str) -> None:
            try:
                v = max(0, int(txt))
                self.setting_changed.emit("loop_count", v)
            except ValueError:
                pass

        self.loop_n_edit.textChanged.connect(_on_loop_n_change)
        ln_row.addWidget(self.loop_n_edit, 0, Qt.AlignVCenter)
        lc.addLayout(ln_row)

        tr = QHBoxLayout()
        tr.setSpacing(0)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setAlignment(Qt.AlignVCenter)
        self.loop_t_cb = ToggleSwitch(checked=loop_t)
        self.loop_t_cb.toggled.connect(
            lambda v: self.setting_changed.emit("loop_timer", v))
        tr.addWidget(self.loop_t_cb, 0, Qt.AlignVCenter)
        tr.addSpacing(10)
        loop_t_lbl = QLabel("Loop on timer (min)")
        loop_t_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:12px; font-weight:400; color:#eef0f5;")
        tr.addWidget(loop_t_lbl, 0, Qt.AlignVCenter)
        tr.addStretch()
        self.interval = QLineEdit(str(loop_int))
        self.interval.setObjectName("keyInput")
        self.interval.setFixedSize(42, 26)
        self.interval.setAlignment(Qt.AlignCenter)
        self.interval.setEnabled(loop_t)
        self.loop_t_cb.toggled.connect(self.interval.setEnabled)

        def _on_interval_change(txt: str) -> None:
            try:
                v = max(1, int(txt))
                self.setting_changed.emit("loop_interval", v)
            except ValueError:
                pass

        self.interval.textChanged.connect(_on_interval_change)
        tr.addWidget(self.interval, 0, Qt.AlignVCenter)
        lc.addLayout(tr)

        def _mutex_loop(others):
            def handler(v: bool) -> None:
                if v:
                    for cb in others:
                        cb.setChecked(False)
            return handler

        self.loop_cb.toggled.connect(
            _mutex_loop([self.loop_count_cb, self.loop_t_cb]))
        self.loop_count_cb.toggled.connect(
            _mutex_loop([self.loop_cb, self.loop_t_cb]))
        self.loop_t_cb.toggled.connect(
            _mutex_loop([self.loop_cb, self.loop_count_cb]))
        bl.addWidget(loop_card)

        hot_card = self._card()
        hc = QVBoxLayout(hot_card)
        hc.setContentsMargins(12, 10, 12, 10)
        hc.setSpacing(7)
        hc.addWidget(self._cap("HOTKEYS"))

        hr_both = QHBoxLayout()
        hr_both.setSpacing(0)
        hr_both.setAlignment(Qt.AlignVCenter)
        for i, (lbl_text, key_val, attr_name, sig_key) in enumerate([
            ("Record",   rec_key,  "rec_edit",  "rec_key"),
            ("Playback", play_key, "play_edit", "play_key"),
        ]):
            if i == 1:
                div = QFrame()
                div.setFrameShape(QFrame.VLine)
                div.setFixedWidth(1)
                div.setStyleSheet(
                    "background: rgba(255,255,255,0.09); border: none;"
                    " margin-top: 2px; margin-bottom: 2px;")
                hr_both.addSpacing(10)
                hr_both.addWidget(div)
                hr_both.addSpacing(10)
            pair = QHBoxLayout()
            pair.setSpacing(6)
            lb = QLabel(lbl_text)
            lb.setStyleSheet(
                f"font-family:{FONT}; font-size:12px; color:#eef0f5;")
            pair.addWidget(lb)
            edit = KeyCapture(key_val)
            edit.key_changed.connect(
                lambda v, k=sig_key: self.setting_changed.emit(k, v))
            setattr(self, attr_name, edit)
            pair.addWidget(edit)
            hr_both.addLayout(pair)
        hc.addLayout(hr_both)

        def _dedup_keys(other_edit: object, clear_sig: str) -> object:
            def handler(v: str) -> None:
                if v and other_edit.key() == v:
                    other_edit._key = ""
                    other_edit.setText("")
                    self.setting_changed.emit(clear_sig, "")
            return handler

        self.rec_edit.key_changed.connect(
            _dedup_keys(self.play_edit, "play_key"))
        self.play_edit.key_changed.connect(
            _dedup_keys(self.rec_edit, "rec_key"))
        bl.addWidget(hot_card)

        wh_card = self._card()
        wc = QVBoxLayout(wh_card)
        wc.setContentsMargins(12, 10, 12, 10)
        wc.setSpacing(8)
        wc.addWidget(self._cap("DISCORD WEBHOOK"))

        wh_url_r = QHBoxLayout()
        wh_url_r.setContentsMargins(0, 0, 0, 0)
        wh_url_r.setSpacing(10)
        wh_url_lbl = QLabel("Webhook URL")
        wh_url_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; color:#7a8299;")
        wh_url_r.addWidget(wh_url_lbl)
        self.wh_url_edit = QLineEdit(parent_cfg.get("webhook_url", ""))
        self.wh_url_edit.setObjectName("keyInput")
        self.wh_url_edit.setFixedHeight(24)
        self.wh_url_edit.setPlaceholderText(
            "https://discord.com/api/webhooks/\u2026")
        self.wh_url_edit.setMinimumWidth(140)
        self.wh_url_edit.setMaximumWidth(140)
        self.wh_url_edit.textChanged.connect(
            lambda v: self.setting_changed.emit("webhook_url", v))
        wh_url_r.addWidget(self.wh_url_edit)

        _anim_in = QPropertyAnimation(self.wh_url_edit, b"maximumWidth")
        _anim_in.setDuration(180)
        _anim_in.setEasingCurve(QEasingCurve.OutCubic)

        def _wh_expand() -> None:
            wh_url_lbl.setVisible(False)
            _anim_in.stop()
            _anim_in.setStartValue(self.wh_url_edit.maximumWidth())
            _anim_in.setEndValue(body.contentsRect().width())
            _anim_in.start()

        def _wh_collapse() -> None:
            _anim_in.stop()
            _anim_in.setStartValue(self.wh_url_edit.maximumWidth())
            _anim_in.setEndValue(140)
            _anim_in.start()
            wh_url_lbl.setVisible(True)

        def _wh_focus_in(
            ev: object, _orig: object = self.wh_url_edit.focusInEvent
        ) -> None:
            _orig(ev)
            _wh_expand()

        def _wh_focus_out(
            ev: object, _orig: object = self.wh_url_edit.focusOutEvent
        ) -> None:
            _orig(ev)
            _wh_collapse()

        self.wh_url_edit.focusInEvent  = _wh_focus_in
        self.wh_url_edit.focusOutEvent = _wh_focus_out
        wc.addLayout(wh_url_r)

        elapsed_row = QHBoxLayout()
        elapsed_row.setSpacing(12)
        self.wh_elapsed_sw = ToggleSwitch(
            checked=parent_cfg.get("webhook_show_elapsed", "1") == "1")
        self.wh_elapsed_sw.toggled.connect(
            lambda v: self.setting_changed.emit("webhook_show_elapsed", v))
        elapsed_lbl = QLabel("Show time elapsed")
        elapsed_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; color:#7a8299;")
        elapsed_row.addWidget(self.wh_elapsed_sw)
        elapsed_row.addWidget(elapsed_lbl)
        elapsed_row.addStretch()
        wc.addLayout(elapsed_row)

        cycles_row = QHBoxLayout()
        cycles_row.setSpacing(12)
        self.wh_cycles_sw = ToggleSwitch(
            checked=parent_cfg.get("webhook_show_cycles", "1") == "1")
        self.wh_cycles_sw.toggled.connect(
            lambda v: self.setting_changed.emit("webhook_show_cycles", v))
        cycles_lbl = QLabel("Show cycle count")
        cycles_lbl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; color:#7a8299;")
        cycles_row.addWidget(self.wh_cycles_sw)
        cycles_row.addWidget(cycles_lbl)
        cycles_row.addStretch()
        wc.addLayout(cycles_row)
        bl.addWidget(wh_card)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        discord_btn = QPushButton("Discord")
        discord_btn.setObjectName("btnDiscord")
        discord_btn.setFixedHeight(30)
        discord_btn.setCursor(Qt.PointingHandCursor)
        discord_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://discord.com/invite/2fraBuhe3m")))
        btn_row.addWidget(discord_btn)

        guide_btn = QPushButton("Guide")
        guide_btn.setObjectName("btnGuide")
        guide_btn.setFixedHeight(30)
        guide_btn.setCursor(Qt.PointingHandCursor)
        guide_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://moris.software/guides/macromaker")))
        btn_row.addWidget(guide_btn)

        lbl_style = (
            f"font-family:{FONT}; font-size:10px; color:#3a3f4d;"
            " margin-top: 1px;")

        credits_lbl = QLabel("Made with \u2665 by moris and tim")
        credits_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        credits_lbl.setStyleSheet(lbl_style)

        version_lbl = QLabel("v1.2.0")
        version_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        version_lbl.setStyleSheet(lbl_style)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(0)
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.addWidget(credits_lbl)
        footer_row.addStretch()
        footer_row.addWidget(version_lbl)

        bottom = QVBoxLayout()
        bottom.setSpacing(0)
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.addLayout(btn_row)
        bottom.addLayout(footer_row)
        bl.addLayout(bottom)

    def _card(self) -> QWidget:
        w = QWidget()
        w.setObjectName("settingsCard")
        w.setAttribute(Qt.WA_StyledBackground, True)
        return w

    def _sep(self) -> QFrame:
        f = QFrame()
        f.setObjectName("sep")
        f.setFixedHeight(1)
        return f

    def _cap(self, t: str) -> QLabel:
        label = QLabel(t)
        label.setStyleSheet(
            f"font-family:{FONT}; font-size:10px; font-weight:700;"
            " color:#7a8299; letter-spacing:1.4px;")
        return label

    def keyPressEvent(self, e: object) -> None:
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            focused = self.focusWidget()
            if focused and isinstance(focused, QLineEdit):
                focused.clearFocus()
            return
        super().keyPressEvent(e)

    def mousePressEvent(self, e: object) -> None:
        focused = self.focusWidget()
        if focused and isinstance(focused, QLineEdit):
            focused.clearFocus()

    def mouseMoveEvent(self, e: object) -> None:
        pass

    def mouseReleaseEvent(self, e: object) -> None:
        pass



class TitleBar(QWidget):
    pin_toggled = Signal(bool)
    cog_clicked = Signal()

    def __init__(self, win: QWidget) -> None:
        super().__init__()
        self.setObjectName("titleBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(34)
        self._win    = win
        self._drag: Optional[object] = None
        self._pinned = False

        lo = QHBoxLayout(self)
        lo.setContentsMargins(12, 0, 8, 0)
        lo.setSpacing(4)

        logo = QLabel()
        _ico_data = base64.b64decode(LOGO_B64)
        _pix = QPixmap()
        _pix.loadFromData(QByteArray(_ico_data))
        logo.setPixmap(
            _pix.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setFixedSize(16, 16)
        lo.addWidget(logo)
        lo.addSpacing(4)

        title = QLabel("moris macro maker - m\u00b3")
        title.setStyleSheet(
            f"font-family: {FONT}; font-size:11px; font-weight:700; color:#eef0f5;")
        lo.addWidget(title)
        lo.addStretch()

        self._pin = QPushButton()
        self._pin.setObjectName("btnPin")
        self._pin.setFixedSize(22, 22)
        self._pin.setIcon(_svg_icon(SVG_PIN, 14, "#52596b"))
        self._pin.setIconSize(QSize(14, 14))
        self._pin.clicked.connect(self._toggle_pin)
        lo.addWidget(self._pin)

        cog = QPushButton()
        cog.setObjectName("btnCog")
        cog.setFixedSize(22, 22)
        cog.setIcon(_svg_icon(SVG_COG, 13, "#52596b"))
        cog.setIconSize(QSize(13, 13))
        cog.clicked.connect(self.cog_clicked)
        lo.addWidget(cog)

        mn = MinimizeBtn()
        mn.clicked.connect(win.showMinimized)
        lo.addWidget(mn)

        cl = QPushButton("\u2715")
        cl.setObjectName("btnClose")
        cl.setFixedSize(22, 22)
        cl.clicked.connect(win.close)
        lo.addWidget(cl)

    def _toggle_pin(self) -> None:
        self._pinned = not self._pinned
        self._pin.setObjectName("btnPinOn" if self._pinned else "btnPin")
        self._pin.style().unpolish(self._pin)
        self._pin.style().polish(self._pin)
        if self._pinned:
            self._pin.setIcon(_svg_icon(SVG_PIN_ON, 14, "#78c8ff"))
        else:
            self._pin.setIcon(_svg_icon(SVG_PIN, 14, "#52596b"))
        self.pin_toggled.emit(self._pinned)

    def mousePressEvent(self, e: object) -> None:
        if e.button() == Qt.LeftButton:
            self._drag = (
                e.globalPosition().toPoint() - self._win.frameGeometry().topLeft())

    def mouseMoveEvent(self, e: object) -> None:
        if self._drag and e.buttons() == Qt.LeftButton:
            self._win.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e: object) -> None:
        self._drag = None


class _InsertPreview(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, _: object) -> None:
        from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
        from PySide6.QtCore import QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 5, 5)
        p.fillPath(path, QColor(120, 200, 255, 12))
        pen = QPen(QColor(120, 200, 255, 110))
        pen.setWidthF(1.0)
        pen.setDashPattern([4, 4])
        p.setPen(pen)
        p.drawPath(path)
        p.end()


class SequencePanel(QWidget):
    events_changed = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("seqPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._events: list       = []
        self._rows:   list       = []
        self._selected: set      = set()
        self._clipboard: list    = []
        self._drag_idx:    Optional[int] = None
        self._drag_ghost:  Optional[QWidget] = None
        self._drag_origin_y: int = 0
        self._drop_idx:    Optional[int] = None
        self._drag_anims:  dict  = {}
        self._drag_offsets: list = []
        self._drag_row_h:  int   = 0
        self._drag_vp:     Optional[QWidget] = None
        self._drag_timer:  Optional[QTimer]  = None
        self._drag_scroll_speed: int = 0
        self._preview_widget: Optional[QWidget] = None

        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        hbar  = QWidget()
        hbar.setFixedHeight(28)
        hbl   = QHBoxLayout(hbar)
        hbl.setContentsMargins(14, 0, 14, 0)
        clear_btn = QPushButton("\u2715 Clear all")
        clear_btn.setObjectName("btnSeqDel")
        clear_btn.setFixedHeight(16)
        clear_btn.clicked.connect(self._clear)
        hbl.addWidget(clear_btn, 0, Qt.AlignVCenter)
        hbl.addStretch()

        add_input_btn = QPushButton("+ Input")
        add_input_btn.setObjectName("btnSeqLink")
        add_input_btn.setFixedHeight(16)
        add_input_btn.clicked.connect(self._add_input)
        hbl.addWidget(add_input_btn)
        hbl.addSpacing(6)

        add_wait_btn = QPushButton("+ Wait")
        add_wait_btn.setObjectName("btnSeqLink")
        add_wait_btn.setFixedHeight(16)
        add_wait_btn.clicked.connect(self._add_wait)
        hbl.addWidget(add_wait_btn)
        hbl.addSpacing(10)

        self._count_lbl = QLabel("0 events")
        self._count_lbl.setStyleSheet("color:#52596b; font-size:10px;")
        hbl.addWidget(self._count_lbl)
        vl.addWidget(hbar)

        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFixedHeight(1)
        vl.addWidget(sep)

        from PySide6.QtWidgets import QScrollArea, QScrollBar
        self._scroll = QScrollArea()
        self._scroll.setObjectName("seqScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            "QScrollArea#seqScroll { border: none; background: transparent; }")

        self._inner   = QWidget()
        self._inner_l = QVBoxLayout(self._inner)
        self._inner_l.setContentsMargins(10, 8, 10, 8)
        self._inner_l.setSpacing(4)
        self._inner_l.addStretch()
        self._scroll.setWidget(self._inner)
        vl.addWidget(self._scroll, 1)

        self._overlay_sb = QScrollBar(Qt.Vertical, self._scroll)
        self._overlay_sb.setFixedWidth(4)
        self._overlay_sb.setStyleSheet(
            "QScrollBar:vertical { width: 4px; background: transparent; border: none; }"
            "QScrollBar::handle:vertical { background: rgba(120,200,255,0.40);"
            " border-radius: 2px; min-height: 18px; }"
            "QScrollBar::handle:vertical:hover { background: rgba(120,200,255,0.70); }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical"
            " { background: transparent; }")
        self._overlay_sb.hide()

        _real = self._scroll.verticalScrollBar()
        _real.rangeChanged.connect(self._on_sb_range_changed)
        _real.valueChanged.connect(self._overlay_sb.setValue)
        self._overlay_sb.valueChanged.connect(_real.setValue)

    def _position_overlay_sb(self) -> None:
        w = self._overlay_sb.width()
        h = self._scroll.height()
        corner_r = 12
        self._overlay_sb.setGeometry(self._scroll.width() - w - 3, 0, w, h - corner_r)
        self._overlay_sb.raise_()

    def _on_sb_range_changed(self, min_val: int, max_val: int) -> None:
        real = self._scroll.verticalScrollBar()
        self._overlay_sb.setRange(min_val, max_val)
        self._overlay_sb.setPageStep(real.pageStep())
        self._overlay_sb.setSingleStep(real.singleStep())
        visible = max_val > min_val
        if visible:
            self._position_overlay_sb()
        self._overlay_sb.setVisible(visible)

    def set_events(self, events: list) -> None:
        self._events = [dict(e) for e in events]
        self._rebuild()

    def _rebuild(self) -> None:
        if self._preview_widget is not None:
            self._inner_l.removeWidget(self._preview_widget)
        for row in self._rows:
            self._inner_l.removeWidget(row)
            row.deleteLater()
        self._rows = []

        for i, ev in enumerate(self._events):
            row = EventRow(i, ev)
            row.deleted.connect(self._on_delete)
            row.changed.connect(self._on_changed)
            row.drag_start.connect(self._on_drag_start)
            row.row_clicked.connect(self._on_row_clicked)
            self._inner_l.insertWidget(self._inner_l.count() - 1, row)
            self._rows.append(row)

        self._selected = {i for i in self._selected if i < len(self._rows)}
        for i in self._selected:
            self._rows[i].set_selected(True)

        nc    = sum(1 for e in self._events if e["type"] == "mouse_click")
        nk    = sum(1 for e in self._events
                    if e["type"] in ("key_press", "key_release"))
        shown = len(self._rows)
        self._count_lbl.setText(
            f"{nc} clicks  \u2022  {nk} keys  \u2022  {shown} total")

    def _clear(self) -> None:
        self._events = []
        self._rebuild()
        autosave([])
        self.events_changed.emit([])

    def _add_input(self) -> None:
        if getattr(self, "_open_input_dlg", None) is not None:
            self._open_input_dlg.raise_()
            return
        dlg = AddInputDialog(self, len(self._events))
        self._open_input_dlg = dlg

        def _accepted() -> None:
            self._open_input_dlg = None
            self._hide_insert_preview()
            ev = dlg.result_event
            if ev is None:
                return
            pos = dlg.result_pos
            self._events.insert(pos, ev)
            self._rebuild()
            self.events_changed.emit(list(self._events))

        def _rejected() -> None:
            self._open_input_dlg = None
            self._hide_insert_preview()

        dlg.pos_preview.connect(self._show_insert_preview)
        dlg.accepted.connect(_accepted)
        dlg.rejected.connect(_rejected)
        dlg.show()

    def _add_wait(self) -> None:
        if getattr(self, "_open_wait_dlg", None) is not None:
            self._open_wait_dlg.raise_()
            return
        dlg = WaitDialog(self, len(self._events))
        self._open_wait_dlg = dlg

        def _accepted() -> None:
            self._open_wait_dlg = None
            ms  = dlg.result_ms
            pos = dlg.result_pos
            if pos > 0 and self._events:
                t = self._events[min(pos - 1, len(self._events) - 1)].get("time", 0.0)
            elif self._events:
                t = self._events[0].get("time", 0.0)
            else:
                t = 0.0
            ev = {"type": "wait", "duration": ms / 1000.0, "time": t}
            self._events.insert(pos, ev)
            self._rebuild()
            self.events_changed.emit(list(self._events))

        dlg.accepted.connect(_accepted)
        dlg.rejected.connect(lambda: setattr(self, "_open_wait_dlg", None))
        dlg.show()

    def _on_drag_start(self, idx: int, global_pos: object) -> None:
        from PySide6.QtCore import QPoint
        src_row = self._rows[idx]
        if src_row._expanded:
            src_row._toggle_expand()
            QApplication.processEvents()

        src_row.setObjectName("seqRowSel")
        src_row.style().unpolish(src_row)
        src_row.style().polish(src_row)

        self._drag_idx     = idx
        self._drop_idx     = idx
        self._drag_anims   = {}
        self._drag_offsets = [0] * len(self._rows)
        src_row.set_dragging(True)

        vp      = self._scroll.viewport()
        vp_pos  = vp.mapFromGlobal(global_pos)
        sb      = self._scroll.verticalScrollBar().value()
        row_h   = src_row.height()
        spacing = self._inner_l.spacing()
        margin_x = self._inner_l.contentsMargins().left()
        margin_y = self._inner_l.contentsMargins().top()
        row_w    = self._inner.width() - margin_x * 2

        self._drag_row_h  = row_h + spacing
        self._drag_base_y: list = []
        for row in self._rows:
            inner_pos = row.mapTo(self._inner, QPoint(0, 0))
            self._drag_base_y.append(inner_pos.y())

        self._drag_cur_y    = {i: float(self._drag_base_y[i])
                               for i in range(len(self._rows))}
        self._drag_target_y = dict(self._drag_cur_y)

        total_content_h = (
            margin_y
            + len(self._rows) * row_h
            + max(0, len(self._rows) - 1) * spacing
            + margin_y
        )
        self._drag_scroll_offset = float(sb)
        self._drag_scroll_max = float(
            max(0, total_content_h - int(self._scroll.viewport().height())))

        self._drag_vp_widgets: list = []
        for i, row in enumerate(self._rows):
            row.setParent(vp)
            row.setFixedWidth(row_w)
            y = self._drag_base_y[i] - sb
            row.move(margin_x, y)
            row.show()
            self._drag_vp_widgets.append(row)

        ghost = QWidget(vp)
        ghost.setFixedSize(row_w, row_h)
        ghost.setStyleSheet(
            "background: rgba(120,200,255,0.15);"
            " border: 1px solid rgba(120,200,255,0.45);"
            " border-radius: 6px;")
        ghost.setAttribute(Qt.WA_TransparentForMouseEvents)
        lbl = QLabel(_ev_label(self._events[idx]), ghost)
        lbl.setStyleSheet(
            "color:#78c8ff; font-size:11px; font-weight:600; padding-left:36px;")
        lbl.setGeometry(0, 0, ghost.width(), ghost.height())
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        ghost.move(margin_x, vp_pos.y() - row_h // 2)
        ghost.raise_()
        ghost.show()
        self._drag_ghost     = ghost
        self._drag_margin_x  = margin_x
        self._drag_margin_y  = margin_y
        self._drag_row_w     = row_w

        self._rows[idx].hide()

        self._drag_timer = QTimer()
        self._drag_timer.setInterval(16)
        self._drag_timer.timeout.connect(self._drag_tick)
        self._drag_timer.start()
        self._drag_last_vp_y      = vp_pos.y()
        self._drag_last_global    = global_pos
        self._drag_vp_screen_top  = None

        vp.setMouseTracking(True)
        vp.grabMouse()
        vp.installEventFilter(self)
        self._drag_vp = vp

    def _drag_tick(self) -> None:
        did_scroll = False
        if self._drag_idx is not None and self._drag_vp is not None:
            vp_y = getattr(self, "_drag_last_vp_y", None)
            if vp_y is not None:
                vp_y   = float(vp_y)
                vp_h   = float(self._drag_vp.height())
                scroll_zone  = 40
                scroll_speed = 0.0
                if vp_y > vp_h - scroll_zone:
                    ratio = min(1.0, (vp_y - (vp_h - scroll_zone)) / scroll_zone)
                    scroll_speed = ratio * 8.0 + 1.0
                elif vp_y < scroll_zone:
                    ratio = min(1.0, (scroll_zone - vp_y) / scroll_zone)
                    scroll_speed = -(ratio * 8.0 + 1.0)

                if scroll_speed != 0.0:
                    old_offset = self._drag_scroll_offset
                    new_offset = max(
                        0.0, min(self._drag_scroll_max, old_offset + scroll_speed))
                    if abs(new_offset - old_offset) > 0.01:
                        did_scroll = True
                        self._drag_scroll_offset = new_offset
                        sb      = new_offset
                        ghost_y = max(0.0, min(vp_h, vp_y))
                        if self._drag_ghost:
                            self._drag_ghost.move(
                                self._drag_margin_x,
                                int(ghost_y) - self._drag_ghost.height() // 2)
                        inner_y = ghost_y + sb - self._drag_margin_y
                        self._update_drop_target(inner_y)
                        for i, row in enumerate(self._drag_vp_widgets):
                            if i == self._drag_idx:
                                continue
                            self._drag_cur_y[i] = float(self._drag_target_y[i])
                            row.move(self._drag_margin_x,
                                     int(self._drag_cur_y[i] - sb))
                        if self._drag_ghost:
                            self._drag_ghost.raise_()

        if not did_scroll:
            sb = getattr(self, "_drag_scroll_offset", 0.0)
            for i, row in enumerate(self._drag_vp_widgets):
                if i == self._drag_idx:
                    continue
                cur = self._drag_cur_y[i]
                tgt = float(self._drag_target_y[i])
                if abs(cur - tgt) > 0.5:
                    self._drag_cur_y[i] = cur + (tgt - cur) * 0.22
                else:
                    self._drag_cur_y[i] = tgt
                row.move(self._drag_margin_x, int(self._drag_cur_y[i] - sb))
            if self._drag_ghost:
                self._drag_ghost.raise_()

    def eventFilter(self, obj: object, e: object) -> bool:
        from PySide6.QtCore import QEvent
        if obj is getattr(self, "_drag_vp", None):
            if e.type() == QEvent.MouseMove:
                self._drag_last_global   = e.globalPosition().toPoint()
                self._drag_vp_screen_top = (
                    e.globalPosition().y() - e.position().y())
                self._drag_mouse_move(e)
                return True
            elif e.type() == QEvent.MouseButtonRelease:
                self._drag_mouse_release(e)
                return True
        return super().eventFilter(obj, e)

    def _drag_mouse_move(self, e: object) -> None:
        if self._drag_idx is None:
            return
        vp_y = e.position().y()
        self._drag_last_vp_y = vp_y
        sb    = getattr(self, "_drag_scroll_offset", 0.0)
        vp_h  = float(self._drag_vp.height())
        ghost_y = max(0.0, min(vp_h, float(vp_y)))
        gh = self._drag_ghost
        gh.move(self._drag_margin_x, int(ghost_y) - gh.height() // 2)
        gh.raise_()
        inner_y = ghost_y + sb - self._drag_margin_y
        self._update_drop_target(inner_y)

    def _update_drop_target(self, inner_y: float) -> None:
        new_drop = len(self._rows) - 1
        for i in range(len(self._rows)):
            base = self._drag_base_y[i]
            if inner_y < base + self._drag_row_h // 2:
                new_drop = i
                break
        if new_drop != self._drop_idx:
            self._drop_idx = new_drop
            from_idx = self._drag_idx
            rh = self._drag_row_h
            for i in range(len(self._rows)):
                if i == from_idx:
                    continue
                if from_idx < new_drop:
                    shift = -rh if (from_idx < i <= new_drop) else 0
                else:
                    shift = rh if (new_drop <= i < from_idx) else 0
                self._drag_target_y[i] = self._drag_base_y[i] + shift

    def _drag_mouse_release(self, e: object) -> None:
        if self._drag_idx is None:
            return
        self._drag_timer.stop()
        self._drag_timer = None

        from_idx     = self._drag_idx
        to_idx       = self._drop_idx if self._drop_idx is not None else from_idx
        self._drag_idx  = None
        self._drop_idx  = None
        saved_scroll    = int(self._drag_scroll_offset)

        self._drag_scroll_speed   = 0
        self._drag_last_vp_y      = None
        self._drag_last_global    = None
        self._drag_vp_screen_top  = None
        self._drag_scroll_offset  = 0.0
        vp = self._drag_vp
        vp.releaseMouse()
        vp.setMouseTracking(False)
        vp.removeEventFilter(self)
        self._drag_vp = None

        if self._drag_ghost:
            self._drag_ghost.hide()
            ghost = self._drag_ghost
            self._drag_ghost = None
        else:
            ghost = None

        sb = self._scroll.verticalScrollBar()

        if from_idx != to_idx:
            ev = self._events.pop(from_idx)
            self._events.insert(to_idx, ev)

        for row in self._rows:
            row.hide()
            row.setParent(None)
        self._rows = []

        if ghost:
            ghost.setParent(None)
            ghost.deleteLater()

        self._rebuild()

        nc = sum(1 for e in self._events if e["type"] == "mouse_click")
        nk = sum(1 for e in self._events
                 if e["type"] in ("key_press", "key_release"))
        self._count_lbl.setText(
            f"{nc} clicks  \u2022  {nk} keys  \u2022  {len(self._rows)} total")

        QTimer.singleShot(
            0, lambda: QTimer.singleShot(0, lambda: sb.setValue(saved_scroll)))
        self.events_changed.emit(list(self._events))

        landed = to_idx
        if 0 <= landed < len(self._rows):
            row = self._rows[landed]
            row.setObjectName("seqRowSel")
            row.style().unpolish(row)
            row.style().polish(row)
            QTimer.singleShot(2000, lambda r=row: (
                r.setObjectName("seqRow"),
                r.style().unpolish(r),
                r.style().polish(r),
            ))

    def mouseMoveEvent(self, e: object) -> None:
        pass

    def mouseReleaseEvent(self, e: object) -> None:
        pass

    def _show_insert_preview(self, pos: int) -> None:
        if not self._rows:
            self._hide_insert_preview()
            return
        pos = max(0, min(len(self._rows), pos))
        row_h = self._rows[0].height()

        if self._preview_widget is None:
            pw = _InsertPreview()
            pw.setFixedHeight(row_h)
            self._preview_widget = pw
        else:
            self._inner_l.removeWidget(self._preview_widget)

        self._inner_l.insertWidget(pos, self._preview_widget)
        self._preview_widget.show()

    def _hide_insert_preview(self) -> None:
        if self._preview_widget is not None:
            self._inner_l.removeWidget(self._preview_widget)
            self._preview_widget.setParent(None)
            self._preview_widget = None

    def _on_row_clicked(self, idx: int, modifiers: int) -> None:
        ctrl  = bool(modifiers & Qt.ControlModifier.value)
        shift = bool(modifiers & Qt.ShiftModifier.value)
        if ctrl:
            if idx in self._selected:
                self._selected.discard(idx)
                self._rows[idx].set_selected(False)
            else:
                self._selected.add(idx)
                self._rows[idx].set_selected(True)
        elif shift and self._selected:
            last = max(self._selected)
            lo, hi = min(last, idx), max(last, idx)
            for i in range(lo, hi + 1):
                if i < len(self._rows):
                    self._selected.add(i)
                    self._rows[i].set_selected(True)
        else:
            for i in list(self._selected):
                if i < len(self._rows):
                    self._rows[i].set_selected(False)
            self._selected = {idx}
            self._rows[idx].set_selected(True)
        self.setFocus()

    def keyPressEvent(self, e: object) -> None:
        key  = e.key()
        mods = e.modifiers()
        ctrl = bool(mods.value & Qt.ControlModifier.value)
        if key == Qt.Key_C and ctrl:
            self._clipboard = [dict(self._events[i])
                               for i in sorted(self._selected)
                               if i < len(self._events)]
        elif key == Qt.Key_V and ctrl:
            if self._clipboard:
                at = max(self._selected) + 1 if self._selected else len(self._events)
                for i, ev in enumerate(self._clipboard):
                    self._events.insert(at + i, dict(ev))
                self._selected = set(range(at, at + len(self._clipboard)))
                self._rebuild()
                self.events_changed.emit(list(self._events))
        elif key == Qt.Key_A and ctrl:
            self._selected = set(range(len(self._rows)))
            for row in self._rows:
                row.set_selected(True)
        elif key in (Qt.Key_Delete, Qt.Key_Backspace) and self._selected:
            for i in sorted(self._selected, reverse=True):
                if 0 <= i < len(self._events):
                    self._events.pop(i)
            self._selected.clear()
            self._rebuild()
            self.events_changed.emit(list(self._events))
        else:
            super().keyPressEvent(e)

    def _on_delete(self, idx: int) -> None:
        if 0 <= idx < len(self._events):
            self._selected.clear()
            self._events.pop(idx)
            self._rebuild()
            self.events_changed.emit(list(self._events))

    def _on_changed(self, idx: int, ev: dict) -> None:
        if 0 <= idx < len(self._events):
            self._events[idx] = ev
            self.events_changed.emit(list(self._events))



def _mac_check_accessibility() -> bool:
    try:
        import ctypes
        lib = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        lib.AXIsProcessTrusted.restype  = ctypes.c_int
        lib.AXIsProcessTrusted.argtypes = []
        return lib.AXIsProcessTrusted() != 0
    except Exception:
        return True


def _mac_check_input_monitoring() -> bool:
    try:
        import Quartz
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown),
            lambda proxy, type_, event, refcon: event,
            None,
        )
        if tap is None:
            return False
        Quartz.CGEventTapEnable(tap, False)
        return True
    except Exception:
        pass
    try:
        import ctypes
        IOKit = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/IOKit.framework/IOKit"
        )
        IOKit.IOHIDCheckAccess.restype  = ctypes.c_int
        IOKit.IOHIDCheckAccess.argtypes = [ctypes.c_uint32]
        return IOKit.IOHIDCheckAccess(1) == 1
    except Exception:
        return False


class MacPermissionsDialog(QDialog):
    def __init__(self, parent: QWidget, has_accessibility: bool, has_input_monitoring: bool) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag: Optional[object] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 18)

        container = QWidget()
        container.setObjectName("mainContainer")
        container.setAttribute(Qt.WA_StyledBackground, True)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(40)
        sh.setColor(QColor(0, 0, 0, 200))
        sh.setOffset(0, 10)
        container.setGraphicsEffect(sh)
        outer.addWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tb = QWidget()
        tb.setObjectName("titleBar")
        tb.setAttribute(Qt.WA_StyledBackground, True)
        tb.setFixedHeight(34)
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(12, 0, 8, 0)
        tbl.setSpacing(4)
        _pix = QPixmap()
        _pix.loadFromData(base64.b64decode(LOGO_B64))
        logo = QLabel()
        logo.setPixmap(_pix.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setFixedSize(16, 16)
        tbl.addWidget(logo)
        tbl.addSpacing(5)
        ttl = QLabel("Permissions Required")
        ttl.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; font-weight:700; color:#eef0f5;")
        tbl.addWidget(ttl)
        tbl.addStretch()
        xb = QPushButton("\u2715")
        xb.setObjectName("btnClose")
        xb.setFixedSize(22, 22)
        xb.clicked.connect(self.accept)
        tbl.addWidget(xb)

        def _tb_press(e: object) -> None:
            if e.button() == Qt.LeftButton:
                self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        def _tb_move(e: object) -> None:
            if self._drag and e.buttons() == Qt.LeftButton:
                self.move(e.globalPosition().toPoint() - self._drag)
        def _tb_release(e: object) -> None:
            self._drag = None
        tb.mousePressEvent   = _tb_press
        tb.mouseMoveEvent    = _tb_move
        tb.mouseReleaseEvent = _tb_release
        root.addWidget(tb)

        body = QWidget()
        body.setAttribute(Qt.WA_StyledBackground, False)
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 14, 16, 16)
        bl.setSpacing(12)

        desc = QLabel(
            "macro maker needs the following macOS permissions to work correctly.\n"
            "Grant them in System Settings, then quit and relaunch the app."
        )
        desc.setObjectName("dlgSubLabel")
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"font-family:{FONT}; font-size:11px; color:#9aa0b0; line-height:150%;")
        bl.addWidget(desc)

        def _perm_row(label: str, sublabel: str, granted: bool, url: str) -> QWidget:
            from PySide6.QtGui import QDesktopServices, QCursor
            from PySide6.QtCore import QUrl
            row = QWidget()
            row.setAttribute(Qt.WA_StyledBackground, True)
            bg_idle  = "rgba(255,255,255,0.03)"
            bg_hover = "rgba(255,255,255,0.07)"
            border   = "rgba(255,255,255,0.07)"
            row.setStyleSheet(
                f"QWidget {{ background: {bg_idle};"
                f" border: 1px solid {border}; border-radius: 8px; }}")
            if not granted:
                row.setCursor(QCursor(Qt.PointingHandCursor))

            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 10, 12, 10)
            rl.setSpacing(10)

            dot = QLabel("\u2713" if granted else "\u2192")
            dot.setFixedSize(18, 18)
            dot.setAlignment(Qt.AlignCenter)
            dot_color = "#3ddc84" if granted else "#89dfff"
            dot.setStyleSheet(
                f"font-family:{FONT}; font-size:11px; font-weight:700;"
                f" color:{dot_color};"
                f" background: {'rgba(61,220,132,0.12)' if granted else 'rgba(137,223,255,0.10)'};"
                f" border-radius: 9px;")
            rl.addWidget(dot, 0, Qt.AlignVCenter)

            txt = QVBoxLayout()
            txt.setSpacing(1)
            name_lbl = QLabel(label)
            name_lbl.setStyleSheet(
                f"font-family:{FONT}; font-size:11px; font-weight:600; color:#eef0f5;"
                " background:transparent; border:none;")
            sub_lbl = QLabel(sublabel if granted else sublabel + " — click to open")
            sub_lbl.setStyleSheet(
                f"font-family:{FONT}; font-size:10px;"
                f" color:{'#7a7a7a' if granted else '#89dfff'};"
                " background:transparent; border:none;")
            txt.addWidget(name_lbl)
            txt.addWidget(sub_lbl)
            rl.addLayout(txt, 1)

            if not granted:
                def _enter(e, r=row, bg=bg_hover, b=border):
                    r.setStyleSheet(
                        f"QWidget {{ background: {bg};"
                        f" border: 1px solid {b}; border-radius: 8px; }}")
                def _leave(e, r=row, bg=bg_idle, b=border):
                    r.setStyleSheet(
                        f"QWidget {{ background: {bg};"
                        f" border: 1px solid {b}; border-radius: 8px; }}")
                def _click(e, u=url):
                    QDesktopServices.openUrl(QUrl(u))
                row.enterEvent    = _enter
                row.leaveEvent    = _leave
                row.mousePressEvent = _click

            return row

        bl.addWidget(_perm_row(
            "Accessibility",
            "Required for keyboard & mouse playback",
            has_accessibility,
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        ))
        bl.addWidget(_perm_row(
            "Input Monitoring",
            "Required for keyboard recording",
            has_input_monitoring,
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
        ))

        hint = QLabel("If the app doesn't appear in the list, click\u00a0+ in the bottom\u00a0left to add it manually.")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(
            f"font-family:{FONT}; font-size:10px; color:#52596b;")
        bl.addWidget(hint)

        root.addWidget(body)
        self.setMinimumWidth(340)



class MainWindow(QWidget):
    _SEQ_MIN_H: int = SEQ_MIN_H

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._events: list             = []
        self._recording: bool          = False
        self._paused: bool             = False
        self._playing: bool            = False
        self._play_worker: Optional[PlayWorker] = None
        self._play_thread: Optional[QThread]    = None
        self._loop_timer:  Optional[QTimer]     = None
        self._listener:    Optional[MacroRecorder] = None
        self._seq_expanded: bool = False
        self._seq_custom_h: int  = 0
        self._resize_dragging: bool = False
        self._resize_start_y:  int  = 0
        self._resize_start_h:  int  = 0

        cfg = reg_load()
        self._speed    = float(cfg.get("speed",        str(DEFAULT_SPEED)))
        self._loop     = cfg.get("loop",               "0") == "1"
        self._loop_t   = cfg.get("loop_timer",         "0") == "1"
        self._loop_int = int(cfg.get("loop_interval",  str(DEFAULT_LOOP_INTERVAL)))
        self._loop_n             = int(cfg.get("loop_count",         str(DEFAULT_LOOP_COUNT)))
        self._loop_count_enabled = cfg.get("loop_count_enabled", "0") == "1"
        self._rec_key  = cfg.get("rec_key",  DEFAULT_REC_KEY)
        self._play_key = cfg.get("play_key", DEFAULT_PLAY_KEY)
        self._wh_show_elapsed = cfg.get("webhook_show_elapsed", "1") == "1"
        self._wh_show_cycles  = cfg.get("webhook_show_cycles",  "1") == "1"

        self._build()
        if _OK:
            self._start_listener()
        self._events = autoload()
        ensure_mmr_icon(MMR_ICO_B64)
        self._sync()
        QTimer.singleShot(0, self._fix_size)
        if sys.platform == "darwin":
            QTimer.singleShot(800, self._check_mac_permissions)

    def _start_listener(self) -> None:
        if self._listener:
            self._listener.stop()
        if hasattr(self, "_listener_thread") and self._listener_thread:
            self._listener_thread.quit()
            self._listener_thread.wait()
        self._listener        = MacroRecorder()
        self._listener_thread = QThread()
        self._listener.moveToThread(self._listener_thread)
        self._listener.set_hotkeys(self._rec_key, self._play_key)
        self._listener.hk_rec.connect(self._hk_rec,       Qt.QueuedConnection)
        self._listener.hk_rec_hold.connect(self._hk_rec_hold, Qt.QueuedConnection)
        self._listener.hk_play.connect(self._hk_play,     Qt.QueuedConnection)
        self._listener.rec_event.connect(self._on_ev, Qt.QueuedConnection)
        self._listener_thread.started.connect(self._listener.start)
        self._listener_thread.start()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        container = QWidget()
        container.setObjectName("mainContainer")
        container.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(container)
        self._container = container

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tb = TitleBar(self)
        tb.pin_toggled.connect(self._on_pin)
        tb.cog_clicked.connect(self._open_settings)
        root.addWidget(tb)

        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        body = QWidget()
        bl   = QHBoxLayout(body)
        bl.setContentsMargins(14, 10, 14, 10)
        bl.setSpacing(0)
        root.addWidget(body)

        col1 = QWidget()
        col1.setFixedWidth(106)
        c1l  = QVBoxLayout(col1)
        c1l.setContentsMargins(0, 0, 14, 0)
        c1l.setSpacing(6)
        c1l.setAlignment(Qt.AlignVCenter)

        self._status_box = QWidget()
        self._status_box.setObjectName("statusBox")
        self._status_box.setFixedSize(92, 32)
        self._status_box.setAttribute(Qt.WA_StyledBackground, True)
        sb_l = QHBoxLayout(self._status_box)
        sb_l.setContentsMargins(8, 0, 8, 0)
        sb_l.setSpacing(6)
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._dot.setAttribute(Qt.WA_StyledBackground, True)
        self._dot.setStyleSheet("background:#52596b; border-radius:4px;")
        sb_l.addWidget(self._dot, 0, Qt.AlignVCenter)
        self._stat = QLabel("Standby")
        self._stat.setObjectName("statusText")
        sb_l.addWidget(self._stat, 1, Qt.AlignVCenter)
        c1l.addWidget(self._status_box)

        self._expand_btn = EditButton()
        self._expand_btn.setFixedSize(92, 32)
        self._expand_btn.clicked.connect(self._toggle_seq)
        c1l.addWidget(self._expand_btn)

        bl.addWidget(col1)
        bl.addWidget(self._vdiv())

        col2 = QWidget()
        col2.setFixedWidth(196)
        c2l  = QVBoxLayout(col2)
        c2l.setContentsMargins(14, 0, 14, 0)
        c2l.setSpacing(6)
        c2l.setAlignment(Qt.AlignVCenter)

        self._rec_btn = RecButton()
        self._rec_btn.setText(self._rec_label())
        self._rec_btn.setFixedHeight(32)
        self._rec_btn.setFixedWidth(168)
        self._rec_btn.clicked.connect(self._toggle_rec)
        c2l.addWidget(self._rec_btn)

        self._play_btn = PlayButton(self._play_key)
        self._play_btn.setFixedHeight(32)
        self._play_btn.setFixedWidth(168)
        self._play_btn.clicked.connect(self._toggle_play)
        c2l.addWidget(self._play_btn)

        bl.addWidget(col2)
        bl.addWidget(self._vdiv())

        col3 = QWidget()
        col3.setFixedWidth(106)
        c3l  = QVBoxLayout(col3)
        c3l.setContentsMargins(14, 0, 0, 0)
        c3l.setSpacing(6)
        c3l.setAlignment(Qt.AlignVCenter)

        self._imp = QPushButton("\u2193  Import")
        self._imp.setObjectName("btnImport")
        self._imp.setFixedHeight(32)
        self._imp.setFixedWidth(92)
        self._imp.clicked.connect(self._import)
        c3l.addWidget(self._imp)

        self._exp = QPushButton("\u2191  Export")
        self._exp.setObjectName("btnExport")
        self._exp.setFixedHeight(32)
        self._exp.setFixedWidth(92)
        self._exp.clicked.connect(self._export)
        c3l.addWidget(self._exp)

        bl.addWidget(col3)

        self._toast_wrap = QWidget()
        self._toast_wrap.setFixedHeight(0)
        self._toast_wrap.setAttribute(Qt.WA_StyledBackground, True)
        self._toast_wrap.setStyleSheet(
            "QWidget { background: transparent; border-top: none; }")
        tw_l = QVBoxLayout(self._toast_wrap)
        tw_l.setContentsMargins(6, 3, 6, 3)
        tw_l.setSpacing(0)

        toast_row = QWidget()
        toast_row.setAttribute(Qt.WA_StyledBackground, True)
        toast_row.setStyleSheet(
            "QWidget { background: rgba(255,255,255,0.07);"
            " border: 1px solid rgba(255,255,255,0.10);"
            " border-radius: 6px; }")
        toast_row.setFixedHeight(24)
        tr_l = QHBoxLayout(toast_row)
        tr_l.setContentsMargins(0, 0, 0, 0)
        tr_l.setSpacing(0)
        tr_l.setAlignment(Qt.AlignCenter)

        self._toast_label_left = QLabel("")
        self._toast_label_left.setStyleSheet(
            f"font-family:{FONT}; font-size:10px; font-weight:400;"
            " color:#52596b; background:transparent; border:none; padding:0;")
        tr_l.addWidget(self._toast_label_left)
        tr_l.addSpacing(4)

        self._toast_label_val = QLabel("")
        self._toast_label_val.setStyleSheet(
            f"font-family:{FONT}; font-size:10px; font-weight:700;"
            " color:#78c8ff; background:transparent; border:none; padding:0;")
        tr_l.addWidget(self._toast_label_val)
        tw_l.addWidget(toast_row)

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._toast_hide)
        self._toast_duration = 3000

        root.addWidget(self._toast_wrap)

        self._seq_panel = SequencePanel()
        self._seq_panel.setFixedHeight(280)
        self._seq_panel.setVisible(False)
        self._seq_panel.events_changed.connect(self._on_seq_changed)
        self._root_layout = root
        root.addWidget(self._seq_panel)

        self._resize_handle = _ResizeHandle(self)
        self._resize_handle.resize_press.connect(self._on_resize_press)
        self._resize_handle.resize_move.connect(self._on_resize_move)
        self._resize_handle.resize_release.connect(self._on_resize_release)
        self._resize_handle.setVisible(False)
        root.addWidget(self._resize_handle)

    def _toast_show(self, label: str, value: str) -> None:
        self._toast_timer.stop()
        self._toast_label_left.setText(label)
        self._toast_label_val.setText(value)
        TOAST_H = 32
        if self._toast_wrap.height() == 0:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.resize(self.width(), self.height() + TOAST_H)
        self._toast_wrap.setFixedHeight(TOAST_H)
        self._toast_timer.start(self._toast_duration)

    def _toast_hide(self) -> None:
        TOAST_H = self._toast_wrap.height()
        self._toast_wrap.setFixedHeight(0)
        cur_h = self.height()
        self.resize(self.width(), cur_h - TOAST_H)
        if not self._seq_expanded:
            self.setFixedHeight(self._base_h)



    def _hk_rec(self) -> None:
        if self._recording:
            self._stop_rec()
        else:
            self._start_rec()

    def _hk_rec_hold(self) -> None:
        if not self._recording:
            return
        if self._paused:
            self._resume_rec()
        else:
            self._pause_rec()

    def _hk_play(self) -> None:
        self._stop_all() if self._playing else self._start_play()

    def _toggle_play(self) -> None:
        self._stop_all() if self._playing else self._start_play()

    def _toggle_rec(self) -> None:
        if self._recording:
            self._stop_rec()
        else:
            self._start_rec()

    def _start_rec(self) -> None:
        if self._playing:
            self._stop_all()
        if self._seq_expanded:
            self._seq_expanded = False
            self._expand_btn.set_expanded(False)
            self._seq_panel.setVisible(False)
            self._resize_handle.hide()
            self.setFixedHeight(self._base_h)
        self._events    = []
        self._recording = True
        self._paused    = False
        if self._listener:
            self._listener.start_recording()
        self._set_status("Recording\u2026", "#ff4b69")
        self._sync()

    def _stop_rec(self) -> None:
        self._recording = False
        self._paused    = False
        if self._listener:
            self._listener.stop_recording()
        self._set_status("Standby", "#52596b")
        autosave(self._events)
        if self._seq_expanded:
            self._seq_panel.set_events(self._seq_events())
        self._sync()

    def _pause_rec(self) -> None:
        self._paused = True
        if self._listener:
            self._listener.pause_recording()
        self._set_status("Paused", "#ffaa32")
        self._sync()

    def _resume_rec(self) -> None:
        self._paused = False
        if self._listener:
            self._listener.resume_recording()
        self._set_status("Recording\u2026", "#ff4b69")
        self._sync()

    def _on_ev(self, ev: dict) -> None:
        self._events.append(ev)
        if self._seq_expanded:
            self._seq_panel.set_events(self._seq_events())

    def _seq_events(self) -> list:
        out: list           = []
        seq_id_counter: int = getattr(self, "_seq_id_counter", 0)
        group_id: int       = 0
        prev_recorded_move  = False
        for ev in self._events:
            tp = ev["type"]
            if tp == "mouse_move":
                if ev.get("recorded"):
                    if not prev_recorded_move:
                        group_id += 1
                    prev_recorded_move = True
                    ev["_group_id"] = group_id
                    if (out and out[-1]["type"] == "mouse_move"
                            and out[-1].get("recorded")):
                        out[-1] = ev
                    else:
                        out.append(ev)
                else:
                    prev_recorded_move = False
                    ev.pop("_group_id", None)
                    out.append(ev)
            else:
                prev_recorded_move = False
                if "_seq_id" not in ev:
                    ev["_seq_id"] = seq_id_counter
                    seq_id_counter += 1
                out.append(ev)
        self._seq_id_counter = seq_id_counter
        return out

    def _start_play(self) -> None:
        if not self._events:
            return
        if self._recording:
            self._stop_rec()
        self._playing          = True
        self._play_cycle_count = 0
        self._play_wall_start  = __import__("time").perf_counter()
        if self._listener:
            self._listener.set_playing(True)
        self._set_status("Playing\u2026", "#32e68c")
        self._run_once()
        self._sync()

    def _run_once(self) -> None:
        self._play_cycle_count = getattr(self, "_play_cycle_count", 0) + 1
        self._play_thread = QThread()
        self._play_worker = PlayWorker(
            self._events,
            self._speed,
            self._listener,
            loop_count        = self._play_cycle_count,
            wh_show_elapsed   = getattr(self, "_wh_show_elapsed", True),
            wh_show_cycles    = getattr(self, "_wh_show_cycles",  True),
            global_wall_start = getattr(self, "_play_wall_start", None),
        )
        self._play_worker.moveToThread(self._play_thread)
        self._play_thread.started.connect(self._play_worker.run)
        self._play_worker.finished.connect(self._play_done)
        self._play_thread.start()

    def _play_done(self) -> None:
        self._play_thread.quit()
        self._play_thread.wait()
        if not self._playing:
            return
        if self._loop:
            self._run_once()
        elif self._loop_count_enabled:
            if self._play_cycle_count >= self._loop_n:
                self._playing = False
                if self._listener:
                    self._listener.set_playing(False)
                self._set_status("Standby", "#52596b")
                self._sync()
                return
            self._run_once()
        elif self._loop_t:
            self._set_status("Waiting\u2026", "#ffaa32")
            self._loop_timer = QTimer(self)
            self._loop_timer.setSingleShot(True)
            self._loop_timer.timeout.connect(
                lambda: (
                    self._set_status("Playing\u2026", "#32e68c"),
                    self._run_once(),
                ))
            self._loop_timer.start(self._loop_int * 60 * 1000)
        else:
            self._playing = False
            if self._listener:
                self._listener.set_playing(False)
            self._set_status("Standby", "#52596b")
            self._sync()

    def _stop_all(self) -> None:
        if self._loop_timer:
            self._loop_timer.stop()
            self._loop_timer = None
        if self._recording:
            self._recording = False
            self._paused    = False
            if self._listener:
                self._listener.stop_recording()
        if self._playing:
            self._playing = False
            if self._listener:
                self._listener.set_playing(False)
            if self._play_worker:
                self._play_worker.stop()
            if self._play_thread:
                self._play_thread.quit()
                self._play_thread.wait()
        self._set_status("Standby", "#52596b")
        self._sync()

    def _rec_label(self) -> str:
        return f"\u2b24  Record  [{self._rec_key}]"

    def _set_status(self, text: str, color: str) -> None:
        self._stat.setText(text)
        self._stat.setStyleSheet(
            f"font-family: {FONT}; font-size:11px; font-weight:700; color:{color};")
        self._dot.setStyleSheet(f"background:{color}; border-radius:4px;")

    def _sync(self) -> None:
        idle = not self._recording and not self._playing
        has  = bool(self._events)
        self._rec_btn.setEnabled(not self._playing)
        self._play_btn.setEnabled(not self._recording and (has or self._playing))
        self._imp.setEnabled(idle)
        self._exp.setEnabled(idle and has)
        if self._recording:
            if self._paused:
                self._rec_btn.set_paused(True)
                self._rec_btn.setText(f"Paused  [{self._rec_key}]")
            else:
                self._rec_btn.set_paused(False)
                self._rec_btn.setText(f"\u25a0  Stop  [{self._rec_key}]")
            self._expand_btn.setEnabled(False)
        else:
            self._rec_btn.set_paused(False)
            self._rec_btn.setText(self._rec_label())
            self._expand_btn.setEnabled(True)
        self._play_btn.set_playing(self._playing)

    def _on_pin(self, on: bool) -> None:
        if sys.platform in ("win32", "darwin"):
            from ..utils.platform_helpers import set_window_topmost
            set_window_topmost(int(self.winId()), on)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, on)
            self.show()

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import", "",
            "Moris Macro (*.mmr);;All files (*.*)")
        if not path:
            return
        try:
            with open(path, "rb") as f:
                header = f.read(4)
            if header != MMR_MAGIC:
                return
            d = mmr_load(path)
            if not isinstance(d, list):
                raise ValueError("unexpected data format")
            self._events = d
            autosave(self._events)
            if self._seq_expanded:
                self._seq_panel.set_events(self._seq_events())
            self._sync()
            self._toast_show("imported", os.path.basename(path))
        except Exception:
            pass

    def _export(self) -> None:
        if not self._events:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "recording.mmr",
            "Moris Macro (*.mmr)")
        if not path:
            return
        if not path.endswith(".mmr"):
            path += ".mmr"
        try:
            mmr_save(self._events, path)
            ensure_mmr_icon(MMR_ICO_B64)
            self._toast_show("exported", os.path.basename(path))
        except Exception:
            pass

    def _open_settings(self) -> None:
        if self._listener:
            self._listener.set_hotkeys("", "")
        dlg = SettingsDlg(
            self, self._speed, self._loop, self._loop_t,
            self._loop_int, self._loop_n, self._loop_count_enabled,
            self._rec_key, self._play_key,
            parent_cfg=reg_load(),
        )
        dlg.setting_changed.connect(self._on_setting)
        dlg.exec()
        self._save_settings()
        if self._listener:
            self._listener.set_hotkeys(self._rec_key, self._play_key)

    def _on_setting(self, key: str, value: object) -> None:
        if key == "speed":
            try:
                self._speed = float(value)
            except (ValueError, TypeError):
                pass
        elif key == "loop":
            self._loop = bool(value)
        elif key == "loop_timer":
            self._loop_t = bool(value)
        elif key == "loop_interval":
            try:
                self._loop_int = max(1, int(value))
            except (ValueError, TypeError):
                pass
        elif key == "loop_count":
            try:
                self._loop_n = max(0, int(value))
            except (ValueError, TypeError):
                pass
        elif key == "loop_count_enabled":
            self._loop_count_enabled = bool(value)
        elif key == "webhook_url":
            self._webhook_url = str(value)
        elif key == "webhook_show_elapsed":
            self._wh_show_elapsed = bool(value)
        elif key == "webhook_show_cycles":
            self._wh_show_cycles = bool(value)
        elif key in ("rec_key", "play_key"):
            if key == "rec_key":
                self._rec_key = str(value)
            else:
                self._play_key = str(value)
            self._play_btn.set_key(self._play_key)
            self._sync()

    def _save_settings(self) -> None:
        cfg = reg_load()
        reg_save({
            "speed":                   self._speed,
            "loop":                    "1" if self._loop   else "0",
            "loop_timer":              "1" if self._loop_t else "0",
            "loop_interval":           self._loop_int,
            "loop_count":              self._loop_n,
            "loop_count_enabled":      "1" if self._loop_count_enabled else "0",
            "rec_key":                 self._rec_key,
            "play_key":                self._play_key,
            "webhook_url":             getattr(
                self, "_webhook_url", cfg.get("webhook_url", "")),
            "webhook_show_elapsed":    "1" if getattr(
                self, "_wh_show_elapsed", True) else "0",
            "webhook_show_cycles":     "1" if getattr(
                self, "_wh_show_cycles", True) else "0",
        })

    def _set_container_radius(self, bottom_rounded: bool) -> None:
        if bottom_rounded:
            self._container.setStyleSheet("")
        else:
            self._container.setStyleSheet(
                "QWidget#mainContainer { background: #121212; border-radius: 12px;"
                " border-bottom-left-radius: 0px;"
                " border-bottom-right-radius: 0px; }")

    def _toggle_seq(self) -> None:
        if self._recording:
            return
        self._seq_expanded = not self._seq_expanded
        self._expand_btn.set_expanded(self._seq_expanded)

        if not hasattr(self, "_slide_timer"):
            self._slide_timer   = QTimer(self)
            self._slide_timer.setInterval(11)
            self._slide_timer.timeout.connect(self._slide_tick)
            self._slide_current = 0.0
            self._slide_target  = 0.0
            self._slide_start   = 0.0
            self._slide_t       = 1.0

        if self._seq_expanded:
            self._seq_panel.set_events(self._seq_events())
            self._seq_panel.setMinimumHeight(0)
            self._seq_panel.setMaximumHeight(16777215)
            self._seq_panel.setFixedHeight(0)
            self._seq_panel.show()
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self._set_container_radius(False)
            self._slide_start     = 0.0
            self._slide_current   = 0.0
            self._slide_target    = float(max(
                self._SEQ_MIN_H,
                self._seq_custom_h if self._seq_custom_h else 280,
            ))
            self._slide_expanding = True
            self._slide_t         = 0.0
            self._slide_timer.start()
        else:
            self._resize_handle.hide()
            self._slide_start     = float(self._seq_panel.height())
            self._slide_current   = self._slide_start
            self._slide_target    = 0.0
            self._slide_expanding = False
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self._slide_t = 0.0
            self._slide_timer.start()

    def _slide_tick(self) -> None:
        self._slide_t = min(1.0, self._slide_t + 0.055)
        t    = self._slide_t
        ease = 1.0 - (1.0 - t) * (1.0 - t) * (1.0 - t)
        self._slide_current = (
            self._slide_start
            + (self._slide_target - self._slide_start) * ease
        )
        seq_h = int(self._slide_current)
        self._seq_panel.setFixedHeight(seq_h)
        self.resize(self.width(), self._base_h + seq_h)

        if self._slide_t >= 1.0:
            self._slide_timer.stop()
            if self._slide_expanding:
                final_h = int(self._slide_target)
                self._seq_panel.setMinimumHeight(self._SEQ_MIN_H)
                self._seq_panel.setMaximumHeight(16777215)
                self._seq_panel.setFixedHeight(final_h)
                self.setMinimumHeight(self._base_h + self._SEQ_MIN_H)
                self.resize(self.width(), self._base_h + final_h)
                self._resize_handle.show()
                self._set_container_radius(True)
            else:
                self._seq_panel.hide()
                self._seq_panel.setMaximumHeight(16777215)
                self._set_container_radius(True)
                self.setFixedHeight(
                    self._base_h + self._toast_wrap.height())

    def _on_resize_press(self, global_pos: object) -> None:
        self._resize_dragging = True
        self._resize_start_y  = global_pos.y()
        self._resize_start_h  = self.height()

    def _on_resize_move(self, global_pos: object) -> None:
        if not self._resize_dragging:
            return
        delta    = global_pos.y() - self._resize_start_y
        new_h    = max(self._base_h + self._SEQ_MIN_H, self._resize_start_h + delta)
        seq_h    = new_h - self._base_h
        self._seq_custom_h = seq_h
        self._seq_panel.setFixedHeight(seq_h)
        self.resize(self.width(), new_h)

    def _on_resize_release(self) -> None:
        self._resize_dragging = False

    def _on_seq_changed(self, events: list) -> None:
        if not events:
            self._events = []
            autosave(self._events)
            self._sync()
            return

        raw_moves = [e for e in self._events if e["type"] == "mouse_move"]

        group_frames: dict = {}
        for ev in raw_moves:
            gid = ev.get("_group_id")
            if gid is not None and ev.get("recorded"):
                if gid not in group_frames:
                    group_frames[gid] = []
                group_frames[gid].append(ev)

        for ev in events:
            if ev.get("type") == "mouse_move" and ev.get("recorded"):
                gid = ev.get("_group_id")
                if gid in group_frames:
                    last = group_frames[gid][-1]
                    for k in ("x", "y", "move_duration", "move_mode"):
                        if k in ev:
                            last[k] = ev[k]

        merged: list = []
        for ev in events:
            tp = ev.get("type")
            if tp == "mouse_move":
                gid = ev.get("_group_id")
                if gid is not None and gid in group_frames:
                    merged.extend(group_frames[gid])
                else:

                    merged.append(dict(ev))
            else:
                merged.append(dict(ev))

        self._events = merged
        autosave(self._events)
        self._sync()

    def _vdiv(self) -> QFrame:
        f = QFrame()
        f.setObjectName("divV")
        f.setFrameShape(QFrame.VLine)
        f.setFixedWidth(1)
        f.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        return f

    def _check_mac_permissions(self) -> None:
        has_acc = _mac_check_accessibility()
        has_im  = _mac_check_input_monitoring()
        if not has_acc or not has_im:
            dlg = MacPermissionsDialog(self, has_acc, has_im)
            dlg.exec()

    def _fix_size(self) -> None:
        self._base_h = self.height()
        self.setFixedWidth(self.width())
        self.setFixedHeight(self._base_h)

    def closeEvent(self, e: object) -> None:
        autosave(self._events)
        if self._listener:
            self._listener.stop()
        if hasattr(self, "_listener_thread") and self._listener_thread:
            self._listener_thread.quit()
            self._listener_thread.wait()
        super().closeEvent(e)