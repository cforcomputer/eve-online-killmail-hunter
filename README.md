# Killmail hunter for EVE Online

## Releases

See the v1 release for a windows executable.

### Changing settings

- You can adjust which lossmails are shown by editing the `settings.json` file.

  "belt_hunter_mode": true, = will stop showing blueprints and special items, and only show commanders, officers, and belt rats
  "officers": true, = will always show you when someone dies to an officer NPC
  "abyssal_mods": true, = always shows you ships that die with abyss items, ignoring value
  "blueprints": true, = always shows you ships that die with blueprints, ignoring value
  "time_threshold_enabled": true, = only shows you lossmails within the timeframe (seconds)
  "time_threshold": 12000, = default timeframe 200 minutes (aka 3.33 hours)
  "dropped_value_enabled": false, = filters ships by the value that they dropped in the wreck
  "dropped_value": 100 = will only show ships with a dropped greater than the entered number

## Development Installation

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
7. run `python km_hunter.py`

You can change the alert notification by replacing the `alert.wav`'s, as long as they have the same name.

## Building the executable

1. Install pyinstaller
2. run `pyinstaller -F .\km_hunter.py`
3. Copy necessary files mentioned in installation to same folder
