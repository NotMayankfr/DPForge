"""
test_references.py — Pytest suite that validates every reference solution
against an independent brute-force verifier.

Run with:
    python -m pytest test_references.py -v --tb=short
"""

import random
import itertools
import pytest
from collections import deque

from references import (
    climb_stairs,
    frog_jump,
    frog_jump_k,
    max_non_adjacent,
    house_robber_2,
    ninja_training,
    unique_paths,
    unique_paths_with_obstacles,
    min_path_sum,
    subset_sum,
    can_partition,
    knapsack_01,
    min_coins,
    lcs_length,
    edit_distance,
    lis_length,
    max_profit_one_transaction,
    max_profit_unlimited,
)

RNG = random.Random(42)


# ---------------------------------------------------------------------------
# Brute-force helpers
# ---------------------------------------------------------------------------

def bf_climb_stairs(n: int) -> int:
    """Pure recursive Fibonacci (exponential — only for small n)."""
    if n <= 1:
        return 1
    return bf_climb_stairs(n - 1) + bf_climb_stairs(n - 2)


def bf_frog_jump(heights: list) -> int:
    """Brute force: try all 1/2 jump sequences via DFS."""
    n = len(heights)
    best = [10**18]

    def dfs(i, cost):
        if i == n - 1:
            best[0] = min(best[0], cost)
            return
        dfs(i + 1, cost + abs(heights[i + 1] - heights[i]))
        if i + 2 < n:
            dfs(i + 2, cost + abs(heights[i + 2] - heights[i]))

    if n <= 1:
        return 0
    dfs(0, 0)
    return best[0]


def bf_max_non_adjacent(nums: list) -> int:
    """Brute force: try all 2^n subsets."""
    n = len(nums)
    best = 0
    for mask in range(1 << n):
        total = 0
        ok = True
        for i in range(n):
            if mask >> i & 1:
                if i > 0 and mask >> (i - 1) & 1:
                    ok = False
                    break
                total += nums[i]
        if ok:
            best = max(best, total)
    return best


def bf_house_robber_2(nums: list) -> int:
    """Brute force: max non-adjacent on both windows."""
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    return max(bf_max_non_adjacent(nums[:-1]), bf_max_non_adjacent(nums[1:]))


def bf_unique_paths(m: int, n: int) -> int:
    """Combinatorial formula C(m+n-2, m-1)."""
    from math import comb
    return comb(m + n - 2, m - 1)


def bf_subset_sum(nums: list, target: int) -> bool:
    """Brute force: enumerate all 2^n subsets."""
    for mask in range(1 << len(nums)):
        s = sum(nums[i] for i in range(len(nums)) if mask >> i & 1)
        if s == target:
            return True
    return False


def bf_knapsack_01(weights: list, values: list, capacity: int) -> int:
    """Brute force: try all 2^n item subsets."""
    n = len(weights)
    best = 0
    for mask in range(1 << n):
        w = v = 0
        for i in range(n):
            if mask >> i & 1:
                w += weights[i]
                v += values[i]
        if w <= capacity:
            best = max(best, v)
    return best


def bf_min_coins(coins: list, amount: int) -> int:
    """Brute force BFS."""
    if amount == 0:
        return 0
    visited = {0}
    queue = deque([(0, 0)])
    while queue:
        cur, steps = queue.popleft()
        for c in coins:
            nxt = cur + c
            if nxt == amount:
                return steps + 1
            if nxt < amount and nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, steps + 1))
    return -1


def bf_lcs_length(a: str, b: str) -> int:
    """Brute force: enumerate all subsequences of a."""
    best = 0
    for mask in range(1 << len(a)):
        subseq = ''.join(a[i] for i in range(len(a)) if mask >> i & 1)
        # Check if subseq is a subsequence of b
        it = iter(b)
        if all(any(c == q for c in it) for q in subseq):
            best = max(best, len(subseq))
    return best


def bf_lis_length(nums: list) -> int:
    """Brute force: check all subsequences for strictly increasing property."""
    n = len(nums)
    best = 0
    for mask in range(1 << n):
        subseq = [nums[i] for i in range(n) if mask >> i & 1]
        if all(subseq[j] < subseq[j + 1] for j in range(len(subseq) - 1)):
            best = max(best, len(subseq))
    return best


