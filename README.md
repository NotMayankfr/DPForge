# DPForge — Dynamic Programming IDE & Parallel Efficiency Judge

[![CI](https://github.com/NotMayankfr/DPForge/actions/workflows/ci.yml/badge.svg)](https://github.com/NotMayankfr/DPForge/actions)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Accessibility](https://img.shields.io/badge/Lighthouse-100%2F100-success.svg)](ACCESSIBILITY_AUDIT.md)

**DPForge** is a high-craft competitive programming IDE, parallel automated judge, and dynamic programming visualizer specifically engineered for mastering Dynamic Programming (DP) patterns across the full Striver A2Z Dynamic Programming curriculum.

Built to address the shortcomings of generic coding platforms that fail to catch un-memoized recursion, lack state visualizers, or fail to validate reference test oracles.

---

## 🚀 Key Highlights & Engineering Features (Tier 1 & Tier 2)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DPFORGE ARCHITECTURE                               │
├────────────────────────┬───────────────────────────┬────────────────────────────┤
│   FRONTEND LAYER       │     JUDGE CORE (SERVER)   │   VERIFICATION & ORACLES   │
│  - Accessible HTML5    │  - Multi-Language Judge   │  - 595 Pytest Unit Tests   │
│  - WCAG 2.1 AA (100)   │    (Python 3, C++, Java)  │  - Independent Brute-Force │
│  - Responsive Layout   │  - Parallel Test Executor │    Mathematical Oracles    │
│  - Monaco Code Editor  │  - Tight 2.0s TLE Enforcer│  - Deduplicated Max-       │
│  - DP Table Visualizer │  - 256MB Memory Monitor   │    Constraint Test Cases   │
│  - Submissions Stats   │  - SQLite Analytics DB    │  - GitHub Actions Matrix   │
└────────────────────────┴───────────────────────────┴────────────────────────────┘
```

### 1. ⚡ Efficiency Judging: True DP vs. Exponential Brute-Force
- **The Problem**: Generic test runners evaluate small inputs ($N \le 18$, $n \le 30$). An un-memoized $O(2^N)$ brute-force recursion passes easily, defeating the entire purpose of a DP tool.
- **The Solution**: The judge subjects submissions to maximum-constraint test cases (e.g., $n = 45$ for Climbing Stairs, array lengths up to 1,000+) under a **strict 2.0-second time limit**:
  - **$O(N)$ or $O(N^2)$ DP**: Finishes in $< 10$ ms ($\text{Accepted - AC}$).
  - **$O(2^N)$ Brute Force**: Hits exponential complexity ($2^{45} \approx 3.5 \times 10^{13}$ operations) and reliably receives a **Time Limit Exceeded (TLE)** on case 34 ($n=34$).
- **Strictly Distinct Test Generation**: Every test case is strictly distinct and deduplicated (no duplicate inputs masquerading as "50 unique tests").

---

### 2. 📊 Interactive DP-Table Visualizer (Front-End Showpiece)
- **Visual State Space**: Renders 1D and 2D dynamic programming state tables cell-by-cell.
- **Dynamic Transition Highlighting**:
  - **Active Cell**: Glowing animated pulse indicating the current cell being evaluated.
  - **Dependency Cells**: Contrasting amber highlight indicating the exact subproblem states feeding into the current state (e.g., $dp[i-1]$ and $dp[i-2]$).
- **Synchronous Math Card**: Displays the live recurrence equation (e.g., `dp[2][3] = top (3) + left (3) = 6`) with a plain-English explanation of the decision.
- **Playback Controls**: Play, Pause, Step Forward, Step Back, Reset, and variable speed ($0.5\times$ to $5.0\times$).
- **Interactive Rebuilding**: Allows custom sizes and arrays to test edge-case behavior.

---

### 3. 🌐 Multi-Language Judging: Python, C++ 17, and Java 17
- Supports compiling and executing in **Python 3**, **C++ 17** (via `g++`, `clang++`, or `cl`), and **Java 17** (via `javac`/`java`).
- **Compilation Diagnostics**: Fast compile step with explicit **`CE` (Compilation Error)** diagnostics returned if syntax fails.
- Starter code templates and Monaco editor syntax modes switch automatically on language selection.

---

### 4. 🏆 Codeforces-Style Verdicts, Parallel Execution & Memory Limits
- **Parallel Judge**: Test cases execute concurrently across CPU cores using `ThreadPoolExecutor`, evaluating 50 tests in $< 400$ ms.
- **Standardized Competitive Programming Verdicts**:
  - **`AC`** — Accepted (All outputs correct within time and memory limits)
  - **`WA`** — Wrong Answer (Incorrect value on specific test case)
  - **`TLE`** — Time Limit Exceeded ($> 2.0$s execution threshold)
  - **`MLE`** — Memory Limit Exceeded ($> 256$ MB peak memory tracked via `psutil`)
  - **`RE`** — Runtime Error (Non-zero exit code or uncaught exception)
  - **`CE`** — Compilation Error (Compiler diagnostics formatted for easy fixing)
- **Per-Test Performance Badges**: Runtime measured down to the millisecond (`time_ms`) on each test case.

---

### 5. 🛡️ Verified Test Oracles (595 Automated Pytest Verifications)
- Reference solutions in [`references.py`](references.py) are cross-verified against independent, brute-force algorithms on small inputs via [`test_references.py`](test_references.py).
- **595 automated unit tests** run in continuous integration across Python 3.11, 3.12, and 3.13.

---

### 6. ♿ Accessible (WCAG 2.1 AA), Responsive & High-Craft Developer UI
- **Linear/Raycast-Inspired Design System**: Complete aesthetic redesign away from generic prototypes to a sleek, dark-canvas developer tool experience:
  - Custom typography pairing: **Plus Jakarta Sans** (UI) and **JetBrains Mono** (code/matrices).
  - Layered surface architecture (`#08090d` canvas, elevated `#151926` cards, `rgba(255,255,255,0.07)` hairline borders, subtle inner highlights).
  - Pure SVG vector iconography (no emoji soup or toy buttons).
  - Micro-interactions, animated state pills, and glowing active indicators.
- **Responsive Stacked Layout**: Eliminated fixed `min-width: 950px`. Features a fluid CSS layout that collapses into stacked panels on mobile and tablet screens ($\le 768$px).
- **Audit Scores**: Scored **100/100 on Google Lighthouse Accessibility** with **0 axe-core violations** (detailed in [`ACCESSIBILITY_AUDIT.md`](ACCESSIBILITY_AUDIT.md)).
- **Accessibility Features**:
  - Keyboard skip-to-content link (`.skip-link`).
  - Visible focus rings (`:focus-visible`) with dual-color offset.
  - Accessible modal dialogs with focus trap and `Escape` key dismiss.
  - WAI-ARIA landmark roles (`banner`, `main`, `region`, `dialog`, `progressbar`).
  - Screen reader live regions (`aria-live="polite"`).

---

### 7. 📈 Submissions Analytics & Progress Dashboard
- SQLite-backed database ([`submissions.db`](submissions.db)) logs every execution and submission.
- Interactive modal dashboard displaying:
  - Total Submissions & Overall Acceptance Rate (%).
  - Solved problem counts by difficulty (Easy, Medium, Hard).
  - Recent submissions history table with language tags, verdicts, test scores, and execution times.

---

### 8. 💡 4-Step Hints Ladder & Complete Editorials
- Progressive hints ladder integrated into every problem:
  1. **Recursion** (Recurrence relation & base case formulation)
  2. **Memoization** (Top-down caching & state matrix)
  3. **Tabulation** (Bottom-up loop order & base initialization)
  4. **Space Optimization** (Reducing state dimension to $O(1)$ or $O(N)$)
- In-depth editorials with mathematical proofs and complete solutions in Python, C++, and Java.

---

### 9. 🔬 User Research & Usability Testing
- Conducted empirical user research sessions with 5 peer developers to eliminate friction around competitive-programming STDIN formatting and TLE diagnostics.
- Boosted task completion from 60% to 100% and increased System Usability Scale (SUS) score by 26 points (detailed in [`USABILITY_STUDY.md`](USABILITY_STUDY.md)).

---

## 📁 Repository Structure

```
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI matrix (Python 3.11, 3.12, 3.13)
├── index.html                   # Accessible HTML5 interface with Monaco, tabs & modal
├── style.css                    # Responsive CSS with WCAG 2.1 AA contrast & focus tokens
├── app.js                       # Controller: Monaco, Visualizer, Tabs, Submissions
├── problems.json                # All 55 Striver A2Z DP problem statements & test specs
├── editorials.json              # 4-step hints ladder & multi-language reference code
├── server.py                    # Multi-language parallel judge server & SQLite logger
├── references.py                # Reference algorithms used as test oracles
├── test_references.py           # 595+ automated pytest oracle cross-checks
├── submissions.db               # SQLite submission history & metrics
├── ACCESSIBILITY_AUDIT.md       # WCAG 2.1 AA compliance & Lighthouse 100/100 report
├── USABILITY_STUDY.md           # 5-participant usability study & UX iterations
└── README.md
```

---

## 🛠️ Quickstart

### 1. Requirements
- Python 3.10+
- (Optional for C++ judging): `g++` or `clang++` on PATH
- (Optional for Java judging): JDK 17+ (`javac` and `java`) on PATH

### 2. Start the Server
```bash
python server.py
```
Open your browser to: **`http://127.0.0.1:8765`**

### 3. Run Oracle Verification Tests
```bash
python -m pytest test_references.py -v --tb=short
```

---

## ⌨️ Global Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + Enter` (or `Cmd + Enter`) | Run current code against active STDIN |
| `Ctrl + Shift + Enter` | Run all 50 test cases in parallel |
| `Alt + →` | Next problem |
| `Alt + ←` | Previous problem |
| `Esc` | Close test results or stats modal |

---

## 🧪 Verification & Benchmarks

### Efficiency Judging in Action
```text
DP Solution (O(N)):
DP Result: 45/45 passed, verdicts: {'AC'}, runtime: 773ms across all 45 cases

Brute-force Recursion (O(2^N) without memoization):
Brute Force Result: 33/45 passed, TLE count: 12
Case 34 (n=34) TLE in 2000ms: Time limit exceeded (2.0s) — Brute-force/exponential recursion detected!
```

### Pytest Oracle Verification
```text
============================= 595 passed in 2.52s =============================
```
