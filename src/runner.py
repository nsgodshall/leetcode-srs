"""Execute a user's Solution class against hand-curated or example test cases."""

import json
import sys
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from src.tests import HAND_TESTS

_HELPERS = textwrap.dedent("""
    from __future__ import annotations
    import sys, json, math
    from collections import deque

    class ListNode:
        def __init__(self, val=0, next=None):
            self.val = val
            self.next = next
        def __repr__(self):
            return f"ListNode({self.val})"

    class TreeNode:
        def __init__(self, val=0, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right

    def build_list(vals: list) -> ListNode | None:
        if not vals:
            return None
        head = ListNode(vals[0])
        cur = head
        for v in vals[1:]:
            cur.next = ListNode(v)
            cur = cur.next
        return head

    def list_to_arr(head: ListNode | None) -> list:
        res: list = []
        while head:
            res.append(head.val)
            head = head.next
        return res

    def build_tree(vals: list) -> TreeNode | None:
        if not vals:
            return None
        root = TreeNode(vals[0])
        q = deque([root])
        i = 1
        while q and i < len(vals):
            node = q.popleft()
            if i < len(vals) and vals[i] is not None:
                node.left = TreeNode(vals[i])
                q.append(node.left)
            i += 1
            if i < len(vals) and vals[i] is not None:
                node.right = TreeNode(vals[i])
                q.append(node.right)
            i += 1
        return root

    def tree_to_arr(root: TreeNode | None) -> list:
        if not root:
            return []
        res: list = []
        q = deque([root])
        while q:
            node = q.popleft()
            if node:
                res.append(node.val)
                q.append(node.left)
                q.append(node.right)
            else:
                res.append(None)
        while res and res[-1] is None:
            res.pop()
        return res
""")

