"""
scenes.py
=========
Scene / state manager for Super Infinit Quest.

Scenes:
  MenuScene   → title screen with controls guide
  GameScene   → main gameplay loop (60fps)
  CombatScene → math question overlay (overlaid on game)
  WinScene    → victory screen with stats
  DeadScene   → game over screen

The SceneManager owns the tkinter root, canvas, and key-state dict.
It switches between scenes and passes events to the active scene.
"""

import tkinter as tk
import time
from src.engine import GameEngine
from src.renderer import Renderer
from src.entities import C, SCREEN_W, SCREEN_H, TOTAL_STARS


FPS = 60
FRAME_MS = 1000 // FPS


# ── Scene base ────────────────────────────────────────────────────────────────

class Scene:
    def __init__(self, manager):
        self.mgr = manager

    def on_enter(self):  pass
    def on_exit(self):   pass
    def update(self):    pass
    def on_key_press(self, event):   pass
    def on_key_release(self, event): pass


# ── Scene Manager ─────────────────────────────────────────────────────────────

class SceneManager:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.canvas = tk.Canvas(root, width=SCREEN_W, height=SCREEN_H,
                                bg="#1a1a2e", highlightthickness=0)
        self.canvas.pack()

        self.keys: set[str] = set()
        root.bind("<KeyPress>",   self._on_key_press)
        root.bind("<KeyRelease>", self._on_key_release)

        self.scenes = {
            "menu":   MenuScene(self),
            "game":   GameScene(self),
            "win":    WinScene(self),
            "dead":   DeadScene(self),
        }
        self._active_scene = None
        self.switch("menu")

    def switch(self, name: str, **kwargs):
        if self._active_scene:
            self._active_scene.on_exit()
        scene = self.scenes[name]
        if hasattr(scene, "set_kwargs"):
            scene.set_kwargs(**kwargs)
        self._active_scene = scene
        scene.on_enter()

    def _on_key_press(self, event):
        self.keys.add(event.keysym)
        if self._active_scene:
            self._active_scene.on_key_press(event)

    def _on_key_release(self, event):
        self.keys.discard(event.keysym)
        if self._active_scene:
            self._active_scene.on_key_release(event)

    def schedule(self, ms, fn):
        self.root.after(ms, fn)


# ── Menu Scene ────────────────────────────────────────────────────────────────

class MenuScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self._tick = 0

    def on_enter(self):
        self._tick = 0
        self._draw()

    def _draw(self):
        c = self.mgr.canvas
        c.delete("all")

        # Background
        c.create_rectangle(0, 0, SCREEN_W, SCREEN_H, fill=C["bg_sky"])

        # Stars
        import random
        rng = random.Random(3)
        for _ in range(60):
            sx = rng.randint(0, SCREEN_W)
            sy = rng.randint(0, SCREEN_H // 2)
            c.create_oval(sx, sy, sx+1, sy+1, fill="#aaaacc", outline="")

        # Animated glow for title
        pulse = abs((self._tick % 80) - 40) / 40
        glow_r = int(200 + 55 * pulse)
        glow_g = int(180 + 55 * pulse)
        glow_b = int(50 + 100 * pulse)
        glow_color = f"#{glow_r:02x}{glow_g:02x}{glow_b:02x}"

        # Title
        c.create_text(SCREEN_W // 2, 100,
                      text="Super Infinit Quest",
                      font=("Arial", 36, "bold"),
                      fill=glow_color)
        c.create_text(SCREEN_W // 2, 145,
                      text="∞  Conquer Math. Reach the Stars.  ∞",
                      font=("Arial", 14, "italic"),
                      fill="#aaaaee")

        # Draw mini player sprite hint
        self._draw_mini_char(c, SCREEN_W // 2, 210)

        # Controls
        controls = [
            ("← / →  or  A / D", "Move"),
            ("Space / ↑ / W", "Jump"),
            ("Touch enemy", "Math battle"),
            ("Collect ⭐ × 5", "Win!"),
        ]
        c.create_rectangle(200, 280, 600, 420,
                           fill="#111122", outline=C["inf_outer"],
                           width=2)
        c.create_text(SCREEN_W // 2, 296,
                      text="─── CONTROLS ───",
                      font=("Arial", 11, "bold"),
                      fill=C["inf_outer"])
        for i, (key, action) in enumerate(controls):
            y = 320 + i * 22
            c.create_text(310, y, anchor="e",
                          text=key,
                          font=("Courier", 11, "bold"),
                          fill=C["text_hi"])
            c.create_text(320, y, anchor="w",
                          text=f"→  {action}",
                          font=("Arial", 11),
                          fill=C["text_lo"])

        # Math difficulty table
        c.create_rectangle(140, 430, 660, 510,
                           fill="#0d1020", outline="#334", width=1)
        c.create_text(SCREEN_W // 2, 446, text="Math Difficulty by Enemy",
                      font=("Arial", 10, "bold"), fill=C["text_lo"])
        table = [
            (" Green [E] ", "Easy",   "+, −  (1-50)",         "#2ecc71"),
            (" Yellow [M]", "Medium", "×, ÷  (2-12)",         "#f39c12"),
            (" Red [H]   ", "Hard",   "x^n, √n (perfect sq)", "#e74c3c"),
        ]
        for i, (badge, label, ops, col) in enumerate(table):
            tx = 180 + i * 160
            c.create_text(tx, 470, anchor="n",
                          text=badge, font=("Courier", 10, "bold"),
                          fill=col)
            c.create_text(tx, 490, anchor="n",
                          text=ops, font=("Arial", 9),
                          fill="#aaaaaa")

        # Start prompt
        blink = (self._tick // 20) % 2 == 0
        if blink:
            c.create_text(SCREEN_W // 2, 545,
                          text="Press  ENTER  to Start",
                          font=("Arial", 16, "bold"),
                          fill=C["inf_inner"])

        self._tick += 1
        self.mgr.schedule(30, self._draw)

    def _draw_mini_char(self, c, cx, cy):
        """Tiny pixel char for menu."""
        # Body
        pts = [cx, cy-28, cx-16, cy, cx+16, cy]
        c.create_polygon(pts, fill=C["body_main"], outline=C["outline"], width=1)
        # Legs
        c.create_rectangle(cx-12, cy, cx-4, cy+16,
                           fill=C["legs"], outline=C["outline"])
        c.create_rectangle(cx+4, cy, cx+12, cy+16,
                           fill=C["legs"], outline=C["outline"])
        # Shoes
        c.create_rectangle(cx-13, cy+14, cx-3, cy+20,
                           fill=C["shoes"], outline=C["outline"])
        c.create_rectangle(cx+3, cy+14, cx+13, cy+20,
                           fill=C["shoes"], outline=C["outline"])
        # Infinity
        r = 5
        c.create_oval(cx-14, cy-38-r, cx-4, cy-38+r,
                      fill=C["inf_inner"], outline=C["inf_outer"], width=2)
        c.create_oval(cx+4, cy-38-r, cx+14, cy-38+r,
                      fill=C["inf_inner"], outline=C["inf_outer"], width=2)

    def on_key_press(self, event):
        if event.keysym in ("Return", "KP_Enter"):
            self.mgr.switch("game")


# ── Game Scene ────────────────────────────────────────────────────────────────

class GameScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.engine   = None
        self.renderer = None
        self._running = False
        self._combat_widgets: list[tk.Widget] = []
        self._answer_var  = None
        self._answer_entry= None
        self._submit_after= None

    def on_enter(self):
        self.engine   = GameEngine()
        self.renderer = Renderer(self.mgr.canvas)
        self._running = True
        self._loop()

    def on_exit(self):
        self._running = False
        self._clear_combat_widgets()

    def _loop(self):
        if not self._running:
            return

        state = self.engine.state

        if state == "combat":
            if not self._combat_widgets:
                self._show_combat_input()
        else:
            self._clear_combat_widgets()

        self.engine.update(self.mgr.keys)
        self.renderer.render(self.engine)

        new_state = self.engine.state
        if new_state == "win":
            self._running = False
            self._clear_combat_widgets()
            self.mgr.schedule(800, lambda: self.mgr.switch(
                "win", stats=self.engine.math.get_summary(),
                score=self.engine.score,
                coins=self.engine.player.coins_collected))
            return
        if new_state == "dead":
            self._running = False
            self._clear_combat_widgets()
            self.mgr.schedule(600, lambda: self.mgr.switch(
                "dead", stats=self.engine.math.get_summary(),
                score=self.engine.score))
            return

        self.mgr.schedule(FRAME_MS, self._loop)

    # ── Combat input widgets ──────────────────────────────────────────────────

    def _show_combat_input(self):
        root = self.mgr.root
        frame = tk.Frame(root, bg="#16213e",
                         bd=0, highlightthickness=0)
        frame.place(x=SCREEN_W // 2 - 200,
                    y=SCREEN_H // 2 + 30,
                    width=400, height=80)

        # Answer entry
        self._answer_var = tk.StringVar()
        entry = tk.Entry(
            frame,
            textvariable=self._answer_var,
            font=("Courier", 20, "bold"),
            bg="#0d1a2e", fg=C["text_hi"],
            insertbackground=C["text_hi"],
            relief="flat",
            justify="center",
            bd=0,
            highlightthickness=2,
            highlightcolor=C["inf_outer"],
            highlightbackground="#334455",
        )
        entry.place(x=0, y=0, width=280, height=46)
        entry.focus_set()
        self._answer_entry = entry

        # Submit button
        btn = tk.Button(
            frame,
            text="Submit →",
            font=("Arial", 13, "bold"),
            bg=C["inf_outer"], fg="#111",
            activebackground=C["inf_inner"],
            relief="flat", bd=0,
            cursor="hand2",
            command=self._submit_answer,
        )
        btn.place(x=288, y=0, width=112, height=46)

        # Hint label
        hint = tk.Label(
            frame,
            text="Type your answer and press Enter or Submit",
            font=("Arial", 9),
            bg="#16213e", fg=C["text_lo"],
        )
        hint.place(x=0, y=50, width=400, height=28)

        # Bind Enter key
        entry.bind("<Return>", lambda e: self._submit_answer())

        self._combat_widgets = [frame, entry, btn, hint]

    def _submit_answer(self):
        if not self._answer_var:
            return
        answer = self._answer_var.get().strip()
        if not answer:
            return
        result = self.engine.resolve_combat(answer)
        self._clear_combat_widgets()

        # Show result overlay briefly, then resume
        self.mgr.schedule(1400, self._resume_after_combat)

    def _resume_after_combat(self):
        self.engine.exit_combat()

    def _clear_combat_widgets(self):
        for w in self._combat_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._combat_widgets = []
        self._answer_var   = None
        self._answer_entry = None

    def on_key_press(self, event):
        # Prevent space/arrow keys from being consumed by entry widget
        pass


# ── Win Scene ─────────────────────────────────────────────────────────────────

class WinScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self._stats = {}
        self._score = 0
        self._coins = 0

    def set_kwargs(self, stats=None, score=0, coins=0):
        self._stats = stats or {}
        self._score = score
        self._coins = coins

    def on_enter(self):
        self._draw()

    def _draw(self):
        c = self.mgr.canvas
        c.delete("all")

        c.create_rectangle(0, 0, SCREEN_W, SCREEN_H, fill="#0a0a1a")

        # Confetti-like dots
        import random
        rng = random.Random(99)
        for _ in range(120):
            cx2 = rng.randint(0, SCREEN_W)
            cy2 = rng.randint(0, SCREEN_H)
            col = rng.choice(["#FFD700", "#FF6B35", "#4CAF50",
                               "#9C27B0", "#2196F3", "#FF4081"])
            r = rng.randint(2, 6)
            c.create_oval(cx2-r, cy2-r, cx2+r, cy2+r, fill=col, outline="")

        # Title
        c.create_text(SCREEN_W // 2, 80,
                      text="🏆  QUEST COMPLETE!  🏆",
                      font=("Arial", 34, "bold"),
                      fill=C["star_fill"])
        c.create_text(SCREEN_W // 2, 130,
                      text="You collected all 5 stars and conquered the dungeon!",
                      font=("Arial", 13, "italic"),
                      fill="#aaaaee")

        # Stats panel
        c.create_rectangle(160, 165, 640, 430,
                           fill="#11112a", outline=C["inf_outer"], width=2)
        c.create_text(400, 184, text="── GAME STATISTICS ──",
                      font=("Arial", 13, "bold"), fill=C["inf_outer"])

        s = self._stats
        rows = [
            ("Final Score",         f"{self._score:,}"),
            ("Coins Collected",     f"{self._coins}"),
            ("Math Questions",      f"{s.get('total', 0)}"),
            ("Correct Answers",     f"{s.get('correct', 0)}"),
            ("Wrong Answers",       f"{s.get('wrong', 0)}"),
            ("Accuracy",            f"{s.get('accuracy', 0)}%"),
            ("Score from Math",     f"+{s.get('score', 0)}"),
        ]
        for i, (label, val) in enumerate(rows):
            y = 215 + i * 28
            c.create_text(250, y, anchor="e",
                          text=label + ":",
                          font=("Arial", 12), fill=C["text_lo"])
            c.create_text(270, y, anchor="w",
                          text=val,
                          font=("Courier", 12, "bold"),
                          fill=C["text_hi"])

        # History table header
        c.create_text(400, 440,
                      text="Press  R  to Play Again   |   Q  to Quit",
                      font=("Arial", 14, "bold"), fill=C["inf_inner"])

        # Grade
        acc = s.get("accuracy", 0)
        if acc >= 90:   grade, gcol = "S  — Perfect!", "#FFD700"
        elif acc >= 70: grade, gcol = "A  — Excellent!", "#2ecc71"
        elif acc >= 50: grade, gcol = "B  — Good Job!", "#3498db"
        else:           grade, gcol = "C  — Keep Practicing!", "#e74c3c"
        c.create_text(SCREEN_W // 2, 475,
                      text=f"Math Grade:  {grade}",
                      font=("Arial", 16, "bold"),
                      fill=gcol)

        c.create_text(SCREEN_W // 2, 540,
                      text=f"Super Infinit Quest  |  Python + tkinter",
                      font=("Arial", 9, "italic"),
                      fill="#334")

    def on_key_press(self, event):
        if event.keysym in ("r", "R"):
            self.mgr.switch("game")
        if event.keysym in ("q", "Q"):
            self.mgr.root.destroy()


# ── Dead Scene ────────────────────────────────────────────────────────────────

class DeadScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self._stats = {}
        self._score = 0

    def set_kwargs(self, stats=None, score=0, **kwargs):
        self._stats = stats or {}
        self._score = score

    def on_enter(self):
        self._draw()

    def _draw(self):
        c = self.mgr.canvas
        c.delete("all")

        c.create_rectangle(0, 0, SCREEN_W, SCREEN_H, fill="#1a0000")

        c.create_text(SCREEN_W // 2, 100,
                      text="💀  GAME OVER  💀",
                      font=("Arial", 38, "bold"),
                      fill=C["hp_bar"])
        c.create_text(SCREEN_W // 2, 158,
                      text="You ran out of HP in the dungeon...",
                      font=("Arial", 13, "italic"),
                      fill="#aa6666")

        c.create_rectangle(170, 200, 630, 400,
                           fill="#0a0000", outline="#441111", width=2)
        c.create_text(400, 220, text="── YOUR RESULTS ──",
                      font=("Arial", 12, "bold"), fill="#aa4444")

        s = self._stats
        rows = [
            ("Final Score",     f"{self._score:,}"),
            ("Math Questions",  f"{s.get('total', 0)}"),
            ("Correct",         f"{s.get('correct', 0)}"),
            ("Wrong",           f"{s.get('wrong', 0)}"),
            ("Accuracy",        f"{s.get('accuracy', 0)}%"),
        ]
        for i, (label, val) in enumerate(rows):
            y = 250 + i * 28
            c.create_text(300, y, anchor="e",
                          text=label + ":",
                          font=("Arial", 12), fill="#aa7777")
            c.create_text(315, y, anchor="w",
                          text=val,
                          font=("Courier", 12, "bold"),
                          fill="#ffaaaa")

        c.create_text(SCREEN_W // 2, 420,
                      text="Press  R  to Try Again   |   Q  to Quit",
                      font=("Arial", 14, "bold"),
                      fill=C["text_hi"])
        c.create_text(SCREEN_W // 2, 470,
                      text="Tip: Answer math questions faster for bonus points!",
                      font=("Arial", 10, "italic"),
                      fill="#775555")

    def on_key_press(self, event):
        if event.keysym in ("r", "R"):
            self.mgr.switch("game")
        if event.keysym in ("q", "Q"):
            self.mgr.root.destroy()
