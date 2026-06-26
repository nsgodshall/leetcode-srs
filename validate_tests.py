"""Validate all HAND_TESTS expected values against reference implementations."""
import sys, math, heapq, bisect
from collections import deque, Counter, defaultdict
from functools import lru_cache

sys.path.insert(0, ".")
from src.tests import HAND_TESTS

# ── Helpers ───────────────────────────────────────────────────────────────────
class ListNode:
    def __init__(self, val=0, next=None): self.val = val; self.next = next
class TreeNode:
    def __init__(self, val=0, left=None, right=None): self.val=val; self.left=left; self.right=right

def build_list(vals):
    if not vals: return None
    head = ListNode(vals[0]); cur = head
    for v in vals[1:]: cur.next = ListNode(v); cur = cur.next
    return head

def list_to_arr(head):
    res = []
    while head: res.append(head.val); head = head.next
    return res

def build_tree(vals):
    if not vals: return None
    root = TreeNode(vals[0]); q = deque([root]); i = 1
    while q and i < len(vals):
        node = q.popleft()
        if i < len(vals) and vals[i] is not None:
            node.left = TreeNode(vals[i]); q.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TreeNode(vals[i]); q.append(node.right)
        i += 1
    return root

def tree_to_arr(root):
    if not root: return []
    res = []; q = deque([root])
    while q:
        node = q.popleft()
        if node: res.append(node.val); q.append(node.left); q.append(node.right)
        else: res.append(None)
    while res and res[-1] is None: res.pop()
    return res

def cmp(got, exp, mode):
    if mode == "set":
        try: return set(got) == set(exp)
        except TypeError: return sorted(str(x) for x in got) == sorted(str(x) for x in exp)
    if mode == "sorted_lists":
        return sorted(str(x) for x in got) == sorted(str(x) for x in exp)
    if mode == "set_of_tuples":
        return set(tuple(sorted(x)) for x in got) == set(tuple(sorted(x)) for x in exp)
    if mode == "sorted_groups":
        sg = lambda g: sorted([sorted(row) for row in g])
        return sg(got) == sg(exp)
    return got == exp

def build_list_cycle(a):
    # a = [vals, pos]: build list, link tail.next to node at index pos (pos<0 = none)
    vals, pos = a
    head = build_list(vals)
    if head is not None and pos is not None and pos >= 0:
        target = head
        for _ in range(pos): target = target.next
        tail = head
        while tail.next: tail = tail.next
        tail.next = target
    return head

def conv_args(args, arg_types):
    result = []
    for i, a in enumerate(args):
        t = arg_types[i] if arg_types and i < len(arg_types) else None
        if t == "list_node": result.append(build_list(a))
        elif t == "list_node_cycle": result.append(build_list_cycle(a))
        elif t == "tree_node": result.append(build_tree(a))
        else: result.append(a)
    return result

def conv_ret(r, ret_type):
    if ret_type == "list_node": return list_to_arr(r)
    if ret_type == "tree_node": return tree_to_arr(r)
    return r

# ── Reference Implementations ─────────────────────────────────────────────────
REFS = {}

# Arrays & Hashing
def contains_duplicate(nums):
    return len(nums) != len(set(nums))
REFS["contains-duplicate"] = contains_duplicate

def valid_anagram(s, t):
    return sorted(s) == sorted(t)
REFS["valid-anagram"] = valid_anagram

def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen: return [seen[target - n], i]
        seen[n] = i
REFS["two-sum"] = two_sum

def group_anagrams(strs):
    d = defaultdict(list)
    for s in strs: d[tuple(sorted(s))].append(s)
    return list(d.values())
REFS["group-anagrams"] = group_anagrams

def top_k_frequent(nums, k):
    return [x for x, _ in Counter(nums).most_common(k)]
REFS["top-k-frequent-elements"] = top_k_frequent

def product_except_self(nums):
    n = len(nums); res = [1]*n; pre = 1
    for i in range(n): res[i] = pre; pre *= nums[i]
    suf = 1
    for i in range(n-1, -1, -1): res[i] *= suf; suf *= nums[i]
    return res
REFS["product-of-array-except-self"] = product_except_self

def valid_sudoku(board):
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == ".": continue
            b = (r//3)*3 + c//3
            if v in rows[r] or v in cols[c] or v in boxes[b]: return False
            rows[r].add(v); cols[c].add(v); boxes[b].add(v)
    return True
REFS["valid-sudoku"] = valid_sudoku

def longest_consecutive(nums):
    s = set(nums); best = 0
    for n in s:
        if n-1 not in s:
            cur = n; length = 1
            while cur+1 in s: cur += 1; length += 1
            best = max(best, length)
    return best
REFS["longest-consecutive-sequence"] = longest_consecutive

def valid_palindrome(s):
    t = ''.join(c.lower() for c in s if c.isalnum())
    return t == t[::-1]
REFS["valid-palindrome"] = valid_palindrome

# Two Pointers
def two_sum_ii(numbers, target):
    l, r = 0, len(numbers)-1
    while l < r:
        s = numbers[l]+numbers[r]
        if s == target: return [l+1, r+1]
        elif s < target: l += 1
        else: r -= 1
REFS["two-sum-ii-input-array-is-sorted"] = two_sum_ii

def three_sum(nums):
    nums.sort(); res = []
    for i in range(len(nums)-2):
        if i > 0 and nums[i] == nums[i-1]: continue
        l, r = i+1, len(nums)-1
        while l < r:
            s = nums[i]+nums[l]+nums[r]
            if s == 0:
                res.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l+1]: l += 1
                while l < r and nums[r] == nums[r-1]: r -= 1
                l += 1; r -= 1
            elif s < 0: l += 1
            else: r -= 1
    return res
REFS["3sum"] = three_sum

def max_area(height):
    l, r = 0, len(height)-1; res = 0
    while l < r:
        res = max(res, min(height[l], height[r]) * (r-l))
        if height[l] < height[r]: l += 1
        else: r -= 1
    return res
REFS["container-with-most-water"] = max_area

def trap(height):
    l, r = 0, len(height)-1; lmax = rmax = res = 0
    while l < r:
        if height[l] <= height[r]:
            lmax = max(lmax, height[l]); res += lmax - height[l]; l += 1
        else:
            rmax = max(rmax, height[r]); res += rmax - height[r]; r -= 1
    return res
