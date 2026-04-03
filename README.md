# moris macro maker - m³

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![License: MUL](https://img.shields.io/badge/license-MUL-orange.svg)](LICENSE.md) [![Platform: Windows](https://img.shields.io/badge/platform-Windows-informational.svg)](https://www.microsoft.com/windows) [![Discord](https://img.shields.io/badge/Discord-Join-5865F2.svg)](https://discord.com/invite/2fraBuhe3m)

A lightweight macro recording and playback tool for Windows and macOS.

---

## Features

- **Full Input Recording** - Captures keyboard presses, mouse clicks, movement, scrolling, and right-click dragging in real-time
- **Playback Control** - Replay at adjustable speed with configurable loop count and interval timing
- **Custom Hotkeys** - Bind any key to start/stop recording and playback (default: F1 / F2); hold to pause instead of stopping
- **Event Editing** - Add, copy (Ctrl+C), and paste (Ctrl+V) inputs; use Insert After preview to place new inputs precisely
- **Loop Above** - Insert a Loop Above event to loop a subset of inputs within a sequence without re-recording
- **Mouse Movement** - Linear or Humanoid movement modes with configurable move duration and set-position support
- **Right-Click Dragging** - Records and replays right-click drag actions using raw hardware input for accurate delta-based playback
- **Webhook Support** - Trigger Discord or HTTP webhooks during playback for notifications and integrations
- **Auto-Save** - Your last session is automatically saved and restored on next launch
- **Save / Load Macros** - Export and import macros as `.mmr` files; share and reuse across sessions
- **macOS Support** - Full macOS compatibility with the same feature set as Windows
- **Cross-Platform Input** - Runs on Windows and macOS using native OS APIs for reliable, low-level input simulation

---

## System Requirements

- **OS**: Windows 7 or later (64-bit recommended), macOS
- **Python**: 3.10 or higher
- **Dependencies**: PySide6, pynput, requests

---

## Installation

### Option 1: From Source

```bash
git clone https://github.com/m0r1s/macro-maker.git
cd macro-maker
pip install PySide6 pynput requests
python src/macro_maker/main.py
```

### Option 2: Windows Standalone (.exe)

Download the latest release from the [Releases](https://github.com/m0r1s/macro-maker/releases) page and run the `.exe` - no Python required.

### Troubleshooting Installation

**`python` is not recognized**
- Reinstall Python and check "Add Python to PATH" during setup

**`No module named 'PySide6'`**
- Run: `pip install PySide6 pynput requests`

**`pynput` fails to install**
- Install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), then retry

---

## Quick Start

### 1. Record a Macro

- Press **F1** to start recording
- Perform your actions - mouse movements, clicks, scrolling, typing
- Press **F1** again to stop
- Your macro is auto-saved

### 2. Play It Back

- Press **F2** to play
- Press **F2** again to stop early
- Adjust speed in the UI (e.g. 0.5x for slower, 2x for faster)

### 3. Customize

- Set loop count, change hotkeys, add Loop Above events, copy/paste inputs, use Linear or Humanoid mouse movement, and hook into Discord

---

## Performance & Limitations

### What Works Well

- Browser automation (clicking, form filling, navigation)
- In-Game Repetitive Task Automation
- Data entry and repetitive typing tasks
- UI testing and workflow replay
- Custom shortcut sequences

### Known Limitations

- **Coordinate-based** - mouse positions are absolute; changing screen resolution affects playback
- **No conditional logic** - macros run the same way every time
- **Anti-cheat** - games with anti-cheat systems may rarely block input simulation

---

## Roadmap

### Completed
- Full keyboard and mouse recording
- Adjustable playback speed
- Loop count and loop interval
- Custom hotkeys
- Discord webhook events
- Auto-save and `.mmr` file format
- macOS support
- Loop Above, Linear/Humanoid mouse movement
- Right-click dragging recording

### Planned
- [ ] Macro scheduling (run at a specific time)
- [ ] Conditional event logic
- [ ] Debug Mode - step-by-step playback
- [ ] Multi-macro scheduling

---

## Architecture

```
src/macro_maker/
├── main.py                      Entry point
├── recorder.py                  Keyboard and mouse listener
├── player.py                    Playback engine (PlayWorker)
├── ui/
│   ├── main_window.py           Main window and dialogs
│   ├── widgets.py               UI components
│   └── styles.py                Qt stylesheets
└── utils/
    ├── constants.py             App-wide constants and defaults
    ├── serialization.py         Save/load and webhook logic
    └── platform_helpers.py      Windows API wrappers
```

---

## License

This project is licensed under the **MORIS UNIVERSAL LICENSE (MUL)** - see [LICENSE.md](LICENSE.md) for full terms.

**Summary:**
- Personal, non-commercial use only
- Attribution to the original author is required
- Commercial use and redistribution without the license are prohibited

---

## Support

- **Discord**: [discord.com/invite/2fraBuhe3m](https://discord.com/invite/2fraBuhe3m)
- **Issues**: Open a GitHub issue with your Windows version, Python version, and steps to reproduce/.mmr file

When reporting a bug, include:
1. Windows version
2. Python version (`python --version`)
3. Steps to reproduce or .mmr file
4. Error message or screenshot

---

## Show Your Support

If m³ saves you time, consider starring the repo on GitHub and/or join the Discord - it helps others find the project.

Made with ♡ by _**moris**_ and _**tim**_
