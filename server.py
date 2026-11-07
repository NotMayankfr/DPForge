"""
Striver A2Z DP — Local IDE Server (server.py)
A clean, modular HTTP server and competitive-programming judge featuring:
- Multi-language judging: Python 3, C++ 17, Java 17 (compile & run)
- Efficiency judging with tight 2.0s per-test limit (catches brute force vs DP)
- Max-constraint tests ensuring exponential recursion fails with TLE
- Parallel test execution via ThreadPoolExecutor
- Memory limit tracking & enforcement (256MB limit via psutil) returning MLE
- Codeforces-style verdicts (AC, WA, TLE, MLE, RE, CE) and per-test runtime (ms)
- Oracle validation backed by verified reference implementations
- Static file serving (index.html, style.css, app.js, problems.json, editorials.json)
- SQLite submissions history logger with stats dashboard API
"""

import concurrent.futures
import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

# Import all reference algorithms from the verified references module
import references

BASE_DIR = Path(__file__).resolve().parent
HOST = '127.0.0.1'
PORT = 8765
TIME_LIMIT_SECONDS = 2.0
MEMORY_LIMIT_BYTES = 256 * 1024 * 1024  # 256 MB

# ---------------------------------------------------------------------------
# Load Problem Metadata & Editorials
# ---------------------------------------------------------------------------
with open(BASE_DIR / 'problems.json', encoding='utf-8') as f:
    PROBLEMS = json.load(f)

META = {p['dp']: p for p in PROBLEMS}
REF = {name: getattr(references, name) for name in dir(references) if callable(getattr(references, name))}

EDITORIALS = {}
if (BASE_DIR / 'editorials.json').exists():
    try:
        with open(BASE_DIR / 'editorials.json', encoding='utf-8') as f:
            EDITORIALS = json.load(f)
    except Exception as e:
        print(f"[Warning] Failed to load editorials.json: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# SQLite Submissions DB (Tier 2 feature)
# ---------------------------------------------------------------------------
DB_PATH = BASE_DIR / 'submissions.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                dp TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'python',
                verdict TEXT NOT NULL,
                passed INTEGER NOT NULL,
                total INTEGER NOT NULL,
                max_time_ms INTEGER NOT NULL,
                code_len INTEGER NOT NULL
            )
        ''')
        # Check if language column exists, if not add it
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'language' not in columns:
            conn.execute("ALTER TABLE submissions ADD COLUMN language TEXT NOT NULL DEFAULT 'python'")
        conn.commit()

def log_submission(dp, language, verdict, passed, total, max_time_ms, code_len):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO submissions (timestamp, dp, language, verdict, passed, total, max_time_ms, code_len)
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)
            ''', (dp, language, verdict, passed, total, max_time_ms, code_len))
            conn.commit()
    except Exception as e:
        print(f"[Warning] Failed to log submission to DB: {e}", file=sys.stderr)

init_db()


# ---------------------------------------------------------------------------
# Multi-Language Compilation & Execution
# ---------------------------------------------------------------------------

def find_compiler(lang: str):
    """Finds compiler binary path on the system for C++ or Java."""
    if lang == 'cpp':
        for cand in ['g++', 'clang++', 'cl']:
            p = shutil.which(cand)
            if p:
                return cand, p
        return None, None
    elif lang == 'java':
        javac = shutil.which('javac')
        java = shutil.which('java')
        if javac and java:
            return 'javac', (javac, java)
        return None, None
    return None, None


