# NPC loot hunter for EVE Online

## Installation

1. Download the folder
2. Install the latest version of python (I use bundled anaconda)
3. Install the required python packages, along with [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
4. `simpleaudio`, `tkinter`, `websockets`, `webbrowser`
5. Make sure that the following files are present in the same folder:
   1. alert.wav
   2. blue_alert.wav
   3. orange_alert.wav
   4. abyssals.txt
   5. blueprints.txt
   6. settings.json
6. adjust settings.json for personal preferences
7. run `python socket4.py`

You can change the alert notification by replacing the `alert.wav`, as long as it has the same name.

## Building the executable

1. Install pyinstaller
2. run `pyinstaller -F .\socket4.py`
3. Copy necessary files mentioned in installation to same folder
