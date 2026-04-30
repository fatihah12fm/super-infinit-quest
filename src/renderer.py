"""
renderer.py
===========
Tkinter canvas renderer for Super Infinit Quest.

Draws:
  - Scrolling parallax background (3 layers)
  - Ground
  - All entities (platforms, obstacles, coins, stars, enemies, player)
  - HUD (score, HP bar, score bar, stars counter, mini-map)
  - Combat overlay
  - Message toast
  - Finish flag
"""

import math
import tkinter as tk
from src.entities import C, GROUND_Y, LEVEL_LENGTH, SCREEN_W, SCREEN_H


class Renderer:

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self._bg_offset = 0.0

    # ── Full frame render ─────────────────────────────────────────────────────

    def render(self, engine):
        c = self.canvas
        c.delete("all")
        snap = engine.get_state_snapshot()
        cam_x = snap["cam_x"]

        self._draw_background(cam_x)
        self._draw_ground(cam_x)
        self._draw_finish_flag(engine.finish_x, cam_x)

        for plat in engine.platforms:
            plat.draw(c, cam_x)
        for obs in engine.obstacles:
            obs.draw(c, cam_x)
        for coin in engine.coins:
            if coin.active:
                coin.draw(c, cam_x)
        for star in engine.stars:
            if star.active:
                star.draw(c, cam_x)
        for enemy in engine.enemies:
            if not enemy.defeated:
                enemy.draw(c, cam_x)

        engine.player.draw(c, cam_x)

        self._draw_hud(snap)

        if snap["message"]:
            self._draw_toast(snap["message"])

        if snap["state"] == "combat":
            self._draw_combat_overlay(engine)

    # ── Background (3-layer parallax) ─────────────────────────────────────────

    def _draw_background(self, cam_x):
        c = self.canvas
        # Layer 0: sky gradient (static)
        c.create_rectangle(0, 0, SCREEN_W, SCREEN_H,
                           fill=C["bg_sky"], outline="")

        # Stars in sky
        import random
        rng = random.Random(7)
        for _ in range(80):
            sx = rng.randint(0, SCREEN_W)
            sy = rng.randint(0, int(SCREEN_H * 0.65))
            r  = rng.random()
            alpha_tag = f"bgstar_{sx}_{sy}"
            if r > 0.85:
                c.create_oval(sx-1, sy-1, sx+1, sy+1,
                              fill="#FFFFFF", outline="")
            else:
                c.create_oval(sx, sy, sx+1, sy+1,
                              fill="#aaaacc", outline="")

        # Layer 1: distant hills (slow parallax)
        off1 = int(cam_x * 0.15) % SCREEN_W
        for rep in range(3):
            ox = rep * SCREEN_W - off1
            pts = [
                ox, SCREEN_H,
                ox, GROUND_Y - 60,
                ox + 100, GROUND_Y - 160,
                ox + 200, GROUND_Y - 60,
                ox + 300, GROUND_Y - 120,
                ox + 400, GROUND_Y - 60,
                ox + SCREEN_W, GROUND_Y - 60,
                ox + SCREEN_W, SCREEN_H,
            ]
            c.create_polygon(pts, fill=C["bg_mid"], outline="")

        # Layer 2: midground hills (medium parallax)
        off2 = int(cam_x * 0.35) % SCREEN_W
        for rep in range(3):
            ox = rep * SCREEN_W - off2
            pts = [
                ox, SCREEN_H,
                ox, GROUND_Y - 30,
                ox + 80, GROUND_Y - 90,
                ox + 180, GROUND_Y - 30,
                ox + 250, GROUND_Y - 70,
                ox + 360, GROUND_Y - 30,
                ox + SCREEN_W, GROUND_Y - 30,
                ox + SCREEN_W, SCREEN_H,
            ]
            c.create_polygon(pts, fill="#0d2d4f", outline="")

    def _draw_ground(self, cam_x):
        c = self.canvas
        # Ground fill
        c.create_rectangle(0, GROUND_Y, SCREEN_W, SCREEN_H,
                           fill=C["ground"], outline="")
        # Ground top strip
        c.create_rectangle(0, GROUND_Y, SCREEN_W, GROUND_Y + 8,
                           fill=C["ground_top"], outline="")
        # Tile marks
        tile_w = 40
        start = -int(cam_x) % tile_w
        for tx in range(start, SCREEN_W, tile_w):
            c.create_line(tx, GROUND_Y, tx, GROUND_Y + 8,
                          fill="#1a5a8a", width=1)

    def _draw_finish_flag(self, finish_x, cam_x):
        c = self.canvas
        fx = finish_x - cam_x
        if fx < -60 or fx > SCREEN_W + 60:
            return
        # Pole
        c.create_rectangle(fx, GROUND_Y - 120, fx + 6, GROUND_Y,
                           fill="#CCCCCC", outline="#999")
        # Flag
        pts = [fx + 6, GROUND_Y - 120,
               fx + 46, GROUND_Y - 100,
               fx + 6, GROUND_Y - 80]
        c.create_polygon(pts, fill="#e74c3c", outline="#c0392b")
        c.create_text(fx + 26, GROUND_Y - 100, text="FINISH",
                      font=("Arial", 8, "bold"), fill="white")

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, snap):
        c = self.canvas
        # Background strip
        c.create_rectangle(0, 0, SCREEN_W, 54,
                           fill="#00000088", outline="")

        # Score
        c.create_text(12, 8, anchor="nw",
                      text=f"SCORE  {snap['score']:07d}",
                      font=("Courier", 13, "bold"),
                      fill=C["text_hi"])

        # Stars counter
        star_txt = "⭐" * snap["stars"] + "☆" * (5 - snap["stars"])
        c.create_text(SCREEN_W // 2, 10, anchor="n",
                      text=f"Stars: {star_txt}",
                      font=("Arial", 11, "bold"),
                      fill=C["text_hi"])

        # Coins
        c.create_text(SCREEN_W - 12, 8, anchor="ne",
                      text=f"🪙 {snap['coins']}",
                      font=("Arial", 11, "bold"),
                      fill=C["coin"])

        # HP bar
        hp_pct = snap["hp"] / snap["max_hp"]
        bar_w, bar_h = 140, 10
        bx, by = 12, 34
        c.create_rectangle(bx, by, bx + bar_w, by + bar_h,
                           fill=C["hp_bg"], outline="#444", width=1)
        c.create_rectangle(bx, by,
                           bx + int(bar_w * hp_pct), by + bar_h,
                           fill=C["hp_bar"], outline="")
        c.create_text(bx + bar_w + 5, by + bar_h // 2,
                      anchor="w",
                      text=f"HP {snap['hp']}/{snap['max_hp']}",
                      font=("Arial", 9), fill="#ffaaaa")

        # Score bar (fills as you earn points)
        bar2_w = 160
        bx2 = SCREEN_W // 2 - bar2_w // 2
        by2 = 30
        pct2 = min(1.0, snap["score_bar"] / 100)
        c.create_rectangle(bx2, by2, bx2 + bar2_w, by2 + 8,
                           fill=C["score_bg"], outline="#444", width=1)
        c.create_rectangle(bx2, by2,
                           bx2 + int(bar2_w * pct2), by2 + 8,
                           fill=C["score_bar"], outline="")
        c.create_text(bx2 + bar2_w // 2, by2 + 4,
                      text="Score Bar",
                      font=("Arial", 7), fill="#aaffaa")

        # Mini-map
        self._draw_minimap(snap)

    def _draw_minimap(self, snap):
        c = self.canvas
        mw, mh = 120, 12
        mx0 = SCREEN_W - mw - 12
        my0 = 32
        c.create_rectangle(mx0, my0, mx0 + mw, my0 + mh,
                           fill="#111133", outline="#334")
        # Player dot
        px_ratio = max(0, min(1, snap["cam_x"] / LEVEL_LENGTH))
        pdx = mx0 + int(px_ratio * mw)
        c.create_rectangle(pdx - 2, my0 + 2, pdx + 2, my0 + mh - 2,
                           fill=C["inf_inner"], outline="")
        c.create_text(mx0 + mw // 2, my0 - 5, text="MAP",
                      font=("Arial", 7), fill="#556")

    # ── Toast message ─────────────────────────────────────────────────────────

    def _draw_toast(self, text):
        c = self.canvas
        c.create_text(SCREEN_W // 2, SCREEN_H - 80,
                      text=text,
                      font=("Arial", 14, "bold"),
                      fill=C["text_hi"],
                      anchor="center")

    # ── Combat overlay ────────────────────────────────────────────────────────

    def _draw_combat_overlay(self, engine):
        """
        Draws the math combat dialog.
        Input widgets are handled by the scene, not here.
        This method just draws the static overlay background and text.
        """
        c = self.canvas
        prob = engine.combat_problem
        if not prob:
            return

        # Dim background
        c.create_rectangle(0, 0, SCREEN_W, SCREEN_H,
                           fill="#00000099", outline="")

        # Dialog box
        bx, by, bw, bh = 160, 140, 480, 280
        c.create_rectangle(bx, by, bx + bw, by + bh,
                           fill="#16213e", outline=C["inf_outer"],
                           width=3)
        # Header
        diff_colors = {"easy": "#2ecc71", "medium": "#f39c12", "hard": "#e74c3c"}
        dc = diff_colors.get(prob["difficulty"], "#ffffff")
        c.create_rectangle(bx, by, bx + bw, by + 38,
                           fill=dc, outline="")
        c.create_text(bx + bw // 2, by + 19,
                      text=f"⚔  MATH BATTLE  [{prob['difficulty'].upper()}]",
                      font=("Arial", 13, "bold"),
                      fill="#FFFFFF")

        # Enemy flavor
        enemy = engine.combat_enemy
        if enemy:
            enemy_name = {
                "easy":   "Slime Goblin",
                "medium": "Math Orc",
                "hard":   "Sigma Dragon"
            }.get(enemy.level, "Enemy")
            c.create_text(bx + bw // 2, by + 60,
                          text=f"🔮  {enemy_name}  challenges you!",
                          font=("Arial", 11), fill="#ccccff")

        # Question
        c.create_text(bx + bw // 2, by + 100,
                      text=prob["question"],
                      font=("Courier", 26, "bold"),
                      fill=C["text_hi"])

        # Reward info
        c.create_text(bx + bw // 2, by + 145,
                      text=(f"Correct → +{prob['base_points']} pts  |  "
                            f"Wrong → -{prob['base_points']//2} pts"),
                      font=("Arial", 10), fill=C["text_lo"])

        # Result feedback (shown briefly after submit)
        if engine.combat_result:
            res = engine.combat_result
            c.create_rectangle(bx + 20, by + 170, bx + bw - 20, by + 205,
                               fill="#000033", outline=res["color"], width=2)
            c.create_text(bx + bw // 2, by + 188,
                          text=res["message"],
                          font=("Arial", 11, "bold"),
                          fill=res["color"])
