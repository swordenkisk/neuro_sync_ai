"""
neuro_sync_ai — Developer Profile
===================================
Persistent behavioral fingerprint for each developer.
Learns and adapts over time — the model improves with every session.

Author  : swordenkisk (https://github.com/swordenkisk)
Created : March 2026
"""

import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path

from .keystroke_collector import BehavioralWindow
from .intent_model import IntentState, IntentPrediction


@dataclass
class SessionSummary:
    """Summary of a single coding session."""
    session_id    : str
    date_ms       : float
    duration_ms   : float
    dominant_state: str
    state_breakdown: Dict[str, float]   # % time in each state
    avg_hesitation: float
    total_keystrokes: int
    flow_periods  : int                  # # of IMPLEMENTING bursts


@dataclass
class DeveloperProfile:
    """
    The living behavioral fingerprint of a developer.
    Evolves with every session — never static.

    This is the core persistent data structure of neuro_sync_ai.
    Each profile is unique to one developer and stored locally.
    """
    profile_id       : str
    created_ms       : float = field(default_factory=lambda: time.time() * 1000)
    last_updated_ms  : float = field(default_factory=lambda: time.time() * 1000)
    session_count    : int   = 0

    # Baseline behavioral metrics (updated per session)
    baseline_interval_ms    : float = 250.0   # Personal avg inter-key interval
    baseline_hesitation     : float = 0.3
    baseline_deletion_ratio : float = 0.15
    typical_flow_speed_ms   : float = 120.0   # Speed when in IMPLEMENTING state

    # State tendencies (how much time this dev spends in each state)
    state_tendencies: Dict[str, float] = field(default_factory=lambda: {
        "EXPLORING"    : 0.15,
        "DESIGNING"    : 0.20,
        "IMPLEMENTING" : 0.40,
        "DEBUGGING"    : 0.15,
        "REFACTORING"  : 0.10,
    })

    # Session history
    sessions: List[SessionSummary] = field(default_factory=list)

    def update_from_session(self, windows: List[BehavioralWindow], predictions: List[IntentPrediction]):
        """
        Update the profile with data from a completed session.
        Uses exponential moving average for smooth adaptation.
        """
        if not windows:
            return

        alpha = 0.2   # Learning rate — how fast profile adapts

        # Update baseline metrics
        avg_interval = sum(w.avg_inter_key_interval for w in windows) / len(windows)
        avg_hes      = sum(w.hesitation_score for w in windows) / len(windows)
        avg_del      = sum(w.deletion_ratio for w in windows) / len(windows)

        self.baseline_interval_ms    = (1-alpha) * self.baseline_interval_ms    + alpha * avg_interval
        self.baseline_hesitation     = (1-alpha) * self.baseline_hesitation     + alpha * avg_hes
        self.baseline_deletion_ratio = (1-alpha) * self.baseline_deletion_ratio + alpha * avg_del

        # Update flow speed from IMPLEMENTING windows
        flow_windows = [w for w, p in zip(windows, predictions) if p.state == IntentState.IMPLEMENTING]
        if flow_windows:
            flow_speed = sum(w.avg_inter_key_interval for w in flow_windows) / len(flow_windows)
            self.typical_flow_speed_ms = (1-alpha) * self.typical_flow_speed_ms + alpha * flow_speed

        # Update state tendencies
        state_counts: Dict[str, int] = {s.value: 0 for s in IntentState}
        for p in predictions:
            state_counts[p.state.value] += 1
        total = len(predictions) or 1
        for state, count in state_counts.items():
            observed = count / total
            self.state_tendencies[state] = (1-alpha) * self.state_tendencies[state] + alpha * observed

        # Record session summary
        dominant = max(state_counts, key=state_counts.get)
        summary = SessionSummary(
            session_id       = f"sess_{self.session_count + 1}",
            date_ms          = time.time() * 1000,
            duration_ms      = sum((w.end_time_ms - w.start_time_ms) for w in windows),
            dominant_state   = dominant,
            state_breakdown  = {s: round(c/total, 3) for s, c in state_counts.items()},
            avg_hesitation   = avg_hes,
            total_keystrokes = sum(len(w.events) for w in windows),
            flow_periods     = len(flow_windows),
        )
        self.sessions.append(summary)
        self.session_count    += 1
        self.last_updated_ms   = time.time() * 1000

    def get_personalized_thresholds(self) -> dict:
        """
        Return behavioral thresholds personalized to THIS developer.
        A fast typist's 'slow' is different from a slow typist's 'slow'.
        """
        return {
            "flow_threshold"    : self.typical_flow_speed_ms * 1.3,
            "hesitation_high"   : self.baseline_hesitation * 1.8,
            "hesitation_low"    : self.baseline_hesitation * 0.5,
            "deletion_high"     : self.baseline_deletion_ratio * 2.5,
        }

    def save(self, path: Optional[str] = None) -> str:
        """Save profile to disk."""
        save_path = Path(path or f"~/.neuro/profiles/{self.profile_id}.nsp").expanduser()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        # Convert SessionSummary objects to dicts
        data["sessions"] = [asdict(s) if hasattr(s, '__dataclass_fields__') else s
                            for s in self.sessions]
        save_path.write_text(json.dumps(data, indent=2))
        return str(save_path)

    @classmethod
    def load(cls, path: str) -> "DeveloperProfile":
        """Load profile from disk."""
        data = json.loads(Path(path).expanduser().read_text())
        sessions_raw = data.pop("sessions", [])
        profile = cls(**data)
        profile.sessions = [SessionSummary(**s) for s in sessions_raw]
        return profile

    @classmethod
    def new(cls) -> "DeveloperProfile":
        """Create a fresh profile with default values."""
        pid = hashlib.sha256(f"{time.time()}-{id(object())}".encode()).hexdigest()[:12]
        return cls(profile_id=pid)

    def summary(self) -> str:
        """Human-readable profile summary."""
        return (
            f"Developer Profile [{self.profile_id}]\n"
            f"  Sessions      : {self.session_count}\n"
            f"  Avg Speed     : {self.baseline_interval_ms:.0f}ms/key\n"
            f"  Flow Speed    : {self.typical_flow_speed_ms:.0f}ms/key\n"
            f"  Hesitation    : {self.baseline_hesitation:.2f}\n"
            f"  Dominant State: {max(self.state_tendencies, key=self.state_tendencies.get)}\n"
        )
