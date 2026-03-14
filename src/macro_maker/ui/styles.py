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

"""QSS stylesheet for the application.

Import :data:`SS` and pass it to ``QApplication.setStyleSheet()``.
"""

from ..utils.constants import FONT_CONFIG

FONT = FONT_CONFIG.family

SS: str = f"""
QWidget {{
    background: transparent;
    color: #eef0f5;
    font-family: {FONT};
    font-size: 12px;
}}
QWidget#mainContainer {{
    background: #13131c;
    border-radius: 12px;
}}
QWidget#titleBar {{
    background: #13131c;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.10);
}}
QFrame#sep  {{ background: rgba(255,255,255,0.08); border: none; }}
QFrame#divV {{ background: rgba(255,255,255,0.08); border: none; }}

QLabel#heading {{
    font-size: 10px; font-weight: 700;
    color: #7a8299; letter-spacing: 1.4px;
    font-family: {FONT};
}}
QLabel#statusText {{ font-size: 11px; font-weight: 700; color: #52596b; font-family: {FONT}; }}
QLabel#infoText   {{ font-size: 10px; color: #52596b; font-family: {FONT}; }}

QPushButton:focus {{ outline: none; }}

QPushButton#btnClose {{
    background: transparent; border: none;
    color: #52596b; font-size: 11px; font-weight: 700;
    border-radius: 5px; padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnClose:hover {{ background: rgba(255,90,112,0.20); color: #ff5a70; }}

QPushButton#btnPin {{
    background: transparent; border: none;
    color: #52596b; font-size: 11px;
    border-radius: 5px; padding: 0px;
}}
QPushButton#btnPin:hover {{ background: rgba(255,255,255,0.07); }}

QPushButton#btnPinOn {{
    background: rgba(120,200,255,0.15); border: none;
    color: #78c8ff; font-size: 11px;
    border-radius: 5px; padding: 0px;
}}
QPushButton#btnPinOn:hover {{ background: rgba(120,200,255,0.26); }}

QPushButton#btnCog {{
    background: transparent; border: none;
    color: #52596b; font-size: 13px;
    border-radius: 5px; padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnCog:hover {{ background: rgba(255,255,255,0.07); color: #eef0f5; }}

QPushButton#btnRecord {{
    background: rgba(255,75,105,0.11);
    border: 1px solid rgba(255,75,105,0.32);
    color: #ff4b69;
    font-size: 11px; font-weight: 700;
    border-radius: 7px;
    padding: 0px 10px;
    text-align: center;
    font-family: {FONT};
}}
QPushButton#btnRecord:hover   {{ background: rgba(255,75,105,0.21); border-color: rgba(255,75,105,0.55); }}
QPushButton#btnRecord:pressed {{ background: rgba(255,75,105,0.32); }}
QPushButton#btnRecord:disabled {{
    background: rgba(255,75,105,0.04); border-color: rgba(255,75,105,0.10);
    color: rgba(255,75,105,0.28);
}}

QPushButton#btnStop {{
    background: rgba(255,170,50,0.09);
    border: 1px solid rgba(255,170,50,0.30);
    color: #ffaa32;
    font-size: 11px; font-weight: 700;
    border-radius: 7px;
    padding: 0px 10px;
    font-family: {FONT};
}}
QPushButton#btnStop:hover   {{ background: rgba(255,170,50,0.19); border-color: rgba(255,170,50,0.55); }}
QPushButton#btnStop:pressed {{ background: rgba(255,170,50,0.29); }}
QPushButton#btnStop:disabled {{
    background: rgba(255,170,50,0.03); border-color: rgba(255,170,50,0.10);
    color: rgba(255,170,50,0.25);
}}

QPushButton#btnImport, QPushButton#btnExport {{
    background: rgba(120,200,255,0.07);
    border: 1px solid rgba(120,200,255,0.22);
    color: #78c8ff;
    font-size: 11px; font-weight: 600;
    border-radius: 7px;
    padding: 0px 10px;
    font-family: {FONT};
}}
QPushButton#btnImport:hover, QPushButton#btnExport:hover {{
    background: rgba(120,200,255,0.16); border-color: rgba(120,200,255,0.45);
}}
QPushButton#btnImport:pressed, QPushButton#btnExport:pressed {{
    background: rgba(120,200,255,0.25);
}}
QPushButton#btnImport:disabled, QPushButton#btnExport:disabled {{
    background: rgba(120,200,255,0.02); border-color: rgba(120,200,255,0.08);
    color: rgba(120,200,255,0.22);
}}

QPushButton#btnDiscord {{
    background: rgba(88,101,242,0.12);
    border: 1px solid rgba(88,101,242,0.35);
    color: #8b9cf4;
    font-size: 11px; font-weight: 600;
    border-radius: 7px;
    padding: 0px 10px;
    font-family: {FONT};
}}
QPushButton#btnDiscord:hover {{
    background: rgba(88,101,242,0.22); border-color: rgba(88,101,242,0.60);
}}
QPushButton#btnDiscord:pressed {{
    background: rgba(88,101,242,0.32);
}}

QFrame#dlgFrame {{
    background: #13131c;
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 12px;
}}
QDoubleSpinBox, QSpinBox {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.13);
    color: #eef0f5;
    font-family: {FONT};
    font-size: 12px;
    padding: 3px 7px; border-radius: 6px; min-height: 24px;
}}
QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: #78c8ff; }}
QDoubleSpinBox::up-button, QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid rgba(255,255,255,0.10);
    border-top-right-radius: 6px;
    background: rgba(255,255,255,0.04);
}}
QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover {{
    background: rgba(255,255,255,0.10);
}}
QDoubleSpinBox::up-button:pressed, QSpinBox::up-button:pressed {{
    background: rgba(255,255,255,0.16);
}}
QDoubleSpinBox::down-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid rgba(255,255,255,0.10);
    border-bottom-right-radius: 6px;
    background: rgba(255,255,255,0.04);
}}
QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
    background: rgba(255,255,255,0.10);
}}
QDoubleSpinBox::down-button:pressed, QSpinBox::down-button:pressed {{
    background: rgba(255,255,255,0.16);
}}
QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{
    width: 0px; height: 0px;
}}
QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{
    width: 0px; height: 0px;
}}

QLineEdit#keyInput {{
    background: #0a0a12;
    border: 1px solid rgba(255,255,255,0.13);
    color: #eef0f5;
    font-family: {FONT};
    font-size: 12px; font-weight: 600;
    padding: 2px 5px; border-radius: 6px;
}}
QLineEdit#keyInput:focus {{ border-color: #78c8ff; background: #0d0d1a; }}
QLabel#dlgLabel {{
    color: #eef0f5;
    font-family: {FONT};
    font-size: 12px;
}}
QLabel#dlgSubLabel {{
    color: #52596b;
    font-family: {FONT};
    font-size: 11px;
}}
QLabel#dlgHeading {{
    font-size: 10px; font-weight: 700;
    color: #7a8299; letter-spacing: 1.4px;
    font-family: {FONT};
}}

QWidget#seqPanel {{
    background: #0e0e16;
    border-top: 1px solid rgba(255,255,255,0.07);
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}}
QScrollArea#seqScroll {{
    background: transparent;
    border: none;
}}
QWidget#seqRow {{
    background: rgba(255,255,255,0.03);
    border-left: 2px solid rgba(255,255,255,0.10);
    border-top: 1px solid rgba(255,255,255,0.05);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    border-right: none;
}}
QWidget#seqRowSel {{
    background: rgba(120,200,255,0.07);
    border-left: 2px solid rgba(120,200,255,0.60);
    border-top: 1px solid rgba(120,200,255,0.15);
    border-bottom: 1px solid rgba(120,200,255,0.15);
    border-right: none;
}}
QPushButton#btnSeqDel {{
    background: transparent; border: none;
    color: #52596b; font-size: 10px; font-weight: 600;
    padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnSeqDel:hover {{ color: #ff5a70; background: transparent; }}
QLabel#btnSeqClose {{
    background: transparent;
    color: #52596b; font-size: 10px; font-weight: 600;
    padding: 0px;
    font-family: {FONT};
}}
QLabel#btnSeqClose:hover {{ color: #ff5a70; background: transparent; }}
QWidget#statusBox {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 7px;
}}
QPushButton#btnEdit {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    color: #9aa3b8;
    font-size: 11px; font-weight: 600;
    border-radius: 7px;
    font-family: {FONT};
}}
QPushButton#btnEdit:hover {{ background: rgba(255,255,255,0.09); color: #c8cfdf; }}
QPushButton#btnEdit:disabled {{ color: #2a2d3a; background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.05); }}
QPushButton#btnSeqLink {{
    background: transparent;
    border: none;
    color: #52596b;
    font-size: 10px; font-weight: 600;
    padding: 0px 2px;
    font-family: {FONT};
}}
QPushButton#btnSeqLink:hover {{
    color: #9aa3b8;
}}
QPushButton#btnInlineEdit {{
    background: transparent;
    border: none;
    color: #52596b;
    font-size: 10px; font-weight: 600;
    padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnInlineEdit:hover {{ color: #9aa3b8; }}
QPushButton#btnExpand {{
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.16);
    color: #9aa3b8;
    font-size: 10px; font-weight: 600;
    border-radius: 4px; padding: 0px 4px;
    font-family: {FONT};
}}
QPushButton#btnExpand:hover {{
    background: rgba(255,255,255,0.13);
    border-color: rgba(255,255,255,0.28);
    color: #c8cfdf;
}}
QPushButton#btnExpand:pressed {{
    background: rgba(255,255,255,0.19);
}}
QComboBox {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.13);
    color: #eef0f5;
    font-family: {FONT};
    font-size: 11px;
    padding: 1px 6px; border-radius: 5px; min-height: 22px;
}}
QComboBox:focus {{ border-color: #78c8ff; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: #1a1a28; border: 1px solid rgba(255,255,255,0.13);
    color: #eef0f5; selection-background-color: rgba(120,200,255,0.18);
}}
QLineEdit#seqEdit {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.13);
    color: #eef0f5;
    font-family: {FONT};
    font-size: 11px;
    padding: 1px 6px; border-radius: 5px; min-height: 22px;
}}
QLineEdit#seqEdit:focus {{ border-color: #78c8ff; }}
"""