# <<<USER_CODE_LINE>>> is replaced with an integer at render time so that
# _extract_trace() can convert absolute line numbers to user-code-relative ones.
_RUNNER_TEMPLATE = textwrap.dedent("""
    # --- helpers ---
    <<<HELPERS>>>

    # --- user solution ---
    <<<USER_CODE>>>

    # --- test runner ---
    import json as _json, traceback as _tb, re as _re

    _USER_CODE_LINE = <<<USER_CODE_LINE>>>
    _TESTS = _json.loads(<<<TESTS_JSON_REPR>>>)

    def _convert_arg(a, t):
        if t == "list_node":
            return build_list(a)
        if t == "list_node_cycle":
            # a = [vals, pos]: build the list, then link the tail's .next to the
            # node at index pos (pos < 0 means no cycle). LeetCode's encoding.
            vals, pos = a
            head = build_list(vals)
            if head is not None and pos is not None and pos >= 0:
                target = head
                for _ in range(pos):
                    target = target.next
                tail = head
                while tail.next:
                    tail = tail.next
                tail.next = target
            return head
        if t == "tree_node":
            return build_tree(a)
        return a

    def _convert_ret(r, t):
        if t == "list_node":
            return list_to_arr(r)
        if t == "tree_node":
            return tree_to_arr(r)
        return r

    def _cmp(got, exp, mode):
        if mode == "set":
            try:
                return set(got) == set(exp)
            except TypeError:
                return sorted(str(x) for x in got) == sorted(str(x) for x in exp)
        if mode == "sorted_lists":
            return sorted(str(x) for x in got) == sorted(str(x) for x in exp)
        if mode == "set_of_tuples":
            return set(tuple(sorted(x)) for x in got) == set(tuple(sorted(x)) for x in exp)
        if mode == "sorted_groups":
            sg = lambda g: sorted([sorted(row) for row in g])
            return sg(got) == sg(exp)
        return got == exp

    def _short(v, n=120):
        s = repr(v)
        return s if len(s) <= n else s[:n] + "..."

    def _extract_trace():
        lines = _tb.format_exc().strip().splitlines()
        result = []
        skip_next = False
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if 'File "' in line and __file__ in line:
                m = _re.search(r'line (\\d+)', line)
                if m:
                    rel = int(m.group(1)) - _USER_CODE_LINE + 1
                    if rel < 1 or ' in <module>' in line:
                        skip_next = True
                        continue
                    line = _re.sub(r'File "[^"]*"', '"<solution>"', line)
                    line = line.replace("line " + m.group(1), "line " + str(rel))
            result.append(line)
        return result

    # locate Solution method for regular problems
    try:
        _sol = Solution()
        _sol_methods = [m for m in dir(_sol) if not m.startswith("_") and callable(getattr(_sol, m))]
        _method = getattr(_sol, _sol_methods[0]) if _sol_methods else None
    except Exception:
        _sol = None
        _method = None

    _records = []

    for _i, _tc in enumerate(_TESTS, 1):
        # design-style: ["ClassName","op",...], [[ctor_args],[op_args],...]
        if _tc.get("design"):
            _ops     = _tc["args"][0]
            _op_args = _tc["args"][1]
            _exp_seq = _tc.get("expected") or [None] * len(_ops)
            _cname   = _ops[0]
            _cls     = globals().get(_cname)
            if _cls is None:
                _records.append(("fail", "[" + str(_i) + "] " + _cname,
                    ["class '" + _cname + "' not defined"]))
                continue
            try:
                _inst = _cls(*_op_args[0])
            except Exception:
                _records.append(("error", "[" + str(_i) + "] " + _cname,
                    ["__init__(" + repr(_op_args[0]) + ")"] + _extract_trace()))
                continue
            _fail_detail = None
            for _op, _oargs, _exp_r in zip(_ops[1:], _op_args[1:], _exp_seq[1:]):
                _m2 = getattr(_inst, _op, None)
                if _m2 is None:
                    _fail_detail = ["method '" + _op + "' not found"]
                    break
                try:
                    _r = _m2(*_oargs)
                    if _exp_r is not None and _r != _exp_r:
                        _fail_detail = [_op + repr(_oargs) + "  expected=" + repr(_exp_r) + "  got=" + repr(_r)]
                        break
                except Exception:
                    _fail_detail = [_op + repr(_oargs)] + _extract_trace()
                    break
            if _fail_detail:
                _records.append(("fail", "[" + str(_i) + "] " + _cname, _fail_detail))
            else:
                _records.append(("pass", "[" + str(_i) + "] " + _cname + " (" + str(len(_ops) - 1) + " ops)", None))
            continue

        # regular single-method problem
        if _method is None:
            print("No Solution class or public method found")
            sys.exit(1)

        _args    = _tc["args"]
        _atypes  = _tc.get("arg_types") or [None] * len(_args)
        _rtype   = _tc.get("ret_type")
        _has_exp = "expected" in _tc
        _exp     = _tc.get("expected")
        _compare = _tc.get("compare")

        _atypes += [None] * (len(_args) - len(_atypes))
        _conv = [_convert_arg(a, t) for a, t in zip(_args, _atypes)]

        try:
            _got = _method(*_conv)
            _got = _convert_ret(_got, _rtype)
        except Exception:
            _records.append(("error", "[" + str(_i) + "]",
                ["inputs=" + _short(_args)] + _extract_trace()))
            continue

        if not _has_exp:
            _records.append(("info", "[" + str(_i) + "]",
                "inputs=" + _short(_args) + "  got=" + _short(_got)))
            continue

        _ok = _cmp(_got, _exp, _compare)
        if _ok:
            _records.append(("pass", "[" + str(_i) + "]", None))
        else:
            _records.append(("fail", "[" + str(_i) + "]",
                "inputs=" + _short(_args) + "  expected=" + _short(_exp) + "  got=" + _short(_got)))

    # render: bar then failures then summary
    _sym = {"pass": ".", "fail": "F", "error": "E", "info": "?"}
    print("".join(_sym[r[0]] for r in _records))

    _failures = [(r[1], r[2]) for r in _records if r[0] in ("fail", "error")]
    _infos    = [(r[1], r[2]) for r in _records if r[0] == "info"]

    if _failures:
        print("-" * 40)
        for _label, _detail in _failures:
            print("FAILED " + _label)
            if isinstance(_detail, list):
                for _dl in _detail:
                    print("       " + _dl)
            elif _detail:
                print("       " + _detail)
    if _infos:
        print("-" * 40)
        for _label, _detail in _infos:
            print("INFO   " + _label + "  " + _detail)

    _n_pass  = sum(1 for r in _records if r[0] == "pass")
    _n_fail  = sum(1 for r in _records if r[0] in ("fail", "error"))
    _n_total = sum(1 for r in _records if r[0] != "info")
    print("-" * 40)
    if _n_fail:
        print(str(_n_fail) + " failed, " + str(_n_pass) + " passed, " + str(_n_total) + " total")
    else:
        print("All " + str(_n_pass) + " passed")
""")


def run_tests(slug: str, user_code: str) -> str:
    """Run tests for *slug*. Dispatches SQL problems to the SQLite runner;
    otherwise runs HAND_TESTS against the user's Python Solution in a subprocess.
    Returns the printable report as a string."""
    from src.sql_tests import is_sql_slug
    if is_sql_slug(slug):
        from src.sql_runner import run_sql_tests
        return run_sql_tests(slug, user_code)

    tests: list[dict[str, Any]] = HAND_TESTS.get(slug, [])
    tests_json = json.dumps(tests)

    # Compute line where user code starts in the rendered script so
    # _extract_trace() can map absolute line numbers back to user-relative ones.
    prefix = (
        _RUNNER_TEMPLATE
        .split("<<<USER_CODE>>>")[0]
        .replace("<<<HELPERS>>>", _HELPERS)
    )
    user_code_line = prefix.count("\n") + 1

    script = (
        _RUNNER_TEMPLATE
        .replace("<<<HELPERS>>>", _HELPERS)
        .replace("<<<TESTS_JSON_REPR>>>", repr(tests_json))
        .replace("<<<USER_CODE_LINE>>>", str(user_code_line))
        .replace("<<<USER_CODE>>>", user_code)
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(script)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=8,
        )
        out = result.stdout + (("\nSTDERR:\n" + result.stderr) if result.stderr.strip() else "")
    except subprocess.TimeoutExpired:
        out = "✗ Timed out after 8 seconds"
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return out.strip()