REFS["trapping-rain-water"] = trap

# Sliding Window
def max_profit(prices):
    best = 0; low = prices[0]
    for p in prices: low = min(low, p); best = max(best, p-low)
    return best
REFS["best-time-to-buy-and-sell-stock"] = max_profit

def length_of_longest_substring(s):
    seen = {}; l = res = 0
    for r, c in enumerate(s):
        if c in seen and seen[c] >= l: l = seen[c]+1
        seen[c] = r; res = max(res, r-l+1)
    return res
REFS["longest-substring-without-repeating-characters"] = length_of_longest_substring

def character_replacement(s, k):
    count = Counter(); l = res = max_f = 0
    for r, c in enumerate(s):
        count[c] += 1; max_f = max(max_f, count[c])
        while (r-l+1) - max_f > k: count[s[l]] -= 1; l += 1
        res = max(res, r-l+1)
    return res
REFS["longest-repeating-character-replacement"] = character_replacement

def check_inclusion(s1, s2):
    if len(s1) > len(s2): return False
    c1 = Counter(s1); c2 = Counter(s2[:len(s1)])
    if c1 == c2: return True
    for i in range(len(s1), len(s2)):
        c2[s2[i]] += 1
        old = s2[i-len(s1)]; c2[old] -= 1
        if c2[old] == 0: del c2[old]
        if c1 == c2: return True
    return False
REFS["permutation-in-string"] = check_inclusion

def min_window(s, t):
    need = Counter(t); missing = len(t); l = 0; best = ""
    for r, c in enumerate(s):
        if need[c] > 0: missing -= 1
        need[c] -= 1
        if missing == 0:
            while need[s[l]] < 0: need[s[l]] += 1; l += 1
            if not best or r-l+1 < len(best): best = s[l:r+1]
            need[s[l]] += 1; missing += 1; l += 1
    return best
REFS["minimum-window-substring"] = min_window

def max_sliding_window(nums, k):
    dq = deque(); res = []
    for i, n in enumerate(nums):
        while dq and nums[dq[-1]] <= n: dq.pop()
        dq.append(i)
        if dq[0] == i-k: dq.popleft()
        if i >= k-1: res.append(nums[dq[0]])
    return res
REFS["sliding-window-maximum"] = max_sliding_window

# Stack
def is_valid_parens(s):
    stack = []; m = {')':'(',']':'[','}':'{'}
    for c in s:
        if c in m:
            if not stack or stack[-1] != m[c]: return False
            stack.pop()
        else: stack.append(c)
    return not stack
REFS["valid-parentheses"] = is_valid_parens

def eval_rpn(tokens):
    stack = []
    for t in tokens:
        if t in "+-*/":
            b, a = stack.pop(), stack.pop()
            if t == '+': stack.append(a+b)
            elif t == '-': stack.append(a-b)
            elif t == '*': stack.append(a*b)
            else: stack.append(int(a/b))
        else: stack.append(int(t))
    return stack[0]
REFS["evaluate-reverse-polish-notation"] = eval_rpn

def generate_parentheses(n):
    res = []
    def bt(s, o, c):
        if len(s) == 2*n: res.append(s); return
        if o < n: bt(s+'(', o+1, c)
        if c < o: bt(s+')', o, c+1)
    bt('', 0, 0); return res
REFS["generate-parentheses"] = generate_parentheses

def daily_temperatures(temps):
    res = [0]*len(temps); stack = []
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t: j = stack.pop(); res[j] = i-j
        stack.append(i)
    return res
REFS["daily-temperatures"] = daily_temperatures

def car_fleet(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True); stack = []
    for pos, spd in pairs:
        t = (target - pos) / spd
        if not stack or t > stack[-1]: stack.append(t)
    return len(stack)
REFS["car-fleet"] = car_fleet

def largest_rectangle(heights):
    stack = []; res = 0
    for i, h in enumerate(heights + [0]):
        start = i
        while stack and stack[-1][1] > h:
            idx, ht = stack.pop(); res = max(res, ht*(i-idx)); start = idx
        stack.append((start, h))
    return res
REFS["largest-rectangle-in-histogram"] = largest_rectangle

# Binary Search
def binary_search(nums, target):
    l, r = 0, len(nums)-1
    while l <= r:
        m = (l+r)//2
        if nums[m] == target: return m
        elif nums[m] < target: l = m+1
        else: r = m-1
    return -1
REFS["binary-search"] = binary_search

def search_matrix(matrix, target):
    m, n = len(matrix), len(matrix[0]); l, r = 0, m*n-1
    while l <= r:
        mid = (l+r)//2; val = matrix[mid//n][mid%n]
        if val == target: return True
        elif val < target: l = mid+1
        else: r = mid-1
    return False
REFS["search-a-2d-matrix"] = search_matrix

def min_eating_speed(piles, h):
    l, r = 1, max(piles)
    while l < r:
        m = (l+r)//2
        if sum(math.ceil(p/m) for p in piles) <= h: r = m
        else: l = m+1
    return l
REFS["koko-eating-bananas"] = min_eating_speed

def find_min(nums):
    l, r = 0, len(nums)-1
    while l < r:
        m = (l+r)//2
        if nums[m] > nums[r]: l = m+1
        else: r = m
    return nums[l]
REFS["find-minimum-in-rotated-sorted-array"] = find_min

def search_rotated(nums, target):
    l, r = 0, len(nums)-1
    while l <= r:
        m = (l+r)//2
        if nums[m] == target: return m
        if nums[l] <= nums[m]:
            if nums[l] <= target < nums[m]: r = m-1
            else: l = m+1
        else:
            if nums[m] < target <= nums[r]: l = m+1
            else: r = m-1
    return -1
REFS["search-in-rotated-sorted-array"] = search_rotated

