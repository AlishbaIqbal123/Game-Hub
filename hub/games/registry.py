from __future__ import annotations
from collections import OrderedDict

from hub.games.game_2048       import Puzzle2048Screen
from hub.games.ludo            import LudoScreen
from hub.games.snake           import SnakeScreen
from hub.games.tic_tac_toe     import TicTacToeScreen
from hub.games.tower_stacking  import TowerStackingScreen
from hub.games.word_search     import WordSearchScreen
from hub.games.connect4        import Connect4Screen
from hub.games.memory_match    import MemoryMatchScreen
from hub.games.hangman         import HangmanScreen
from hub.games.minesweeper     import MinesweeperScreen
from hub.games.spider_solitaire import SpiderScreen
from hub.games.solitaire        import SolitaireScreen
from hub.games.breakout        import BreakoutScreen
from hub.games.whack_a_mole    import WhackAMoleScreen
from hub.games.reaction_time   import ReactionTimeScreen


def build_registry(storage, sounds):
    def _e(key, title, subtitle, emoji, accent, factory):
        return (key, {"key": key, "title": title, "subtitle": subtitle,
                      "emoji": emoji, "accent": accent, "factory": factory})

    return OrderedDict([
        _e("klondike",         "Classic Solitaire",
           "The definitive patience experience — master the deck.",
           "👑", "#ffd60a", lambda: SolitaireScreen(storage, sounds)),

        _e("spider_solitaire", "Spider Solitaire",
           "Strategic card fanning and high-fidelity sequences.",
           "🕷️", "#22d98a", lambda: SpiderScreen(storage, sounds)),

        _e("tic_tac_toe",      "Tic Tac Toe",
           "The ultimate battle of ✕ and ◯ — beat the AI.",
           "⚔️", "#00d4ff", lambda: TicTacToeScreen(storage, sounds)),

        _e("connect4",         "Connect Four",
           "Drop discs and outsmart your opponent's line.",
           "🔴", "#FF4757", lambda: Connect4Screen(storage, sounds)),

        _e("ludo",             "Ludo Royale",
           "Elite board strategy — race your tokens home.",
           "🎲", "#a855f7", lambda: LudoScreen(storage, sounds)),

        _e("minesweeper",      "Minesweeper",
           "Tactical grid clearance — identify all explosives.",
           "💣", "#22d98a", lambda: MinesweeperScreen(storage, sounds)),

        _e("snake",            "Neon Snake",
           "High-speed survival in a glowing arcade world.",
           "🐍", "#22d98a", lambda: SnakeScreen(storage, sounds)),

        _e("breakout",         "Breakout",
           "Physics-based destruction — smash every brick.",
           "🏓", "#00d4ff", lambda: BreakoutScreen(storage, sounds)),

        _e("whack_a_mole",     "Whack-a-Mole",
           "Test your reflexes against the nimble moles.",
           "🐹", "#22d98a", lambda: WhackAMoleScreen(storage, sounds)),

        _e("memory_match",     "Memory Match",
           "Flip and pair emojis in this cognitive challenge.",
           "🃏", "#a855f7", lambda: MemoryMatchScreen(storage, sounds)),

        _e("hangman",          "Hangman",
           "Word-guessing survival — choose letters wisely.",
           "🪢", "#ff4da6", lambda: HangmanScreen(storage, sounds)),

        _e("word_search",      "Word Search",
           "Find hidden patterns in the grid of letters.",
           "🔍", "#4488ff", lambda: WordSearchScreen(storage, sounds)),

        _e("tower_stacking",   "Tower Stacking",
           "Precision timing — build the tallest skyscraper.",
           "🏗️", "#ff4da6", lambda: TowerStackingScreen(storage, sounds)),

        _e("puzzle_2048",      "2048 Puzzle",
           "Combine numerical tiles to reach the master tile.",
           "🔢", "#ffd60a", lambda: Puzzle2048Screen(storage, sounds)),

        _e("reaction_time",    "Reaction Time",
           "Milliseconds matter — test your human limit.",
           "⚡", "#ffd60a", lambda: ReactionTimeScreen(storage, sounds)),
    ])
