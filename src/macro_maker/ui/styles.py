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

from ..utils.constants import FONT_CONFIG

FONT = FONT_CONFIG.family

SS: str = f"""
QWidget {{
    background: transparent;
    color: #f0f0f0;
    font-family: {FONT};
    font-size: 12px;
}}
QWidget#mainContainer {{
    background: #121212;
    border-radius: 12px;
}}
QWidget#titleBar {{
    background: #0a0a0a;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}}
QFrame#sep  {{ background: rgba(255,255,255,0.07); border: none; }}
QFrame#divV {{ background: rgba(255,255,255,0.07); border: none; }}

QLabel#heading {{
    font-size: 10px; font-weight: 700;
    color: #89dfff; letter-spacing: 1.4px;
    text-transform: uppercase;
    font-family: {FONT};
}}
QLabel#statusText {{ font-size: 11px; font-weight: 700; color: #7a7a7a; font-family: {FONT}; }}
QLabel#infoText   {{ font-size: 10px; color: #7a7a7a; font-family: {FONT}; }}

QPushButton:focus {{ outline: none; }}

QPushButton#btnClose {{
    background: transparent; border: none;
    color: #7a7a7a; font-size: 11px; font-weight: 700;
    border-radius: 5px; padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnClose:hover {{ background: rgba(255,90,112,0.18); color: #ff5a70; }}

QPushButton#btnPin {{
    background: transparent; border: none;
    color: #7a7a7a; font-size: 11px;
    border-radius: 5px; padding: 0px;
}}
QPushButton#btnPin:hover {{ background: rgba(255,255,255,0.07); }}

QPushButton#btnPinOn {{
    background: rgba(137,223,255,0.13); border: none;
    color: #89dfff; font-size: 11px;
    border-radius: 5px; padding: 0px;
}}
QPushButton#btnPinOn:hover {{ background: rgba(137,223,255,0.22); }}

QPushButton#btnCog {{
    background: transparent; border: none;
    color: #7a7a7a; font-size: 13px;
    border-radius: 5px; padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnCog:hover {{ background: rgba(255,255,255,0.07); color: #f0f0f0; }}

QPushButton#btnRecord {{
    background: rgba(255,75,105,0.10);
    border: 1px solid rgba(255,75,105,0.30);
    color: #ff4b69;
    font-size: 11px; font-weight: 700;
    border-radius: 10px;
    padding: 0px 10px;
    text-align: center;
    font-family: {FONT};
}}
QPushButton#btnRecord:hover   {{ background: rgba(255,75,105,0.20); border-color: rgba(255,75,105,0.52); }}
QPushButton#btnRecord:pressed {{ background: rgba(255,75,105,0.30); }}
QPushButton#btnRecord:disabled {{
    background: rgba(255,75,105,0.04); border-color: rgba(255,75,105,0.10);
    color: rgba(255,75,105,0.25);
}}

QPushButton#btnStop {{
    background: rgba(255,170,50,0.08);
    border: 1px solid rgba(255,170,50,0.28);
    color: #ffaa32;
    font-size: 11px; font-weight: 700;
    border-radius: 10px;
    padding: 0px 10px;
    font-family: {FONT};
}}
QPushButton#btnStop:hover   {{ background: rgba(255,170,50,0.18); border-color: rgba(255,170,50,0.52); }}
QPushButton#btnStop:pressed {{ background: rgba(255,170,50,0.28); }}
QPushButton#btnStop:disabled {{
    background: rgba(255,170,50,0.03); border-color: rgba(255,170,50,0.10);
    color: rgba(255,170,50,0.22);
}}

QPushButton#btnImport, QPushButton#btnExport {{
    background: rgba(137,223,255,0.11);
    border: 1px solid rgba(137,223,255,0.26);
    color: #89dfff;
    font-size: 11px; font-weight: 600;
    border-radius: 10px;
    padding: 0px 10px;
    font-family: {FONT};
}}
QPushButton#btnImport:hover, QPushButton#btnExport:hover {{
    background: rgba(137,223,255,0.18); border-color: rgba(137,223,255,0.46);
}}
QPushButton#btnImport:pressed, QPushButton#btnExport:pressed {{
    background: rgba(137,223,255,0.26);
}}
QPushButton#btnImport:disabled, QPushButton#btnExport:disabled {{
    background: rgba(137,223,255,0.02); border-color: rgba(137,223,255,0.08);
    color: rgba(137,223,255,0.20);
}}

QPushButton#btnDiscord {{
    background: rgba(88,101,242,0.11);
    border: 1px solid rgba(88,101,242,0.32);
    color: #8b9cf4;
    font-size: 11px; font-weight: 600;
    border-radius: 10px;
    padding: 0px 10px;
    font-family: {FONT};
}}
QPushButton#btnDiscord:hover {{
    background: rgba(88,101,242,0.20); border-color: rgba(88,101,242,0.56);
}}
QPushButton#btnDiscord:pressed {{
    background: rgba(88,101,242,0.30);
}}

QPushButton#btnGuide {{
    background: rgba(100,200,150,0.10);
    border: 1px solid rgba(100,200,150,0.28);
    color: #64c896;
    font-size: 11px; font-weight: 600;
    border-radius: 10px;
    padding: 0px 10px;
    font-family: {FONT};
}}
QPushButton#btnGuide:hover {{
    background: rgba(100,200,150,0.20); border-color: rgba(100,200,150,0.52);
}}
QPushButton#btnGuide:pressed {{
    background: rgba(100,200,150,0.30);
}}

QWidget#settingsCard {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
}}

QPushButton#btnTypeDropdown {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    color: #7a8299;
    font-size: 11px; font-weight: 600;
    border-radius: 6px;
    padding: 0px 10px;
    text-align: left;
    font-family: {FONT};
}}
QPushButton#btnTypeDropdown:hover {{
    background: rgba(255,255,255,0.09);
    border-color: rgba(255,255,255,0.18);
    color: #eef0f5;
}}

QFrame#typePopupInner {{
    background: #1a1a1a;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 8px;
}}
QPushButton#btnTypeOption {{
    background: transparent;
    border: none;
    color: #c0c5d0;
    font-size: 11px; font-weight: 500;
    border-radius: 5px;
    padding: 0px 8px;
    text-align: left;
    font-family: {FONT};
}}
QPushButton#btnTypeOption:hover {{
    background: rgba(137,223,255,0.10);
    color: #89dfff;
}}
QPushButton#btnTypeOptionSel {{
    background: rgba(137,223,255,0.12);
    border: none;
    color: #89dfff;
    font-size: 11px; font-weight: 600;
    border-radius: 5px;
    padding: 0px 8px;
    text-align: left;
    font-family: {FONT};
}}
QPushButton#btnTypeOptionSel:hover {{
    background: rgba(137,223,255,0.18);
}}

QPushButton#btnSpeedPreset {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    color: #7a8299;
    font-size: 10px; font-weight: 600;
    border-radius: 5px;
    font-family: {FONT};
}}
QPushButton#btnSpeedPreset:hover {{
    background: rgba(137,223,255,0.10);
    border-color: rgba(137,223,255,0.28);
    color: #89dfff;
}}
QPushButton#btnSpeedPreset:pressed {{
    background: rgba(137,223,255,0.20);
}}

QFrame#dlgFrame {{
    background: #121212;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
}}
QDoubleSpinBox, QSpinBox {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    color: #f0f0f0;
    font-family: {FONT};
    font-size: 12px;
    padding: 3px 7px; border-radius: 6px; min-height: 24px;
}}
QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: #89dfff; }}
QDoubleSpinBox::up-button, QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid rgba(255,255,255,0.08);
    border-top-right-radius: 6px;
    background: rgba(255,255,255,0.04);
}}
QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover {{
    background: rgba(255,255,255,0.09);
}}
QDoubleSpinBox::up-button:pressed, QSpinBox::up-button:pressed {{
    background: rgba(255,255,255,0.15);
}}
QDoubleSpinBox::down-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid rgba(255,255,255,0.08);
    border-bottom-right-radius: 6px;
    background: rgba(255,255,255,0.04);
}}
QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
    background: rgba(255,255,255,0.09);
}}
QDoubleSpinBox::down-button:pressed, QSpinBox::down-button:pressed {{
    background: rgba(255,255,255,0.15);
}}
QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{
    width: 0px; height: 0px;
}}
QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{
    width: 0px; height: 0px;
}}

QLineEdit#keyInput {{
    background: #080808;
    border: 1px solid rgba(255,255,255,0.10);
    color: #f0f0f0;
    font-family: {FONT};
    font-size: 12px; font-weight: 600;
    padding: 2px 5px; border-radius: 6px;
}}
QLineEdit#keyInput:focus {{ border-color: #89dfff; background: #0e0e0e; }}
QLabel#dlgLabel {{
    color: #f0f0f0;
    font-family: {FONT};
    font-size: 12px;
}}
QLabel#dlgSubLabel {{
    color: #7a7a7a;
    font-family: {FONT};
    font-size: 11px;
}}
QLabel#dlgHeading {{
    font-size: 10px; font-weight: 700;
    color: #89dfff; letter-spacing: 1.4px;
    text-transform: uppercase;
    font-family: {FONT};
}}

QWidget#seqPanel {{
    background: #0a0a0a;
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
    border-left: 2px solid rgba(255,255,255,0.09);
    border-top: 1px solid rgba(255,255,255,0.05);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    border-right: none;
}}
QWidget#seqRowSel {{
    background: rgba(137,223,255,0.06);
    border-left: 2px solid rgba(137,223,255,0.55);
    border-top: 1px solid rgba(137,223,255,0.13);
    border-bottom: 1px solid rgba(137,223,255,0.13);
    border-right: none;
}}
QLabel#btnRowDel {{
    background: transparent; border: none;
    color: #52596b; font-size: 11px; font-weight: 700;
    padding: 0px;
    font-family: {FONT};
}}
QLabel#btnRowDel:hover {{ background: transparent; color: #ff5a70; }}
QWidget#seqRowSelected {{
    background: rgba(255,255,255,0.06);
    border-left: 2px solid rgba(255,255,255,0.30);
    border-top: 1px solid rgba(255,255,255,0.08);
    border-bottom: 1px solid rgba(255,255,255,0.08);
    border-right: none;
}}
QPushButton#btnSeqDel {{
    background: transparent; border: none;
    color: #7a7a7a; font-size: 10px; font-weight: 600;
    padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnSeqDel:hover {{ color: #ff5a70; background: transparent; }}
QLabel#btnSeqClose {{
    background: transparent;
    color: #7a7a7a; font-size: 10px; font-weight: 600;
    padding: 0px;
    font-family: {FONT};
}}
QLabel#btnSeqClose:hover {{ color: #ff5a70; background: transparent; }}
QWidget#statusBox {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
}}
QPushButton#btnEdit {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    color: #aaaaaa;
    font-size: 11px; font-weight: 600;
    border-radius: 10px;
    font-family: {FONT};
}}
QPushButton#btnEdit:hover {{ background: rgba(255,255,255,0.09); color: #d8d8d8; }}
QPushButton#btnEdit:disabled {{ color: #333333; background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.05); }}
QPushButton#btnSeqLink {{
    background: transparent;
    border: none;
    color: #7a7a7a;
    font-size: 10px; font-weight: 600;
    padding: 0px 2px;
    font-family: {FONT};
}}
QPushButton#btnSeqLink:hover {{
    color: #aaaaaa;
}}
QPushButton#btnInlineEdit {{
    background: transparent;
    border: none;
    color: #7a7a7a;
    font-size: 10px; font-weight: 600;
    padding: 0px;
    font-family: {FONT};
}}
QPushButton#btnInlineEdit:hover {{ color: #aaaaaa; }}
QPushButton#btnExpand {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.13);
    color: #aaaaaa;
    font-size: 10px; font-weight: 600;
    border-radius: 5px; padding: 0px 4px;
    font-family: {FONT};
}}
QPushButton#btnExpand:hover {{
    background: rgba(255,255,255,0.12);
    border-color: rgba(255,255,255,0.24);
    color: #d8d8d8;
}}
QPushButton#btnExpand:pressed {{
    background: rgba(255,255,255,0.18);
}}
QComboBox {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    color: #f0f0f0;
    font-family: {FONT};
    font-size: 11px;
    padding: 1px 6px; border-radius: 6px; min-height: 22px;
}}
QComboBox:focus {{ border-color: #89dfff; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: #121212; border: 1px solid rgba(255,255,255,0.12);
    color: #f0f0f0; selection-background-color: rgba(137,223,255,0.16);
}}
QLineEdit#seqEdit {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    color: #f0f0f0;
    font-family: {FONT};
    font-size: 11px;
    padding: 1px 6px; border-radius: 6px; min-height: 22px;
}}
QLineEdit#seqEdit:focus {{ border-color: #89dfff; }}
"""