def find_median_sorted_arrays(nums1, nums2):
    merged = sorted(nums1 + nums2); n = len(merged)
    if n % 2: return float(merged[n//2])
    return (merged[n//2-1] + merged[n//2]) / 2.0
REFS["median-of-two-sorted-arrays"] = find_median_sorted_arrays

# Linked List
def _reverse_list(head):
    prev = None
    while head: nxt = head.next; head.next = prev; prev = head; head = nxt
    return prev
REFS["reverse-linked-list"] = _reverse_list

def _merge_two(l1, l2):
    dummy = ListNode(); cur = dummy
    while l1 and l2:
        if l1.val <= l2.val: cur.next = l1; l1 = l1.next
        else: cur.next = l2; l2 = l2.next
        cur = cur.next
    cur.next = l1 or l2
    return dummy.next
REFS["merge-two-sorted-lists"] = _merge_two

def _remove_nth(head, n):
    dummy = ListNode(0, head); fast = slow = dummy
    for _ in range(n+1): fast = fast.next
    while fast: fast = fast.next; slow = slow.next
    slow.next = slow.next.next
    return dummy.next
REFS["remove-nth-node-from-end-of-list"] = _remove_nth

def _add_two(l1, l2):
    dummy = ListNode(); cur = dummy; carry = 0
    while l1 or l2 or carry:
        v = carry
        if l1: v += l1.val; l1 = l1.next
        if l2: v += l2.val; l2 = l2.next
        carry, v = divmod(v, 10); cur.next = ListNode(v); cur = cur.next
    return dummy.next
REFS["add-two-numbers"] = _add_two

def find_duplicate(nums):
    slow = fast = nums[0]
    while True:
        slow = nums[slow]; fast = nums[nums[fast]]
        if slow == fast: break
    slow = nums[0]
    while slow != fast: slow = nums[slow]; fast = nums[fast]
    return slow
REFS["find-the-duplicate-number"] = find_duplicate

def _merge_k(lists_raw):
    nodes = [build_list(l) for l in lists_raw] if lists_raw else []
    h = []; dummy = ListNode(); cur = dummy
    for i, node in enumerate(nodes):
        if node: heapq.heappush(h, (node.val, i, node))
    while h:
        val, i, node = heapq.heappop(h); cur.next = node; cur = cur.next
        if node.next: heapq.heappush(h, (node.next.val, i, node.next))
    return dummy.next
REFS["merge-k-sorted-lists"] = _merge_k

def _reverse_k_group(head, k):
    dummy = ListNode(0, head); gp = dummy
    while True:
        kth = gp
        for _ in range(k):
            kth = kth.next
            if not kth: return dummy.next
        gn = kth.next; prev, cur = gn, gp.next
        while cur != gn:
            nxt = cur.next; cur.next = prev; prev = cur; cur = nxt
        tmp = gp.next; gp.next = kth; gp = tmp
REFS["reverse-nodes-in-k-group"] = _reverse_k_group

def linked_list_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next; fast = fast.next.next
        if slow is fast: return True
    return False
REFS["linked-list-cycle"] = linked_list_cycle

# Trees
def _invert(root):
    if not root: return None
    root.left, root.right = _invert(root.right), _invert(root.left); return root
REFS["invert-binary-tree"] = _invert

def max_depth(root):
    if not root: return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
REFS["maximum-depth-of-binary-tree"] = max_depth

def diameter(root):
    res = [0]
    def dfs(node):
        if not node: return 0
        l, r = dfs(node.left), dfs(node.right); res[0] = max(res[0], l+r); return 1+max(l,r)
    dfs(root); return res[0]
REFS["diameter-of-binary-tree"] = diameter

def is_balanced(root):
    def dfs(n):
        if not n: return 0
        l, r = dfs(n.left), dfs(n.right)
        if l < 0 or r < 0 or abs(l-r) > 1: return -1
        return 1+max(l,r)
    return dfs(root) >= 0
REFS["balanced-binary-tree"] = is_balanced

def is_same(p, q):
    if not p and not q: return True
    if not p or not q or p.val != q.val: return False
    return is_same(p.left, q.left) and is_same(p.right, q.right)
REFS["same-tree"] = is_same

def is_subtree(root, sub):
    if not sub: return True
    if not root: return False
    if is_same(root, sub): return True
    return is_subtree(root.left, sub) or is_subtree(root.right, sub)
REFS["subtree-of-another-tree"] = is_subtree

def lca_bst(root, p, q):
    while root:
        if p < root.val and q < root.val: root = root.left
        elif p > root.val and q > root.val: root = root.right
        else: return root.val
REFS["lowest-common-ancestor-of-a-binary-search-tree"] = lca_bst

def level_order(root):
    if not root: return []
    res = []; q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft(); level.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
        res.append(level)
    return res
REFS["binary-tree-level-order-traversal"] = level_order

def right_side_view(root):
    if not root: return []
    res = []; q = deque([root])
    while q:
        for _ in range(len(q)-1):
            node = q.popleft()
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
        node = q.popleft(); res.append(node.val)
        if node.left: q.append(node.left)
        if node.right: q.append(node.right)
    return res
REFS["binary-tree-right-side-view"] = right_side_view

def count_good(root):
    def dfs(node, mx):
        if not node: return 0
        good = 1 if node.val >= mx else 0
        return good + dfs(node.left, max(mx, node.val)) + dfs(node.right, max(mx, node.val))
    return dfs(root, float('-inf'))
REFS["count-good-nodes-in-binary-tree"] = count_good

def is_valid_bst(root):
    def dfs(n, lo, hi):
        if not n: return True
        if not (lo < n.val < hi): return False
        return dfs(n.left, lo, n.val) and dfs(n.right, n.val, hi)
    return dfs(root, float('-inf'), float('inf'))
REFS["validate-binary-search-tree"] = is_valid_bst

def kth_smallest(root, k):
    stack = []; cur = root
    while stack or cur:
        while cur: stack.append(cur); cur = cur.left
        cur = stack.pop(); k -= 1
        if k == 0: return cur.val
        cur = cur.right
REFS["kth-smallest-element-in-a-bst"] = kth_smallest

def _build_from_traversals(pre, ino):
    def build(p, i):
        if not p: return None
        root = TreeNode(p[0]); idx = i.index(p[0])
        root.left = build(p[1:1+idx], i[:idx])
        root.right = build(p[1+idx:], i[idx+1:])
        return root
    return build(pre, ino)
REFS["construct-binary-tree-from-preorder-and-inorder-traversal"] = _build_from_traversals

def max_path_sum(root):
    res = [float('-inf')]
    def dfs(n):
        if not n: return 0
        l = max(0, dfs(n.left)); r = max(0, dfs(n.right))
        res[0] = max(res[0], n.val+l+r); return n.val+max(l,r)
    dfs(root); return res[0]
REFS["binary-tree-maximum-path-sum"] = max_path_sum

# Heap
def last_stone_weight(stones):
    h = [-s for s in stones]; heapq.heapify(h)
    while len(h) > 1:
        a, b = -heapq.heappop(h), -heapq.heappop(h)
        if a != b: heapq.heappush(h, -(a-b))
    return -h[0] if h else 0
REFS["last-stone-weight"] = last_stone_weight

def k_closest(points, k):
    return sorted(points, key=lambda p: p[0]**2+p[1]**2)[:k]
REFS["k-closest-points-to-origin"] = k_closest

def find_kth_largest(nums, k):
    return sorted(nums, reverse=True)[k-1]
REFS["kth-largest-element-in-an-array"] = find_kth_largest

def task_scheduler(tasks, n):
    counts = list(Counter(tasks).values()); max_c = max(counts)
    return max(len(tasks), (max_c-1)*(n+1) + counts.count(max_c))
REFS["task-scheduler"] = task_scheduler

# Backtracking
def subsets_fn(nums):
    res = [[]]
    for n in nums: res += [s+[n] for s in res]
    return res
REFS["subsets"] = subsets_fn

def combination_sum(candidates, target):
    res = []
    def bt(start, path, rem):
        if rem == 0: res.append(path[:]); return
        for i in range(start, len(candidates)):
            if candidates[i] <= rem:
                path.append(candidates[i]); bt(i, path, rem-candidates[i]); path.pop()
    bt(0, [], target); return res
REFS["combination-sum"] = combination_sum

def permutations_fn(nums):
    if len(nums) <= 1: return [list(nums)]
    res = []
    for i, n in enumerate(nums):
        for p in permutations_fn(nums[:i]+nums[i+1:]): res.append([n]+p)
    return res
REFS["permutations"] = permutations_fn

def subsets_ii(nums):
    nums.sort(); res = [[]]; prev_size = 0
    for i, n in enumerate(nums):
        start = prev_size if i > 0 and nums[i] == nums[i-1] else 0
        prev_size = len(res)
        res += [s+[n] for s in res[start:]]
    return res
REFS["subsets-ii"] = subsets_ii

def combination_sum_ii(candidates, target):
    candidates.sort(); res = []
    def bt(start, path, rem):
        if rem == 0: res.append(path[:]); return
        for i in range(start, len(candidates)):
            if candidates[i] > rem: break
            if i > start and candidates[i] == candidates[i-1]: continue
            path.append(candidates[i]); bt(i+1, path, rem-candidates[i]); path.pop()
    bt(0, [], target); return res
REFS["combination-sum-ii"] = combination_sum_ii

def word_search(board, word):
    R, C = len(board), len(board[0])
    def dfs(r, c, i):
        if i == len(word): return True
        if not (0<=r<R and 0<=c<C) or board[r][c] != word[i]: return False
        tmp = board[r][c]; board[r][c] = '#'
        found = any(dfs(r+dr, c+dc, i+1) for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)])
        board[r][c] = tmp; return found
    import copy; b = copy.deepcopy(board)
    R, C = len(b), len(b[0])
    def dfs2(r, c, i):
        if i == len(word): return True
        if not (0<=r<R and 0<=c<C) or b[r][c] != word[i]: return False
        tmp = b[r][c]; b[r][c] = '#'
        found = any(dfs2(r+dr, c+dc, i+1) for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)])
        b[r][c] = tmp; return found
    return any(dfs2(r, c, 0) for r in range(R) for c in range(C))
