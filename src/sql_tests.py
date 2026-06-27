"""Bundled SQL problems and their hand-curated test fixtures.

SQL problems are an offline pilot: unlike the Python NeetCode set (fetched from
LeetCode by prepare.py), each SQL problem here ships with its full problem
statement *and* its test data baked in. That mirrors how Python problems get
hand-curated pass/fail data in tests.py — LeetCode never exposes expected query
results, so they have to be written by hand anyway.

Two dicts are exported:

* ``SQL_PROBLEMS`` — slug -> problem dict, the same shape data.py expects for
  Python problems plus a few SQL-only keys (``lang``, ``sql_schema``,
  ``sql_snippet``, ``reference``). data.load_problems() merges these in so they
  show up in the list with no network/prepare.py step.

* ``SQL_TESTS`` — slug -> list of test cases. Each case is one independent
  in-memory database:

      {
          "schema":        "<DDL + INSERTs run with executescript()>",
          "expected_cols": ["FirstName", ...],   # required output columns, in order
          "expected_rows": [["Allen", ...], ...],# expected result set
          "ordered":       False,                # True only when the prompt requires ORDER BY
      }

  sql_runner.py runs the user's query against ``schema`` and compares the result
  to ``expected_cols`` / ``expected_rows``.
"""

# ── 175. Combine Two Tables ────────────────────────────────────────────────

_COMBINE_TWO_TABLES_SCHEMA = """
CREATE TABLE Person (
    personId  INTEGER PRIMARY KEY,
    lastName  TEXT,
    firstName TEXT
);
CREATE TABLE Address (
    addressId INTEGER PRIMARY KEY,
    personId  INTEGER,
    city      TEXT,
    state     TEXT
);
INSERT INTO Person (personId, lastName, firstName) VALUES
    (1, 'Wang', 'Allen'),
    (2, 'Alice', 'Bob');
INSERT INTO Address (addressId, personId, city, state) VALUES
    (1, 2, 'New York City', 'New York'),
    (2, 3, 'Leetcode', 'California');
"""

# ── 176. Second Highest Salary ─────────────────────────────────────────────

_SECOND_SALARY_SCHEMA_1 = """
CREATE TABLE Employee (id INTEGER PRIMARY KEY, salary INTEGER);
INSERT INTO Employee (id, salary) VALUES (1, 100), (2, 200), (3, 300);
"""

_SECOND_SALARY_SCHEMA_2 = """
CREATE TABLE Employee (id INTEGER PRIMARY KEY, salary INTEGER);
INSERT INTO Employee (id, salary) VALUES (1, 100);
"""

# ── 182. Duplicate Emails ──────────────────────────────────────────────────

_DUPLICATE_EMAILS_SCHEMA = """
CREATE TABLE Person (id INTEGER PRIMARY KEY, email TEXT);
INSERT INTO Person (id, email) VALUES
    (1, 'a@b.com'),
    (2, 'c@d.com'),
    (3, 'a@b.com');
"""


# All SQL editorials are AI-generated (see banner). They are written for this
# offline pilot because there is no scraped NeetCode editorial for SQL problems.
_AI_BANNER = (
    "⚠  AI-GENERATED EDITORIAL\n"
    "This explanation was written by an AI model (Claude), not the official\n"
    "LeetCode/NeetCode editorial. It may contain mistakes — verify the logic\n"
    "and run the tests before trusting it.\n"
    "────────────────────────────────────────\n\n"
)

_COMBINE_TWO_TABLES_EDITORIAL = _AI_BANNER + """\
Goal: report firstName, lastName, city, and state for every person — even those
who have no matching row in Address.

Approach — LEFT JOIN
The key requirement is "every person must appear, with null for a missing
address." An INNER JOIN would silently drop people without an address (in the
sample data, Allen has no Address row and would vanish). A LEFT JOIN keeps every
row from the left table (Person) and fills the Address columns with NULL when
there is no match.

```sql
SELECT p.firstName, p.lastName, a.city, a.state
FROM Person p
LEFT JOIN Address a ON p.personId = a.personId;
```

Why it works
- LEFT JOIN preserves all Person rows; unmatched ones get NULL city/state.
- We join on personId, the foreign key linking the two tables.
- No ORDER BY is needed — the prompt allows any order.

Common mistake
Using a plain JOIN (= INNER JOIN). It passes only if every person happens to
have an address, then fails the moment one doesn't.

Complexity: one pass over Person with a lookup into Address — O(n + m) with an
index on Address.personId.
"""

_SECOND_HIGHEST_SALARY_EDITORIAL = _AI_BANNER + """\
Goal: return the second highest DISTINCT salary, or NULL when it doesn't exist
(e.g. only one employee, or everyone earns the same).

The tricky part is the "doesn't exist" case. The query must return a single row
containing NULL rather than returning zero rows.

Approach — DISTINCT + ORDER BY + LIMIT/OFFSET, wrapped in a scalar subquery
Sort the distinct salaries high to low, then skip the top one and take the next:

```sql
SELECT (
    SELECT DISTINCT salary
    FROM Employee
    ORDER BY salary DESC
    LIMIT 1 OFFSET 1
) AS SecondHighestSalary;
```

Why it works
- DISTINCT collapses ties so "200, 200, 100" still has a real second value.
- ORDER BY salary DESC puts the highest first; OFFSET 1 skips it; LIMIT 1 takes
  the runner-up.
- The inner query returns no rows when there's no second salary. Wrapping it as
  a SELECT (...) scalar subquery turns "no rows" into a single NULL row — which
  is exactly what the problem asks for.

Watch the output column name
The grader expects the column to be named SecondHighestSalary, so the AS alias
is required, not cosmetic.

Alternative

```sql
SELECT MAX(salary) AS SecondHighestSalary
FROM Employee
WHERE salary < (SELECT MAX(salary) FROM Employee);
```

MAX over an empty set also yields NULL, so this handles the edge case too.

Complexity: O(n log n) for the sort (or O(n) for the MAX-based version).
"""

