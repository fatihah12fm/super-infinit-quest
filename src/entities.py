"""
entities.py
===========
All game entities: Player, Enemy, Coin, Star, Obstacle, Platform.

Each entity holds:
  - position (x, y)
  - size (w, h)
  - velocity (vx, vy)
  - state flags
  - draw() method using tkinter canvas tags

Player sprite is drawn pixel-art style matching the reference image:
  - Dark red triangle body
  - Golden infinity symbol on head
  - Orange legs, teal shoes
  - Holding a red weapon
"""

import math


# ── Color palette (matches reference image) ───────────────────────────────────
C = {
    "body_dark":    "#5C0A0A",
    "body_main":    "#8B1A1A",
    "body_light":   "#A52020",
    "legs":         "#E8950A",
    "shoes":        "#1ABC9C",
    "inf_outer":    "#D4A017",
    "inf_inner":    "#F0C040",
    "weapon":       "#8B1A1A",
    "weapon_dark":  "#5C0A0A",
    "outline":      "#111111",
    "eye":          "#1a1a1a",
    "white":        "#FFFFFF",
    "coin":         "#FFD700",
    "coin_rim":     "#B8860B",
    "star_fill":    "#FFD700",
    "star_outline": "#FFA500",
    "enemy_body":   "#6B21A8",
    "enemy_eye":    "#FF4444",
    "platform":     "#5D4E37",
    "platform_top": "#8B7355",
    "spike":        "#C0392B",
    "bg_sky":       "#1a1a2e",
    "bg_mid":       "#16213e",
    "ground":       "#0f3460",
    "ground_top":   "#1a4a7a",
    "score_bar":    "#2ecc71",
    "score_bg":     "#1e3a1e",
    "hp_bar":       "#e74c3c",
    "hp_bg":        "#3a1e1e",
    "text_hi":      "#FFD700",
    "text_lo":      "#aaaaaa",
}

GRAVITY = 0.45
JUMP_FORCE = -15
MOVE_SPEED = 5
GROUND_Y = 500     # pixel Y of the main ground
LEVEL_LENGTH = 5000
SCREEN_W = 800
SCREEN_H = 600
TOTAL_STARS = 5


# ── Base Entity ───────────────────────────────────────────────────────────────