REFS["word-search"] = word_search

def palindrome_part(s):
    res = []
    def bt(start, path):
        if start == len(s): res.append(path[:]); return
        for end in range(start+1, len(s)+1):
            sub = s[start:end]
            if sub == sub[::-1]: path.append(sub); bt(end, path); path.pop()
    bt(0, []); return res
REFS["palindrome-partitioning"] = palindrome_part

def letter_combinations(digits):
    if not digits: return []
    m = {'2':'abc','3':'def','4':'ghi','5':'jkl','6':'mno','7':'pqrs','8':'tuv','9':'wxyz'}
    res = ['']
    for d in digits: res = [p+c for p in res for c in m[d]]
    return res
REFS["letter-combinations-of-a-phone-number"] = letter_combinations

def n_queens(n):
    res = []; cols = set(); d1 = set(); d2 = set()
    board = [['.']*n for _ in range(n)]
    def bt(row):
        if row == n: res.append([''.join(r) for r in board]); return
        for col in range(n):
            if col in cols or (row-col) in d1 or (row+col) in d2: continue
            cols.add(col); d1.add(row-col); d2.add(row+col)
            board[row][col] = 'Q'; bt(row+1); board[row][col] = '.'
            cols.discard(col); d1.discard(row-col); d2.discard(row+col)
    bt(0); return res
REFS["n-queens"] = n_queens

def word_search_ii(board, words):
    import copy
    trie = {}
    for w in words:
        node = trie
        for c in w: node = node.setdefault(c, {})
        node['$'] = w
    b = copy.deepcopy(board)
    R, C = len(b), len(b[0]); res = []
    def dfs(r, c, node):
        ch = b[r][c]
        if ch not in node: return
        nxt = node[ch]
        if '$' in nxt: res.append(nxt.pop('$'))
        b[r][c] = '#'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<R and 0<=nc<C: dfs(nr, nc, nxt)
        b[r][c] = ch
    for r in range(R):
        for c in range(C): dfs(r, c, trie)
    return res
REFS["word-search-ii"] = word_search_ii

# Graphs
def num_islands(grid):
    import copy; g = [list(row) for row in copy.deepcopy(grid)]
    R, C = len(g), len(g[0]); count = 0
    def dfs(r, c):
        if not (0<=r<R and 0<=c<C) or g[r][c] != '1': return
        g[r][c] = '0'
        for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]: dfs(r+dr, c+dc)
    for r in range(R):
        for c in range(C):
            if g[r][c] == '1': dfs(r,c); count += 1
    return count
REFS["number-of-islands"] = num_islands

def max_area_island(grid):
    import copy; g = [list(row) for row in copy.deepcopy(grid)]
    R, C = len(g), len(g[0]); best = 0
    def dfs(r, c):
        if not (0<=r<R and 0<=c<C) or g[r][c] != 1: return 0
        g[r][c] = 0
        return 1+sum(dfs(r+dr,c+dc) for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)])
    for r in range(R):
        for c in range(C): best = max(best, dfs(r,c))
    return best
