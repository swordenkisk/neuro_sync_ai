"""
neuro_sync_ai — Demo Session
==============================
Demonstrates the intent prediction engine with simulated keystroke data.

Run: python examples/demo_session.py

Author: swordenkisk | https://github.com/swordenkisk
"""

import sys
import time
sys.path.insert(0, "..")

from neuro_sync_ai import NeuralIntentEngine


def simulate_flow_state(engine, n=60):
    """Fast typing — IMPLEMENTING / flow state."""
    for _ in range(n):
        engine.on_keystroke("ALPHA")
        time.sleep(0.001)   # simulate fast typing


def simulate_debugging(engine, n=40):
    """Lots of deletions + pauses — DEBUGGING state."""
    for i in range(n):
        if i % 3 == 0:
            engine.on_keystroke("BACKSPACE")
            time.sleep(0.002)
        engine.on_keystroke("ALPHA")
        time.sleep(0.003)


def simulate_designing(engine, n=30):
    """Slow deliberate typing with long pauses — DESIGNING state."""
    for _ in range(n):
        engine.on_keystroke("ALPHA")
        time.sleep(0.008)   # slow, deliberate


def main():
    print("=" * 60)
    print("  neuro_sync_ai — Developer Intent Prediction Demo")
    print("  Author: swordenkisk | March 2026")
    print("=" * 60)

    engine = NeuralIntentEngine()
    session_id = engine.start_session()
    print(f"\n✅ Session started: {session_id}\n")

    # --- Phase 1: Designing ---
    print("📐 Simulating DESIGNING phase (slow, deliberate typing)...")
    simulate_designing(engine)
    pred = engine.predict_intent()
    print(f"   Intent: {pred.state.value} (confidence: {pred.confidence:.0%})")
    if pred.suggestion:
        print(f"   💬 Suggestion: {pred.suggestion}")

    # --- Phase 2: Flow / Implementing ---
    print("\n⚡ Simulating IMPLEMENTING phase (fast flow typing)...")
    simulate_flow_state(engine)
    pred = engine.predict_intent()
    print(f"   Intent: {pred.state.value} (confidence: {pred.confidence:.0%})")
    if pred.should_intervene:
        print(f"   💬 Suggestion: {pred.suggestion}")
    else:
        print("   🤫 Silent — respecting developer flow state.")

    # --- Phase 3: Debugging ---
    print("\n🐛 Simulating DEBUGGING phase (erratic deletions)...")
    simulate_debugging(engine)
    pred = engine.predict_intent()
    print(f"   Intent: {pred.state.value} (confidence: {pred.confidence:.0%})")
    if pred.suggestion:
        print(f"   💬 Suggestion: {pred.suggestion}")

    # --- End Session ---
    print("\n" + "=" * 60)
    result = engine.end_session()
    print("✅ Session complete!")
    print(result["summary"])
    print(f"   Predictions made : {result['predictions']}")
    print(f"   Profile saved to : {result['profile_file']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
