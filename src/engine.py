"""
engine.py
=========
Core game logic engine.

Responsibilities:
  - Level generation (procedural platform/enemy/coin/star layout)
  - Game loop tick (update all entities)
  - Collision detection & response
  - Camera system (smooth follow)
  - Win/lose condition checking
  - Score & progress management

Design Algoritma:
  - Procedural level generation using seed-based random placement
  - Camera: lerp(cam_x, player.x - center, 0.1)
  - Collision: AABB (Axis-Aligned Bounding Box)
  - Score formula: in math_engine.py
"""

import random
from src.entities import (
    Player, Enemy, Coin, Star, Obstacle, Platform,
    GROUND_Y, C
)
from src.math_engine import MathEngine


LEVEL_LENGTH   = 5000   # total pixel width of the level
SCREEN_W       = 800
SCREEN_H       = 600
TOTAL_STARS    = 5      # must collect all 5 to win


class GameEngine:

    def __init__(self):
        self.math = MathEngine()
        self.reset()

    def reset(self):
        self.math.reset_stats()
        self.player = Player(80, GROUND_Y - 60)
        self.platforms: list[Platform] = []
        self.enemies:   list[Enemy]    = []
        self.coins:     list[Coin]     = []
        self.stars:     list[Star]     = []
        self.obstacles: list[Obstacle] = []

        self.cam_x     = 0.0
        self.score     = 0
        self.score_bar = 0      # 0-100 progress toward star unlock
        self.level_num = 1
        self.state     = "playing"   # playing | combat | win | dead
        self.message   = ""
        self.msg_timer = 0

        self.combat_problem = None
        self.combat_enemy   = None
        self.combat_result  = None   # "correct" | "wrong" | None
        self.combat_timer   = 0

        self._generate_level()

    # ── Level Generation ──────────────────────────────────────────────────────

    def _generate_level(self, seed=42):
        rng = random.Random(seed + self.level_num * 137)

        # Ground-level coins
        x = 150
        while x < LEVEL_LENGTH - 200:
            self.coins.append(Coin(x, GROUND_Y - 25))
            x += rng.randint(60, 130)

        # Platforms + elevated coins
        px = 200
        while px < LEVEL_LENGTH - 300:
            pw = rng.randint(90, 200)
            ph_offset = rng.randint(80, 200)
            py = GROUND_Y - ph_offset
            moving = rng.random() < 0.3
            mr = rng.randint(60, 120) if moving else 0
            self.platforms.append(
                Platform(px, py, pw, moving=moving, move_range=mr)
            )
            # Coins on platform
            for i in range(rng.randint(1, 3)):
                self.coins.append(Coin(px + 20 + i * 40, py - 20))
            px += rng.randint(150, 300)

        # Spikes/obstacles
        ox = 300
        while ox < LEVEL_LENGTH - 200:
            kind = "spike" if rng.random() < 0.7 else "wall"
            self.obstacles.append(Obstacle(ox, GROUND_Y - 20, kind))
            ox += rng.randint(200, 400)

        # Stars spread evenly across the level
        star_xs = [
            LEVEL_LENGTH // 6,
            LEVEL_LENGTH * 2 // 6,
            LEVEL_LENGTH * 3 // 6,
            LEVEL_LENGTH * 4 // 6,
            LEVEL_LENGTH * 5 // 6,
        ]
        for sx in star_xs:
            plat = self._nearest_platform(sx)
            sy = (plat.y - 50) if plat else (GROUND_Y - 180)
            self.stars.append(Star(sx, sy))

        # Enemies - mix of difficulties
        lvls = ["easy", "easy", "medium", "medium", "hard"]
        rng.shuffle(lvls)
        ex = 350
        for lvl in lvls:
            self.enemies.append(Enemy(ex, GROUND_Y - 44, level=lvl,
                                      patrol_range=rng.randint(60, 140)))
            ex += rng.randint(400, 700)

        # Finish flag area marker
        self.finish_x = LEVEL_LENGTH - 120

    def _nearest_platform(self, tx):
        if not self.platforms:
            return None
        return min(self.platforms, key=lambda p: abs(p.x + p.w // 2 - tx))

    # ── Main Update (one frame) ───────────────────────────────────────────────

    def update(self, keys):
        """
        Called every frame (~60 fps).
        keys: set of currently pressed key names.
        """
        if self.state != "playing":
            # Handle combat timer
            if self.state == "combat":
                pass   # input handled by scene
            if self.msg_timer > 0:
                self.msg_timer -= 1
                if self.msg_timer == 0:
                    self.message = ""
            return

        p = self.player

        # ── Input → physics ──────────────────────────────────────────────────
        moving = False
        if "Left" in keys or "a" in keys:
            p.move_left(); moving = True
        if "Right" in keys or "d" in keys:
            p.move_right(); moving = True
        if not moving:
            p.stop_x()
        if "space" in keys or "Up" in keys or "w" in keys:
            p.jump()

        p.apply_gravity()

        # Update platforms first (some are moving)
        for plat in self.platforms:
            plat.update()

        p.update_position(self.platforms, GROUND_Y)

        # ── Camera (smooth lerp) ─────────────────────────────────────────────
        target_cam = p.x - SCREEN_W // 3
        self.cam_x += (target_cam - self.cam_x) * 0.12
        self.cam_x = max(0, min(self.cam_x, LEVEL_LENGTH - SCREEN_W))

        # ── Entity updates ────────────────────────────────────────────────────
        for e in self.enemies:
            if not e.defeated:
                e.update()
        for c in self.coins:
            if c.active:
                c.update()

        # ── Collision: coins ──────────────────────────────────────────────────
        for coin in self.coins:
            if coin.active and p.collides_with(coin):
                coin.active = False
                self._add_score(Coin.VALUE, "coin")
                self.player.coins_collected += 1

        # ── Collision: stars ──────────────────────────────────────────────────
        for star in self.stars:
            if star.active and p.collides_with(star):
                star.active = False
                self.player.stars_collected += 1
                self._add_score(300, "star")
                self._show_msg(f"⭐ Star {self.player.stars_collected}/{TOTAL_STARS} !")
                if self.player.stars_collected >= TOTAL_STARS:
                    self.state = "win"
                    return

        # ── Collision: obstacles ──────────────────────────────────────────────
        for obs in self.obstacles:
            if p.collides_with(obs):
                if p.take_damage(1):
                    self._add_score(-30, "obstacle")
                    self._show_msg("Ouch! -30")
                    p.vy = -8   # bounce up
                    p.x += 40 if p.vx <= 0 else -40

        # ── Collision: enemies ────────────────────────────────────────────────
        for enemy in self.enemies:
            if enemy.defeated or enemy.active is False:
                continue
            if p.collides_with(enemy):
                # Trigger math combat
                self.state = "combat"
                self.combat_enemy = enemy
                self.combat_problem = self.math.generate_problem(enemy.level)
                self.combat_result = None
                return

        # ── Boundary (fall into pit) ──────────────────────────────────────────
        if p.y > SCREEN_H + 100:
            if p.take_damage(2):
                p.x = max(60, self.cam_x + 80)
                p.y = GROUND_Y - 80
                p.vy = 0
                self._show_msg("Fell into the void! -2 HP")

        # ── Death check ───────────────────────────────────────────────────────
        if p.hp <= 0:
            self.state = "dead"

        # ── Score bar progress ────────────────────────────────────────────────
        self.score_bar = min(100, int(self.score / 50))

        # ── Msg timer ────────────────────────────────────────────────────────
        if self.msg_timer > 0:
            self.msg_timer -= 1
            if self.msg_timer == 0:
                self.message = ""

    # ── Combat resolution ─────────────────────────────────────────────────────

    def resolve_combat(self, answer: str) -> dict:
        """
        Called when player submits answer during combat.
        Returns result dict with score_delta, correct, message.
        """
        import time
        result = self.math.record_result(
            self.combat_problem, answer, time_taken=0.0
        )

        if result["correct"]:
            self.combat_enemy.defeated = True
            self.combat_enemy.active = False
            pts = result["score_delta"]
            self._add_score(pts, "combat_win")
            result["message"] = f"Correct! +{pts} pts  Enemy defeated!"
            result["color"] = "#2ecc71"
        else:
            if self.player.take_damage(1):
                self._add_score(result["score_delta"], "combat_loss")
            result["message"] = (
                f"Wrong! Answer was {self.combat_problem['answer']}. "
                f"{result['score_delta']} pts"
            )
            result["color"] = "#e74c3c"

        self.combat_result = result
        return result

    def exit_combat(self):
        """Return to playing state after combat feedback shown."""
        self.state = "playing"
        self.combat_enemy   = None
        self.combat_problem = None
        self.combat_result  = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _add_score(self, delta: int, reason: str = ""):
        self.score = max(0, self.score + delta)
        self.player.score = self.score

    def _show_msg(self, text: str, duration: int = 100):
        self.message = text
        self.msg_timer = duration

    def get_state_snapshot(self) -> dict:
        p = self.player
        return {
            "score":      self.score,
            "hp":         p.hp,
            "max_hp":     p.MAX_HP,
            "stars":      p.stars_collected,
            "coins":      p.coins_collected,
            "score_bar":  self.score_bar,
            "state":      self.state,
            "message":    self.message,
            "cam_x":      self.cam_x,
            "math_stats": self.math.get_summary(),
        }