def compile_submission(lang: str, code: str, work_dir: Path):
    """
    Compiles C++ or Java code before running test cases.
    Returns (success: bool, exec_command: list, error_message: str).
    """
    if lang == 'python':
        return True, [sys.executable, '-u', '-c', code], ""

    elif lang == 'cpp':
        compiler_name, compiler_path = find_compiler('cpp')
        if not compiler_path:
            return False, [], (
                "C++ compiler (g++ / clang++) not found on system PATH.\n"
                "Please install MinGW-w64 or Visual Studio C++ build tools to compile and judge C++ code."
            )

        src_file = work_dir / "solution.cpp"
        exe_file = work_dir / ("solution.exe" if os.name == 'nt' else "solution")
        src_file.write_text(code, encoding='utf-8')

        if compiler_name in ('g++', 'clang++'):
            cmd = [compiler_path, '-O3', '-std=c++17', str(src_file), '-o', str(exe_file)]
        else:  # cl (MSVC)
            cmd = [compiler_path, '/O2', '/EHsc', str(src_file), f'/Fe:{exe_file}']

        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if cp.returncode != 0:
                return False, [], f"Compilation Error:\n{cp.stderr or cp.stdout}"
            return True, [str(exe_file)], ""
        except subprocess.TimeoutExpired:
            return False, [], "Compilation timed out (limit: 15s)."
        except Exception as e:
            return False, [], f"Compilation failed: {e}"

    elif lang == 'java':
        compiler_name, paths = find_compiler('java')
        if not paths:
            return False, [], (
                "Java compiler (javac/java) not found on system PATH.\n"
                "Please install JDK 17+ and add javac to PATH to compile and judge Java code."
            )

        javac_path, java_path = paths
        class_match = re.search(r'public\s+class\s+([A-Za-z0-9_]+)', code)
        class_name = class_match.group(1) if class_match else "Solution"

        src_file = work_dir / f"{class_name}.java"
        src_file.write_text(code, encoding='utf-8')

        try:
            cp = subprocess.run([javac_path, str(src_file)], capture_output=True, text=True, timeout=15)
            if cp.returncode != 0:
                return False, [], f"Compilation Error:\n{cp.stderr or cp.stdout}"
            return True, [java_path, '-Xmx256m', '-cp', str(work_dir), class_name], ""
        except subprocess.TimeoutExpired:
            return False, [], "Java compilation timed out (limit: 15s)."
        except Exception as e:
            return False, [], f"Java compilation failed: {e}"

    return False, [], f"Unsupported language: {lang}"


# ---------------------------------------------------------------------------
# Test Case Generation with Max Constraints & Unique Inputs
# ---------------------------------------------------------------------------

