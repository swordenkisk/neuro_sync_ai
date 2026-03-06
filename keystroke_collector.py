"""
neuro_sync_ai — Keystroke Collector
=====================================
Captures raw behavioral signals from developer typing sessions
at millisecond resolution.

Author  : swordenkisk (https://github.com/swordenkisk)
Created : March 2026
License : MIT + Intellectual Property Notice (see LICENSE)

ORIGINAL INVENTION: The concept of using keystroke micro-patterns
to infer developer intent in real-time is an original contribution
by swordenkisk, first implemented March 2026.
"""

import time
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pathlib import Path


@dataclass
class KeystrokeEvent:
    """A single captured keystroke event with full behavioral metadata."""
    timestamp_ms: float          # Epoch milliseconds
    key_code: str                # Key identifier (anonymized)
    event_type: str              # 'press' | 'release' | 'hold'
    inter_key_interval: float    # ms since last keystroke
    is_deletion: bool            # Backspace / Delete
    is_navigation: bool          # Arrow keys, Home, End, etc.
    is_modifier: bool            # Ctrl, Alt, Shift
    pause_before_ms: float       # Silence duration before this key
    session_id: str              # Anonymous session identifier


@dataclass
class BehavioralWindow:
    """
    A sliding window of keystroke events representing
    a unit of developer behavior for intent analysis.
    """
    events: List[KeystrokeEvent] = field(default_factory=list)
    window_size: int = 50
    start_time_ms: float = 0.0
    end_time_ms: float = 0.0

    # Derived metrics
    avg_inter_key_interval: float = 0.0
    deletion_ratio: float = 0.0
    pause_count: int = 0
    burst_count: int = 0
    hesitation_score: float = 0.0

    def compute_metrics(self):
        """Compute behavioral metrics from raw events."""
        if not self.events:
            return

        intervals = [e.inter_key_interval for e in self.events if e.inter_key_interval > 0]
        deletions = [e for e in self.events if e.is_deletion]
        pauses    = [e for e in self.events if e.pause_before_ms > 500]  # >500ms = pause
        bursts    = self._detect_bursts()

        self.avg_inter_key_interval = sum(intervals) / len(intervals) if intervals else 0
        self.deletion_ratio         = len(deletions) / len(self.events)
        self.pause_count            = len(pauses)
        self.burst_count            = len(bursts)
        self.hesitation_score       = self._compute_hesitation()
        self.start_time_ms          = self.events[0].timestamp_ms
        self.end_time_ms            = self.events[-1].timestamp_ms

    def _detect_bursts(self, threshold_ms: float = 150) -> List[List[KeystrokeEvent]]:
        """Detect rapid typing bursts (consecutive keys under threshold_ms apart)."""
        bursts, current_burst = [], []
        for event in self.events:
            if event.inter_key_interval < threshold_ms:
                current_burst.append(event)
            else:
                if len(current_burst) > 3:
                    bursts.append(current_burst)
                current_burst = [event]
        return bursts

    def _compute_hesitation(self) -> float:
        """
        Compute a 0.0-1.0 hesitation score.
        High score = developer is uncertain / confused.
        Low score  = developer is in flow / confident.
        """
        if not self.events:
            return 0.0
        pause_weight     = min(self.pause_count / 10, 1.0) * 0.4
        deletion_weight  = min(self.deletion_ratio * 2, 1.0) * 0.4
        interval_weight  = min(self.avg_inter_key_interval / 2000, 1.0) * 0.2
        return round(pause_weight + deletion_weight + interval_weight, 3)


class KeystrokeCollector:
    """
    Real-time keystroke behavioral signal collector.

    Captures developer typing patterns in a privacy-preserving way:
    - Key content is NEVER stored, only key metadata
    - All data is local-only by default
    - Session IDs are anonymized hashes

    Usage:
        collector = KeystrokeCollector()
        collector.start_session()
        # ... developer types ...
        window = collector.get_current_window()
        collector.end_session()
    """

    PAUSE_THRESHOLD_MS  = 500    # ms of silence = a "pause"
    BURST_THRESHOLD_MS  = 150    # ms between keys = a "burst"
    WINDOW_SIZE         = 50     # keystrokes per analysis window

    def __init__(self, storage_dir: str = "~/.neuro/sessions"):
        self.storage_dir  = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._events: List[KeystrokeEvent]   = []
        self._session_id: Optional[str]      = None
        self._session_start: Optional[float] = None
        self._last_key_time: Optional[float] = None
        self._active                         = False

    def start_session(self) -> str:
        """Begin a new capture session. Returns session ID."""
        self._session_id    = self._generate_session_id()
        self._session_start = time.time() * 1000
        self._events        = []
        self._active        = True
        return self._session_id

    def record_keystroke(
        self,
        key_code: str,
        event_type: str = "press"
    ) -> Optional[KeystrokeEvent]:
        """
        Record a single keystroke event.
        Key content is abstracted to category only (never stored raw).
        """
        if not self._active:
            return None

        now_ms = time.time() * 1000
        interval = (now_ms - self._last_key_time) if self._last_key_time else 0
        pause    = interval if interval > self.PAUSE_THRESHOLD_MS else 0.0

        # Anonymize key — only store behavioral category
        category = self._categorize_key(key_code)

        event = KeystrokeEvent(
            timestamp_ms       = now_ms,
            key_code           = category,           # anonymized
            event_type         = event_type,
            inter_key_interval = interval,
            is_deletion        = category == "DELETE",
            is_navigation      = category == "NAV",
            is_modifier        = category == "MOD",
            pause_before_ms    = pause,
            session_id         = self._session_id,
        )

        self._events.append(event)
        self._last_key_time = now_ms
        return event

    def get_current_window(self) -> BehavioralWindow:
        """Get the latest behavioral window with computed metrics."""
        recent = self._events[-self.WINDOW_SIZE:]
        window = BehavioralWindow(events=recent, window_size=self.WINDOW_SIZE)
        window.compute_metrics()
        return window

    def get_full_session(self) -> List[KeystrokeEvent]:
        return list(self._events)

    def end_session(self) -> str:
        """End session and save to disk. Returns path to saved file."""
        self._active = False
        path = self.storage_dir / f"{self._session_id}.json"
        data = {
            "session_id"   : self._session_id,
            "start_ms"     : self._session_start,
            "end_ms"       : time.time() * 1000,
            "event_count"  : len(self._events),
            "events"       : [asdict(e) for e in self._events],
        }
        path.write_text(json.dumps(data, indent=2))
        return str(path)

    @staticmethod
    def _categorize_key(key_code: str) -> str:
        """
        Abstract raw key to behavioral category.
        This ensures NO content is ever stored — only behavior.
        """
        key = key_code.upper()
        if key in ("BACKSPACE", "DELETE"):
            return "DELETE"
        if key in ("LEFT", "RIGHT", "UP", "DOWN", "HOME", "END", "PAGEUP", "PAGEDOWN"):
            return "NAV"
        if key in ("CTRL", "ALT", "SHIFT", "META", "SUPER"):
            return "MOD"
        if key in ("RETURN", "ENTER"):
            return "ENTER"
        if key in ("TAB",):
            return "TAB"
        if key == "SPACE":
            return "SPACE"
        if len(key) == 1 and key.isalpha():
            return "ALPHA"
        if len(key) == 1 and key.isdigit():
            return "DIGIT"
        return "SYMBOL"

    @staticmethod
    def _generate_session_id() -> str:
        """Generate an anonymous session ID."""
        raw = f"{time.time()}-{id(object())}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
