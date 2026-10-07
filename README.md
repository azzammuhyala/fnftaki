# FNF Mod - Only with Taki's song!!

<div align="center">
    <img src="previews/Crucify - 3091.webp" alt="Preview" height="300">
    <br>
    <img src="previews/Crucify - 12207.webp" alt="Preview" height="300">
    <br>
    <img src="previews/Markov - 47092.webp" alt="Preview" height="300">
    <br>
    <img src="previews/Come Along With Me - 55827.webp" alt="Preview" height="300">
</div>

I just made **Taki** ~~VS Demon Fever~~ **FNF** using PyScript and PyGame library. This game is quite simple, with only
12 songs and is ready to play without a main menu. If your device is quite low-end, i'm sure you won't even be able to
reach 24 FPS (LOL). PyScript runs on top of Python also still using Tree Walk Interpreter too, which is quite slow and
heavy for that.

## Requirements
- Python (above `3.10`)
- PyScript `pip install pyscript-programming-language` (above `1.14.0`)
- PyGame `pip install pygame` or `pip install pygame-ce`

## Run the game
Execute this command (run the file `main.pys` with pyscript interpreter):
```sh
python -m pyscript main.pys
```
> NOTE: Read the comment header in `options.pys` file first before execute it! (all gameplay options and credits are
there)

### If you're want to play on mobile
You need to install a mobile app that can run Python, PyScript and display the PyGame window. I recommend you using
[**PyramIDE: Python 3 IDE**](https://play.google.com/store/apps/details?id=iiec.pyramide.python&pcampaignid=web_share)
or **Pydroid 3**. After that, you need to install the required libraries. Once that's done and without any issues, copy
the Python code below. `GAME_PATH` is the game's folder, which contains the `main.pys` file and the `assets/` folder
required by the game.
```py
# WARNING: Make sure you're using PyScript>=1.14.0

# Your game folder:
GAME_PATH = r'/storage/emulated/0/Download/taki-v2.1.0/fnftaki'

import os

# WARNING: This configuration section must be at the top before importing pygame or pyscript because it will be read
# when it is first imported so that the configuration can be implemented
os.environ['PYSCRIPT_NO_TYPECHECK'] = '1'
os.chdir(GAME_PATH)

import pyscript
import pygame  # trigger to open pygame window

with open('main.pys', 'r', encoding=pyscript.pys_sys.encoding) as file:
    source = pyscript.core.buffer.PysFileBuffer(file)
    del file

# `globals=undefined` prevents using the python namespace where python and pyscript builtins differ
# `flags=NO_COLOR` disables ansi colors when errors occur, sometimes applications don't apply ansi colors which
# causes corrupted output text
pyscript.pys_exec(source, pyscript.undefined, pyscript.NO_COLOR)
```
After that, don't forget to open `options.pys` and change the value of the `MOBILE` option to `1`:
```py
MOBILE = 1
```