REFS["max-area-of-island"] = max_area_island

def walls_and_gates(rooms):
    import copy; r = copy.deepcopy(rooms)
    R, C = len(r), len(r[0]); INF = 2147483647; q = deque()
    for i in range(R):
        for j in range(C):
            if r[i][j] == 0: q.append((i,j))
    while q:
        row, col = q.popleft()
        for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr,nc = row+dr,col+dc
            if 0<=nr<R and 0<=nc<C and r[nr][nc]==INF:
                r[nr][nc] = r[row][col]+1; q.append((nr,nc))
    return r
REFS["walls-and-gates"] = walls_and_gates

def rotting_oranges(grid):
    import copy; g = copy.deepcopy(grid)
    R, C = len(g), len(g[0]); q = deque(); fresh = 0
    for r in range(R):
        for c in range(C):
            if g[r][c] == 2: q.append((r,c,0))
            elif g[r][c] == 1: fresh += 1
    if fresh == 0: return 0
    time = 0
    while q:
        r,c,t = q.popleft()
        for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr,nc = r+dr,c+dc
            if 0<=nr<R and 0<=nc<C and g[nr][nc]==1:
                g[nr][nc]=2; fresh-=1; time=t+1; q.append((nr,nc,t+1))
    return time if fresh==0 else -1
REFS["rotting-oranges"] = rotting_oranges

def pacific_atlantic(heights):
    R, C = len(heights), len(heights[0])
    def bfs(starts):
        visited = set(starts); q = deque(starts)
        while q:
            r,c = q.popleft()
            for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                nr,nc = r+dr,c+dc
                if 0<=nr<R and 0<=nc<C and (nr,nc) not in visited and heights[nr][nc]>=heights[r][c]:
                    visited.add((nr,nc)); q.append((nr,nc))
        return visited
    pac = bfs([(r,0) for r in range(R)] + [(0,c) for c in range(C)])
    atl = bfs([(r,C-1) for r in range(R)] + [(R-1,c) for c in range(C)])
    return sorted([list(p) for p in pac & atl])
REFS["pacific-atlantic-water-flow"] = pacific_atlantic

def solve_surrounded(board):
    import copy; b = copy.deepcopy(board)
    R, C = len(b), len(b[0])
    def dfs(r, c):
        if not(0<=r<R and 0<=c<C) or b[r][c]!='O': return
        b[r][c]='T'
        for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]: dfs(r+dr,c+dc)
    for r in range(R): dfs(r,0); dfs(r,C-1)
    for c in range(C): dfs(0,c); dfs(R-1,c)
    for r in range(R):
        for c in range(C):
            if b[r][c]=='O': b[r][c]='X'
            elif b[r][c]=='T': b[r][c]='O'
    return b
REFS["surrounded-regions"] = solve_surrounded

def can_finish(numCourses, prerequisites):
    adj = defaultdict(list)
    for a,b in prerequisites: adj[b].append(a)
    visited = set(); cycle = set()
    def dfs(v):
        if v in cycle: return False
        if v in visited: return True
        cycle.add(v)
        for nb in adj[v]:
            if not dfs(nb): return False
        cycle.remove(v); visited.add(v); return True
    return all(dfs(v) for v in range(numCourses))
REFS["course-schedule"] = can_finish

def find_order(numCourses, prerequisites):
    adj = defaultdict(list); indegree = [0]*numCourses
    for a,b in prerequisites: adj[b].append(a); indegree[a]+=1
    q = deque(v for v in range(numCourses) if indegree[v]==0); res=[]
    while q:
        v = q.popleft(); res.append(v)
        for nb in adj[v]:
            indegree[nb]-=1
            if indegree[nb]==0: q.append(nb)
    return res if len(res)==numCourses else []
REFS["course-schedule-ii"] = find_order

def valid_tree(n, edges):
    if len(edges) != n-1: return False
    adj = defaultdict(list)
    for a,b in edges: adj[a].append(b); adj[b].append(a)
    visited = set(); q = deque([0]); visited.add(0)
    while q:
        v = q.popleft()
        for nb in adj[v]:
            if nb not in visited: visited.add(nb); q.append(nb)
    return len(visited)==n
REFS["graph-valid-tree"] = valid_tree

def count_components(n, edges):
    parent = list(range(n))
    def find(x):
        while parent[x] != x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for a,b in edges: parent[find(a)]=find(b)
    return len(set(find(i) for i in range(n)))
REFS["number-of-connected-components-in-an-undirected-graph"] = count_components

def find_redundant(edges):
    parent = list(range(len(edges)+1))
    def find(x):
        while parent[x] != x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for a,b in edges:
        if find(a)==find(b): return [a,b]
        parent[find(a)]=find(b)
REFS["redundant-connection"] = find_redundant

def ladder_length(begin, end, word_list):
    word_set = set(word_list)
    if end not in word_set: return 0
    q = deque([(begin,1)])
    while q:
        word, length = q.popleft()
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                nw = word[:i]+c+word[i+1:]
                if nw == end: return length+1
                if nw in word_set: word_set.remove(nw); q.append((nw,length+1))
    return 0
REFS["word-ladder"] = ladder_length

def reconstruct_itinerary(tickets):
    adj = defaultdict(list)
    for a,b in sorted(tickets, reverse=True): adj[a].append(b)
    res = []
    def dfs(src):
        while adj[src]: dfs(adj[src].pop())
        res.append(src)
    dfs("JFK"); return res[::-1]
REFS["reconstruct-itinerary"] = reconstruct_itinerary

def min_cost_connect(points):
    n = len(points); visited = set(); h = [(0,0)]; res = 0
    while len(visited) < n:
        cost, i = heapq.heappop(h)
        if i in visited: continue
        visited.add(i); res += cost
        for j in range(n):
            if j not in visited:
                d = abs(points[i][0]-points[j][0])+abs(points[i][1]-points[j][1])
                heapq.heappush(h,(d,j))
    return res
REFS["min-cost-to-connect-all-points"] = min_cost_connect

def network_delay(times, n, k):
    adj = defaultdict(list)
    for u,v,w in times: adj[u].append((v,w))
    dist = {k:0}; h = [(0,k)]
    while h:
        d,u = heapq.heappop(h)
        if d > dist.get(u,float('inf')): continue
        for v,w in adj[u]:
            nd = d+w
            if nd < dist.get(v,float('inf')): dist[v]=nd; heapq.heappush(h,(nd,v))
    return max(dist.values()) if len(dist)==n else -1