class Entity:
    def __init__(self, x, y, w, h):
        self.x = float(x)
        self.y = float(y)
        self.w = w
        self.h = h
        self.vx = 0.0
        self.vy = 0.0
        self.active = True
        self._tags = []

    @property
    def rect(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def collides_with(self, other):
        ax1, ay1, ax2, ay2 = self.rect
        bx1, by1, bx2, by2 = other.rect
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    def clear(self, canvas):
        for tag in self._tags:
            canvas.delete(tag)
        self._tags = []


# ── Platform ──────────────────────────────────────────────────────────────────

class Platform(Entity):
    def __init__(self, x, y, w, h=18, moving=False,
                 move_range=0, move_speed=1.5):
        super().__init__(x, y, w, h)
        self.moving = moving
        self.move_range = move_range
        self.move_speed = move_speed
        self._origin_x = x
        self._dir = 1

    def update(self):
        if not self.moving:
            return
        self.x += self.move_speed * self._dir
        if abs(self.x - self._origin_x) >= self.move_range:
            self._dir *= -1

    def draw(self, canvas, cam_x=0):
        px = self.x - cam_x
        tag = f"plat_{id(self)}"
        canvas.delete(tag)
        canvas.create_rectangle(
            px, self.y, px + self.w, self.y + self.h,
            fill=C["platform"], outline=C["outline"], width=1, tags=tag
        )
        canvas.create_rectangle(
            px, self.y, px + self.w, self.y + 5,
            fill=C["platform_top"], outline="", tags=tag
        )
        self._tags = [tag]


# ── Obstacle ──────────────────────────────────────────────────────────────────

class Obstacle(Entity):
    KIND_SPIKE = "spike"
    KIND_WALL  = "wall"

    def __init__(self, x, y, kind=KIND_SPIKE):
        if kind == Obstacle.KIND_SPIKE:
            super().__init__(x, y, 20, 20)
        else:
            super().__init__(x, y, 20, 40)
        self.kind = kind

    def draw(self, canvas, cam_x=0):
        px = self.x - cam_x
        tag = f"obs_{id(self)}"
        canvas.delete(tag)
        if self.kind == Obstacle.KIND_SPIKE:
            pts = [px + 10, self.y, px, self.y + 20, px + 20, self.y + 20]
            canvas.create_polygon(pts, fill=C["spike"],
                                  outline=C["outline"], tags=tag)
        else:
            canvas.create_rectangle(
                px, self.y, px + self.w, self.y + self.h,
                fill="#555555", outline=C["outline"], tags=tag
            )
        self._tags = [tag]


# ── Coin ──────────────────────────────────────────────────────────────────────

class Coin(Entity):
    RADIUS = 9
    VALUE  = 10

    def __init__(self, x, y):
        r = Coin.RADIUS
        super().__init__(x - r, y - r, r * 2, r * 2)
        self._float_offset = 0.0
        self._float_dir = 1
        self._base_y = float(y - r)

    def update(self):
        self._float_offset += 0.06 * self._float_dir
        if abs(self._float_offset) > 4:
            self._float_dir *= -1
        self.y = self._base_y + self._float_offset

    def draw(self, canvas, cam_x=0):
        px = self.x - cam_x + Coin.RADIUS
        py = self.y + Coin.RADIUS
        tag = f"coin_{id(self)}"
        canvas.delete(tag)
        canvas.create_oval(
            px - Coin.RADIUS, py - Coin.RADIUS,
            px + Coin.RADIUS, py + Coin.RADIUS,
            fill=C["coin"], outline=C["coin_rim"], width=2, tags=tag
        )
        canvas.create_text(px, py, text="¢",
                           font=("Arial", 9, "bold"),
                           fill=C["coin_rim"], tags=tag)
        self._tags = [tag]


# ── Star ──────────────────────────────────────────────────────────────────────

class Star(Entity):
    RADIUS = 14

    def __init__(self, x, y):
        r = Star.RADIUS
        super().__init__(x - r, y - r, r * 2, r * 2)
        self._pulse = 0.0

    def _star_points(self, cx, cy, outer, inner, n=5):
        pts = []
        for i in range(n * 2):
            angle = math.pi / n * i - math.pi / 2
            r = outer if i % 2 == 0 else inner
            pts.extend([cx + r * math.cos(angle), cy + r * math.sin(angle)])
        return pts

    def draw(self, canvas, cam_x=0):
        px = self.x - cam_x + Star.RADIUS
        py = self.y + Star.RADIUS
        self._pulse = (self._pulse + 0.05) % (2 * math.pi)
        scale = 1.0 + 0.08 * math.sin(self._pulse)
        tag = f"star_{id(self)}"
        canvas.delete(tag)
        pts = self._star_points(px, py, Star.RADIUS * scale,
                                Star.RADIUS * 0.45 * scale)
        canvas.create_polygon(pts, fill=C["star_fill"],
                              outline=C["star_outline"], width=1.5, tags=tag)
        canvas.create_text(px, py, text="★",
                           font=("Arial", 7), fill="#FFF8DC", tags=tag)
        self._tags = [tag]


# ── Enemy ─────────────────────────────────────────────────────────────────────

class Enemy(Entity):
    def __init__(self, x, y, level="easy", patrol_range=100):
        super().__init__(x, y, 34, 40)
        self.level = level      # determines math difficulty
        self.patrol_range = patrol_range
        self._origin_x = float(x)
        self._dir = 1
        self.speed = 1.2
        self.defeated = False
        self._anim = 0

    def update(self):
        self.x += self.speed * self._dir
        self._anim += 0.08
        if abs(self.x - self._origin_x) >= self.patrol_range:
            self._dir *= -1

    def draw(self, canvas, cam_x=0):
        px = self.x - cam_x
        py = self.y
        tag = f"enemy_{id(self)}"
        canvas.delete(tag)

        bob = math.sin(self._anim) * 2

        # Body (slime-like)
        canvas.create_oval(
            px, py + bob, px + self.w, py + self.h + bob,
            fill=C["enemy_body"], outline=C["outline"], width=1, tags=tag
        )
        # Eyes
        ex1, ex2 = px + 7, px + 21
        ey = py + 14 + bob
        for ex in [ex1, ex2]:
            canvas.create_oval(ex, ey, ex + 6, ey + 6,
                               fill="#FFFFFF", outline=C["outline"], tags=tag)
            canvas.create_oval(ex + 1, ey + 1, ex + 4, ey + 4,
                               fill=C["enemy_eye"], outline="", tags=tag)
        # Difficulty label
        lvl_colors = {"easy": "#2ecc71", "medium": "#f39c12", "hard": "#e74c3c"}
        lvl_labels = {"easy": "E", "medium": "M", "hard": "H"}
        canvas.create_text(px + self.w // 2, py + self.h + 10 + bob,
                           text=lvl_labels[self.level],
                           font=("Arial", 9, "bold"),
                           fill=lvl_colors[self.level], tags=tag)
        self._tags = [tag]


# ── Player ────────────────────────────────────────────────────────────────────

class Player(Entity):
    MAX_HP    = 5
    COYOTE    = 6   # coyote-time frames

    def __init__(self, x, y):
        super().__init__(x, y, 36, 52)
        self.hp = Player.MAX_HP
        self.score = 0
        self.stars_collected = 0
        self.coins_collected = 0
        self.on_ground = False
        self._facing = 1     # 1=right, -1=left
        self._walk_frame = 0
        self._coyote_timer = 0
        self._inv_timer = 0   # invincibility frames after hit
        self._anim_tick = 0

    # ── Physics ──────────────────────────────────────────────────────────────

    def apply_gravity(self):
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > 18:
                self.vy = 18

    def jump(self):
        can_jump = self.on_ground or self._coyote_timer > 0
        if can_jump:
            self.vy = JUMP_FORCE
            self.on_ground = False
            self._coyote_timer = 0

    def move_left(self):
        self.vx = -MOVE_SPEED
        self._facing = -1

    def move_right(self):
        self.vx = MOVE_SPEED
        self._facing = 1

    def stop_x(self):
        self.vx = 0

    def update_position(self, platforms, ground_y):
        """
        Move player, resolve collisions.
        Algorithm:
          1. Apply horizontal movement
          2. Resolve horizontal platform collisions
          3. Apply vertical movement
          4. Resolve vertical platform collisions + ground
          5. Update coyote timer
        """
        self.x += self.vx
        # Horizontal collision with platforms
        for plat in platforms:
            if self._overlaps(plat):
                if self.vx > 0:
                    self.x = plat.x - self.w
                elif self.vx < 0:
                    self.x = plat.x + plat.w

        self.y += self.vy
        was_on_ground = self.on_ground
        self.on_ground = False

        # Ground
        if self.y + self.h >= ground_y:
            self.y = ground_y - self.h
            self.vy = 0
            self.on_ground = True

        # Platform top collision
        for plat in platforms:
            if self._overlaps(plat) and self.vy >= 0:
                if self.y + self.h - self.vy <= plat.y + 4:
                    self.y = plat.y - self.h
                    self.vy = 0
                    self.on_ground = True

        # Coyote time
        if was_on_ground and not self.on_ground:
            self._coyote_timer = Player.COYOTE
        elif self._coyote_timer > 0:
            self._coyote_timer -= 1

        # Invincibility countdown
        if self._inv_timer > 0:
            self._inv_timer -= 1

        self._anim_tick += 1
        if self.on_ground and self.vx != 0:
            self._walk_frame = (self._walk_frame + 1) % 6

    def _overlaps(self, other):
        return (self.x < other.x + other.w and self.x + self.w > other.x and
                self.y < other.y + other.h and self.y + self.h > other.y)

    def take_damage(self, amount=1):
        if self._inv_timer > 0:
            return False
        self.hp -= amount
        self._inv_timer = 60   # 1 second invincibility
        return True

    def is_invincible(self):
        return self._inv_timer > 0

    # ── Pixel-Art Draw ────────────────────────────────────────────────────────
    # Matches the reference sprite: triangle body, infinity crown, orange legs,
    # teal shoes, red weapon in hand.

    def draw(self, canvas, cam_x=0):
        px = self.x - cam_x
        py = self.y
        tag = f"player_{id(self)}"
        canvas.delete(tag)

        # Blink when invincible
        if self._inv_timer > 0 and (self._inv_timer // 4) % 2 == 0:
            self._tags = [tag]
            return

        flip = self._facing == -1
        cx = px + self.w // 2

        def mx(x_offset):
            """Mirror x-offset based on facing direction."""
            return cx + (x_offset if not flip else -x_offset)

        # ── Shoes (teal) ──────────────────────────────────────────────────────
        canvas.create_rectangle(
            mx(-14), py + 44, mx(-2), py + 52,
            fill=C["shoes"], outline=C["outline"], width=1, tags=tag
        )
        canvas.create_rectangle(
            mx(2), py + 44, mx(14), py + 52,
            fill=C["shoes"], outline=C["outline"], width=1, tags=tag
        )

        # ── Legs (orange) ─────────────────────────────────────────────────────
        leg_bob = 0
        if self.on_ground and self.vx != 0:
            leg_bob = 3 if self._walk_frame < 3 else -3

        canvas.create_rectangle(
            mx(-13), py + 32 + leg_bob, mx(-3), py + 46 + leg_bob,
            fill=C["legs"], outline=C["outline"], width=1, tags=tag
        )
        canvas.create_rectangle(
            mx(3), py + 32 - leg_bob, mx(13), py + 46 - leg_bob,
            fill=C["legs"], outline=C["outline"], width=1, tags=tag
        )

        # ── Body (dark-red triangle) ──────────────────────────────────────────
        body_pts = [
            mx(0),   py + 2,    # apex
            mx(-18), py + 34,   # bottom-left
            mx(18),  py + 34,   # bottom-right
        ]
        canvas.create_polygon(body_pts,
                              fill=C["body_main"],
                              outline=C["outline"], width=1, tags=tag)
        # Dark shading on one side
        shade_pts = [
            mx(0),   py + 2,
            mx(-18), py + 34,
            mx(-6),  py + 34,
        ]
        canvas.create_polygon(shade_pts, fill=C["body_dark"],
                              outline="", tags=tag)
        # Highlight
        hi_pts = [
            mx(0),  py + 2,
            mx(8),  py + 16,
            mx(16), py + 34,
        ]
        canvas.create_polygon(hi_pts, fill=C["body_light"],
                              outline="", tags=tag)

        # Eyes on body
        canvas.create_rectangle(
            mx(-7), py + 16, mx(-2), py + 23,
            fill=C["eye"], outline="", tags=tag
        )
        canvas.create_rectangle(
            mx(2), py + 16, mx(7), py + 23,
            fill=C["eye"], outline="", tags=tag
        )

        # ── Weapon (right side) ───────────────────────────────────────────────
        wx_start = mx(18)
        wx_end   = mx(30)
        canvas.create_rectangle(
            wx_start, py + 18, wx_end, py + 28,
            fill=C["weapon"], outline=C["outline"], width=1, tags=tag
        )
        canvas.create_rectangle(
            wx_end - 4, py + 16, wx_end + 6, py + 30,
            fill=C["weapon_dark"], outline=C["outline"], width=1, tags=tag
        )

        # ── Infinity Crown ────────────────────────────────────────────────────
        self._draw_infinity(canvas, cx, py - 8, tag)

        self._tags = [tag]

    def _draw_infinity(self, canvas, cx, cy, tag):
        """Draw ∞ symbol as two golden loops above the character."""
        r = 7
        # Left loop
        canvas.create_oval(cx - 16, cy - r, cx - 2, cy + r,
                           fill=C["inf_inner"], outline=C["inf_outer"],
                           width=2, tags=tag)
        # Right loop
        canvas.create_oval(cx + 2, cy - r, cx + 16, cy + r,
                           fill=C["inf_inner"], outline=C["inf_outer"],
                           width=2, tags=tag)
        # Center cross (creates the figure-8)
        canvas.create_oval(cx - 5, cy - 4, cx + 5, cy + 4,
                           fill=C["inf_inner"], outline=C["inf_outer"],
                           width=1, tags=tag)