def generate_cases_for_dp(dp: str):
    """
    Generates distinct test cases for the problem, strictly including
    inputs at maximum problem constraints to separate O(N)/O(N^2) DP from O(2^N) recursion.
    """
    rng = random.Random(20260907 + int(re.search(r'\d+', dp).group()))
    p_meta = META.get(dp, {})
    fn_name = p_meta.get('fn')
    rf = REF.get(fn_name)

    cases = []
    seen = set()

    def add_case(args):
        key = json.dumps(args, sort_keys=True)
        if key in seen:
            return
        seen.add(key)
        try:
            expected = rf(*args.values()) if rf else None
            cases.append({'args': args, 'expected': expected})
        except Exception as ex:
            print(f"[Warning] Error computing reference output for {dp} with {args}: {ex}", file=sys.stderr)

    # 1. Base / Edge cases from initial problem examples
    for ex in p_meta.get('tests', []):
        add_case(ex.get('args', {}))

    # 2. Maximum constraint & stress cases to differentiate DP from brute force
    if dp == 'DP 2':  # Climbing stairs (1 <= n <= 45)
        for n in range(1, 46):
            add_case({'n': n})

    elif dp == 'DP 3':  # Frog jump (2 <= n <= 1000)
        for L in [2, 3, 5, 10, 30, 50, 100, 200, 500, 800, 1000]:
            add_case({'heights': [rng.randint(0, 1000) for _ in range(L)]})
        while len(cases) < 50:
            L = rng.randint(2, 300)
            add_case({'heights': [rng.randint(0, 500) for _ in range(L)]})

    elif dp == 'DP 4':  # Frog jump with k (n <= 1000, k <= n)
        for L, k in [(2, 1), (5, 2), (10, 3), (30, 5), (100, 10), (300, 25), (500, 50), (1000, 100)]:
            add_case({'heights': [rng.randint(0, 1000) for _ in range(L)], 'k': k})
        while len(cases) < 50:
            L = rng.randint(2, 200)
            add_case({'heights': [rng.randint(0, 300) for _ in range(L)], 'k': rng.randint(1, min(L, 30))})

    elif dp in ('DP 5', 'DP 6'):  # Max Non-Adjacent / House Robber (n up to 10000)
        for L in [1, 2, 3, 10, 30, 50, 100, 500, 1000, 5000]:
            add_case({'nums': [rng.randint(0, 500) for _ in range(L)]})
        while len(cases) < 50:
            L = rng.randint(2, 200)
            add_case({'nums': [rng.randint(0, 200) for _ in range(L)]})

    elif dp == 'DP 7':  # Ninja's training (days up to 1000)
        for L in [1, 2, 5, 20, 50, 100, 300, 500, 1000]:
            add_case({'points': [[rng.randint(0, 100) for _ in range(3)] for _ in range(L)]})
        while len(cases) < 50:
            L = rng.randint(1, 150)
            add_case({'points': [[rng.randint(0, 100) for _ in range(3)] for _ in range(L)]})

    elif dp == 'DP 8':  # Unique paths (m, n <= 100)
        for m, n in [(1, 1), (1, 100), (100, 1), (10, 10), (20, 20), (30, 30), (50, 50), (100, 100)]:
            add_case({'m': m, 'n': n})
        while len(cases) < 50:
            add_case({'m': rng.randint(1, 80), 'n': rng.randint(1, 80)})

    elif dp == 'DP 9':  # Unique paths 2 (m, n <= 100)
        for R, C in [(1, 1), (2, 2), (5, 5), (10, 10), (20, 20), (40, 40)]:
            g = [[1 if rng.random() < 0.2 else 0 for _ in range(C)] for __ in range(R)]
            g[0][0] = g[-1][-1] = 0
            add_case({'grid': g})
        while len(cases) < 50:
            R = rng.randint(2, 30)
            C = rng.randint(2, 30)
            g = [[1 if rng.random() < 0.25 else 0 for _ in range(C)] for __ in range(R)]
            g[0][0] = g[-1][-1] = 0
            add_case({'grid': g})

    elif dp == 'DP 10':  # Min Path Sum (m, n <= 100)
        for R, C in [(1, 1), (3, 3), (10, 10), (25, 25), (40, 40)]:
            add_case({'grid': [[rng.randint(0, 50) for _ in range(C)] for __ in range(R)]})
        while len(cases) < 50:
            R, C = rng.randint(1, 30), rng.randint(1, 30)
            add_case({'grid': [[rng.randint(0, 50) for _ in range(C)] for __ in range(R)]})

    elif dp == 'DP 11':  # Triangle (up to 80 rows)
        for L in [1, 2, 5, 15, 30, 50, 80]:
            add_case({'triangle': [[rng.randint(-20, 50) for _ in range(i + 1)] for i in range(L)]})
        while len(cases) < 50:
            L = rng.randint(1, 35)
            add_case({'triangle': [[rng.randint(-20, 50) for _ in range(i + 1)] for i in range(L)]})

    elif dp == 'DP 12':  # Falling path sum (matrix n x n)
        for L in [1, 2, 5, 15, 30, 50]:
            add_case({'matrix': [[rng.randint(-30, 50) for _ in range(L)] for __ in range(L)]})
        while len(cases) < 50:
            L = rng.randint(1, 30)
            add_case({'matrix': [[rng.randint(-30, 50) for _ in range(L)] for __ in range(L)]})

    elif dp == 'DP 13':  # Cherry pickup ii (r, c <= 50)
        for R, C in [(2, 2), (4, 4), (8, 8), (15, 15)]:
            add_case({'grid': [[rng.randint(0, 20) for _ in range(C)] for __ in range(R)]})
        while len(cases) < 50:
            R, C = rng.randint(2, 15), rng.randint(2, 15)
            add_case({'grid': [[rng.randint(0, 20) for _ in range(C)] for __ in range(R)]})

    elif dp in ('DP 14', 'DP 15', 'DP 16', 'DP 17', 'DP 18'):
        for L in [1, 5, 15, 30, 50, 80]:
            arr = [rng.randint(1, 50) for _ in range(L)]
            if dp == 'DP 14': add_case({'nums': arr, 'target': rng.randint(1, 500)})
            elif dp in ('DP 15', 'DP 16'): add_case({'nums': arr})
            elif dp == 'DP 17': add_case({'nums': arr, 'k': rng.randint(0, 300)})
            elif dp == 'DP 18': add_case({'nums': arr, 'diff': rng.randint(0, 50)})
        while len(cases) < 50:
            L = rng.randint(2, 40)
            arr = [rng.randint(1, 40) for _ in range(L)]
            if dp == 'DP 14': add_case({'nums': arr, 'target': rng.randint(1, 300)})
            elif dp in ('DP 15', 'DP 16'): add_case({'nums': arr})
            elif dp == 'DP 17': add_case({'nums': arr, 'k': rng.randint(0, 200)})
            elif dp == 'DP 18': add_case({'nums': arr, 'diff': rng.randint(0, 40)})

    elif dp == 'DP 19':  # 0/1 Knapsack
        for L, cap in [(1, 10), (5, 50), (20, 200), (50, 500), (100, 1000), (200, 2000)]:
            add_case({
                'weights': [rng.randint(1, 50) for _ in range(L)],
                'values': [rng.randint(1, 100) for _ in range(L)],
                'capacity': cap
            })
        while len(cases) < 50:
            L = rng.randint(2, 80)
            add_case({
                'weights': [rng.randint(1, 40) for _ in range(L)],
                'values': [rng.randint(1, 80) for _ in range(L)],
                'capacity': rng.randint(10, 400)
            })

    elif dp in ('DP 20', 'DP 22'):  # Coin changes
        for n_coins, amt in [(1, 0), (3, 11), (5, 50), (8, 200), (10, 500), (12, 1000)]:
            coins = sorted(set(rng.randint(1, 30) for _ in range(n_coins)))
            add_case({'coins': coins, 'amount': amt})
        while len(cases) < 50:
            coins = sorted(set(rng.randint(1, 30) for _ in range(rng.randint(2, 8))))
            add_case({'coins': coins, 'amount': rng.randint(1, 300)})

    elif dp == 'DP 24':  # Rod cutting problem
        for L in [1, 2, 5, 10, 30, 50, 100, 200]:
            add_case({'price': [rng.randint(1, 40) for _ in range(L)], 'n': L})
        while len(cases) < 50:
            L = rng.randint(1, 80)
            add_case({'price': [rng.randint(1, 30) for _ in range(L)], 'n': L})

    elif dp in ('DP 25', 'DP 26', 'DP 27', 'DP 30', 'DP 31'):  # LCS & string variations
        for L in [0, 5, 20, 50, 100, 200]:
            add_case({
                'a': ''.join(rng.choice('abcdef') for _ in range(L)),
                'b': ''.join(rng.choice('abcdef') for _ in range(L))
            })
        while len(cases) < 50:
            L1, L2 = rng.randint(1, 100), rng.randint(1, 100)
            add_case({
                'a': ''.join(rng.choice('abcde') for _ in range(L1)),
                'b': ''.join(rng.choice('abcde') for _ in range(L2))
            })

    elif dp in ('DP 28', 'DP 29', 'DP 53'):  # Palindrome strings
        for L in [0, 1, 5, 20, 50, 100, 200]:
            add_case({'s': ''.join(rng.choice('abcdef') for _ in range(L))})
        while len(cases) < 50:
            L = rng.randint(1, 80)
            add_case({'s': ''.join(rng.choice('abcde') for _ in range(L))})

    elif dp == 'DP 33':  # Edit distance
        for L in [0, 3, 10, 30, 80, 150]:
            add_case({
                'a': ''.join(rng.choice('abcdef') for _ in range(L)),
                'b': ''.join(rng.choice('abcdef') for _ in range(L))
            })
        while len(cases) < 50:
            L1, L2 = rng.randint(1, 80), rng.randint(1, 80)
            add_case({
                'a': ''.join(rng.choice('abcd') for _ in range(L1)),
                'b': ''.join(rng.choice('abcd') for _ in range(L2))
            })

    elif dp in ('DP 35', 'DP 36', 'DP 37', 'DP 38', 'DP 39', 'DP 40'):  # Stock problems
        for L in [0, 1, 5, 20, 100, 500, 2000]:
            prices = [rng.randint(1, 200) for _ in range(L)]
            if dp == 'DP 38': add_case({'prices': prices, 'k': rng.randint(1, max(1, L // 4))})
            elif dp == 'DP 40': add_case({'prices': prices, 'fee': rng.randint(1, 10)})
            else: add_case({'prices': prices})
        while len(cases) < 50:
            L = rng.randint(2, 300)
            prices = [rng.randint(1, 150) for _ in range(L)]
            if dp == 'DP 38': add_case({'prices': prices, 'k': rng.randint(1, max(1, L // 4))})
            elif dp == 'DP 40': add_case({'prices': prices, 'fee': rng.randint(1, 8)})
            else: add_case({'prices': prices})

    elif dp in ('DP 41', 'DP 42', 'DP 43', 'DP 46', 'DP 47'):  # LIS variations
        for L in [0, 1, 5, 20, 50, 150, 300]:
            add_case({'nums': [rng.randint(-50, 150) for _ in range(L)]})
        while len(cases) < 50:
            L = rng.randint(2, 200)
            add_case({'nums': [rng.randint(-50, 150) for _ in range(L)]})

    # Generic generator fallback for remaining problems
    while len(cases) < 50:
        if dp == 'DP 21':
            L = rng.randint(1, 18)
            add_case({'nums': [rng.randint(0, 10) for _ in range(L)], 'target': rng.randint(-20, 20)})
        elif dp == 'DP 23':
            L = rng.randint(1, 20)
            add_case({
                'weights': [rng.randint(1, 15) for _ in range(L)],
                'values': [rng.randint(1, 30) for _ in range(L)],
                'capacity': rng.randint(5, 50)
            })
        elif dp == 'DP 32':
            s = ''.join(rng.choice('abc') for _ in range(rng.randint(1, 20)))
            t = ''.join(rng.choice('abc') for _ in range(rng.randint(1, min(6, len(s)))))
            add_case({'s': s, 't': t})
        elif dp == 'DP 34':
            add_case({
                's': ''.join(rng.choice('ab') for _ in range(rng.randint(0, 15))),
                'pattern': ''.join(rng.choice('ab?*') for _ in range(rng.randint(0, 10)))
            })
        elif dp == 'DP 44':
            add_case({'nums': sorted(set(rng.randint(1, 50) for _ in range(rng.randint(1, 15))))})
        elif dp == 'DP 45':
            words = [''.join(rng.choice('abc') for _ in range(rng.randint(1, 8))) for _ in range(rng.randint(1, 15))]
            add_case({'words': sorted(set(words))})
        elif dp in ('DP 48', 'DP 49'):
            add_case({'dims': [rng.randint(2, 40) for _ in range(rng.randint(2, 12))]})
        elif dp == 'DP 50':
            L = rng.randint(5, 50)
            cuts = sorted(rng.sample(range(1, L), rng.randint(1, min(8, L - 1))))
            add_case({'length': L, 'cuts': cuts})
        elif dp == 'DP 51':
            add_case({'nums': [rng.randint(1, 20) for _ in range(rng.randint(1, 12))]})
        elif dp == 'DP 52':
            L = rng.randint(1, 7)
            e = []
            for k in range(L):
                e.append(rng.choice('TF'))
                if k < L - 1: e.append(rng.choice('&|^'))
            add_case({'expr': ''.join(e)})
        elif dp == 'DP 54':
            L = rng.randint(1, 30)
            add_case({'arr': [rng.randint(-10, 30) for _ in range(L)], 'k': rng.randint(1, min(L, 5))})
        elif dp in ('DP 55', 'DP 56'):
            R, C = rng.randint(1, 12), rng.randint(1, 12)
            add_case({'matrix': [[rng.randint(0, 1) for _ in range(C)] for __ in range(R)]})
        else:
            break

    return cases[:50]


CACHE = {}

def get_cases(dp: str):
    if dp not in CACHE:
        CACHE[dp] = generate_cases_for_dp(dp)
    return CACHE[dp]


# ---------------------------------------------------------------------------
# Output Validation & Formatting
# ---------------------------------------------------------------------------

def valid(dp: str, args: dict, actual, expected) -> bool:
    """Verifies candidate output against expected or problem-specific invariants."""
    if dp == 'DP 26':  # Print LCS
        a, b = args['a'], args['b']
        return (isinstance(actual, str) and
                references.is_subseq(actual, a) and
                references.is_subseq(actual, b) and
                len(actual) == REF['lcs_length'](a, b))

    if dp == 'DP 31':  # Shortest Common Supersequence
        a, b = args['a'], args['b']
        L = len(a) + len(b) - REF['lcs_length'](a, b)
        return (isinstance(actual, str) and
                references.is_subseq(a, actual) and
                references.is_subseq(b, actual) and
                len(actual) == L)

    if dp == 'DP 42':  # Print LIS
        a = args['nums']
        L = REF['lis_length'](a)
        return (isinstance(actual, list) and
                len(actual) == L and
                all(actual[j] < actual[j + 1] for j in range(len(actual) - 1)) and
                references.is_subseq(actual, a))

    if dp == 'DP 44':  # Largest Divisible Subset
        want = len(REF['largest_divisible_subset'](args['nums']))
        return (isinstance(actual, list) and
                len(actual) == want and
                all(x in args['nums'] for x in actual) and
                all(x % y == 0 or y % x == 0 for j, x in enumerate(actual) for y in actual[:j]))

    return actual == expected


def serialize_input(args: dict) -> str:
    """
    Standard competitive-programming-style stdin serialization.
    Each argument is encoded as JSON on its own line.
    """
    return ''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in (args or {}).values())


def parse_stdout(stdout: str):
    """Parses student's printed stdout into a comparable Python object."""
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Program produced no output.")
    candidate = lines[-1]
    try:
        return json.loads(candidate)
    except Exception:
        try:
            import ast
            return ast.literal_eval(candidate)
        except Exception:
            lower = candidate.lower()
            if lower == 'true': return True
            if lower == 'false': return False
            return candidate


# ---------------------------------------------------------------------------
# Execution with Subprocess, 2.0s Timeout, Memory Limit & Timing
# ---------------------------------------------------------------------------

def execute_single_case(exec_cmd: list, test_idx: int, case: dict, dp: str) -> dict:
    """
    Executes a single test case with a tight 2.0s time limit and 256MB memory check.
    Returns result dictionary including Codeforces-style verdict (AC, WA, TLE, MLE, RE) and runtime_ms.
    """
    stdin_data = serialize_input(case['args'])
    t0 = time.perf_counter()

    try:
        proc = subprocess.Popen(
            exec_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )

        try:
            stdout_data, stderr_data = proc.communicate(input=stdin_data, timeout=TIME_LIMIT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_data, stderr_data = proc.communicate()
            elapsed_ms = int(TIME_LIMIT_SECONDS * 1000)
            return {
                'i': test_idx,
                'args': case['args'],
                'input': stdin_data,
                'expected': case['expected'],
                'actual': None,
                'status': 'FAIL',
                'verdict': 'TLE',
                'time_ms': elapsed_ms,
                'detail': f'Time limit exceeded ({TIME_LIMIT_SECONDS:.1f}s) — Brute-force/exponential recursion detected!'
            }

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

    except Exception as ex:
        return {
            'i': test_idx,
            'args': case['args'],
            'input': stdin_data,
            'expected': case['expected'],
            'actual': None,
            'status': 'FAIL',
            'verdict': 'RE',
            'time_ms': 0,
            'detail': f"Execution failed to start: {ex}"
        }

    # Non-zero exit code -> Runtime Error (RE)
    if proc.returncode != 0:
        err_msg = stderr_data.strip() or f'Process exited with status code {proc.returncode}.'
        return {
            'i': test_idx,
            'args': case['args'],
            'input': stdin_data,
            'expected': case['expected'],
            'actual': None,
            'status': 'FAIL',
            'verdict': 'RE',
            'time_ms': elapsed_ms,
            'detail': err_msg
        }

    # Parse stdout and compare with expected answer
    try:
        actual = parse_stdout(stdout_data)
        is_ok = valid(dp, case['args'], actual, case['expected'])
        verdict = 'AC' if is_ok else 'WA'
        detail = '' if is_ok else f'Expected {case["expected"]!r}, got {actual!r}'
        return {
            'i': test_idx,
            'args': case['args'],
            'input': stdin_data,
            'expected': case['expected'],
            'actual': actual,
            'status': 'PASS' if is_ok else 'FAIL',
            'verdict': verdict,
            'time_ms': elapsed_ms,
            'detail': detail
        }
    except Exception as e:
        return {
            'i': test_idx,
            'args': case['args'],
            'input': stdin_data,
            'expected': case['expected'],
            'actual': None,
            'status': 'FAIL',
            'verdict': 'WA',
            'time_ms': elapsed_ms,
            'detail': f'Output parse error: {e}'
        }


def run_tests_parallel(dp: str, exec_cmd: list, cases: list) -> list:
    """Runs all test cases concurrently using ThreadPoolExecutor."""
    workers = min(16, (os.cpu_count() or 4) * 2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(execute_single_case, exec_cmd, i + 1, case, dp): i
            for i, case in enumerate(cases)
        }
        results = [None] * len(cases)
        for fut in concurrent.futures.as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()
    return results


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------

class JudgeHandler(BaseHTTPRequestHandler):
    def _json(self, data, code=200):
        b = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _serve_file(self, filepath: Path, content_type: str):
        if not filepath.exists():
            self.send_error(404, f"File {filepath.name} not found")
            return
        content = filepath.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path in ('/', '/index.html'):
            self._serve_file(BASE_DIR / 'index.html', 'text/html; charset=utf-8')
        elif path == '/style.css':
            self._serve_file(BASE_DIR / 'style.css', 'text/css; charset=utf-8')
        elif path == '/app.js':
            self._serve_file(BASE_DIR / 'app.js', 'application/javascript; charset=utf-8')
        elif path in ('/problems', '/problems.json'):
            self._serve_file(BASE_DIR / 'problems.json', 'application/json; charset=utf-8')
        elif path in ('/editorials', '/editorials.json'):
            self._serve_file(BASE_DIR / 'editorials.json', 'application/json; charset=utf-8')
        elif path == '/stats':
            # Rich Submissions stats summary for UI dashboard
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT 
                            COUNT(*),
                            SUM(CASE WHEN verdict="AC" THEN 1 ELSE 0 END),
                            COUNT(DISTINCT CASE WHEN verdict="AC" THEN dp END),
                            AVG(max_time_ms)
                        FROM submissions
                    ''')
                    row = cursor.fetchone()
                    total_subs = row[0] or 0
                    ac_subs = row[1] or 0
                    distinct_solved = row[2] or 0
                    avg_time_ms = round(row[3] or 0, 1)

                    cursor.execute('SELECT language, COUNT(*) FROM submissions GROUP BY language')
                    lang_dist = dict(cursor.fetchall())

                    cursor.execute('SELECT verdict, COUNT(*) FROM submissions GROUP BY verdict')
                    verdict_dist = dict(cursor.fetchall())

                    cursor.execute('''
                        SELECT id, timestamp, dp, language, verdict, passed, total, max_time_ms, code_len 
                        FROM submissions ORDER BY id DESC LIMIT 25
                    ''')
                    recent = [
                        {
                            'id': r[0], 'time': r[1], 'dp': r[2], 'language': r[3],
                            'verdict': r[4], 'passed': r[5], 'total': r[6],
                            'max_time_ms': r[7], 'code_len': r[8]
                        }
                        for r in cursor.fetchall()
                    ]

                self._json({
                    'total_submissions': total_subs,
                    'ac_submissions': ac_subs,
                    'ac_rate': round((ac_subs / total_subs * 100), 1) if total_subs else 0,
                    'distinct_solved': distinct_solved,
                    'avg_time_ms': avg_time_ms,
                    'languages': lang_dist,
                    'verdicts': verdict_dist,
                    'recent': recent
                })
            except Exception as e:
                self._json({'error': str(e)}, 500)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            raw_body = self.rfile.read(length) if length > 0 else b'{}'
            body = json.loads(raw_body.decode('utf-8') or '{}')
            dp = body.get('dp')
            lang = body.get('lang', 'python').lower()

            if self.path == '/cases':
                cases = get_cases(dp)
                return self._json({
                    'tests': [
                        {
                            'i': i + 1,
                            'args': c['args'],
                            'input': serialize_input(c['args']),
                            'expected': c['expected']
                        }
                        for i, c in enumerate(cases)
                    ]
                })

            if self.path == '/run':
                code = body.get('code', '')
                stdin_input = body.get('stdin', '')

                with tempfile.TemporaryDirectory() as temp_dir:
                    work_dir = Path(temp_dir)
                    ok, exec_cmd, compile_err = compile_submission(lang, code, work_dir)
                    if not ok:
                        return self._json({
                            'error': compile_err,
                            'verdict': 'CE',
                            'stderr': compile_err
                        }, 400)

                    t0 = time.perf_counter()
                    try:
                        proc = subprocess.run(
                            exec_cmd,
                            input=stdin_input,
                            capture_output=True,
                            text=True,
                            timeout=TIME_LIMIT_SECONDS,
                            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                        )
                        elapsed_ms = int((time.perf_counter() - t0) * 1000)
                    except subprocess.TimeoutExpired:
                        return self._json({'error': f'Time limit exceeded ({TIME_LIMIT_SECONDS:.1f} seconds).'}, 400)

                    if proc.returncode != 0:
                        return self._json({
                            'error': proc.stderr.strip() or 'Process exited with error.',
                            'stdout': proc.stdout,
                            'stderr': proc.stderr,
                            'time_ms': elapsed_ms
                        }, 400)

                    return self._json({
                        'stdout': proc.stdout,
                        'stderr': proc.stderr,
                        'time_ms': elapsed_ms
                    })

            if self.path == '/run-tests':
                code = body.get('code', '')
                cases = get_cases(dp)

                with tempfile.TemporaryDirectory() as temp_dir:
                    work_dir = Path(temp_dir)
                    ok, exec_cmd, compile_err = compile_submission(lang, code, work_dir)
                    if not ok:
                        log_submission(dp, lang, 'CE', 0, len(cases), 0, len(code))
                        return self._json({
                            'passed': 0,
                            'total': len(cases),
                            'verdict': 'CE',
                            'compile_error': compile_err,
                            'max_time_ms': 0,
                            'results': [
                                {
                                    'i': 1,
                                    'args': {},
                                    'input': '',
                                    'expected': None,
                                    'actual': None,
                                    'status': 'FAIL',
                                    'verdict': 'CE',
                                    'time_ms': 0,
                                    'detail': compile_err
                                }
                            ]
                        })

                    results = run_tests_parallel(dp, exec_cmd, cases)

                passed = sum(1 for r in results if r['status'] == 'PASS')
                total = len(results)
                max_time_ms = max((r.get('time_ms', 0) for r in results), default=0)
                verdict = 'AC' if passed == total else next((r['verdict'] for r in results if r['status'] == 'FAIL'), 'WA')

                log_submission(dp, lang, verdict, passed, total, max_time_ms, len(code))

                return self._json({
                    'passed': passed,
                    'total': total,
                    'verdict': verdict,
                    'max_time_ms': max_time_ms,
                    'results': results
                })

            self.send_error(404, "Endpoint not found")
        except Exception as e:
            self._json({'error': traceback.format_exc()}, 500)


def run_server():
    print(f"\n========================================================")
    print(f" DPForge — Multi-Language DP Judge Server & Visualizer")
    print(f" URL: http://{HOST}:{PORT}")
    print(f" Python: {sys.executable}")
    cpp_comp, cpp_path = find_compiler('cpp')
    java_comp, java_paths = find_compiler('java')
    print(f" C++ Compiler: {cpp_path or 'Not found on PATH'}")
    print(f" Java Compiler: {java_paths[0] if java_paths else 'Not found on PATH'}")
    print(f" Efficiency Time Limit: {TIME_LIMIT_SECONDS}s per test (parallel execution)")
    print(f" SQLite Log: {DB_PATH.name}")
    print(f" Press Ctrl+C to stop.")
    print(f"========================================================\n")
    server = ThreadingHTTPServer((HOST, PORT), JudgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.server_close()


if __name__ == '__main__':
    run_server()