REFS["network-delay-time"] = network_delay

def swim_in_water(grid):
    n = len(grid); h = [(grid[0][0],0,0)]; visited = set(); visited.add((0,0))
    while h:
        t,r,c = heapq.heappop(h)
        if r==n-1 and c==n-1: return t
        for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr,nc = r+dr,c+dc
            if 0<=nr<n and 0<=nc<n and (nr,nc) not in visited:
                visited.add((nr,nc)); heapq.heappush(h,(max(t,grid[nr][nc]),nr,nc))
REFS["swim-in-rising-water"] = swim_in_water

def alien_order(words):
    adj = defaultdict(set); indegree = {c:0 for w in words for c in w}
    for i in range(len(words)-1):
        a,b = words[i],words[i+1]; ml = min(len(a),len(b))
        if len(a)>len(b) and a[:ml]==b[:ml]: return ""
        for j in range(ml):
            if a[j]!=b[j]:
                if b[j] not in adj[a[j]]: adj[a[j]].add(b[j]); indegree[b[j]]+=1
                break
    q = deque(c for c in indegree if indegree[c]==0); res=""
    while q:
        c = q.popleft(); res+=c
        for nb in adj[c]:
            indegree[nb]-=1
            if indegree[nb]==0: q.append(nb)
    return res if len(res)==len(indegree) else ""
REFS["alien-dictionary"] = alien_order

def cheapest_flights(n, flights, src, dst, k):
    dp = [float('inf')]*n; dp[src]=0
    for _ in range(k+1):
        tmp = dp[:]
        for u,v,w in flights:
            if dp[u]+w < tmp[v]: tmp[v]=dp[u]+w
        dp=tmp
    return dp[dst] if dp[dst]<float('inf') else -1
REFS["cheapest-flights-within-k-stops"] = cheapest_flights

def longest_increasing_path(matrix):
    R, C = len(matrix), len(matrix[0])
    @lru_cache(None)
    def dfs(r,c):
        return 1+max((dfs(r+dr,c+dc) for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]
                      if 0<=r+dr<R and 0<=c+dc<C and matrix[r+dr][c+dc]>matrix[r][c]),default=0)
    return max(dfs(r,c) for r in range(R) for c in range(C))
REFS["longest-increasing-path-in-a-matrix"] = longest_increasing_path

# 1-D DP
def climb_stairs(n):
    a,b=1,1
    for _ in range(n-1): a,b=b,a+b
    return b
REFS["climbing-stairs"] = climb_stairs

def min_cost_climbing(cost):
    n=len(cost); dp=[0]*(n+1)
    for i in range(2,n+1): dp[i]=min(dp[i-1]+cost[i-1],dp[i-2]+cost[i-2])
    return dp[n]
REFS["min-cost-climbing-stairs"] = min_cost_climbing

def house_robber(nums):
    p2=p=0
    for n in nums: p2,p=p,max(p,p2+n)
    return p
REFS["house-robber"] = house_robber

def house_robber_ii(nums):
    def rob(arr):
        p2=p=0
        for n in arr: p2,p=p,max(p,p2+n)
        return p
    if len(nums)==1: return nums[0]
    return max(rob(nums[:-1]),rob(nums[1:]))
REFS["house-robber-ii"] = house_robber_ii

def longest_palindrome(s):
    res=""
    for i in range(len(s)):
        for l,r in [(i,i),(i,i+1)]:
            while l>=0 and r<len(s) and s[l]==s[r]: l-=1; r+=1
            if r-l-1>len(res): res=s[l+1:r]
    return res
REFS["longest-palindromic-substring"] = longest_palindrome

def count_palindromes(s):
    count=0
    for i in range(len(s)):
        for l,r in [(i,i),(i,i+1)]:
            while l>=0 and r<len(s) and s[l]==s[r]: count+=1; l-=1; r+=1
    return count
REFS["palindromic-substrings"] = count_palindromes

def decode_ways(s):
    if not s or s[0]=='0': return 0
    n=len(s); dp=[0]*(n+1); dp[0]=1; dp[1]=1
    for i in range(2,n+1):
        if s[i-1]!='0': dp[i]+=dp[i-1]
        two=int(s[i-2:i])
        if 10<=two<=26: dp[i]+=dp[i-2]
    return dp[n]
REFS["decode-ways"] = decode_ways

def coin_change(coins, amount):
    dp=[float('inf')]*(amount+1); dp[0]=0
    for i in range(1,amount+1):
        for c in coins:
            if c<=i: dp[i]=min(dp[i],dp[i-c]+1)
    return dp[amount] if dp[amount]<float('inf') else -1
REFS["coin-change"] = coin_change

def max_product(nums):
    res=nums[0]; mn=mx=nums[0]
    for n in nums[1:]:
        candidates=(n,n*mx,n*mn); mn=min(candidates); mx=max(candidates); res=max(res,mx)
    return res
REFS["maximum-product-subarray"] = max_product

def word_break(s, wordDict):
    ws=set(wordDict); n=len(s); dp=[False]*(n+1); dp[0]=True
    for i in range(1,n+1):
        for j in range(i):
            if dp[j] and s[j:i] in ws: dp[i]=True; break
    return dp[n]
REFS["word-break"] = word_break

def lis_fn(nums):
    tails=[]
    for n in nums:
        pos=bisect.bisect_left(tails,n)
        if pos==len(tails): tails.append(n)
        else: tails[pos]=n
    return len(tails)
REFS["longest-increasing-subsequence"] = lis_fn

def can_partition(nums):
    total=sum(nums)
    if total%2: return False
    target=total//2; dp=set([0])
    for n in nums: dp|={x+n for x in dp}
    return target in dp
REFS["partition-equal-subset-sum"] = can_partition

def unique_paths(m, n):
    dp=[[1]*n for _ in range(m)]
    for r in range(1,m):
        for c in range(1,n): dp[r][c]=dp[r-1][c]+dp[r][c-1]
    return dp[m-1][n-1]
REFS["unique-paths"] = unique_paths

