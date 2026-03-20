"""Tests for the three financial skills."""
from __future__ import annotations

import pytest

from src.skills.equity_research import _extract_verdict, _parse_sections, _extract_price_target
from src.skills.prediction_market_coach import (
    _kelly_verdict, _extract_grade, _grade_to_score, _detect_biases,
)
from src.skills.financial_dispatch import _apply_editorial_standards
from src.models import TradeGradeRequest


# ---------------------------------------------------------------------------
# equity-research skill
# ---------------------------------------------------------------------------
class TestEquityResearchParsing:
    def test_parse_sections_extracts_headers(self):
        text = "## Investment Summary & Rating\nBuy rating.\n## Key Risks\nRisk 1."
        sections = _parse_sections(text)
        assert "Investment Summary & Rating" in sections
        assert "Key Risks" in sections
        assert "Buy rating." in sections["Investment Summary & Rating"]

    def test_extract_verdict_buy(self):
        assert _extract_verdict("We initiate with a Buy rating.") == "Buy"

    def test_extract_verdict_overweight(self):
        assert _extract_verdict("Overweight, price target €120.") == "Overweight"

    def test_extract_verdict_default_hold(self):
        assert _extract_verdict("No clear view here.") == "Hold"

    def test_extract_price_target_dollar(self):
        text = "12-month price target of $145."
        pt = _extract_price_target(text)
        assert pt is not None
        assert "145" in pt

    def test_extract_price_target_euro(self):
        text = "Target price: €78.50"
        pt = _extract_price_target(text)
        assert pt is not None
        assert "78" in pt

    def test_extract_price_target_none(self):
        pt = _extract_price_target("No specific price target given.")
        assert pt is None


# ---------------------------------------------------------------------------
# prediction-market-coach skill
# ---------------------------------------------------------------------------
class TestKellyVerdictClassification:
    def test_optimal_sizing(self):
        # Actual = 5%, Kelly recommended = 5%
        assert _kelly_verdict(5.0, 5.0) == "optimal"

    def test_over_sizing(self):
        # Actual = 20%, Kelly = 5%  → ratio = 4 → "over"
        assert _kelly_verdict(20.0, 5.0) == "over"

    def test_under_sizing(self):
        # Actual = 1%, Kelly = 5%  → ratio = 0.2 → "under"
        assert _kelly_verdict(1.0, 5.0) == "under"

    def test_no_edge(self):
        # Kelly = 0 → any positive bet is "no_edge"
        assert _kelly_verdict(2.0, 0.0) == "no_edge"

    def test_zero_size_with_zero_kelly(self):
        assert _kelly_verdict(0.0, 0.0) == "optimal"


class TestGradeExtraction:
    def test_extracts_explicit_grade(self):
        assert _extract_grade("Grade: A — excellent process.") == "A"

    def test_extracts_grade_b(self):
        assert _extract_grade("Grade: B — good work overall.") == "B"

    def test_defaults_to_c(self):
        assert _extract_grade("No grade mentioned here.") == "C"


class TestGradeToScore:
    def test_a_is_highest(self):
        assert _grade_to_score("A") == 9.0

    def test_f_is_lowest(self):
        assert _grade_to_score("F") == 1.0

    def test_ordering(self):
        assert _grade_to_score("A") > _grade_to_score("B") > _grade_to_score("C") > \
               _grade_to_score("D") > _grade_to_score("F")


class TestBiasDetection:
    def test_detects_overconfidence(self):
        biases = _detect_biases("The trader was clearly overconfident in their edge estimate.")
        assert "overconfidence" in biases

    def test_detects_recency_bias(self):
        biases = _detect_biases("Heavy recency bias — too influenced by recent events.")
        assert "recency_bias" in biases

    def test_detects_football_overconcentration(self):
        biases = _detect_biases("Too focused on football markets.")
        assert "football_overconcentration" in biases

    def test_no_false_positives_on_clean_text(self):
        biases = _detect_biases("Clean process, well-calibrated Kelly, no issues.")
        assert biases == []


# ---------------------------------------------------------------------------
# financial-dispatch skill
# ---------------------------------------------------------------------------
class TestEditorialStandards:
    def test_replaces_plummeted(self):
        result = _apply_editorial_standards("Markets plummeted 3% today.")
        assert "plummeted" not in result
        assert "fell sharply" in result

    def test_replaces_soared(self):
        result = _apply_editorial_standards("The index soared to new highs.")
        assert "soared" not in result
        assert "rose sharply" in result

    def test_replaces_massive(self):
        result = _apply_editorial_standards("A massive rally ensued.")
        assert "massive" not in result

    def test_replaces_only_time_will_tell(self):
        result = _apply_editorial_standards("Only time will tell what happens.")
        assert "only time will tell" not in result.lower()

    def test_clean_text_unchanged(self):
        clean = "The DAX fell 1.2% as ECB officials signalled a more cautious stance on rate cuts."
        result = _apply_editorial_standards(clean)
        assert result == clean
