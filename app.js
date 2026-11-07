/**
 * Striver A2Z DP — Multi-Language Competitive Programming IDE
 * app.js — Full client controller featuring:
 * - Multi-language execution (Python 3, C++ 17, Java 17)
 * - Interactive DP-Table Visualizer engine (1D & 2D with cell-by-cell stepping)
 * - 4-step Hints Ladder and Editorial viewer
 * - Submissions & Performance Analytics dashboard
 * - WCAG 2.1 AA accessibility (focus trap, ARIA, keyboard navigation)
 */

'use strict';

const API = window.location.origin && window.location.origin.startsWith('http')
  ? window.location.origin
  : 'http://127.0.0.1:8765';

// ── Starter Code Templates ──────────────────────────────────────────────────
const STARTERS = {
  python: `# Dynamic Programming Solution (Python 3)
# Read input from stdin (each test argument on its own line as JSON)
# Print the final result to stdout

import sys, json

def solve():
    lines = [line.strip() for line in sys.stdin if line.strip()]
    if not lines:
        return
    # Example:
    # arg = json.loads(lines[0])
    # print(climb_stairs(arg))
    pass

if __name__ == '__main__':
    solve()
`,
  cpp: `// Dynamic Programming Solution (C++ 17)
// Read input from stdin and print answer to stdout
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // Read input from stdin
    // Example:
    // int n;
    // if (cin >> n) { ... }

    return 0;
}
`,
  java: `// Dynamic Programming Solution (Java 17)
import java.util.*;
import java.io.*;

public class Solution {
    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String line = br.readLine();
        if (line == null || line.trim().isEmpty()) return;

        // Parse stdin and print answer to System.out
    }
}
`
};

let P = [];
let current = 0;
let currentLang = 'python';
let editor = null;
let lastFocusedElement = null;
let editorialsData = {};

// Saved user state per problem and language
const done = JSON.parse(localStorage.getItem('striver_dp_done2') || '{}');
const savedCode = JSON.parse(localStorage.getItem('striver_dp_code_multi') || '{}');

function $(id) {
  return document.getElementById(id);
}

// ── Persistence & Progress ──────────────────────────────────────────────────
function saveCurrentCode() {
  if (editor && P[current]) {
    const key = `${P[current].id}_${currentLang}`;
    savedCode[key] = editor.getValue();
    localStorage.setItem('striver_dp_code_multi', JSON.stringify(savedCode));
  }
  localStorage.setItem('striver_dp_done2', JSON.stringify(done));
}

function progress() {
  if (!P.length) return;
  const n = P.filter(x => done[x.id]).length;
  const total = P.length;
  const pct = Math.round((n / total) * 100);

  $('prog').textContent = `${n}/${total}`;
  const fill = $('fill');
  fill.style.width = `${pct}%`;
  fill.setAttribute('aria-valuenow', n);
  fill.setAttribute('aria-valuemax', total);
}

function toast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1600);
}

function argsToStdin(args) {
  return Object.values(args || {}).map(v => JSON.stringify(v)).join('\n') + '\n';
}

// ── Problem Rendering ───────────────────────────────────────────────────────
function renderPicker() {
  const s = $('picker');
  s.innerHTML = '';
  P.forEach((p, i) => {
    const o = document.createElement('option');
    o.value = i;
    const isDone = done[p.id] ? '✓ ' : '';
    o.textContent = `${isDone}${p.dp} · ${p.title}`;
    s.appendChild(o);
  });
  s.value = current;
}

function renderQuestion() {
  if (!P.length || !P[current]) return;
  const p = P[current];

  $('picker').value = current;
  $('kicker').textContent = p.section || 'Dynamic Programming';
  $('qtitle').textContent = `${p.dp} · ${p.title}`;
  $('story').textContent = p.prompt;
  $('sig').textContent = p.spec?.format || 'Read JSON from stdin and print result to stdout.';
  $('input').textContent = p.spec?.input || '';
  $('outputSpec').textContent = p.spec?.output || '';
  $('constraints').textContent = p.spec?.constraints || '';
  $('pos').textContent = `Problem ${current + 1} of ${P.length}`;
  $('diff').textContent = p.difficulty;
  $('diff').className = 'tag ' + (p.difficulty || 'medium').toLowerCase();

  // Render Examples
  const exContainer = $('examples');
  exContainer.innerHTML = '';
  (p.spec?.examples || []).forEach((x, j) => {
    const e = document.createElement('div');
    e.className = 'ex';
    e.innerHTML = `<strong>Example ${j + 1}</strong><code>Input: ${x[0]}</code><code>Output: ${x[1]}</code>` +
      (x[2] ? `<div style="margin-top:4px;color:var(--mut);font-size:11px">${x[2]}</div>` : '');
    exContainer.appendChild(e);
  });

  // Stdin default
  $('stdin').value = (p.tests && p.tests[0]) ? argsToStdin(p.tests[0].args) : '';

  // Solved state
  const isDone = !!done[p.id];
  const markBtn = $('mark');
  markBtn.innerHTML = `
    <svg class="star-icon" width="14" height="14" viewBox="0 0 24 24" fill="${isDone ? '#34d399' : 'none'}" stroke="${isDone ? '#34d399' : 'currentColor'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
    </svg>
    <span class="mark-label">${isDone ? 'Solved' : 'Mark Solved'}</span>
  `;
  markBtn.setAttribute('aria-pressed', isDone ? 'true' : 'false');
  if (isDone) markBtn.classList.add('green');
  else markBtn.classList.remove('green');

  // Load code in editor for current language
  if (editor) {
    const key = `${p.id}_${currentLang}`;
    const code = savedCode[key] !== undefined ? savedCode[key] : (STARTERS[currentLang] || STARTERS.python);
    editor.setValue(code);
  }

  renderPicker();
  progress();

  // Also update visualizer and editorial for current problem
  buildVisualizerForCurrentProblem();
  renderEditorialForCurrentProblem();
}