def lcs_fn(t1, t2):
    m,n=len(t1),len(t2); dp=[[0]*(n+1) for _ in range(m+1)]
    for i in range(1,m+1):
        for j in range(1,n+1):
            if t1[i-1]==t2[j-1]: dp[i][j]=dp[i-1][j-1]+1
            else: dp[i][j]=max(dp[i-1][j],dp[i][j-1])
    return dp[m][n]
REFS["longest-common-subsequence"] = lcs_fn

def max_profit_cooldown(prices):
    hold=buy=float('-inf'); sold=rest=0
    for p in prices:
        ph=hold; ps=sold
        hold=max(ph,rest-p); sold=ph+p; rest=max(rest,ps)
    return max(sold,rest)
REFS["best-time-to-buy-and-sell-stock-with-cooldown"] = max_profit_cooldown

def coin_change_ii(amount, coins):
    dp=[0]*(amount+1); dp[0]=1
    for c in coins:
        for i in range(c,amount+1): dp[i]+=dp[i-c]
    return dp[amount]
REFS["coin-change-ii"] = coin_change_ii

def target_sum(nums, target):
    dp={0:1}
    for n in nums:
        ndp=defaultdict(int)
        for s,c in dp.items(): ndp[s+n]+=c; ndp[s-n]+=c
        dp=ndp
    return dp.get(target,0)
REFS["target-sum"] = target_sum

def interleaving(s1, s2, s3):
    if len(s1)+len(s2)!=len(s3): return False
    dp=[[False]*(len(s2)+1) for _ in range(len(s1)+1)]; dp[0][0]=True
    for i in range(len(s1)+1):
        for j in range(len(s2)+1):
            if i>0 and dp[i-1][j] and s1[i-1]==s3[i+j-1]: dp[i][j]=True
            if j>0 and dp[i][j-1] and s2[j-1]==s3[i+j-1]: dp[i][j]=True
    return dp[len(s1)][len(s2)]
REFS["interleaving-string"] = interleaving

def edit_dist(w1, w2):
    m,n=len(w1),len(w2); dp=list(range(n+1))
    for i in range(1,m+1):
        prev=dp[0]; dp[0]=i
        for j in range(1,n+1):
            tmp=dp[j]
            dp[j]=(prev if w1[i-1]==w2[j-1] else 1+min(prev,dp[j],dp[j-1])); prev=tmp
    return dp[n]
REFS["edit-distance"] = edit_dist

def num_distinct(s, t):
    n=len(t); dp=[0]*(n+1); dp[0]=1
    for c in s:
        for j in range(n-1,-1,-1):
            if c==t[j]: dp[j+1]+=dp[j]
    return dp[n]
REFS["distinct-subsequences"] = num_distinct

def max_coins(nums):
    nums=[1]+list(nums)+[1]; n=len(nums); dp=[[0]*n for _ in range(n)]
    for length in range(2,n):
        for l in range(n-length):
            r=l+length
            for k in range(l+1,r): dp[l][r]=max(dp[l][r],nums[l]*nums[k]*nums[r]+dp[l][k]+dp[k][r])
    return dp[0][n-1]
REFS["burst-balloons"] = max_coins

def regex_match(s, p):
    @lru_cache(None)
    def dp(i,j):
        if j==len(p): return i==len(s)
        first=i<len(s) and p[j] in {s[i],'.'}
        if j+1<len(p) and p[j+1]=='*':
            return dp(i,j+2) or (first and dp(i+1,j))
        return first and dp(i+1,j+1)
    return dp(0,0)
REFS["regular-expression-matching"] = regex_match

# Greedy
def max_subarray(nums):
    cur=res=nums[0]
    for n in nums[1:]: cur=max(n,cur+n); res=max(res,cur)
    return res
REFS["maximum-subarray"] = max_subarray

def can_jump(nums):
    reach=0
    for i,n in enumerate(nums):
        if i>reach: return False
        reach=max(reach,i+n)
    return True
REFS["jump-game"] = can_jump

def jump_ii(nums):
    jumps=cur_end=far=0
    for i in range(len(nums)-1):
        far=max(far,i+nums[i])
        if i==cur_end: jumps+=1; cur_end=far
    return jumps
REFS["jump-game-ii"] = jump_ii

def gas_station(gas, cost):
    if sum(gas)<sum(cost): return -1
    total=start=0
    for i,(g,c) in enumerate(zip(gas,cost)):
        total+=g-c
        if total<0: total=0; start=i+1
    return start
REFS["gas-station"] = gas_station

def is_n_straight_hand(hand, groupSize):
    if len(hand)%groupSize: return False
    count=Counter(hand)
    for k in sorted(count):
        if count[k]>0:
            n=count[k]
            for i in range(groupSize):
                if count[k+i]<n: return False
                count[k+i]-=n
    return True
REFS["hand-of-straights"] = is_n_straight_hand

def merge_triplets(triplets, target):
    res=[0,0,0]
    for t in triplets:
        if t[0]<=target[0] and t[1]<=target[1] and t[2]<=target[2]:
            res=[max(res[i],t[i]) for i in range(3)]
    return res==list(target)
REFS["merge-triplets-to-form-target-triplet"] = merge_triplets

def partition_labels(s):
    last={c:i for i,c in enumerate(s)}; res=[]; start=end=0
    for i,c in enumerate(s):
        end=max(end,last[c])
        if i==end: res.append(end-start+1); start=i+1
    return res
REFS["partition-labels"] = partition_labels

def check_valid_string(s):
    lo=hi=0
    for c in s:
        lo += 1 if c=='(' else -1
        hi += 1 if c!=')' else -1
        if hi<0: return False
        lo=max(lo,0)
    return lo==0
REFS["valid-parenthesis-string"] = check_valid_string

# Intervals
def insert_interval(intervals, new_interval):
    res=[]; i=0; n=len(intervals)
    while i<n and intervals[i][1]<new_interval[0]: res.append(intervals[i]); i+=1
    while i<n and intervals[i][0]<=new_interval[1]:
        new_interval=[min(new_interval[0],intervals[i][0]),max(new_interval[1],intervals[i][1])]; i+=1
    res.append(new_interval)
    while i<n: res.append(intervals[i]); i+=1
    return res
REFS["insert-interval"] = insert_interval

def merge_intervals(intervals):
    iv=[list(x) for x in intervals]; iv.sort(); res=[iv[0]]
    for s,e in iv[1:]:
        if s<=res[-1][1]: res[-1][1]=max(res[-1][1],e)
        else: res.append([s,e])
    return res
