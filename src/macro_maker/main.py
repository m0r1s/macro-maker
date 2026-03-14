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

"""Entry point for the macro_maker application."""

import sys
import os
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from macro_maker.ui.main_window import MainWindow
from macro_maker.ui.styles import SS
from macro_maker.utils.serialization import ensure_mmr_icon
from macro_maker.utils.constants import MMR_ICO_B64, LOGO_B64


def main() -> None:
    """Launch the macro_maker application.

    Creates the QApplication, applies the global stylesheet, shows the
    main window, and enters the Qt event loop.
    """
    ensure_mmr_icon(MMR_ICO_B64)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(SS)
    pixmap = QPixmap()
    pixmap.loadFromData(base64.b64decode(LOGO_B64))
    app.setWindowIcon(QIcon(pixmap))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
