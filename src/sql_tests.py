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