REFS["merge-intervals"] = merge_intervals

def erase_overlap(intervals):
    intervals=sorted(intervals,key=lambda x:x[1]); count=0; prev_end=float('-inf')
    for s,e in intervals:
        if s>=prev_end: prev_end=e
        else: count+=1
    return count
REFS["non-overlapping-intervals"] = erase_overlap

def meeting_rooms(intervals):
    intervals=sorted(intervals)
    for i in range(1,len(intervals)):
        if intervals[i][0]<intervals[i-1][1]: return False
    return True
REFS["meeting-rooms"] = meeting_rooms

def meeting_rooms_ii(intervals):
    intervals=sorted(intervals); h=[]
    for s,e in intervals:
        if h and h[0]<=s: heapq.heapreplace(h,e)
        else: heapq.heappush(h,e)
    return len(h)
REFS["meeting-rooms-ii"] = meeting_rooms_ii

def min_interval(intervals, queries):
    intervals=sorted(intervals); h=[]; res={}; i=0
    for q in sorted(queries):
        while i<len(intervals) and intervals[i][0]<=q:
            l,r=intervals[i]; heapq.heappush(h,(r-l+1,r)); i+=1
        while h and h[0][1]<q: heapq.heappop(h)
        res[q]=h[0][0] if h else -1
    return [res[q] for q in queries]
REFS["minimum-interval-to-include-each-query"] = min_interval

# Math & Geometry
def rotate_image(matrix):
    import copy; m=copy.deepcopy(matrix); n=len(m)
    for r in range(n):
        for c in range(n): m[c][n-1-r]=matrix[r][c]
    return m
REFS["rotate-image"] = rotate_image

def spiral_order(matrix):
    res = []; top = left = 0; bottom = len(matrix)-1; right = len(matrix[0])-1
    while top <= bottom and left <= right:
        for c in range(left, right+1): res.append(matrix[top][c])
        top += 1
        for r in range(top, bottom+1): res.append(matrix[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left-1, -1): res.append(matrix[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top-1, -1): res.append(matrix[r][left])
            left += 1
    return res
REFS["spiral-matrix"] = spiral_order

def set_zeroes(matrix):
    import copy; m=copy.deepcopy(matrix); R=len(m); C=len(m[0])
    rows=set(); cols=set()
    for r in range(R):
        for c in range(C):
            if m[r][c]==0: rows.add(r); cols.add(c)
    for r in rows:
        for c in range(C): m[r][c]=0
    for c in cols:
        for r in range(R): m[r][c]=0
    return m
REFS["set-matrix-zeroes"] = set_zeroes

def is_happy(n):
    def nxt(x): return sum(int(d)**2 for d in str(x))
    seen=set()
    while n!=1:
        if n in seen: return False
        seen.add(n); n=nxt(n)
    return True
REFS["happy-number"] = is_happy

def plus_one(digits):
    digits=list(digits)
    for i in range(len(digits)-1,-1,-1):
        if digits[i]<9: digits[i]+=1; return digits
        digits[i]=0
    return [1]+digits
REFS["plus-one"] = plus_one

def multiply_strings(num1, num2):
    if num1=='0' or num2=='0': return '0'
    m,n=len(num1),len(num2); pos=[0]*(m+n)
    for i in range(m-1,-1,-1):
        for j in range(n-1,-1,-1):
            mul=int(num1[i])*int(num2[j]); p1,p2=i+j,i+j+1
            s=mul+pos[p2]; pos[p2]=s%10; pos[p1]+=s//10
    return ''.join(str(d) for d in pos).lstrip('0') or '0'
REFS["multiply-strings"] = multiply_strings

def reverse_integer(x):
    sign=1 if x>=0 else -1; x=abs(x)
    rev=int(str(x)[::-1])*sign
    return rev if -(2**31)<=rev<=2**31-1 else 0
REFS["reverse-integer"] = reverse_integer

# Bit Manipulation
def single_number(nums):
    res=0
    for n in nums: res^=n
    return res
REFS["single-number"] = single_number

def hamming_weight(n):
    return bin(n).count('1')
REFS["number-of-1-bits"] = hamming_weight

def count_bits(n):
    return [bin(i).count('1') for i in range(n+1)]
REFS["counting-bits"] = count_bits

def reverse_bits(n):
    res=0
    for _ in range(32): res=(res<<1)|(n&1); n>>=1
    return res
REFS["reverse-bits"] = reverse_bits

def missing_number(nums):
    n=len(nums); return n*(n+1)//2-sum(nums)
REFS["missing-number"] = missing_number

def get_sum(a, b):
    mask=0xFFFFFFFF
    while b&mask:
        carry=(a&b)<<1; a=a^b; b=carry
    return a if b==0 else (a&mask) if (a&mask)<=0x7FFFFFFF else (a&mask)-0x100000000
REFS["sum-of-two-integers"] = get_sum

# ── Validation Loop ───────────────────────────────────────────────────────────
failures = []
slugs_checked = 0

for slug, tests in HAND_TESTS.items():
    if slug not in REFS:
        continue
    ref = REFS[slug]
    slugs_checked += 1
    for i, tc in enumerate(tests, 1):
        if tc.get("design"):
            continue
        if "expected" not in tc:
            continue
        args = tc["args"]
        arg_types = tc.get("arg_types")
        ret_type = tc.get("ret_type")
        compare = tc.get("compare")
        exp = tc["expected"]

        try:
            conv = conv_args(args, arg_types or [])
            got = ref(*conv)
            got = conv_ret(got, ret_type)
        except Exception as e:
            failures.append(f"ERROR  [{slug}] case {i}: {type(e).__name__}: {e}  args={args}")
            continue

        if not cmp(got, exp, compare):
            failures.append(
                f"FAIL   [{slug}] case {i}:  args={args}  expected={exp}  got={got}"
            )

not_covered = [s for s in HAND_TESTS if s not in REFS]

print(f"Checked {slugs_checked} slugs  ({len(not_covered)} skipped: design-only or encode-decode)")
if not_covered:
    print(f"Skipped: {not_covered}")
print()
if failures:
    for f in failures: print(f)
    print(f"\n{len(failures)} failure(s) found.")
else:
    print("0 failures found.")
