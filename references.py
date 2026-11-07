"""
references.py — All DP reference implementations for the Striver A2Z DP IDE.

These functions serve as test oracles: the server compares student submissions
against these implementations for every generated test case.
"""

import bisect


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def is_subseq(x, s):
    """Return True if x is a subsequence of s."""
    it = iter(s)
    return all(any(c == q for c in it) for q in x)


# ---------------------------------------------------------------------------
# 1D DP
# ---------------------------------------------------------------------------

def climb_stairs(n: int) -> int:
    """DP 2 — Number of ways to climb n stairs (1 or 2 steps at a time)."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def frog_jump(heights: list) -> int:
    """DP 3 — Minimum energy for frog to reach last stair (jump 1 or 2)."""
    h = heights
    d = [0] + [10**18] * (len(h) - 1)
    for i in range(1, len(h)):
        d[i] = d[i - 1] + abs(h[i] - h[i - 1])
        if i > 1:
            d[i] = min(d[i], d[i - 2] + abs(h[i] - h[i - 2]))
    return d[-1]


def frog_jump_k(heights: list, k: int) -> int:
    """DP 4 — Minimum energy for frog to reach last stair (jump up to k)."""
    h = heights
    d = [0] + [10**18] * (len(h) - 1)
    for i in range(1, len(h)):
        for j in range(1, min(k, i) + 1):
            d[i] = min(d[i], d[i - j] + abs(h[i] - h[i - j]))
    return d[-1]


def max_non_adjacent(nums: list) -> int:
    """DP 5 — Maximum sum with no two adjacent elements selected."""
    p2 = p1 = 0
    for x in nums:
        p2, p1 = p1, max(p1, p2 + x)
    return p1


def house_robber_2(nums: list) -> int:
    """DP 6 — Maximum robbery on circular street (first and last adjacent)."""
    if len(nums) == 1:
        return nums[0]

    def rob_linear(arr):
        p2 = p1 = 0
        for v in arr:
            p2, p1 = p1, max(p1, p2 + v)
        return p1

    return max(rob_linear(nums[:-1]), rob_linear(nums[1:]))


# ---------------------------------------------------------------------------
# 2D / 3D DP and DP on Grids
# ---------------------------------------------------------------------------

def ninja_training(points: list) -> int:
    """DP 7 — Maximum points for ninja training (no same activity on consecutive days)."""
    d = [0, 0, 0]
    for row in points:
        d = [
            max(d[1], d[2]) + row[0],
            max(d[0], d[2]) + row[1],
            max(d[0], d[1]) + row[2],
        ]
    return max(d)


def unique_paths(m: int, n: int) -> int:
    """DP 8 — Count paths from top-left to bottom-right (right/down only)."""
    d = [1] * n
    for _ in range(1, m):
        for j in range(1, n):
            d[j] += d[j - 1]
    return d[-1]


def unique_paths_with_obstacles(grid: list) -> int:
    """DP 9 — Count paths in grid avoiding obstacles (cells marked 1)."""
    if not grid or grid[0][0]:
        return 0
    d = [0] * len(grid[0])
    d[0] = 1
    for row in grid:
        for j, x in enumerate(row):
            if x:
                d[j] = 0
            elif j:
                d[j] += d[j - 1]
    return d[-1]


def min_path_sum(grid: list) -> int:
    """DP 10 — Minimum path sum from top-left to bottom-right."""
    d = [10**18] * len(grid[0])
    d[0] = 0
    for row in grid:
        d[0] += row[0]
        for j in range(1, len(row)):
            d[j] = min(d[j], d[j - 1]) + row[j]
    return d[-1]


def triangle_min_path(triangle: list) -> int:
    """DP 11 — Minimum path sum top-to-bottom in a triangle."""
    d = triangle[-1][:]
    for i in range(len(triangle) - 2, -1, -1):
        d = [triangle[i][j] + min(d[j], d[j + 1]) for j in range(i + 1)]
    return d[0]


def min_falling_path(matrix: list) -> int:
    """DP 12 — Minimum falling path sum (can move to adjacent column)."""
    d = matrix[0][:]
    for row in matrix[1:]:
        d = [
            x + min(d[max(0, j - 1):min(len(d), j + 2)])
            for j, x in enumerate(row)
        ]
    return min(d)


def cherry_pickup_ii(grid: list) -> int:
    """DP 13 — Maximum cherries by two robots moving from row 0 to last row."""
    R, C = len(grid), len(grid[0])
    NEG_INF = -(10**9)
    # d[a][b] = best total cherries when robot1 at col a, robot2 at col b
    d = [[NEG_INF] * C for _ in range(C)]
    d[0][C - 1] = grid[0][0] + grid[0][C - 1]
    for i in range(1, R):
        nd = [[NEG_INF] * C for _ in range(C)]
        for a in range(C):
            for b in range(C):
                best = max(
                    (d[x][y]
                     for x in (a - 1, a, a + 1)
                     for y in (b - 1, b, b + 1)
                     if 0 <= x < C and 0 <= y < C),
                    default=NEG_INF,
                )
                if best > NEG_INF:
                    nd[a][b] = best + grid[i][a] + (grid[i][b] if a != b else 0)
        d = nd
    return max(map(max, d))


# ---------------------------------------------------------------------------
# DP on Subsequences (Subset / Knapsack / Coin)
# ---------------------------------------------------------------------------

def subset_sum(nums: list, target: int) -> bool:
    """DP 14 — True if some subset sums to target."""
    reachable = {0}
    for x in nums:
        reachable |= {s + x for s in list(reachable) if s + x <= target}
    return target in reachable


def can_partition(nums: list) -> bool:
    """DP 15 — True if array can be split into two equal-sum subsets."""
    total = sum(nums)
    return total % 2 == 0 and subset_sum(nums, total // 2)


def min_subset_sum_difference(nums: list) -> int:
    """DP 16 — Minimum absolute difference between two subset sums."""
    total = sum(nums)
    reachable = {0}
    for x in nums:
        reachable |= {s + x for s in list(reachable)}
    return min(abs(total - 2 * s) for s in reachable)


def count_subsets(nums: list, k: int) -> int:
    """DP 17 — Count subsets whose elements sum exactly to k."""
    if k < 0:
        return 0
    dp = [0] * (k + 1)
    dp[0] = 1
    for x in nums:
        for s in range(k, -1, -1):
            if s >= x:
                dp[s] += dp[s - x]
    return dp[k]


def count_partitions(nums: list, diff: int) -> int:
    """DP 18 — Count partitions into S1, S2 where sum(S1) - sum(S2) = diff."""
    total = sum(nums)
    if total < diff or (total - diff) % 2 != 0:
        return 0
    return count_subsets(nums, (total - diff) // 2)


def knapsack_01(weights: list, values: list, capacity: int) -> int:
    """DP 19 — 0/1 knapsack: maximum value within capacity."""
    dp = [0] * (capacity + 1)
    for W, V in zip(weights, values):
        for x in range(capacity, W - 1, -1):
            dp[x] = max(dp[x], dp[x - W] + V)
    return dp[capacity]


def min_coins(coins: list, amount: int) -> int:
    """DP 20 — Minimum coins to make amount; -1 if impossible."""
    dp = [0] + [10**9] * amount
    for x in range(1, amount + 1):
        for c in coins:
            if c <= x:
                dp[x] = min(dp[x], dp[x - c] + 1)
    return -1 if dp[amount] >= 10**9 else dp[amount]


def target_sum(nums: list, target: int) -> int:
    """DP 21 — Count sign assignments (+/-) so expression equals target."""
    total = sum(nums)
    if abs(target) > total or (total + target) % 2 != 0:
        return 0
    return count_subsets(nums, (total + target) // 2)


def coin_change_combinations(coins: list, amount: int) -> int:
    """DP 22 — Count distinct combinations of coins summing to amount."""
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for x in range(c, amount + 1):
            dp[x] += dp[x - c]
    return dp[amount]


def unbounded_knapsack(weights: list, values: list, capacity: int) -> int:
    """DP 23 — Unbounded knapsack: unlimited copies of each item."""
    dp = [0] * (capacity + 1)
    for W, V in zip(weights, values):
        for x in range(W, capacity + 1):
            dp[x] = max(dp[x], dp[x - W] + V)
    return dp[capacity]


def rod_cut(price: list, n: int) -> int:
    """DP 24 — Maximum revenue by cutting rod of length n."""
    dp = [0] * (n + 1)
    for length in range(1, n + 1):
        for c in range(1, length + 1):
            dp[length] = max(dp[length], price[c - 1] + dp[length - c])
    return dp[n]


# ---------------------------------------------------------------------------
# DP on Strings
# ---------------------------------------------------------------------------

def lcs_length(a: str, b: str) -> int:
    """DP 25 — Length of longest common subsequence."""
    d = [0] * (len(b) + 1)
    for x in a:
        nd = [0]
        for j, y in enumerate(b, 1):
            nd.append(d[j - 1] + 1 if x == y else max(d[j], nd[-1]))
        d = nd
    return d[-1]


def print_lcs(a: str, b: str) -> str:
    """DP 26 — Return one longest common subsequence string."""
    m, n = len(a), len(b)
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if a[i] == b[j]:
                d[i + 1][j + 1] = d[i][j] + 1
            else:
                d[i + 1][j + 1] = max(d[i][j + 1], d[i + 1][j])
    i, j = m, n
    out = []
    while i and j:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif d[i - 1][j] >= d[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return ''.join(reversed(out))


def longest_common_substring(a: str, b: str) -> int:
    """DP 27 — Length of longest common contiguous substring."""
    d = [0] * (len(b) + 1)
    ans = 0
    for x in a:
        nd = [0]
        for j, y in enumerate(b, 1):
            nd.append(d[j - 1] + 1 if x == y else 0)
            ans = max(ans, nd[-1])
        d = nd
    return ans


def lps_length(s: str) -> int:
    """DP 28 — Length of longest palindromic subsequence."""
    return lcs_length(s, s[::-1])


def min_insertions_palindrome(s: str) -> int:
    """DP 29 — Minimum insertions to make string a palindrome."""
    return len(s) - lps_length(s)


def min_insert_delete(a: str, b: str) -> int:
    """DP 30 — Minimum insertions + deletions to convert a into b."""
    return len(a) + len(b) - 2 * lcs_length(a, b)


def shortest_common_supersequence(a: str, b: str) -> str:
    """DP 31 — Shortest string containing both a and b as subsequences."""
    m, n = len(a), len(b)
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                d[i][j] = d[i - 1][j - 1] + 1
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1])
    i, j = m, n
    out = []
    while i and j:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif d[i - 1][j] <= d[i][j - 1]:
            out.append(a[i - 1])
            i -= 1
        else:
            out.append(b[j - 1])
            j -= 1
    out.extend(reversed(a[:i]))
    out.extend(reversed(b[:j]))
    return ''.join(reversed(out))


def num_distinct(s: str, t: str) -> int:
    """DP 32 — Number of distinct subsequences of s equal to t."""
    d = [0] * (len(t) + 1)
    d[0] = 1
    for c in s:
        for j in range(len(t), 0, -1):
            if c == t[j - 1]:
                d[j] += d[j - 1]
    return d[-1]


def edit_distance(a: str, b: str) -> int:
    """DP 33 — Minimum edit distance (insert, delete, replace)."""
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        nd = [i]
        for j, y in enumerate(b, 1):
            if x == y:
                nd.append(d[j - 1])
            else:
                nd.append(1 + min(d[j], nd[-1], d[j - 1]))
        d = nd
    return d[-1]


def wildcard_match(s: str, pattern: str) -> bool:
    """DP 34 — Wildcard matching ('?' = one char, '*' = any sequence)."""
    d = [False] * (len(pattern) + 1)
    d[0] = True
    for j, c in enumerate(pattern, 1):
        d[j] = d[j - 1] and c == '*'
    for x in s:
        nd = [False] * (len(pattern) + 1)
        for j, c in enumerate(pattern, 1):
            if c == '*':
                nd[j] = d[j] or nd[j - 1]
            else:
                nd[j] = d[j - 1] if (c == '?' or c == x) else False
        d = nd
    return d[-1]


# ---------------------------------------------------------------------------
# DP on Stocks
# ---------------------------------------------------------------------------

def max_profit_one_transaction(prices: list) -> int:
    """DP 35 — Best time to buy and sell stock (one transaction)."""
    mn = 10**18
    ans = 0
    for x in prices:
        mn = min(mn, x)
        ans = max(ans, x - mn)
    return ans


def max_profit_unlimited(prices: list) -> int:
    """DP 36 — Maximum profit with unlimited transactions."""
    return sum(max(0, b - a) for a, b in zip(prices, prices[1:]))


def max_profit_two_transactions(prices: list) -> int:
    """DP 37 — Maximum profit with at most two transactions."""
    b1 = b2 = -(10**18)
    s1 = s2 = 0
    for x in prices:
        b1 = max(b1, -x)
        s1 = max(s1, b1 + x)
        b2 = max(b2, s1 - x)
        s2 = max(s2, b2 + x)
    return s2


def max_profit_k_transactions(prices: list, k: int) -> int:
    """DP 38 — Maximum profit with at most k transactions."""
    if k >= len(prices) // 2:
        return max_profit_unlimited(prices)
    buy = [-(10**18)] * (k + 1)
    sell = [0] * (k + 1)
    for x in prices:
        for t in range(1, k + 1):
            buy[t] = max(buy[t], sell[t - 1] - x)
            sell[t] = max(sell[t], buy[t] + x)
    return sell[k]


def max_profit_cooldown(prices: list) -> int:
    """DP 39 — Maximum profit with cooldown (must wait 1 day after selling)."""
    if not prices:
        return 0
    hold = -prices[0]
    sold = 0
    rest = 0
    for x in prices[1:]:
        hold, sold, rest = max(hold, rest - x), hold + x, sold
    return max(sold, rest)


def max_profit_fee(prices: list, fee: int) -> int:
    """DP 40 — Maximum profit with transaction fee per trade."""
    cash = 0
    hold = -(10**18)
    for x in prices:
        old = cash
        cash = max(cash, hold + x - fee)
        hold = max(hold, old - x)
    return cash


# ---------------------------------------------------------------------------
# DP on LIS
# ---------------------------------------------------------------------------

def lis_length(nums: list) -> int:
    """DP 41 — Length of longest strictly increasing subsequence (O(n^2))."""
    if not nums:
        return 0
    d = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                d[i] = max(d[i], d[j] + 1)
    return max(d)


def print_lis(nums: list) -> list:
    """DP 42 — Return one longest strictly increasing subsequence."""
    if not nums:
        return []
    n = len(nums)
    d = [1] * n
    p = list(range(n))
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i] and d[j] + 1 > d[i]:
                d[i] = d[j] + 1
                p[i] = j
    idx = max(range(n), key=lambda x: d[x])
    out = []
    while p[idx] != idx:
        out.append(nums[idx])
        idx = p[idx]
    out.append(nums[idx])
    return out[::-1]


def lis_length_nlogn(nums: list) -> int:
    """DP 43 — LIS length using O(n log n) patience sorting."""
    tails = []
    for x in nums:
        j = bisect.bisect_left(tails, x)
        if j == len(tails):
            tails.append(x)
        else:
            tails[j] = x
    return len(tails)


def largest_divisible_subset(nums: list) -> list:
    """DP 44 — Largest subset where every pair has divisibility relation."""
    if not nums:
        return []
    nums = sorted(nums)
    n = len(nums)
    d = [1] * n
    p = list(range(n))
    for i in range(n):
        for j in range(i):
            if nums[i] % nums[j] == 0 and d[j] + 1 > d[i]:
                d[i] = d[j] + 1
                p[i] = j
    idx = max(range(n), key=lambda x: d[x])
    out = []
    while p[idx] != idx:
        out.append(nums[idx])
        idx = p[idx]
    out.append(nums[idx])
    return out[::-1]


def longest_string_chain(words: list) -> int:
    """DP 45 — Longest chain where each next word inserts one character."""
    dp = {}
    for w in sorted(words, key=len):
        dp[w] = 1 + max(
            (dp.get(w[:i] + w[i + 1:], 0) for i in range(len(w))),
            default=0
        )
    return max(dp.values(), default=0)


def longest_bitonic_subsequence(nums: list) -> int:
    """DP 46 — Longest subsequence that strictly increases then strictly decreases."""
    n = len(nums)
    inc = [1] * n
    dec = [1] * n
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                inc[i] = max(inc[i], inc[j] + 1)
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n):
            if nums[j] < nums[i]:
                dec[i] = max(dec[i], dec[j] + 1)
    return max((inc[i] + dec[i] - 1 for i in range(n)), default=0)


def number_of_lis(nums: list) -> int:
    """DP 47 — Count of longest increasing subsequences."""
    if not nums:
        return 0
    n = len(nums)
    L = [1] * n  # LIS length ending at i
    C = [1] * n  # count of LIS ending at i
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                if L[j] + 1 > L[i]:
                    L[i] = L[j] + 1
                    C[i] = C[j]
                elif L[j] + 1 == L[i]:
                    C[i] += C[j]
    m = max(L)
    return sum(c for l, c in zip(L, C) if l == m)


# ---------------------------------------------------------------------------
# MCM DP / Partition DP
# ---------------------------------------------------------------------------

def matrix_chain_min_cost(dims: list) -> int:
    """DP 48 — Minimum scalar multiplications for matrix chain."""
    n = len(dims) - 1
    dp = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = 10**30
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]
                dp[i][j] = min(dp[i][j], cost)
    return dp[0][n - 1] if n else 0


def matrix_chain_min_cost_tabulation(dims: list) -> int:
    """DP 49 — Same as matrix_chain_min_cost (bottom-up tabulation variant)."""
    return matrix_chain_min_cost(dims)


def min_cost_cut(length: int, cuts: list) -> int:
    """DP 50 — Minimum cost to cut a stick at given positions."""
    c = sorted([0] + cuts + [length])
    n = len(c)
    dp = [[0] * n for _ in range(n)]
    for ln in range(2, n):
        for i in range(n - ln):
            j = i + ln
            dp[i][j] = 10**30
            for k in range(i + 1, j):
                dp[i][j] = min(dp[i][j], c[j] - c[i] + dp[i][k] + dp[k][j])
    return dp[0][-1]


def burst_balloons(nums: list) -> int:
    """DP 51 — Maximum coins by bursting balloons in optimal order."""
    b = [1] + nums + [1]
    n = len(b)
    dp = [[0] * n for _ in range(n)]
    for ln in range(2, n):
        for i in range(n - ln):
            j = i + ln
            for k in range(i + 1, j):
                dp[i][j] = max(dp[i][j], b[i] * b[k] * b[j] + dp[i][k] + dp[k][j])
    return dp[0][-1]


def count_true_parenthesizations(expr: str) -> int:
    """DP 52 — Count parenthesizations of boolean expression that evaluate to True."""
    memo = {}

    def f(i, j, want):
        if i > j:
            return 0
        if i == j:
            return int((expr[i] == 'T') == want)
        if (i, j, want) in memo:
            return memo[i, j, want]
        ans = 0
        for k in range(i + 1, j, 2):
            lt = f(i, k - 1, 1)
            lf = f(i, k - 1, 0)
            rt = f(k + 1, j, 1)
            rf = f(k + 1, j, 0)
            op = expr[k]
            if op == '&':
                ans += lt * rt if want else lt * rf + lf * rt + lf * rf
            elif op == '|':
                ans += lt * rt + lt * rf + lf * rt if want else lf * rf
            else:  # '^'
                ans += lt * rf + lf * rt if want else lt * rt + lf * rf
        memo[i, j, want] = ans
        return ans

    return f(0, len(expr) - 1, 1)


def min_pal_partition_cuts(s: str) -> int:
    """DP 53 — Minimum cuts to partition string into palindromic substrings."""
    if not s:
        return 0
    n = len(s)
    # is_pal[i][j] = True if s[i..j] is a palindrome
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            is_pal[i][j] = s[i] == s[j] and (j - i < 2 or is_pal[i + 1][j - 1])
    dp = [0] * n
    for i in range(n):
        if is_pal[0][i]:
            dp[i] = 0
        else:
            dp[i] = min(dp[j - 1] + 1 for j in range(1, i + 1) if is_pal[j][i])
    return dp[-1]


def max_partition_sum(arr: list, k: int) -> int:
    """DP 54 — Maximum sum by partitioning array into groups of at most k."""
    n = len(arr)
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        mx = -(10**18)
        for ln in range(1, min(k, i) + 1):
            mx = max(mx, arr[i - ln])
            dp[i] = max(dp[i], dp[i - ln] + mx * ln)
    return dp[n]


# ---------------------------------------------------------------------------
# DP on Squares
# ---------------------------------------------------------------------------

def maximal_rectangle(matrix: list) -> int:
    """DP 55 — Area of largest rectangle containing only 1s."""
    if not matrix:
        return 0
    c = len(matrix[0])
    h = [0] * c
    ans = 0
    for row in matrix:
        for j, x in enumerate(row):
            h[j] = h[j] + 1 if str(x) == '1' else 0
        # Largest rectangle in histogram
        st = []
        for i, x in enumerate(h + [0]):
            while st and h[st[-1]] > x:
                H = h[st.pop()]
                L = st[-1] if st else -1
                ans = max(ans, H * (i - L - 1))
            st.append(i)
    return ans


def count_all_one_squares(matrix: list) -> int:
    """DP 56 — Count all square submatrices consisting entirely of 1s."""
    if not matrix:
        return 0
    R, C = len(matrix), len(matrix[0])
    dp = [[0] * C for _ in range(R)]
    ans = 0
    for i in range(R):
        for j in range(C):
            if str(matrix[i][j]) == '1':
                if i == 0 or j == 0:
                    dp[i][j] = 1
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
                ans += dp[i][j]
    return ans
