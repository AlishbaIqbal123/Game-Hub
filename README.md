# Neon Game Hub

A Python-based mini game platform with a futuristic dark UI, animated screen transitions, reusable UI components, score tracking, and one file per game.

## Tech Stack

- Python
- PyQt6 for the main interface
- Pygame for sound, vectors, and timer-friendly game logic helpers

## Included Games

- Tic Tac Toe with AI
- Basic Ludo
- Snake
- Word Search
- Tower Stacking
- 2048 Puzzle

## Project Structure

```text
game_hub/
├── main.py
├── README.md
├── design/
│   ├── design_system.md
│   ├── game_screen_mockup.svg
│   ├── home_mockup.svg
│   ├── pause_menu_mockup.svg
│   └── settings_mockup.svg
└── hub/
    ├── core/
    │   ├── sound.py
    │   ├── storage.py
    │   └── theme.py
    ├── games/
    │   ├── game_2048.py
    │   ├── ludo.py
    │   ├── registry.py
    │   ├── snake.py
    │   ├── tic_tac_toe.py
    │   ├── tower_stacking.py
    │   └── word_search.py
    └── ui/
        ├── base_game_screen.py
        ├── components.py
        ├── dashboard.py
        ├── main_window.py
        ├── pause_menu.py
        ├── settings.py
        └── transitions.py
```

## Run

```powershell
py -3 main.py
```

From the `game_hub` folder.

From the workspace root you can also run:

```powershell
py -3 run_game_hub.py
```

If you want Windows to launch the UI and return control immediately, use:

```powershell
.\start_game_hub.bat
```

## Smoke Test

```powershell
py -3 main.py --smoke-test
```

## Notes

- Settings and high scores are saved in `.hub_data/state.json`.
- Sound effects are generated on first run and cached under `.hub_data/sounds`.
- The `design` folder contains mockups, palette guidance, and font suggestions.