def bf_max_profit_one_transaction(prices: list) -> int:
    """Brute force O(n^2)."""
    best = 0
    n = len(prices)
    for i in range(n):
        for j in range(i + 1, n):
            best = max(best, prices[j] - prices[i])
    return best


# ---------------------------------------------------------------------------
# Tests: climb_stairs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 16))
def test_climb_stairs(n):
    assert climb_stairs(n) == bf_climb_stairs(n), f"climb_stairs({n}) mismatch"


# ---------------------------------------------------------------------------
# Tests: frog_jump
# ---------------------------------------------------------------------------

def _gen_heights(max_len=8):
    cases = []
    for _ in range(40):
        L = RNG.randint(2, max_len)
        cases.append([RNG.randint(0, 50) for _ in range(L)])
    return cases


@pytest.mark.parametrize("heights", _gen_heights())
def test_frog_jump(heights):
    assert frog_jump(heights) == bf_frog_jump(heights), (
        f"frog_jump({heights}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: max_non_adjacent
# ---------------------------------------------------------------------------

def _gen_arrays(max_len=12):
    cases = []
    for _ in range(40):
        L = RNG.randint(1, max_len)
        cases.append([RNG.randint(0, 20) for _ in range(L)])
    return cases


@pytest.mark.parametrize("nums", _gen_arrays())
def test_max_non_adjacent(nums):
    assert max_non_adjacent(nums) == bf_max_non_adjacent(nums), (
        f"max_non_adjacent({nums}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: house_robber_2
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nums", _gen_arrays())
def test_house_robber_2(nums):
    assert house_robber_2(nums) == bf_house_robber_2(nums), (
        f"house_robber_2({nums}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: unique_paths
# ---------------------------------------------------------------------------

def _grid_dims():
    return [(RNG.randint(1, 8), RNG.randint(1, 8)) for _ in range(30)]


@pytest.mark.parametrize("m,n", _grid_dims())
def test_unique_paths(m, n):
    assert unique_paths(m, n) == bf_unique_paths(m, n), (
        f"unique_paths({m},{n}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: subset_sum
# ---------------------------------------------------------------------------

def _subset_cases():
    cases = []
    for _ in range(40):
        L = RNG.randint(0, 12)
        nums = [RNG.randint(0, 10) for _ in range(L)]
        target = RNG.randint(0, 35)
        cases.append((nums, target))
    return cases


@pytest.mark.parametrize("nums,target", _subset_cases())
def test_subset_sum(nums, target):
    assert subset_sum(nums, target) == bf_subset_sum(nums, target), (
        f"subset_sum({nums},{target}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: knapsack_01
# ---------------------------------------------------------------------------

def _knapsack_cases():
    cases = []
    for _ in range(40):
        n = RNG.randint(0, 10)
        weights = [RNG.randint(1, 8) for _ in range(n)]
        values = [RNG.randint(0, 20) for _ in range(n)]
        capacity = RNG.randint(0, 20)
        cases.append((weights, values, capacity))
    return cases


@pytest.mark.parametrize("weights,values,capacity", _knapsack_cases())
def test_knapsack_01(weights, values, capacity):
    assert knapsack_01(weights, values, capacity) == bf_knapsack_01(weights, values, capacity), (
        f"knapsack_01({weights},{values},{capacity}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: min_coins
# ---------------------------------------------------------------------------

def _coins_cases():
    cases = []
    for _ in range(40):
        coins = sorted(set(RNG.randint(1, 8) for _ in range(RNG.randint(1, 4))))
        amount = RNG.randint(0, 20)
        cases.append((coins, amount))
    return cases


@pytest.mark.parametrize("coins,amount", _coins_cases())
def test_min_coins(coins, amount):
    assert min_coins(coins, amount) == bf_min_coins(coins, amount), (
        f"min_coins({coins},{amount}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: lcs_length
# ---------------------------------------------------------------------------

def _lcs_cases():
    cases = []
    for _ in range(40):
        a = ''.join(RNG.choice('abcd') for _ in range(RNG.randint(0, 8)))
        b = ''.join(RNG.choice('abcd') for _ in range(RNG.randint(0, 8)))
        cases.append((a, b))
    return cases


@pytest.mark.parametrize("a,b", _lcs_cases())
def test_lcs_length(a, b):
    assert lcs_length(a, b) == bf_lcs_length(a, b), (
        f"lcs_length({a!r},{b!r}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: edit_distance (triangle inequality + symmetry)
# ---------------------------------------------------------------------------

def _edit_cases():
    cases = []
    for _ in range(30):
        a = ''.join(RNG.choice('abc') for _ in range(RNG.randint(0, 6)))
        b = ''.join(RNG.choice('abc') for _ in range(RNG.randint(0, 6)))
        cases.append((a, b))
    return cases


@pytest.mark.parametrize("a,b", _edit_cases())
def test_edit_distance_symmetry(a, b):
    """edit_distance must be symmetric."""
    assert edit_distance(a, b) == edit_distance(b, a), (
        f"edit_distance not symmetric for ({a!r},{b!r})"
    )


@pytest.mark.parametrize("a,b", _edit_cases())
def test_edit_distance_triangle(a, b):
    """edit_distance(a,'') == len(a) and edit_distance('',b) == len(b)."""
    assert edit_distance(a, '') == len(a), f"edit_distance({a!r},'') should be {len(a)}"
    assert edit_distance('', b) == len(b), f"edit_distance('',{b!r}) should be {len(b)}"


@pytest.mark.parametrize("a,b", _edit_cases())
def test_edit_distance_identity(a, b):
    """edit_distance(x,x) == 0."""
    assert edit_distance(a, a) == 0
    assert edit_distance(b, b) == 0


# ---------------------------------------------------------------------------
# Tests: lis_length
# ---------------------------------------------------------------------------

def _lis_cases():
    cases = []
    for _ in range(40):
        L = RNG.randint(0, 10)
        nums = [RNG.randint(-10, 20) for _ in range(L)]
        cases.append(nums)
    return cases


@pytest.mark.parametrize("nums", _lis_cases())
def test_lis_length(nums):
    assert lis_length(nums) == bf_lis_length(nums), (
        f"lis_length({nums}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: max_profit_one_transaction
# ---------------------------------------------------------------------------

def _price_cases():
    cases = []
    for _ in range(40):
        L = RNG.randint(0, 15)
        prices = [RNG.randint(0, 50) for _ in range(L)]
        cases.append(prices)
    return cases


@pytest.mark.parametrize("prices", _price_cases())
def test_max_profit_one_transaction(prices):
    assert max_profit_one_transaction(prices) == bf_max_profit_one_transaction(prices), (
        f"max_profit_one_transaction({prices}) mismatch"
    )


# ---------------------------------------------------------------------------
# Tests: max_profit_unlimited (monotone property)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prices", _price_cases())
def test_max_profit_unlimited_non_negative(prices):
    """Profit must be >= 0."""
    assert max_profit_unlimited(prices) >= 0


@pytest.mark.parametrize("prices", _price_cases())
def test_max_profit_unlimited_ge_one_transaction(prices):
    """Unlimited profit >= one-transaction profit."""
    assert max_profit_unlimited(prices) >= max_profit_one_transaction(prices)


# ---------------------------------------------------------------------------
# Extra: ninja_training (brute force vs reference for small inputs)
# ---------------------------------------------------------------------------

def _ninja_cases():
    cases = []
    for _ in range(20):
        days = RNG.randint(1, 6)
        pts = [[RNG.randint(0, 20) for _ in range(3)] for _ in range(days)]
        cases.append(pts)
    return cases


def bf_ninja_training(points):
    """Brute force: try all activity sequences where no same on consecutive days."""
    if not points:
        return 0
    n = len(points)
    best = 0
    for seq in itertools.product(range(3), repeat=n):
        if any(seq[i] == seq[i + 1] for i in range(n - 1)):
            continue
        total = sum(points[d][seq[d]] for d in range(n))
        best = max(best, total)
    return best


@pytest.mark.parametrize("points", _ninja_cases())
def test_ninja_training(points):
    assert ninja_training(points) == bf_ninja_training(points), (
        f"ninja_training({points}) mismatch"
    )
