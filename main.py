"""
Super Infinit Quest
===================
A math-based platformer game built with Python + tkinter.

Architecture:
  main.py          → entry point, launches the game
  src/engine.py    → core game logic engine (algorithms)
  src/entities.py  → Player, Enemy, Coin, Star, Obstacle classes
  src/math_engine.py → math problem generator & validator
  src/renderer.py  → tkinter canvas renderer
  src/scenes.py    → scene/state manager (menu, game, result)
"""

import tkinter as tk
from src.scenes import SceneManager


def main():
    root = tk.Tk()
    root.title("Super Infinit Quest")
    root.resizable(False, False)
    root.configure(bg="#1a1a2e")

    # Center window
    w, h = 800, 600
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    app = SceneManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
