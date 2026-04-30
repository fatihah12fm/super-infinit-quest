# 📊 Analisis: Super Infinit Quest

> Dokumen ini memenuhi requirement **Konten dari Project** sesuai ketentuan dosen:  
> Formulasi masalah → Desain algoritma → Implementasi → Desain game → Analisis

---

## 1. Formulasi Masalah Matematis

### Masalah yang Dimodelkan
Game ini memodelkan **tes kemampuan aritmetika bertingkat** sebagai mekanik pertarungan:

| Tingkat | Operasi | Domain | Contoh |
|---------|---------|--------|--------|
| Easy   | +, −    | ℤ [1, 50] | 23 + 17 = 40 |
| Medium | ×, ÷    | ℤ [2×2, 12×12] | 7 × 8 = 56 |
| Hard   | x^n, √x | Bases 2–9, Perfect squares | √144 = 12 |

### Constraint Sistem
- Jawaban HARUS integer (float tolerance < 0.001)
- Soal pengurangan: hasil ≥ 0 (a ≥ b dijamin)
- Soal pembagian: hasil selalu integer (b × answer = a)
- Soal akar: hanya perfect squares → jawaban selalu integer

---

## 2. Desain Algoritma

### 2.1 Algoritma Generasi Soal
```
generate_problem(level):
  if level == "easy":
    op = random({+, -})
    a, b = random(1, 50)
    if op == "-": ensure a >= b
    return {question: "a op b = ?", answer: compute(a, op, b)}
  
  if level == "medium":
    op = random({×, ÷})
    if op == "×": a, b = random(2,12); ans = a*b
    if op == "÷": b = random(2,12); ans = random(2,12); a = b*ans
    return {question, answer: ans}
  
  if level == "hard":
    op = random({^, √})
    if op == "^": base = random(2,9); exp = random(2,3); ans = base**exp
    if op == "√": val = choice(PERFECT_SQUARES); ans = sqrt(val)
    return {question, answer: ans}
```

### 2.2 Algoritma Validasi
```
validate_answer(given, expected):
  try:
    val = float(given)
    return |val - expected| < 0.001
  except ValueError:
    return False
```

### 2.3 Algoritma Skor
```
calculate_score(base, time_taken, time_limit, correct):
  if not correct:
    return -(base // 2)   # penalty
  
  remaining = max(0, time_limit - time_taken)
  speed_bonus = floor(base × (remaining / time_limit) × 0.5)
  return base + speed_bonus
```

**Analisis:** Bonus kecepatan mendorong pemain untuk berpikir cepat, bukan hanya benar.

### 2.4 Algoritma Fisika (Gravity + AABB Collision)
```
update_position(platforms, ground_y):
  # Step 1: Horizontal
  x += vx
  for each platform:
    if overlaps(platform):
      resolve horizontal

  # Step 2: Vertical
  y += vy
  on_ground = False
  
  if y + h >= ground_y:
    y = ground_y - h; vy = 0; on_ground = True
  
  for each platform:
    if overlaps AND vy >= 0 AND prev_y_bottom <= plat.top + 4:
      y = plat.y - h; vy = 0; on_ground = True
  
  # Coyote time (6 frames grace period)
  if was_on_ground AND NOT on_ground:
    coyote_timer = 6
```

**Coyote time** adalah teknik game design: memberikan pemain 6 frame toleransi untuk melompat setelah meninggalkan platform — membuat kontrol terasa responsif.

### 2.5 Algoritma Kamera (Lerp)
```
camera_update():
  target_cam = player.x - SCREEN_W / 3
  cam_x += (target_cam - cam_x) × 0.12   # linear interpolation
  cam_x = clamp(cam_x, 0, LEVEL_LENGTH - SCREEN_W)
```

Lerp (Linear Interpolation) membuat kamera mengikuti pemain secara halus, tidak kaku.

