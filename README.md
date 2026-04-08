# FNF Mod - Friday Night Fever - Only with Taki's song!!

<div align="center">
    <img src="preview.gif" alt="Preview">
</div>

I just made Taki VS Demon Fever using PyScript and PyGame library. This game is quite simple, with only 9 songs and
is ready to play without a main menu. If your device is quite low-end, i'm sure you won't even be able to reach 24 FPS
lol. PyScript runs on top of Python, which is quite slow and heavy for that.

## Requirements
- Python (above `3.10`)
- PyScript `pip install pyscript-programming-language` (above `1.12.9`, recommended)
- PyGame `pip install pygame-ce` or `pip install pygame`

## Run Game
Execute this command (run the file `main.pys` with pyscript interpreter):
```sh
python -m pyscript main.pys
```
> NOTE: Read the comment header in `main.pys` file first before execute it! (all gameplay options and creator credits
are there)

### If you're want to play on mobile
You need to install a mobile app that can run Python, PyScript and display the PyGame window. I recommend using
**PyramIDE: Python 3 IDE** (recommended) or **Pydroid 3**. After that, you need to install the required libraries.
Once that's done and without any issues, copy the Python code below. `GAME_PATH` is the game's folder, which contains
the `main.pys` file and the `assets/` folder required by the game.
```py
# Your game folder:
GAME_PATH = r'/storage/emulated/0/Download/taki-v1.4'

import os

# WARNING: This configuration section must be at the top before importing pygame or pyscript because it will be read
# when it is first imported so that the configuration can be implemented
os.chdir(GAME_PATH)
os.environ['PYSCRIPT_NO_GIL'] = '1'
os.environ['PYSCRIPT_NO_TYPECHECK'] = '1'

import pyscript
import pygame

with open('main.pys', 'r', encoding='utf-8') as file:
    source = file.read()

del file

# `globals=undefined` prevents using the python namespace where python and pyscript builtins differ
# `flags=NO_COLOR` disables ansi colors when errors occur, sometimes applications don't apply ansi colors which
# causes corrupted output text
pyscript.pys_exec(source, pyscript.undefined, pyscript.NO_COLOR)
```