"""
tests/test_math_engine.py
=========================
Unit tests for the MathEngine (core algorithm).
Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.math_engine import MathEngine


@pytest.fixture
def engine():
    return MathEngine()


class TestGeneration:
    def test_easy_returns_correct_keys(self, engine):
        p = engine.generate_problem("easy")
        assert "question" in p
        assert "answer" in p
        assert "difficulty" in p
        assert "base_points" in p
        assert "time_limit" in p

    def test_easy_answer_correct(self, engine):
        """Generated easy question must be self-consistent."""
        for _ in range(50):
            p = engine.generate_problem("easy")
            # Parse question like "23 + 17 = ?"
            parts = p["question"].replace(" = ?", "").split()
            a, op, b = int(parts[0]), parts[1], int(parts[2])
            if op == "+":
                assert p["answer"] == a + b
            else:
                assert p["answer"] == a - b
                assert p["answer"] >= 0   # no negative results

    def test_medium_multiplication(self, engine):
        for _ in range(30):
            p = engine.generate_problem("medium")
            q = p["question"]
            if "×" in q:
                parts = q.replace(" = ?", "").split()
                a, b = int(parts[0]), int(parts[2])
                assert p["answer"] == a * b

    def test_medium_division_integer(self, engine):
        for _ in range(30):
            p = engine.generate_problem("medium")
            q = p["question"]
            if "÷" in q:
                parts = q.replace(" = ?", "").split()
                a, b = int(parts[0]), int(parts[2])
                assert a % b == 0   # always exact division
                assert p["answer"] == a // b

    def test_hard_power(self, engine):
        import math
        for _ in range(40):
            p = engine.generate_problem("hard")
            q = p["question"]
            if "^" in q:
                parts = q.replace(" = ?", "").split()
                base, exp = int(parts[0]), int(parts[2])
                assert p["answer"] == base ** exp

    def test_hard_sqrt_perfect_square(self, engine):
        import math
        for _ in range(40):
            p = engine.generate_problem("hard")
            q = p["question"]
            if "√" in q:
                val = int(q.replace("√", "").replace(" = ?", ""))
                expected = int(math.sqrt(val))
                assert p["answer"] == expected
                assert expected * expected == val   # confirm perfect square

    def test_difficulty_labels(self, engine):
        for lvl in ["easy", "medium", "hard"]:
            p = engine.generate_problem(lvl)
            assert p["difficulty"] == lvl


class TestValidation:
    def test_correct_integer(self, engine):
        assert engine.validate_answer("42", 42) is True

    def test_correct_float_tolerance(self, engine):
        assert engine.validate_answer("12.0", 12) is True

    def test_wrong_answer(self, engine):
        assert engine.validate_answer("99", 42) is False

    def test_empty_string(self, engine):
        assert engine.validate_answer("", 42) is False

    def test_invalid_string(self, engine):
        assert engine.validate_answer("abc", 42) is False

    def test_negative_answer(self, engine):
        assert engine.validate_answer("-5", -5) is True


class TestScoreCalculation:
    def test_correct_no_speed_bonus(self, engine):
        """No time remaining → no speed bonus."""
        pts = engine.calculate_score(100, 12, 12, correct=True)
        assert pts == 100  # base only

    def test_correct_max_speed_bonus(self, engine):
        """All time remaining → max speed bonus = base * 0.5."""
        pts = engine.calculate_score(100, 0, 10, correct=True)
        assert pts == 150  # 100 + 50

    def test_wrong_penalty(self, engine):
        pts = engine.calculate_score(100, 0, 10, correct=False)
        assert pts == -50

    def test_medium_timing(self, engine):
        pts = engine.calculate_score(100, 5, 10, correct=True)
        # remaining=5, bonus = floor(100 * 0.5 * 0.5) = 25
        assert pts == 125


class TestStatistics:
    def test_record_correct(self, engine):
        p = engine.generate_problem("easy")
        result = engine.record_result(p, str(p["answer"]), 3.0)
        assert result["correct"] is True
        assert result["score_delta"] > 0
        assert engine.correct_answers == 1
        assert engine.wrong_answers == 0

    def test_record_wrong(self, engine):
        p = engine.generate_problem("easy")
        wrong = str(p["answer"] + 99)
        result = engine.record_result(p, wrong, 3.0)
        assert result["correct"] is False
        assert result["score_delta"] < 0
        assert engine.wrong_answers == 1

    def test_accuracy_100(self, engine):
        for _ in range(5):
            p = engine.generate_problem("easy")
            engine.record_result(p, str(p["answer"]), 1.0)
        assert engine.get_accuracy() == 100.0

    def test_accuracy_50(self, engine):
        for i in range(4):
            p = engine.generate_problem("easy")
            ans = str(p["answer"]) if i < 2 else str(p["answer"] + 99)
            engine.record_result(p, ans, 1.0)
        assert engine.get_accuracy() == 50.0

    def test_reset(self, engine):
        p = engine.generate_problem("easy")
        engine.record_result(p, str(p["answer"]), 1.0)
        engine.reset_stats()
        assert engine.total_questions == 0
        assert engine.correct_answers == 0

    def test_summary_keys(self, engine):
        s = engine.get_summary()
        for key in ["total", "correct", "wrong", "accuracy", "score", "history"]:
            assert key in s
