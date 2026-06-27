"""Execute a user's SQL query against the hand-curated fixtures in sql_tests.py.

Each SQL problem has one or more independent test cases (see SQL_TESTS). For a
case we spin up an in-memory SQLite database, run the case's schema (DDL + seed
INSERTs), execute the user's query, and compare the result set — both the output
columns and the rows — to the expected answer.

Output is formatted to match runner.run_tests() so the TUI's shared renderer and
the "All N passed" SRS auto-prompt work without special-casing SQL.
"""

import sqlite3
from typing import Any

from src.sql_tests import SQL_TESTS

# SQLite has no busy timeout for pure-CPU queries, but a runaway query on these
# tiny fixtures is not a realistic concern; the interrupt handler below caps the
# number of VM steps as a cheap safety net against accidental cartesian blowups.
_MAX_VM_STEPS = 5_000_000


def _short(v: Any, n: int = 120) -> str:
    s = repr(v)
    return s if len(s) <= n else s[:n] + "..."


def _strip_query(code: str) -> str:
    """Return the query with the trailing ';' removed (sqlite3 executes one
    statement at a time; a trailing semicolon is fine, but multiple statements
    raise — so we keep only up to the first terminating semicolon)."""
    code = code.strip()
    # Drop everything after the first ';' that ends a statement so a stray second
    # statement (or trailing comment) doesn't trip "execute only one statement".
    if ";" in code:
        code = code[: code.index(";") + 1]
    return code


def _run_one(case: dict, query: str) -> tuple[list[str], list[list]]:
    """Run *query* against a fresh in-memory DB seeded with case['schema'].

    Returns (column_names, rows). Raises sqlite3.Error on a bad query.
    """
    con = sqlite3.connect(":memory:")
    try:
        steps = 0

        def _guard() -> int:
            nonlocal steps
            steps += 1
            return 1 if steps > _MAX_VM_STEPS else 0

        con.executescript(case["schema"])
        con.set_progress_handler(_guard, 1000)
        cur = con.execute(query)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchall()]
        return cols, rows
    finally:
        con.close()


def _cols_match(got: list[str], expected: list[str]) -> bool:
    # LeetCode enforces output column names/aliases; compare case-insensitively
    # and order-sensitively, which is what graders effectively do.
    return [c.lower() for c in got] == [c.lower() for c in expected]


def _rows_match(got: list[list], expected: list[list], ordered: bool) -> bool:
    if ordered:
        return got == expected
    # Order-insensitive: compare as multisets of rows. Rows can contain None, so
    # use repr-keyed sorting rather than relying on mixed-type comparisons.
    key = lambda rows: sorted(repr(r) for r in rows)
    return key(got) == key(expected)


def run_sql_tests(slug: str, user_code: str) -> str:
    """Run SQL_TESTS for *slug* against *user_code*. Returns a printable report."""
    cases = SQL_TESTS.get(slug, [])
    if not cases:
        return "No SQL tests for this problem."

    query = _strip_query(user_code)
    if not query or query.lstrip().startswith("--") and "\n" not in query:
        return "No query found. Press e to write a SQL query first."

    records: list[tuple[str, str, Any]] = []
    for i, case in enumerate(cases, 1):
        label = f"[{i}]"
        try:
            cols, rows = _run_one(case, query)
        except sqlite3.Error as e:
            records.append(("error", label, [f"SQL error: {e}"]))
            continue

        exp_cols = case["expected_cols"]
        exp_rows = case["expected_rows"]

        if not _cols_match(cols, exp_cols):
            records.append(("fail", label, [
                f"wrong columns  expected={_short(exp_cols)}  got={_short(cols)}",
            ]))
            continue

        if not _rows_match(rows, exp_rows, case.get("ordered", False)):
            order_note = " (order matters)" if case.get("ordered") else ""
            records.append(("fail", label, [
                f"wrong rows{order_note}",
                f"expected={_short(exp_rows)}",
                f"got=     {_short(rows)}",
            ]))
            continue

        records.append(("pass", f"{label} ({len(rows)} rows)", None))

    return _render(records)


def _render(records: list[tuple[str, str, Any]]) -> str:
    """Format records the same way runner.py does (bar, failures, summary)."""
    sym = {"pass": ".", "fail": "F", "error": "E"}
    out: list[str] = ["".join(sym[r[0]] for r in records)]

    failures = [(r[1], r[2]) for r in records if r[0] in ("fail", "error")]
    if failures:
        out.append("-" * 40)
        for label, detail in failures:
            out.append("FAILED " + label)
            for line in detail or []:
                out.append("       " + line)

    n_pass = sum(1 for r in records if r[0] == "pass")
    n_fail = sum(1 for r in records if r[0] in ("fail", "error"))
    n_total = len(records)
    out.append("-" * 40)
    if n_fail:
        out.append(f"{n_fail} failed, {n_pass} passed, {n_total} total")
    else:
        out.append(f"All {n_pass} passed")

    return "\n".join(out)