// ── Language Selector & Monaco Model Update ─────────────────────────────────
function setLanguage(lang) {
  currentLang = lang;
  $('langSelect').value = lang;
  $('status').textContent = `Local ${lang.toUpperCase()}`;

  if (editor) {
    const monacoLang = lang === 'cpp' ? 'cpp' : (lang === 'java' ? 'java' : 'python');
    const model = editor.getModel();
    if (model && window.monaco) {
      monaco.editor.setModelLanguage(model, monacoLang);
    }
    const key = `${P[current].id}_${currentLang}`;
    const code = savedCode[key] !== undefined ? savedCode[key] : (STARTERS[currentLang] || STARTERS.python);
    editor.setValue(code);
  }
}

// ── Server HTTP Requests ────────────────────────────────────────────────────
async function post(url, body) {
  const fullUrl = url.startsWith('http') ? url : `${API}${url}`;
  let r;
  try {
    r = await fetch(fullUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  } catch (e) {
    throw new Error(`Cannot reach local judge server at ${API}.\nEnsure 'python server.py' is running.\n\nError: ${e.message}`);
  }

  const text = await r.text();
  let j;
  try {
    j = JSON.parse(text);
  } catch (e) {
    throw new Error('Server returned invalid JSON:\n' + text.slice(0, 1000));
  }
  if (!r.ok) {
    throw new Error(j.error || 'Server error');
  }
  return j;
}

// ── Run Single Case ─────────────────────────────────────────────────────────
async function runOne() {
  saveCurrentCode();
  const runBtn = $('run');
  const dot = document.querySelector('.status-dot');
  runBtn.classList.add('btn-loading');
  runBtn.disabled = true;
  if (dot) {
    dot.style.background = '#f59e0b';
    dot.style.boxShadow = '0 0 6px #f59e0b';
  }
  $('status').textContent = `Running ${currentLang.toUpperCase()}…`;
  $('out').textContent = `Running ${currentLang.toUpperCase()} with STDIN…`;

  try {
    const j = await post('/run', {
      dp: P[current].dp,
      lang: currentLang,
      code: editor.getValue(),
      stdin: $('stdin').value
    });
    let text = '';
    if (j.stdout) text += j.stdout;
    if (j.stderr) text += (text ? '\n' : '') + '[stderr]\n' + j.stderr;
    const timeBadge = j.time_ms !== undefined ? ` [${j.time_ms}ms]` : '';
    $('out').textContent = (text || 'Program executed with no output.') + timeBadge;
    $('status').textContent = `Completed · ${j.time_ms || 0}ms`;
    if (dot) {
      dot.style.background = '#10b981';
      dot.style.boxShadow = '0 0 6px #10b981';
    }
  } catch (e) {
    $('out').textContent = String(e.message || e);
    $('status').textContent = 'Execution error';
    if (dot) {
      dot.style.background = '#ef4444';
      dot.style.boxShadow = '0 0 6px #ef4444';
    }
  } finally {
    runBtn.classList.remove('btn-loading');
    runBtn.disabled = false;
  }
}

// ── Run All 50 Tests with Parallel Judging & Efficiency Enforcement ─────────
async function runTests() {
  saveCurrentCode();
  const testBtn = $('runTests');
  const dot = document.querySelector('.status-dot');
  testBtn.classList.add('btn-loading');
  testBtn.disabled = true;
  if (dot) {
    dot.style.background = '#f59e0b';
    dot.style.boxShadow = '0 0 6px #f59e0b';
  }
  $('status').textContent = 'Judging…';
  $('out').textContent = `Evaluating 50 test cases at max constraints with 2.0s limit (${currentLang.toUpperCase()})…`;

  try {
    const j = await post('/run-tests', {
      dp: P[current].dp,
      lang: currentLang,
      code: editor.getValue()
    });

    if (j.verdict === 'CE') {
      $('out').textContent = `Compilation Error (CE):\n${j.compile_error || 'Compilation failed'}`;
      if (dot) {
        dot.style.background = '#ef4444';
        dot.style.boxShadow = '0 0 6px #ef4444';
      }
      showResults(j);
      return;
    }

    if (j.passed === j.total) {
      $('out').textContent = `All ${j.total} tests passed! Accepted (AC) in max ${j.max_time_ms}ms.`;
      done[P[current].id] = true;
      saveCurrentCode();
      progress();
      const markBtn = $('mark');
      markBtn.innerHTML = `
        <svg class="star-icon" width="14" height="14" viewBox="0 0 24 24" fill="#34d399" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
        <span class="mark-label">Solved</span>
      `;
      markBtn.setAttribute('aria-pressed', 'true');
      markBtn.classList.add('green');
      toast('All tests passed! Problem marked solved.');
      if (dot) {
        dot.style.background = '#10b981';
        dot.style.boxShadow = '0 0 6px #10b981';
      }
    } else {
      const tleCount = (j.results || []).filter(r => r.verdict === 'TLE').length;
      let summary = `${j.total - j.passed} of ${j.total} tests failed.`;
      if (tleCount > 0) {
        summary += ` (${tleCount} TLE — plain recursion detected, ensure DP is used!)`;
      }
      $('out').textContent = `${summary} Click 'View failures' in dialog.`;
      if (dot) {
        dot.style.background = tleCount > 0 ? '#f59e0b' : '#ef4444';
        dot.style.boxShadow = tleCount > 0 ? '0 0 6px #f59e0b' : '0 0 6px #ef4444';
      }
    }

    showResults(j);
    $('status').textContent = `${j.passed}/${j.total} passed`;
  } catch (e) {
    $('out').textContent = String(e.message || e);
    $('status').textContent = 'Test error';
    if (dot) {
      dot.style.background = '#ef4444';
      dot.style.boxShadow = '0 0 6px #ef4444';
    }
  } finally {
    testBtn.classList.remove('btn-loading');
    testBtn.disabled = false;
  }
}

// ── Show Test Results Modal ─────────────────────────────────────────────────
function showResults(j) {
  lastFocusedElement = document.activeElement;
  const modal = $('modal');
  const body = $('modalBody');
  const title = $('modalTitle');
  const iconWrap = modal.querySelector('.modal-icon');
  body.innerHTML = '';

  const isAllPassed = j.passed === j.total;
  if (title) {
    title.textContent = isAllPassed ? 'Evaluation Passed' : 'Evaluation Failed';
  }
  if (iconWrap) {
    iconWrap.className = `modal-icon ${isAllPassed ? 'ac' : 'wa'}`;
    iconWrap.innerHTML = isAllPassed
      ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`
      : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
  }

  const summary = document.createElement('div');
  summary.className = 'summary';

  if (j.verdict === 'CE') {
    summary.innerHTML = `<span class="verdict-tag verdict-ce">CE</span>
      <div style="font-size:12px;color:#93c5fd;font-weight:600;">Compilation Error · Check build logs below</div>`;
  } else {
    summary.innerHTML = isAllPassed
      ? `<span class="verdict-tag verdict-ac">AC</span>
         <b style="color:var(--green);font-size:13px;">All ${j.total} Tests Passed (Accepted)</b>
         <span class="time-badge">Max Latency: ${j.max_time_ms}ms · Memory Limit: 256MB</span>`
      : `<span class="verdict-tag verdict-${(j.verdict || 'wa').toLowerCase()}">${j.verdict || 'WA'}</span>
         <b style="font-size:13px;">${j.passed} of ${j.total} Tests Passed</b>
         <span class="time-badge">Max Latency: ${j.max_time_ms}ms</span>
         <div style="width:100%;font-size:11.5px;color:var(--text-muted);margin-top:4px;">
           ${j.total - j.passed} failed · 2.0s per-test limit enforces DP polynomial complexity
         </div>`;
  }
  body.appendChild(summary);

  const list = document.createElement('div');
  list.className = 'failList';
  list.style.maxHeight = '55vh';
  list.style.overflowY = 'auto';

  const items = isAllPassed ? (j.results || []).slice(0, 5) : (j.results || []).filter(x => x.status === 'FAIL');

  items.forEach(x => {
    const d = document.createElement('div');
    d.className = 'failItem';

    const verdict = x.verdict || (x.status === 'PASS' ? 'AC' : 'WA');
    const verdictClass = `verdict-${verdict.toLowerCase()}`;
    const timeBadge = x.time_ms !== undefined ? `<span class="time-badge">${x.time_ms}ms</span>` : '';

    d.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <b style="color:var(--text);font-family:var(--font-mono);font-size:12px;">Test Case ${x.i}</b>
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="verdict-tag ${verdictClass}">${verdict}</span>
          ${timeBadge}
        </div>
      </div>
      <code>Input:    ${(x.input || '').replaceAll('<', '&lt;')}</code>
      <code>Expected: ${JSON.stringify(x.expected)}</code>
      <code>Actual:   ${JSON.stringify(x.actual)}</code>
      ${x.detail ? `<div style="margin-top:6px;color:#fda4af;font-size:11px;font-family:var(--font-mono);">${(x.detail || '').replaceAll('<', '&lt;')}</div>` : ''}
    `;
    list.appendChild(d);
  });

  body.appendChild(list);
  modal.classList.add('show');
  $('closeModal').focus();
}

