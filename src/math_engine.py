"""
math_engine.py
==============
Core mathematical problem generation and validation.

Implements:
  - Tiered question generator (Easy / Medium / Hard)
  - Answer validator with tolerance for float answers
  - Score calculator based on difficulty + speed
  - Statistics tracker (correct, wrong, avg time)

Formulasi Masalah Matematis:
  Easy   : +, -  (integers 1-50)
  Medium : *, /  (integers 2-12)
  Hard   : ^, sqrt (perfect squares, small bases)

Desain Algoritma:
  - generate_problem(level) → dict{question, answer, difficulty, points}
  - validate_answer(given, expected) → bool
  - calculate_score(base_points, time_taken, correct) → int
"""

import random
import math
import time


# ── Difficulty configuration ──────────────────────────────────────────────────
DIFFICULTY = {
    "easy":   {"label": "Easy",   "color": "#2ecc71", "base_pts": 50,  "time_limit": 15},
    "medium": {"label": "Medium", "color": "#f39c12", "base_pts": 100, "time_limit": 12},
    "hard":   {"label": "Hard",   "color": "#e74c3c", "base_pts": 200, "time_limit": 10},
}

PERFECT_SQUARES = [4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225]


class MathEngine:
    """
    Responsible for generating math problems and validating answers.
    Tracks per-session statistics.
    """

    def __init__(self):
        self.reset_stats()

    def reset_stats(self):
        self.total_questions = 0
        self.correct_answers = 0
        self.wrong_answers = 0
        self.total_score_earned = 0
        self.question_history = []   # list of dicts

    # ── Problem Generator ─────────────────────────────────────────────────────

    def generate_problem(self, level: str = "easy") -> dict:
        """
        Generate a math problem based on difficulty level.
        Returns: { question, answer, difficulty, base_points, time_limit }
        """
        if level == "easy":
            return self._gen_easy()
        elif level == "medium":
            return self._gen_medium()
        else:
            return self._gen_hard()

    def _gen_easy(self) -> dict:
        op = random.choice(["+", "-"])
        a = random.randint(1, 50)
        b = random.randint(1, 50)
        if op == "-":
            a, b = max(a, b), min(a, b)   # ensure non-negative result
        answer = a + b if op == "+" else a - b
        return {
            "question": f"{a} {op} {b} = ?",
            "answer": answer,
            "difficulty": "easy",
            "base_points": DIFFICULTY["easy"]["base_pts"],
            "time_limit": DIFFICULTY["easy"]["time_limit"],
        }

    def _gen_medium(self) -> dict:
        op = random.choice(["×", "÷"])
        if op == "×":
            a = random.randint(2, 12)
            b = random.randint(2, 12)
            answer = a * b
            question = f"{a} × {b} = ?"
        else:
            b = random.randint(2, 12)
            answer = random.randint(2, 12)
            a = b * answer
            question = f"{a} ÷ {b} = ?"
        return {
            "question": question,
            "answer": answer,
            "difficulty": "medium",
            "base_points": DIFFICULTY["medium"]["base_pts"],
            "time_limit": DIFFICULTY["medium"]["time_limit"],
        }

    def _gen_hard(self) -> dict:
        op = random.choice(["^", "√"])
        if op == "^":
            base = random.randint(2, 9)
            exp = random.randint(2, 3)
            answer = base ** exp
            question = f"{base} ^ {exp} = ?"
        else:
            val = random.choice(PERFECT_SQUARES)
            answer = int(math.sqrt(val))
            question = f"√{val} = ?"
        return {
            "question": question,
            "answer": answer,
            "difficulty": "hard",
            "base_points": DIFFICULTY["hard"]["base_pts"],
            "time_limit": DIFFICULTY["hard"]["time_limit"],
        }

    # ── Validator ─────────────────────────────────────────────────────────────

    def validate_answer(self, given: str, expected: int | float) -> bool:
        """
        Parse and validate player's answer.
        Returns True if correct, False otherwise.
        """
        try:
            val = float(given.strip())
            return abs(val - float(expected)) < 0.001
        except (ValueError, AttributeError):
            return False

    # ── Score Calculator ──────────────────────────────────────────────────────

    def calculate_score(self, base_points: int, time_taken: float,
                        time_limit: int, correct: bool) -> int:
        """
        Algorithm:
          correct  → score = base_points + speed_bonus
          wrong    → penalty = base_points // 2
          speed_bonus = floor(base_points * (remaining_time / time_limit) * 0.5)
        """
        if not correct:
            return -(base_points // 2)

        remaining = max(0, time_limit - time_taken)
        speed_bonus = int(base_points * (remaining / time_limit) * 0.5)
        return base_points + speed_bonus

    # ── Statistics ────────────────────────────────────────────────────────────

    def record_result(self, problem: dict, given: str,
                      time_taken: float) -> dict:
        """Record one Q&A event. Returns result summary dict."""
        correct = self.validate_answer(given, problem["answer"])
        score_delta = self.calculate_score(
            problem["base_points"], time_taken, problem["time_limit"], correct
        )

        self.total_questions += 1
        if correct:
            self.correct_answers += 1
        else:
            self.wrong_answers += 1
        self.total_score_earned += score_delta

        entry = {
            "question":    problem["question"],
            "correct_ans": problem["answer"],
            "given":       given,
            "correct":     correct,
            "score_delta": score_delta,
            "time_taken":  round(time_taken, 2),
            "difficulty":  problem["difficulty"],
        }
        self.question_history.append(entry)
        return entry

    def get_accuracy(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return round(self.correct_answers / self.total_questions * 100, 1)

    def get_summary(self) -> dict:
        return {
            "total":    self.total_questions,
            "correct":  self.correct_answers,
            "wrong":    self.wrong_answers,
            "accuracy": self.get_accuracy(),
            "score":    self.total_score_earned,
            "history":  self.question_history,
        }
