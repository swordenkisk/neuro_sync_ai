# neuro_sync_ai — Research Foundation

## The Core Question

> Can we infer **what a developer intends to build** by observing *how* they type — independent of *what* they type?

This is the foundational research question of `neuro_sync_ai`.

---

## Why This Has Not Been Done Before

Existing tools in the developer AI space fall into two categories:

**Category A — Content Analysis:**
Tools like GitHub Copilot, Tabnine, and Amazon CodeWhisperer analyze the *content* of code to predict completions. They are sophisticated text transformers applied to source code.

**Category B — Productivity Metrics:**
Tools like WakaTime, CodeTime, and ActivityWatch measure *how much* time developers spend coding. They answer "how long?" not "what state is the developer in?"

**neuro_sync_ai is Category C — Behavioral Intent Inference:**
It analyzes *how* a developer types — the micro-behavioral signals — to answer: *"What is this developer trying to accomplish right now, and should I help them?"*

This category did not exist before March 2026.

---

## The Five Intent States — Behavioral Signatures

### EXPLORING
- Long inter-key intervals (>800ms average)
- Low deletion rate (<10%)
- High pause count
- Behavioral interpretation: developer is reading/navigating, no active coding goal

### DESIGNING
- Medium-slow intervals (400–800ms)
- Moderate deletions (10–25%)
- High hesitation score (>0.4)
- Behavioral interpretation: developer is thinking architecturally, planning structure

### IMPLEMENTING
- Fast intervals (<200ms)
- Low deletions (<15%)
- Low hesitation (<0.25)
- High burst count (>3)
- Behavioral interpretation: developer has a clear plan and is executing — FLOW STATE

### DEBUGGING
- High deletion rate (>35%)
- High hesitation (>0.55)
- Erratic intervals
- Behavioral interpretation: developer is confused, stuck, seeking help

### REFACTORING
- Moderate deletions (20–50%)
- Medium hesitation (0.25–0.55)
- Systematic burst patterns
- Behavioral interpretation: developer is restructuring known code

---

## The Non-Interruption Principle

A critical design decision in `neuro_sync_ai` is the **silence-when-flowing rule**:

> When a developer is in the IMPLEMENTING (flow) state, the system must never generate suggestions, notifications, or interruptions — regardless of confidence level.

This is grounded in cognitive science research showing that interrupting flow state costs an average of 23 minutes of recovery time. The system identifies flow state behaviorally (fast, consistent, low-deletion typing) and goes completely silent.

---

## Privacy Architecture

`neuro_sync_ai` is built on a privacy-first foundation:

1. **No content capture** — raw keystrokes are immediately abstracted to categories (ALPHA, DELETE, NAV, etc.). The actual letters typed are never stored.
2. **Local-only by default** — all profiles and sessions are stored on the developer's machine.
3. **Anonymized session IDs** — SHA-256 hashes, no personally identifiable information.
4. **Opt-in sync** — cloud sync is planned for v2.0 but will always be opt-in.

---

## Original Contributions (March 2026)

1. The five-state developer intent model and its behavioral signatures
2. The keystroke micro-pattern → intent state mapping algorithm
3. The non-interruption principle formalized as a system design rule
4. The persistent per-developer behavioral fingerprint with EMA learning
5. The personalized threshold adaptation method
6. The keystroke anonymization-while-preserving-behavioral-resolution architecture

*— swordenkisk, March 2026*
