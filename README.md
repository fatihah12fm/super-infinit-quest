# 🎮 Super Infinit Quest
> **Mata Kuliah:** Algoritme dan Pemrograman Dasar  
> **Bahasa:** Python 3.10+  
> **Library:** `tkinter` (built-in), `math`, `random` (built-in)  
> **Platform:** Windows / macOS / Linux

---

## 📖 Deskripsi Game

**Super Infinit Quest** adalah game platformer berbasis matematika. Pemain mengendalikan karakter berambut simbol ∞ yang harus menjelajahi dungeon, mengumpulkan **5 bintang utama** untuk menyelesaikan quest, sambil mengalahkan musuh dengan menjawab soal matematika.

### 🎯 Tujuan
- Kumpulkan 5 ⭐ yang tersebar di sepanjang level
- Kalahkan musuh dengan menjawab soal matematika dengan benar
- Kumpulkan koin sebanyak mungkin untuk menaikkan Score Bar
- Hindari rintangan (spike, dinding) agar tidak kehilangan HP

---

## 🚀 Cara Menjalankan

```bash
# Clone repositori
git clone https://github.com/USERNAME/super-infinit-quest.git
cd super-infinit-quest

# Jalankan game (tidak perlu install library tambahan)
python main.py
```

**Requirement:** Python 3.10+ (tkinter sudah termasuk bawaan Python)

---

## 🎮 Kontrol

| Tombol | Aksi |
|--------|------|
| `←` / `A` | Gerak kiri |
| `→` / `D` | Gerak kanan |
| `Space` / `↑` / `W` | Lompat |
| Sentuh musuh | Mulai Math Battle |
| `Enter` (di combat) | Submit jawaban |
| `R` (di win/dead) | Main lagi |
| `Q` (di win/dead) | Keluar |

---

## 📐 Formulasi Masalah Matematis

Game ini mengimplementasikan tiga tingkat kesulitan soal:

### Level Easy (Musuh Hijau)
- **Operasi:** Penjumlahan (+) dan Pengurangan (−)
- **Rentang:** Bilangan bulat 1–50
- **Contoh:** `23 + 17 = ?`, `45 − 12 = ?`
- **Base Points:** +50 (benar), −25 (salah)

### Level Medium (Musuh Kuning)
- **Operasi:** Perkalian (×) dan Pembagian (÷)
- **Rentang:** Faktor 2–12
- **Contoh:** `7 × 8 = ?`, `84 ÷ 7 = ?`
- **Base Points:** +100 (benar), −50 (salah)

### Level Hard (Musuh Merah)
- **Operasi:** Pangkat (^) dan Akar Kuadrat (√)
- **Rentang:** Basis 2–9 exp 2–3, perfect squares 4–225
- **Contoh:** `5 ^ 3 = ?`, `√144 = ?`
- **Base Points:** +200 (benar), −100 (salah)

---

## 🔢 Desain Algoritma

### 1. Score Formula
```
correct  → score = base_points + speed_bonus
wrong    → penalty = base_points // 2
speed_bonus = floor(base_points × (remaining_time / time_limit) × 0.5)
```

### 2. Physics (Gravity + Collision)
```
Step 1: Apply horizontal velocity → resolve horizontal platform collisions
Step 2: Apply gravity (vy += 0.55, max 18)
Step 3: Apply vertical velocity → resolve vertical platform collisions + ground
Step 4: Coyote-time tracking (6 frames)
```

### 3. Camera (Smooth Follow)
```python
cam_x += (target_x - cam_x) * 0.12   # lerp factor
```

### 4. Collision Detection
```
AABB (Axis-Aligned Bounding Box):
  overlap = (ax1 < bx2) AND (ax2 > bx1) AND (ay1 < by2) AND (ay2 > by1)
```

### 5. Level Generation (Procedural)
```
Seed-based random using: seed = base_seed + level_num × 137
Generates: platforms, coins, enemies, stars, obstacles
```

---

## 📁 Struktur File

```
super_infinit_quest/
├── main.py                  # Entry point
├── src/
│   ├── __init__.py
│   ├── math_engine.py       # Problem generator & validator
│   ├── entities.py          # Player, Enemy, Coin, Star, Obstacle, Platform
│   ├── engine.py            # Core game logic + level generation
│   ├── renderer.py          # Tkinter canvas rendering
│   └── scenes.py            # Scene manager (Menu, Game, Win, Dead)
├── docs/
│   └── analysis.md          # Game analysis & reflection
└── README.md
```

---

## 🧩 Logic Engine (Inti: Algoritma)

File `src/math_engine.py` adalah **inti algoritma** game ini:

```python
class MathEngine:
    def generate_problem(level)      # Generator soal berdasarkan difficulty
    def validate_answer(given, exp)  # Validator dengan float tolerance
    def calculate_score(...)         # Formula skor + speed bonus
    def record_result(...)           # Pencatatan statistik per soal
    def get_summary()                # Ringkasan akurasi & total score
```

---

## 📊 Analisis Game

Lihat [`docs/analysis.md`](docs/analysis.md) untuk analisis lengkap tentang:
- Bagaimana game membantu memahami konsep matematika
- Failure case & batasan sistem
- Refleksi algoritma vs UI

---

## 🏆 Win Condition
- Kumpulkan **5 bintang** yang tersebar di level
- HP tidak boleh habis (mulai dengan 5 HP)
- Setiap soal yang dijawab benar = musuh kalah + skor naik

## 💀 Fail Condition
- HP = 0 (dari jawaban salah + kena rintangan)
- Jatuh ke jurang (−2 HP)