### 2.6 Level Generation (Deterministic Random)
```
generate_level(seed):
  rng = Random(seed + level_num × 137)   # deterministic
  
  # Place ground coins at x += random(60, 130)
  # Place platforms at px += random(150, 300) with random heights
  # Place 30% moving platforms
  # Place obstacles at ox += random(200, 400)
  # Place 5 stars at LEVEL_LENGTH × k/6 for k in 1..5
  # Place 5 enemies with increasing difficulty
```

---

## 3. Implementasi Logic Engine

File: `src/math_engine.py`

**Ini adalah inti algoritma**, terpisah dari UI:
- `MathEngine` tidak bergantung pada tkinter
- Bisa diuji unit secara independen
- Menyimpan statistik lengkap per sesi
- Input/output murni Python (dict, str, int, float)

---

## 4. Desain Game Layer

Arsitektur yang digunakan adalah **Scene-Entity-Engine**:

```
SceneManager (tkinter root)
├── MenuScene      → title screen
├── GameScene      → game loop, memanggil GameEngine.update() setiap frame
│   ├── GameEngine → update physics, collision, score
│   └── Renderer   → draw ke canvas
├── WinScene       → victory + stats
└── DeadScene      → game over + stats
```

Separasi ini memastikan **logic engine tidak bergantung pada UI** (sesuai ketentuan PDF: "inti: algoritma, bukan UI").

### Visualisasi yang Ada
- Parallax background (3 layer, kecepatan berbeda)
- Karakter pixel-art dengan animasi walking, invincibility blink
- HP bar, Score bar, mini-map
- Enemy dengan label difficulty (E/M/H)
- Combat overlay dengan timer feedback
- Win/Dead screen dengan grade matematika

---

## 5. Analisis: Bagaimana Game Membantu Pemahaman?

### 5.1 Pembelajaran Melalui Konteks
Daripada mengerjakan soal di buku, pemain menghadapi soal dalam konteks **pertarungan yang mendesak**. Ini menciptakan:
- **Stakes nyata:** jawaban salah = HP berkurang
- **Motivasi intrinsik:** ingin mengalahkan musuh, bukan sekadar menjawab
- **Repetisi natural:** banyak musuh = banyak latihan tanpa terasa membosankan

### 5.2 Diferensiasi Kesulitan
Tiga tingkat soal memastikan:
- Pemain **tidak frustrasi** di awal (mulai easy)
- Ada **tantangan progresif** yang mendorong belajar
- Operasi harder (^, √) punya **base points lebih besar** = insentif untuk belajar

### 5.3 Failure Case & Batasan
| Failure Case | Konsekuensi | Catatan |
|---|---|---|
| Jawaban salah | −HP, penalty skor | Mendorong ketelitian |
| Jawab lambat | Tidak ada speed bonus | Mendorong kecepatan |
| HP habis | Game Over | Batasan keras |
| Jatuh ke jurang | −2 HP | Batasan platformer |

### 5.4 Limitasi Sistem (Constraint)
- Tidak semua metode/soal terlihat sama — ada 3 level berbeda
- Ada time limit per soal (10–15 detik)
- Skor negatif mungkin terjadi → harus strategis memilih pertarungan
- Musuh tidak bisa dilewati tanpa bertarung (harus berhadapan)

### 5.5 Nilai Edukasi
Setelah bermain, pemain diharapkan:
1. Lancar dengan operasi +, −, ×, ÷ sederhana
2. Mengenal pangkat kecil (2²–9³)
3. Mengenal akar kuadrat sempurna (√4–√225)
4. Memahami bahwa kecepatan berpikir matematika itu terlatih

---

## 6. Teknologi yang Digunakan

| Komponen | Library | Alasan |
|---|---|---|
| GUI/Canvas | `tkinter` (built-in) | Tidak perlu install, lintas platform |
| Matematika | `math` (built-in) | `sqrt`, `floor` |
| Randomisasi | `random` (built-in) | Soal & level generation |
| Timing | `time` (built-in) | Speed bonus calculation |

**Tidak menggunakan:** Unity, Unreal, web framework, atau library eksternal apapun — sesuai ketentuan PDF.