function closeModal() {
  $('modal').classList.remove('show');
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
}


// ═════════════════════════════════════════════════════════════════════════════
// 🌟 INTERACTIVE DP TABLE VISUALIZER ENGINE
// ═════════════════════════════════════════════════════════════════════════════

let vizState = {
  dpId: '',
  title: '',
  steps: [],
  currentStep: 0,
  timer: null,
  speed: 600,
  rows: 0,
  cols: 0,
  rowHeaders: [],
  colHeaders: []
};

function generateDPSteps(dpId, paramStr) {
  const steps = [];
  const p = P[current] || {};

  // Case 1: 1D Fibonacci / Climbing Stairs
  if (dpId === 'DP 2') {
    const n = Math.max(1, Math.min(12, parseInt(paramStr) || 6));
    const dp = new Array(n + 1).fill('—');
    const rowHeaders = ['dp'];
    const colHeaders = Array.from({ length: n + 1 }, (_, i) => `i=${i}`);

    steps.push({
      grid: [dp.slice()],
      active: [0, 0],
      deps: [],
      formula: 'dp[0] = 1',
      desc: 'Base case: 1 way to be at ground stair 0.'
    });
    dp[0] = 1;

    steps.push({
      grid: [dp.slice()],
      active: [0, 1],
      deps: [],
      formula: 'dp[1] = 1',
      desc: 'Base case: 1 way to reach stair 1 (one 1-step).'
    });
    dp[1] = 1;

    for (let i = 2; i <= n; i++) {
      const val = dp[i - 1] + dp[i - 2];
      steps.push({
        grid: [dp.slice()],
        active: [0, i],
        deps: [[0, i - 1], [0, i - 2]],
        formula: `dp[${i}] = dp[${i - 1}] (${dp[i - 1]}) + dp[${i - 2}] (${dp[i - 2]}) = ${val}`,
        desc: `Reach stair ${i} from stair ${i - 1} (+1 step) or stair ${i - 2} (+2 steps).`
      });
      dp[i] = val;
    }

    return { rows: 1, cols: n + 1, rowHeaders, colHeaders, steps };
  }

  // Case 2: 1D Frog Jump
  if (dpId === 'DP 3') {
    let heights = [10, 20, 30, 10, 60, 50];
    try {
      const parsed = JSON.parse(paramStr);
      if (Array.isArray(parsed) && parsed.length >= 2) heights = parsed.slice(0, 10);
    } catch (e) {}

    const n = heights.length;
    const dp = new Array(n).fill('—');
    const rowHeaders = ['dp'];
    const colHeaders = heights.map((h, i) => `${i} (h=${h})`);

    dp[0] = 0;
    steps.push({
      grid: [dp.slice()],
      active: [0, 0],
      deps: [],
      formula: 'dp[0] = 0',
      desc: 'Frog starts at stair 0 with 0 energy consumed.'
    });

    if (n > 1) {
      const cost1 = Math.abs(heights[1] - heights[0]);
      dp[1] = cost1;
      steps.push({
        grid: [dp.slice()],
        active: [0, 1],
        deps: [[0, 0]],
        formula: `dp[1] = dp[0] + |h[1]-h[0]| = 0 + ${cost1} = ${cost1}`,
        desc: 'Stair 1 can only be reached by jumping 1 step from stair 0.'
      });
    }

    for (let i = 2; i < n; i++) {
      const j1 = dp[i - 1] + Math.abs(heights[i] - heights[i - 1]);
      const j2 = dp[i - 2] + Math.abs(heights[i] - heights[i - 2]);
      const minCost = Math.min(j1, j2);
      steps.push({
        grid: [dp.slice()],
        active: [0, i],
        deps: [[0, i - 1], [0, i - 2]],
        formula: `dp[${i}] = min(dp[${i-1}]+|h[${i}]-h[${i-1}]|, dp[${i-2}]+|h[${i}]-h[${i-2}]|) = min(${j1}, ${j2}) = ${minCost}`,
        desc: `Choose minimum between jumping from i-1 (${j1}) and jumping from i-2 (${j2}).`
      });
      dp[i] = minCost;
    }

    return { rows: 1, cols: n, rowHeaders, colHeaders, steps };
  }

  // Case 3: 2D Grid Unique Paths (m x n)
  if (dpId === 'DP 8' || dpId === 'DP 9' || dpId === 'DP 10') {
    let m = 3, n = 4;
    const parts = paramStr.split(/[,\s]+/).map(Number).filter(x => !isNaN(x) && x > 0);
    if (parts.length >= 2) {
      m = Math.min(6, parts[0]);
      n = Math.min(6, parts[1]);
    }

    const grid = Array.from({ length: m }, () => new Array(n).fill('—'));
    const rowHeaders = Array.from({ length: m }, (_, r) => `Row ${r}`);
    const colHeaders = Array.from({ length: n }, (_, c) => `Col ${c}`);

    // Base cell (0, 0)
    grid[0][0] = 1;
    steps.push({
      grid: grid.map(r => r.slice()),
      active: [0, 0],
      deps: [],
      formula: 'dp[0][0] = 1',
      desc: '1 path to be at starting position (0, 0).'
    });

    // Fill row by row
    for (let r = 0; r < m; r++) {
      for (let c = 0; c < n; c++) {
        if (r === 0 && c === 0) continue;
        const top = r > 0 ? grid[r - 1][c] : 0;
        const left = c > 0 ? grid[r][c - 1] : 0;
        const val = top + left;
        const deps = [];
        if (r > 0) deps.push([r - 1, c]);
        if (c > 0) deps.push([r, c - 1]);

        steps.push({
          grid: grid.map(row => row.slice()),
          active: [r, c],
          deps,
          formula: `dp[${r}][${c}] = top (${top}) + left (${left}) = ${val}`,
          desc: `Paths to (${r}, ${c}) = paths from top + paths from left.`
        });
        grid[r][c] = val;
      }
    }

    return { rows: m, cols: n, rowHeaders, colHeaders, steps };
  }

  // Case 4: 2D LCS (Strings s1, s2)
  if (dpId === 'DP 24' || dpId === 'DP 25' || dpId === 'DP 26' || dpId === 'DP 33') {
    let s1 = 'abcde', s2 = 'ace';
    const parts = paramStr.split(/[,\s]+/);
    if (parts.length >= 2 && parts[0] && parts[1]) {
      s1 = parts[0].slice(0, 6);
      s2 = parts[1].slice(0, 6);
    }
    const m = s1.length, n = s2.length;
    const grid = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
    const rowHeaders = ['Ø', ...s1.split('')];
    const colHeaders = ['Ø', ...s2.split('')];

    steps.push({
      grid: grid.map(r => r.slice()),
      active: [0, 0],
      deps: [],
      formula: 'dp[0][j] = 0, dp[i][0] = 0',
      desc: 'Base case: empty string LCS with any string is 0.'
    });

    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        const c1 = s1[i - 1], c2 = s2[j - 1];
        let val, formula, deps;
        if (c1 === c2) {
          val = grid[i - 1][j - 1] + 1;
          formula = `s1[${i-1}]=='${c1}' == s2[${j-1}]=='${c2}': dp[${i}][${j}] = dp[${i-1}][${j-1}] + 1 = ${val}`;
          deps = [[i - 1, j - 1]];
        } else {
          val = Math.max(grid[i - 1][j], grid[i][j - 1]);
          formula = `s1[${i-1}]!=s2[${j-1}]: dp[${i}][${j}] = max(dp[${i-1}][${j}], dp[${i}][${j-1}]) = ${val}`;
          deps = [[i - 1, j], [i, j - 1]];
        }

        steps.push({
          grid: grid.map(r => r.slice()),
          active: [i, j],
          deps,
          formula,
          desc: c1 === c2 ? `Characters match ('${c1}')! Extend diagonal LCS by +1.` : `Characters mismatch: take max of top (${grid[i-1][j]}) and left (${grid[i][j-1]}).`
        });
        grid[i][j] = val;
      }
    }

    return { rows: m + 1, cols: n + 1, rowHeaders, colHeaders, steps };
  }

  // Default Fallback: 1D generic table
  const size = 6;
  const dp = new Array(size).fill('—');
  const rowHeaders = ['dp'];
  const colHeaders = Array.from({ length: size }, (_, i) => `i=${i}`);
  for (let i = 0; i < size; i++) {
    dp[i] = i * 2;
    steps.push({
      grid: [dp.slice()],
      active: [0, i],
      deps: i > 0 ? [[0, i - 1]] : [],
      formula: `dp[${i}] = ${dp[i]}`,
      desc: `Computing optimal subproblem value for state index ${i}.`
    });
  }
  return { rows: 1, cols: size, rowHeaders, colHeaders, steps };
}

