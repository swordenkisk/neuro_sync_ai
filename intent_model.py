"""
neuro_sync_ai — Intent Model
==============================
The core innovation: inferring developer intent from behavioral signals.

This module implements the Intent State Machine and the predictive
suggestion engine — the heart of neuro_sync_ai.

Author  : swordenkisk (https://github.com/swordenkisk)
Created : March 2026
License : MIT + Intellectual Property Notice (see LICENSE)

═══════════════════════════════════════════════════════════════════
INTELLECTUAL PROPERTY NOTICE
═══════════════════════════════════════════════════════════════════
The IntentStateMachine and its behavioral signal mappings,
the five-state developer intent model (EXPLORING, DESIGNING,
IMPLEMENTING, DEBUGGING, REFACTORING), and the method of
inferring these states from keystroke micro-patterns in real-time
are ORIGINAL INVENTIONS by swordenkisk, first implemented
and documented in March 2026.

This is NOT based on any prior art in autocomplete, code completion,
or static code analysis. This system operates exclusively on
BEHAVIORAL SIGNALS — independent of code content.
═══════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import json
import time
from pathlib import Path

from .keystroke_collector import BehavioralWindow


# ─── Intent States ───────────────────────────────────────────────

class IntentState(Enum):
    """
    The five fundamental developer intent states.
    Each state has a distinct behavioral signature.

    ORIGINAL CLASSIFICATION by swordenkisk — March 2026.
    """
    EXPLORING     = "EXPLORING"      # Browsing, reading — no clear direction
    DESIGNING     = "DESIGNING"      # Structural thinking — slow, deliberate
    IMPLEMENTING  = "IMPLEMENTING"   # Flow state — fast, confident execution
    DEBUGGING     = "DEBUGGING"      # Erratic deletions — high confusion signal
    REFACTORING   = "REFACTORING"    # Systematic rewrites — structured changes


# ─── Behavioral Thresholds ───────────────────────────────────────

INTENT_THRESHOLDS = {
    IntentState.EXPLORING: {
        "avg_interval_min"   : 800,    # Very slow typing
        "deletion_ratio_max" : 0.1,    # Few deletions — just reading
        "hesitation_min"     : 0.3,
        "pause_count_min"    : 5,
    },
    IntentState.DESIGNING: {
        "avg_interval_min"   : 400,    # Slow, deliberate typing
        "deletion_ratio_max" : 0.25,
        "hesitation_min"     : 0.4,
        "pause_count_min"    : 3,
    },
    IntentState.IMPLEMENTING: {
        "avg_interval_max"   : 200,    # Fast typing
        "deletion_ratio_max" : 0.15,
        "hesitation_max"     : 0.25,   # Low hesitation = flow state
        "burst_count_min"    : 3,
    },
    IntentState.DEBUGGING: {
        "deletion_ratio_min" : 0.35,   # High deletion rate
        "hesitation_min"     : 0.55,   # High confusion
        "avg_interval_max"   : 600,
    },
    IntentState.REFACTORING: {
        "deletion_ratio_min" : 0.20,
        "deletion_ratio_max" : 0.50,
        "hesitation_min"     : 0.25,
        "hesitation_max"     : 0.55,
        "burst_count_min"    : 2,
    },
}


# ─── Intent Prediction Result ────────────────────────────────────

@dataclass
class IntentPrediction:
    """
    The output of the intent engine for a given behavioral window.
    """
    state            : IntentState
    confidence       : float                          # 0.0 – 1.0
    secondary_state  : Optional[IntentState] = None
    suggestion       : Optional[str]         = None
    should_intervene : bool                  = False  # Should the tool speak up?
    raw_scores       : Dict[str, float]      = field(default_factory=dict)
    timestamp_ms     : float                 = field(default_factory=lambda: time.time() * 1000)

    def to_dict(self) -> dict:
        return {
            "state"           : self.state.value,
            "confidence"      : self.confidence,
            "secondary_state" : self.secondary_state.value if self.secondary_state else None,
            "suggestion"      : self.suggestion,
            "should_intervene": self.should_intervene,
            "timestamp_ms"    : self.timestamp_ms,
        }


# ─── Suggestion Templates ────────────────────────────────────────

SUGGESTIONS: Dict[IntentState, List[str]] = {
    IntentState.EXPLORING: [
        "You seem to be exploring the codebase. Want me to generate a map of related files?",
        "Looks like you're reading — should I summarize this module?",
        "Navigation mode detected. Want to jump to related definitions?",
    ],
    IntentState.DESIGNING: [
        "You seem to be designing a structure. Want a scaffold for this pattern?",
        "Deliberate typing detected — are you planning an interface? I can draft one.",
        "Design phase detected. Want me to generate a class diagram from what you have?",
    ],
    IntentState.IMPLEMENTING: [
        # Flow state — do NOT interrupt. Stay silent.
    ],
    IntentState.DEBUGGING: [
        "High confusion signal detected. Want me to explain what this section does?",
        "Looks like you're stuck. Want me to trace the execution path?",
        "Debugging pattern detected. Should I run a quick analysis on this block?",
    ],
    IntentState.REFACTORING: [
        "Refactoring pattern detected. Want me to suggest a cleaner structure?",
        "Systematic rewrites detected. Should I apply this pattern to similar blocks?",
        "You're refactoring — want me to identify all similar patterns in the file?",
    ],
}


# ─── Intent State Machine ────────────────────────────────────────

class IntentStateMachine:
    """
    Core algorithm: maps behavioral window metrics to IntentState.

    Uses a weighted scoring system across all five states and
    returns the highest-confidence prediction.

    This is the original algorithm invented by swordenkisk.
    """

    def __init__(self):
        self._history: List[IntentPrediction] = []
        self._state_smoothing_window = 5   # smooth over last N predictions

    def predict(self, window: BehavioralWindow) -> IntentPrediction:
        """
        Given a BehavioralWindow, predict the developer's current intent state.
        """
        scores = self._score_all_states(window)
        best_state, best_score = max(scores.items(), key=lambda x: x[1])

        # Find secondary state
        sorted_states = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        secondary = sorted_states[1][0] if len(sorted_states) > 1 else None

        # Apply temporal smoothing — avoid flickering between states
        smoothed_state = self._smooth_state(best_state)

        # Determine if we should intervene
        should_intervene = self._should_intervene(smoothed_state, best_score, window)

        # Generate suggestion
        suggestion = self._generate_suggestion(smoothed_state) if should_intervene else None

        prediction = IntentPrediction(
            state            = smoothed_state,
            confidence       = round(best_score, 3),
            secondary_state  = secondary,
            suggestion       = suggestion,
            should_intervene = should_intervene,
            raw_scores       = {s.value: round(v, 3) for s, v in scores.items()},
        )

        self._history.append(prediction)
        return prediction

    def _score_all_states(self, w: BehavioralWindow) -> Dict[IntentState, float]:
        """Score every intent state against the current behavioral window."""
        scores = {}
        for state in IntentState:
            scores[state] = self._score_state(state, w)
        # Normalize to sum = 1
        total = sum(scores.values()) or 1
        return {s: v / total for s, v in scores.items()}

    def _score_state(self, state: IntentState, w: BehavioralWindow) -> float:
        """
        Compute a raw score for a given state based on behavioral window metrics.
        Higher score = more behavioral evidence for this state.
        """
        t = INTENT_THRESHOLDS.get(state, {})
        score = 0.0

        # Interval checks
        if "avg_interval_min" in t and w.avg_inter_key_interval >= t["avg_interval_min"]:
            score += 1.0
        if "avg_interval_max" in t and w.avg_inter_key_interval <= t["avg_interval_max"]:
            score += 1.0

        # Deletion ratio checks
        if "deletion_ratio_min" in t and w.deletion_ratio >= t["deletion_ratio_min"]:
            score += 1.5   # strong signal
        if "deletion_ratio_max" in t and w.deletion_ratio <= t["deletion_ratio_max"]:
            score += 0.5

        # Hesitation checks
        if "hesitation_min" in t and w.hesitation_score >= t["hesitation_min"]:
            score += 1.5
        if "hesitation_max" in t and w.hesitation_score <= t["hesitation_max"]:
            score += 0.5

        # Pause count checks
        if "pause_count_min" in t and w.pause_count >= t["pause_count_min"]:
            score += 1.0

        # Burst count checks
        if "burst_count_min" in t and w.burst_count >= t["burst_count_min"]:
            score += 1.0

        return max(score, 0.01)  # avoid zero scores

    def _smooth_state(self, current: IntentState) -> IntentState:
        """
        Apply temporal smoothing — require N consecutive signals
        before switching state, to avoid rapid flickering.
        """
        if len(self._history) < self._state_smoothing_window:
            return current

        recent = [p.state for p in self._history[-self._state_smoothing_window:]]
        most_common = max(set(recent), key=recent.count)
        recent_count = recent.count(most_common)

        # Only switch if majority of recent history agrees
        if recent_count >= self._state_smoothing_window // 2:
            return most_common
        return current

    def _should_intervene(
        self, state: IntentState, confidence: float, window: BehavioralWindow
    ) -> bool:
        """
        Decide if the tool should offer a suggestion.

        Key principle: NEVER interrupt flow state (IMPLEMENTING).
        Only speak when the developer is likely to welcome help.
        """
        if state == IntentState.IMPLEMENTING:
            return False     # Never interrupt flow
        if confidence < 0.40:
            return False     # Not confident enough
        if window.hesitation_score < 0.2 and state != IntentState.EXPLORING:
            return False     # Developer seems fine
        return True

    def _generate_suggestion(self, state: IntentState) -> Optional[str]:
        """Pick a contextual suggestion for the given intent state."""
        import random
        options = SUGGESTIONS.get(state, [])
        return random.choice(options) if options else None

    def get_history(self) -> List[dict]:
        return [p.to_dict() for p in self._history]

    def reset_history(self):
        self._history = []