_DUPLICATE_EMAILS_EDITORIAL = _AI_BANNER + """\
Goal: report every email address that appears more than once.

Approach — GROUP BY + HAVING
Group the rows by email so each distinct address becomes one group, then keep
only the groups whose row count exceeds one.

```sql
SELECT email AS Email
FROM Person
GROUP BY email
HAVING COUNT(*) > 1;
```

Why it works
- GROUP BY email buckets identical addresses together.
- COUNT(*) is the size of each bucket.
- HAVING filters on that aggregate (WHERE can't — it runs before grouping).

Remember: WHERE vs HAVING
WHERE filters individual rows before aggregation; HAVING filters groups after
aggregation. Counting duplicates is inherently a post-aggregation condition, so
it must live in HAVING.

Alternative (self-join)

```sql
SELECT DISTINCT a.email AS Email
FROM Person a
JOIN Person b ON a.email = b.email AND a.id <> b.id;
```

Readable but typically slower than GROUP BY on large tables.

Complexity: O(n) with a hash-based grouping.
"""


SQL_PROBLEMS: dict[str, dict] = {
    "combine-two-tables": {
        "id": 175,
        "title": "Combine Two Tables",
        "slug": "combine-two-tables",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Person\n"
            "  personId (int, primary key), firstName (varchar), lastName (varchar)\n\n"
            "Table: Address\n"
            "  addressId (int, primary key), personId (int), city (varchar), state (varchar)\n\n"
            "Write a solution to report the first name, last name, city, and state of "
            "each person in the Person table. If the address of a personId is not "
            "present in the Address table, report null instead.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output columns: firstName, lastName, city, state"
        ),
        "sql_schema": _COMBINE_TWO_TABLES_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "Every person must appear in the output, even without an address — "
            "that points at a LEFT JOIN.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT p.firstName, p.lastName, a.city, a.state\n"
            "FROM Person p\n"
            "LEFT JOIN Address a ON p.personId = a.personId;"
        ),
        "editorial": _COMBINE_TWO_TABLES_EDITORIAL,
    },
    "second-highest-salary": {
        "id": 176,
        "title": "Second Highest Salary",
        "slug": "second-highest-salary",
        "difficulty": "Medium",
        "lang": "sql",
        "content_text": (
            "Table: Employee\n"
            "  id (int, primary key), salary (int)\n\n"
            "Write a solution to find the second highest **distinct** salary from the "
            "Employee table. If there is no second highest salary, return null "
            "(None).\n\n"
            "Output column: SecondHighestSalary"
        ),
        "sql_schema": _SECOND_SALARY_SCHEMA_1.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "The hard part is the empty/None case. A scalar subquery that returns "
            "no row yields NULL automatically.",
            "DISTINCT + ORDER BY salary DESC + LIMIT 1 OFFSET 1 isolates the runner-up.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT (\n"
            "    SELECT DISTINCT salary\n"
            "    FROM Employee\n"
            "    ORDER BY salary DESC\n"
            "    LIMIT 1 OFFSET 1\n"
            ") AS SecondHighestSalary;"
        ),
        "editorial": _SECOND_HIGHEST_SALARY_EDITORIAL,
    },
    "duplicate-emails": {
        "id": 182,
        "title": "Duplicate Emails",
        "slug": "duplicate-emails",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Person\n"
            "  id (int, primary key), email (varchar)\n\n"
            "Write a solution to report all the duplicate emails. An email is a "
            "duplicate if it appears more than once in the table.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output column: Email"
        ),
        "sql_schema": _DUPLICATE_EMAILS_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "GROUP BY the email, then HAVING COUNT(*) > 1 keeps only the repeats.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT email AS Email\n"
            "FROM Person\n"
            "GROUP BY email\n"
            "HAVING COUNT(*) > 1;"
        ),
        "editorial": _DUPLICATE_EMAILS_EDITORIAL,
    },
}


SQL_TESTS: dict[str, list[dict]] = {
    "combine-two-tables": [
        {
            "schema": _COMBINE_TWO_TABLES_SCHEMA,
            "expected_cols": ["firstName", "lastName", "city", "state"],
            "expected_rows": [
                ["Allen", "Wang", None, None],
                ["Bob", "Alice", "New York City", "New York"],
            ],
            "ordered": False,
        },
    ],
    "second-highest-salary": [
        {
            "schema": _SECOND_SALARY_SCHEMA_1,
            "expected_cols": ["SecondHighestSalary"],
            "expected_rows": [[200]],
            "ordered": False,
        },
        {
            "schema": _SECOND_SALARY_SCHEMA_2,
            "expected_cols": ["SecondHighestSalary"],
            "expected_rows": [[None]],
            "ordered": False,
        },
    ],
    "duplicate-emails": [
        {
            "schema": _DUPLICATE_EMAILS_SCHEMA,
            "expected_cols": ["Email"],
            "expected_rows": [["a@b.com"]],
            "ordered": False,
        },
    ],
}


def is_sql_slug(slug: str) -> bool:
    return slug in SQL_PROBLEMS