function renderVisualizerStep(stepIdx) {
  if (!vizState.steps.length) return;
  const step = vizState.steps[stepIdx];
  vizState.currentStep = stepIdx;

  $('vizStepCounter').textContent = `Step ${stepIdx + 1} of ${vizState.steps.length}`;
  $('vizStateFormula').textContent = step.formula;
  $('vizStateExplanation').textContent = step.desc;

  // Render DOM table
  const container = $('vizGridContainer');
  let table = container.querySelector('.dp-table');

  if (!table || table.dataset.rows != vizState.rows || table.dataset.cols != vizState.cols) {
    container.innerHTML = '';
    table = document.createElement('table');
    table.className = 'dp-table';
    table.dataset.rows = vizState.rows;
    table.dataset.cols = vizState.cols;

    // Header row
    const headTr = document.createElement('tr');
    const cornerTh = document.createElement('th');
    cornerTh.className = 'dp-header-cell';
    cornerTh.textContent = 'State';
    headTr.appendChild(cornerTh);

    vizState.colHeaders.forEach(colName => {
      const th = document.createElement('th');
      th.className = 'dp-header-cell';
      th.textContent = colName;
      headTr.appendChild(th);
    });
    table.appendChild(headTr);

    // Grid body rows
    for (let r = 0; r < vizState.rows; r++) {
      const tr = document.createElement('tr');
      const rowTh = document.createElement('th');
      rowTh.className = 'dp-header-cell';
      rowTh.textContent = vizState.rowHeaders[r] || `r=${r}`;
      tr.appendChild(rowTh);

      for (let c = 0; c < vizState.cols; c++) {
        const td = document.createElement('td');
        td.id = `dp_cell_${r}_${c}`;
        td.className = 'dp-cell';
        td.textContent = '—';
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
    container.appendChild(table);
  }

  // Update cell values and styling
  for (let r = 0; r < vizState.rows; r++) {
    for (let c = 0; c < vizState.cols; c++) {
      const cell = $(`dp_cell_${r}_${c}`);
      if (!cell) continue;

      const val = step.grid[r][c];
      cell.textContent = val;

      cell.classList.remove('active', 'dep', 'computed');

      if (val !== '—') {
        cell.classList.add('computed');
      }

      if (step.active[0] === r && step.active[1] === c) {
        cell.classList.add('active');
      } else if (step.deps.some(d => d[0] === r && d[1] === c)) {
        cell.classList.add('dep');
      }
    }
  }
}

function buildVisualizerForCurrentProblem() {
  if (!P[current]) return;
  const p = P[current];
  $('vizProblemTitle').textContent = `${p.dp} · ${p.title} Table Visualizer`;

  // Default param according to problem
  if (p.dp === 'DP 2') $('vizParamInput').value = '6';
  else if (p.dp === 'DP 3') $('vizParamInput').value = '[10, 20, 30, 10, 60, 50]';
  else if (p.dp === 'DP 8') $('vizParamInput').value = '3, 4';
  else if (p.dp === 'DP 25') $('vizParamInput').value = 'abcde, ace';
  else $('vizParamInput').value = '6';

  const data = generateDPSteps(p.dp, $('vizParamInput').value);
  vizState.dpId = p.dp;
  vizState.title = p.title;
  vizState.rows = data.rows;
  vizState.cols = data.cols;
  vizState.rowHeaders = data.rowHeaders;
  vizState.colHeaders = data.colHeaders;
  vizState.steps = data.steps;
  vizState.currentStep = 0;

  stopVizPlay();
  renderVisualizerStep(0);
}

function stopVizPlay() {
  if (vizState.timer) {
    clearInterval(vizState.timer);
    vizState.timer = null;
    const playBtn = $('vizPlay');
    if (playBtn) {
      playBtn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Play</span>
      `;
    }
  }
}

function toggleVizPlay() {
  if (vizState.timer) {
    stopVizPlay();
  } else {
    const playBtn = $('vizPlay');
    if (playBtn) {
      playBtn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true">
          <rect x="6" y="4" width="4" height="16"></rect>
          <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
        <span>Pause</span>
      `;
    }
    vizState.speed = parseInt($('vizSpeed').value) || 600;
    vizState.timer = setInterval(() => {
      if (vizState.currentStep < vizState.steps.length - 1) {
        renderVisualizerStep(vizState.currentStep + 1);
      } else {
        stopVizPlay();
      }
    }, vizState.speed);
  }
}

function initVisualizerEvents() {
  $('vizReset').onclick = () => {
    stopVizPlay();
    renderVisualizerStep(0);
  };
  $('vizPrev').onclick = () => {
    stopVizPlay();
    if (vizState.currentStep > 0) renderVisualizerStep(vizState.currentStep - 1);
  };
  $('vizNext').onclick = () => {
    stopVizPlay();
    if (vizState.currentStep < vizState.steps.length - 1) renderVisualizerStep(vizState.currentStep + 1);
  };
  $('vizPlay').onclick = toggleVizPlay;
  $('vizBuildBtn').onclick = () => {
    const data = generateDPSteps(P[current].dp, $('vizParamInput').value);
    vizState.rows = data.rows;
    vizState.cols = data.cols;
    vizState.rowHeaders = data.rowHeaders;
    vizState.colHeaders = data.colHeaders;
    vizState.steps = data.steps;
    vizState.currentStep = 0;
    stopVizPlay();
    renderVisualizerStep(0);
  };
  $('vizSpeed').onchange = () => {
    vizState.speed = parseInt($('vizSpeed').value) || 600;
    if (vizState.timer) {
      stopVizPlay();
      toggleVizPlay();
    }
  };
}


// ═════════════════════════════════════════════════════════════════════════════
// 📖 EDITORIAL & HINTS VIEWER
// ═════════════════════════════════════════════════════════════════════════════

async function loadEditorials() {
  try {
    const res = await fetch(`${API}/editorials`);
    if (res.ok) {
      editorialsData = await res.json();
    }
  } catch (e) {
    console.warn('Could not load editorials from API:', e);
  }
}

function renderEditorialForCurrentProblem() {
  if (!P[current]) return;
  const p = P[current];
  const container = $('editorialContainer');
  const ed = editorialsData[p.dp];
  const tierColors = ['#f43f5e', '#f59e0b', '#6366f1', '#10b981'];

  if (!ed) {
    container.innerHTML = `
      <div class="editorial-hero">
        <h2>${p.dp} · ${p.title}</h2>
        <div class="editorial-intuition-box">
          <b>Summary:</b> ${p.prompt}
        </div>
      </div>
      <div class="hints-header-row">
        <div class="hints-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
          <span>Progressive Hints Ladder</span>
        </div>
        <button id="btnToggleAllHints" class="btn-expand-all" onclick="toggleAllLadderSteps()">Collapse All</button>
      </div>
      <div class="editorial-ladder-step open" style="--step-color: #f43f5e;">
        <button class="editorial-step-head" onclick="toggleLadderStep(this)" aria-expanded="true">
          <div class="editorial-step-left">
            <span class="step-dot" style="background:#f43f5e; box-shadow:0 0 8px #f43f5e;"></span>
            <span class="editorial-step-badge">1. Recursion</span>
          </div>
          <div class="editorial-step-right">
            <span class="editorial-complexity">O(2^N) Time · Exponential</span>
            <svg class="step-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
        </button>
        <div class="editorial-step-body">
          <div class="editorial-step-content">Define state recurrence relation and base cases. Un-memoized recursion triggers Time Limit Exceeded (TLE) under the judge's tight 2.0s limit.</div>
        </div>
      </div>
      <div class="editorial-ladder-step open" style="--step-color: #f59e0b;">
        <button class="editorial-step-head" onclick="toggleLadderStep(this)" aria-expanded="true">
          <div class="editorial-step-left">
            <span class="step-dot" style="background:#f59e0b; box-shadow:0 0 8px #f59e0b;"></span>
            <span class="editorial-step-badge">2. Memoization (Top-Down)</span>
          </div>
          <div class="editorial-step-right">
            <span class="editorial-complexity">O(N) Time · O(N) Space</span>
            <svg class="step-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
        </button>
        <div class="editorial-step-body">
          <div class="editorial-step-content">Cache subproblem solutions in an array or matrix to eliminate redundant recursion branches.</div>
        </div>
      </div>
      <div class="editorial-ladder-step open" style="--step-color: #6366f1;">
        <button class="editorial-step-head" onclick="toggleLadderStep(this)" aria-expanded="true">
          <div class="editorial-step-left">
            <span class="step-dot" style="background:#6366f1; box-shadow:0 0 8px #6366f1;"></span>
            <span class="editorial-step-badge">3. Tabulation (Bottom-Up)</span>
          </div>
          <div class="editorial-step-right">
            <span class="editorial-complexity">O(N) Time · O(N) Table</span>
            <svg class="step-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
        </button>
        <div class="editorial-step-body">
          <div class="editorial-step-content">Iterate from base cases upward to eliminate recursion call-stack overhead entirely.</div>
        </div>
      </div>
      <div class="editorial-ladder-step open" style="--step-color: #10b981;">
        <button class="editorial-step-head" onclick="toggleLadderStep(this)" aria-expanded="true">
          <div class="editorial-step-left">
            <span class="step-dot" style="background:#10b981; box-shadow:0 0 8px #10b981;"></span>
            <span class="editorial-step-badge">4. Space Optimization</span>
          </div>
          <div class="editorial-step-right">
            <span class="editorial-complexity">O(N) Time · O(1) Space</span>
            <svg class="step-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
        </button>
        <div class="editorial-step-body">
          <div class="editorial-step-content">Track only the previous 1 or 2 required states instead of allocating an entire row or matrix.</div>
        </div>
      </div>
    `;
    return;
  }

  const ladderStepsHtml = (ed.ladder || []).map((step, idx) => {
    const isFirstTwo = idx < 2;
    const tierColor = tierColors[idx % 4];
    return `
      <div class="editorial-ladder-step ${isFirstTwo ? 'open' : ''}" style="--step-color: ${tierColor};">
        <button class="editorial-step-head" onclick="toggleLadderStep(this)" aria-expanded="${isFirstTwo}">
          <div class="editorial-step-left">
            <span class="step-dot" style="background:${tierColor}; box-shadow:0 0 8px ${tierColor};"></span>
            <span class="editorial-step-badge">${step.step}</span>
          </div>
          <div class="editorial-step-right">
            <span class="editorial-complexity">${step.complexity}</span>
            <svg class="step-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
        </button>
        <div class="editorial-step-body">
          <div class="editorial-step-content">${step.explanation}</div>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="editorial-hero">
      <h2>${p.dp} · ${ed.title || p.title}</h2>
      <div class="editorial-intuition-box">
        <b>Intuition & Proof:</b> ${ed.intuition}
      </div>
    </div>

    <div class="hints-header-row">
      <div class="hints-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        <span>Progressive Hints Ladder</span>
      </div>
      <button id="btnToggleAllHints" class="btn-expand-all" onclick="toggleAllLadderSteps()">Expand All</button>
    </div>

    ${ladderStepsHtml}

    <div class="editorial-code-section">
      <div class="code-section-header">
        <div class="code-section-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="16 18 22 12 16 6"></polyline>
            <polyline points="8 6 2 12 8 18"></polyline>
          </svg>
          <span>Reference Implementation</span>
        </div>
        <div class="grow"></div>
        <div class="lang-pills">
          <button class="lang-pill active" onclick="loadEditorialCode('python', this)">Python 3</button>
          <button class="lang-pill" onclick="loadEditorialCode('cpp', this)">C++ 17</button>
          <button class="lang-pill" onclick="loadEditorialCode('java', this)">Java 17</button>
        </div>
        <button class="copy-code-btn" onclick="copyEditorialCode(this)" aria-label="Copy code">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>Copy</span>
        </button>
      </div>
      <div id="editorialCodeBlock" class="editorial-code-box">
        <pre style="margin:0;"><code>${(ed.code?.python || '').replaceAll('<', '&lt;')}</code></pre>
      </div>
    </div>
  `;
}

window.toggleLadderStep = function(headBtn) {
  const step = headBtn.closest('.editorial-ladder-step');
  if (!step) return;
  const isOpen = step.classList.toggle('open');
  headBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
};

window.toggleAllLadderSteps = function() {
  const steps = document.querySelectorAll('.editorial-ladder-step');
  const anyClosed = Array.from(steps).some(s => !s.classList.contains('open'));
  steps.forEach(s => {
    if (anyClosed) s.classList.add('open');
    else s.classList.remove('open');
    const btn = s.querySelector('.editorial-step-head');
    if (btn) btn.setAttribute('aria-expanded', anyClosed ? 'true' : 'false');
  });
  const btn = $('btnToggleAllHints');
  if (btn) btn.textContent = anyClosed ? 'Collapse All' : 'Expand All';
};

window.copyEditorialCode = async function(btn) {
  const block = $('editorialCodeBlock');
  if (!block) return;
  const code = block.innerText;
  try {
    await navigator.clipboard.writeText(code);
    const originalText = btn.innerHTML;
    btn.classList.add('copied');
    btn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
      <span>Copied!</span>
    `;
    setTimeout(() => {
      btn.classList.remove('copied');
      btn.innerHTML = originalText;
    }, 1800);
  } catch (e) {
    toast('Code copied');
  }
};

window.loadEditorialCode = function(lang, btn) {
  const p = P[current];
  const ed = editorialsData[p.dp];
  if (!ed || !ed.code) return;
  const block = $('editorialCodeBlock');
  if (block) {
    block.innerHTML = `<pre style="margin:0;"><code>${(ed.code[lang] || '').replaceAll('<', '&lt;')}</code></pre>`;
  }
  if (btn && btn.parentElement) {
    btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
};


// ═════════════════════════════════════════════════════════════════════════════
// 📊 SUBMISSIONS & STATS DASHBOARD
// ═════════════════════════════════════════════════════════════════════════════

async function openStatsDashboard() {
  lastFocusedElement = document.activeElement;
  const modal = $('statsModal');
  modal.classList.add('show');
  $('closeStatsModal').focus();

  try {
    const res = await fetch(`${API}/stats`);
    if (!res.ok) throw new Error('Failed to load stats');
    const data = await res.json();

    $('kpiTotal').textContent = data.total_submissions || 0;
    $('kpiAc').textContent = data.ac_submissions || 0;
    $('kpiRate').textContent = `${data.ac_rate || 0}%`;
    $('kpiSolved').textContent = `${data.distinct_solved || 0} / ${P.length || 55}`;

    const tbody = $('historyTableBody');
    tbody.innerHTML = '';

    if (!data.recent || !data.recent.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--mut);">No submissions recorded yet. Run some code!</td></tr>';
      return;
    }

    data.recent.forEach(r => {
      const tr = document.createElement('tr');
      const verdict = r.verdict || 'WA';
      const verdictClass = `verdict-${verdict.toLowerCase()}`;

      tr.innerHTML = `
        <td style="color:var(--mut);">${r.id}</td>
        <td style="white-space:nowrap;font-size:11px;">${r.time}</td>
        <td><b>${r.dp}</b></td>
        <td><span style="font-family:monospace;font-size:11px;">${(r.language || 'python').toUpperCase()}</span></td>
        <td><span class="verdict-tag ${verdictClass}">${verdict}</span></td>
        <td>${r.passed} / ${r.total}</td>
        <td style="font-family:monospace;">${r.max_time_ms}ms</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error('Failed to fetch stats:', e);
  }
}

function closeStatsDashboard() {
  $('statsModal').classList.remove('show');
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
}


// ═════════════════════════════════════════════════════════════════════════════
// 🔀 TAB SWITCHING LOGIC
// ═════════════════════════════════════════════════════════════════════════════

function switchTab(tabId) {
  const tabs = [
    { btn: $('tabEditor'), pane: $('paneEditor') },
    { btn: $('tabVisualizer'), pane: $('paneVisualizer') },
    { btn: $('tabEditorial'), pane: $('paneEditorial') }
  ];

  tabs.forEach(t => {
    if (t.btn.id === tabId) {
      t.btn.classList.add('active');
      t.btn.setAttribute('aria-selected', 'true');
      t.pane.style.display = 'flex';
      t.pane.classList.add('active');
    } else {
      t.btn.classList.remove('active');
      t.btn.setAttribute('aria-selected', 'false');
      t.pane.style.display = 'none';
      t.pane.classList.remove('active');
    }
  });

  if (tabId === 'tabEditor' && editor) {
    editor.layout();
  } else if (tabId === 'tabVisualizer') {
    renderVisualizerStep(vizState.currentStep || 0);
  }
}


// ═════════════════════════════════════════════════════════════════════════════
// ⌨️ EVENT HANDLERS & ACCESSIBILITY SHORTCUTS
// ═════════════════════════════════════════════════════════════════════════════

function initEvents() {
  // Run and tests
  $('run').onclick = runOne;
  $('runTests').onclick = runTests;

  // Problem navigation
  $('prev').onclick = () => {
    if (current > 0) {
      saveCurrentCode();
      current--;
      renderQuestion();
    }
  };

  $('next').onclick = () => {
    if (current < P.length - 1) {
      saveCurrentCode();
      current++;
      renderQuestion();
    }
  };

  $('picker').onchange = () => {
    saveCurrentCode();
    current = Number($('picker').value);
    renderQuestion();
  };

  $('reset').onclick = () => {
    if (editor) {
      editor.setValue(STARTERS[currentLang] || STARTERS.python);
      saveCurrentCode();
      toast('Starter code restored');
    }
  };

  $('copy').onclick = async () => {
    if (editor) {
      await navigator.clipboard.writeText(editor.getValue());
      toast('Code copied to clipboard');
    }
  };

  $('clearOut').onclick = () => {
    $('out').textContent = '';
  };

  $('mark').onclick = () => {
    if (!P[current]) return;
    const id = P[current].id;
    done[id] = !done[id];
    saveCurrentCode();
    progress();
    renderQuestion();
    toast(done[id] ? 'Marked as solved' : 'Marked as unsolved');
  };

  // Language selector
  $('langSelect').onchange = () => {
    saveCurrentCode();
    setLanguage($('langSelect').value);
  };

  // Tabs
  $('tabEditor').onclick = () => switchTab('tabEditor');
  $('tabVisualizer').onclick = () => switchTab('tabVisualizer');
  $('tabEditorial').onclick = () => switchTab('tabEditorial');

  // Stats Modal
  $('openStats').onclick = openStatsDashboard;
  $('closeStatsModal').onclick = closeStatsDashboard;
  $('closeModal').onclick = closeModal;

  // Keyboard navigation
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (e.shiftKey) {
        runTests();
      } else {
        runOne();
      }
    }
    if (e.key === 'Escape') {
      if ($('modal').classList.contains('show')) closeModal();
      if ($('statsModal').classList.contains('show')) closeStatsDashboard();
    }
    if (e.altKey && e.key === 'ArrowRight') $('next').click();
    if (e.altKey && e.key === 'ArrowLeft') $('prev').click();
  });

  // Modal backdrop click
  $('modal').onclick = e => { if (e.target === $('modal')) closeModal(); };
  $('statsModal').onclick = e => { if (e.target === $('statsModal')) closeStatsDashboard(); };

  initVisualizerEvents();
}


// ── Monaco Initialization ───────────────────────────────────────────────────
function initFallbackEditor() {
  let ta = $('fallbackEditor');
  if (!ta) {
    ta = document.createElement('textarea');
    ta.id = 'fallbackEditor';
    ta.style.width = '100%';
    ta.style.height = '100%';
    ta.style.fontFamily = 'monospace';
    ta.style.fontSize = '14px';
    ta.style.background = '#080c13';
    ta.style.color = '#e9eef7';
    ta.style.border = 'none';
    ta.style.padding = '10px';
    $('editor').appendChild(ta);
  }
  editor = {
    getValue: () => ta.value,
    setValue: v => { ta.value = v; },
    getModel: () => null,
    layout: () => {}
  };
  renderQuestion();
}

function initMonaco() {
  if (typeof require !== 'undefined') {
    require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs' } });
    require(['vs/editor/editor.main'], () => {
      try {
        editor = monaco.editor.create($('editor'), {
          language: currentLang === 'cpp' ? 'cpp' : (currentLang === 'java' ? 'java' : 'python'),
          theme: 'vs-dark',
          automaticLayout: true,
          fontSize: 14,
          lineHeight: 22,
          minimap: { enabled: false },
          tabSize: 4,
          insertSpaces: true,
          scrollBeyondLastLine: false,
          wordWrap: 'off'
        });
        renderQuestion();
      } catch (e) {
        console.warn('Monaco create failed, falling back:', e);
        initFallbackEditor();
      }
    }, () => initFallbackEditor());
  } else {
    initFallbackEditor();
  }
}


// ── App Bootstrap ───────────────────────────────────────────────────────────
async function init() {
  initEvents();

  // Load problem metadata
  try {
    const res = await fetch(`${API}/problems`);
    if (res.ok) {
      P = await res.json();
    }
  } catch (e) {
    console.warn('Could not fetch /problems from API, checking local fallback:', e);
  }

  if (!P || !P.length) {
    try {
      const res = await fetch('problems.json');
      if (res.ok) {
        P = await res.json();
      }
    } catch (e) {
      console.error('Failed to load problems.json:', e);
    }
  }

  await loadEditorials();
  initMonaco();
}

window.addEventListener('DOMContentLoaded', init);
