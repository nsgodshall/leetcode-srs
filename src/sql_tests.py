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

# Second dataset for Combine Two Tables: every person has an address (exercises
# the matched path, complementing the unmatched/NULL case above).
_COMBINE_TWO_TABLES_SCHEMA_2 = """
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
    (1, 'Smith', 'Carol'),
    (2, 'Jones', 'David');
INSERT INTO Address (addressId, personId, city, state) VALUES
    (1, 1, 'Austin', 'Texas'),
    (2, 2, 'Reno', 'Nevada');
"""

# Second dataset for Duplicate Emails: no duplicates → empty result.
_DUPLICATE_EMAILS_SCHEMA_2 = """
CREATE TABLE Person (id INTEGER PRIMARY KEY, email TEXT);
INSERT INTO Person (id, email) VALUES
    (1, 'x@y.com'),
    (2, 'z@y.com');
"""

# Third dataset for Duplicate Emails: two distinct duplicated addresses.
_DUPLICATE_EMAILS_SCHEMA_3 = """
CREATE TABLE Person (id INTEGER PRIMARY KEY, email TEXT);
INSERT INTO Person (id, email) VALUES
    (1, 'a@b.com'),
    (2, 'a@b.com'),
    (3, 'c@d.com'),
    (4, 'c@d.com'),
    (5, 'e@f.com');
"""

# ── 181. Employees Earning More Than Their Managers ────────────────────────

_EMP_MANAGERS_SCHEMA = """
CREATE TABLE Employee (
    id        INTEGER PRIMARY KEY,
    name      TEXT,
    salary    INTEGER,
    managerId INTEGER
);
INSERT INTO Employee (id, name, salary, managerId) VALUES
    (1, 'Joe',   70000, 3),
    (2, 'Henry', 80000, 4),
    (3, 'Sam',   60000, NULL),
    (4, 'Max',   90000, NULL);
"""

# ── 183. Customers Who Never Order ─────────────────────────────────────────

_CUSTOMERS_NEVER_ORDER_SCHEMA = """
CREATE TABLE Customers (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE Orders (id INTEGER PRIMARY KEY, customerId INTEGER);
INSERT INTO Customers (id, name) VALUES
    (1, 'Joe'),
    (2, 'Henry'),
    (3, 'Sam'),
    (4, 'Max');
INSERT INTO Orders (id, customerId) VALUES
    (1, 3),
    (2, 1);
"""

# ── 584. Find Customer Referee ─────────────────────────────────────────────

_CUSTOMER_REFEREE_SCHEMA = """
CREATE TABLE Customer (id INTEGER PRIMARY KEY, name TEXT, referee_id INTEGER);
INSERT INTO Customer (id, name, referee_id) VALUES
    (1, 'Will', NULL),
    (2, 'Jane', NULL),
    (3, 'Alex', 2),
    (4, 'Bill', NULL),
    (5, 'Zack', 1),
    (6, 'Mark', 2);
"""

# ── 595. Big Countries ─────────────────────────────────────────────────────

_BIG_COUNTRIES_SCHEMA = """
CREATE TABLE World (
    name       TEXT PRIMARY KEY,
    continent  TEXT,
    area       INTEGER,
    population  INTEGER,
    gdp        INTEGER
);
INSERT INTO World (name, continent, area, population, gdp) VALUES
    ('Afghanistan', 'Asia',   652230,  25500100, 20343000000),
    ('Albania',     'Europe', 28748,   2831741,  12960000000),
    ('Algeria',     'Africa', 2381741, 37100000, 188681000000),
    ('Andorra',     'Europe', 468,     78115,    3712000000),
    ('Angola',      'Africa', 1246700, 20609294, 100990000000);
"""

# ── 596. Classes More Than 5 Students ──────────────────────────────────────

_CLASSES_5_SCHEMA = """
CREATE TABLE Courses (student TEXT, class TEXT);
INSERT INTO Courses (student, class) VALUES
    ('A', 'Math'),
    ('B', 'English'),
    ('C', 'Math'),
    ('D', 'Biology'),
    ('E', 'Math'),
    ('F', 'Computer'),
    ('G', 'Math'),
    ('H', 'Math'),
    ('I', 'Math');
"""

# ── 197. Rising Temperature ────────────────────────────────────────────────
# recordDate is stored as TEXT 'YYYY-MM-DD'. The grader runs SQLite, so date
# math uses SQLite functions (DATE(d,'+1 day')) rather than MySQL's DATEDIFF.

_RISING_TEMP_SCHEMA = """
CREATE TABLE Weather (
    id          INTEGER PRIMARY KEY,
    recordDate  TEXT,
    temperature INTEGER
);
INSERT INTO Weather (id, recordDate, temperature) VALUES
    (1, '2015-01-01', 10),
    (2, '2015-01-02', 25),
    (3, '2015-01-03', 20),
    (4, '2015-01-04', 30);
"""

# ── 1148. Article Views I ──────────────────────────────────────────────────

_ARTICLE_VIEWS_SCHEMA = """
CREATE TABLE Views (
    article_id INTEGER,
    author_id  INTEGER,
    viewer_id  INTEGER,
    view_date  TEXT
);
INSERT INTO Views (article_id, author_id, viewer_id, view_date) VALUES
    (1, 3, 5, '2019-08-01'),
    (1, 3, 6, '2019-08-02'),
    (2, 7, 7, '2019-08-01'),
    (2, 7, 6, '2019-08-02'),
    (4, 7, 1, '2019-07-22'),
    (3, 4, 4, '2019-07-21'),
    (3, 4, 4, '2019-07-21');
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

_EMP_MANAGERS_EDITORIAL = _AI_BANNER + """\
Goal: list employees who earn strictly more than their own manager.

Approach — self-join
A manager is just another row in the same Employee table. Join the table to
itself: alias e for the employee and m for their manager, matched on
e.managerId = m.id. Then keep rows where the employee out-earns the manager.

```sql
SELECT e.name AS Employee
FROM Employee e
JOIN Employee m ON e.managerId = m.id
WHERE e.salary > m.salary;
```

Why it works
- The self-join pairs each employee with their manager's row.
- An INNER JOIN is correct here: employees with no manager (managerId IS NULL)
  can't out-earn a manager and should be excluded — the join drops them
  automatically.

Output column must be aliased Employee.

Complexity: O(n) with an index on id; O(n²) for a naive nested loop.
"""

_CUSTOMERS_NEVER_ORDER_EDITORIAL = _AI_BANNER + """\
Goal: find customers who have never placed an order.

Approach — anti-join with NOT IN
Collect the customerIds that appear in Orders, then select customers whose id is
not among them.

```sql
SELECT name AS Customers
FROM Customers
WHERE id NOT IN (SELECT customerId FROM Orders);
```

Why it works
- The subquery is the set of customers who *did* order.
- NOT IN keeps everyone outside that set.

A NULL caveat worth knowing
NOT IN behaves surprisingly if the subquery can return NULL: `x NOT IN (1, NULL)`
is never true. Orders.customerId has no NULLs here so it's safe, but the robust
alternatives avoid the trap:

```sql
SELECT c.name AS Customers
FROM Customers c
LEFT JOIN Orders o ON c.id = o.customerId
WHERE o.customerId IS NULL;
```

The LEFT JOIN keeps every customer; unmatched ones have NULL order columns, which
the WHERE then isolates.

Complexity: O(n + m).
"""

_CUSTOMER_REFEREE_EDITORIAL = _AI_BANNER + """\
Goal: report customers who were NOT referred by the customer with id = 2.

The catch is NULL. Most customers have referee_id = NULL (no referrer), and in
SQL any comparison with NULL (including `referee_id != 2`) yields UNKNOWN, not
true — so those rows would be wrongly dropped.

Approach — handle NULL explicitly

```sql
SELECT name
FROM Customer
WHERE referee_id IS NULL OR referee_id != 2;
```

Why it works
- `referee_id != 2` catches customers referred by someone other than 2.
- `referee_id IS NULL` separately catches customers with no referrer, which the
  inequality silently misses.

Key lesson: three-valued logic
NULL means "unknown," so `NULL != 2` is UNKNOWN and filtered out by WHERE. Any
time a nullable column appears in a negative condition, add an explicit IS NULL
branch (or use COALESCE).

Complexity: O(n), a single table scan.
"""

_BIG_COUNTRIES_EDITORIAL = _AI_BANNER + """\
Goal: report the name, population, and area of every "big" country — one whose
area is at least 3,000,000 OR whose population is at least 25,000,000.

Approach — a straightforward OR filter

```sql
SELECT name, population, area
FROM World
WHERE area >= 3000000 OR population >= 25000000;
```

Why it works
- The two size criteria are independent, so they're joined with OR: a country
  qualifies if it meets either one.
- Select the columns in the requested order: name, population, area.

Watch the column order
The expected output is name, population, area — not the table's natural order
(area before population). List them explicitly as required.

Complexity: O(n), a single scan.
"""

_CLASSES_5_EDITORIAL = _AI_BANNER + """\
Goal: list every class that has 5 or more students.

Approach — GROUP BY + HAVING

```sql
SELECT class
FROM Courses
GROUP BY class
HAVING COUNT(student) >= 5;
```

Why it works
- GROUP BY class makes one group per class.
- COUNT(student) is that class's enrollment.
- HAVING filters on the aggregate; WHERE can't, because it runs before grouping.

Note: if a student could enroll in the same class twice you'd use
COUNT(DISTINCT student); here each (student, class) pairing is unique.

Complexity: O(n) with hash grouping.
"""

_RISING_TEMP_EDITORIAL = _AI_BANNER + """\
Goal: find the ids of days that were warmer than the immediately previous day.

This grader runs on SQLite, so use SQLite date functions, not MySQL's DATEDIFF.

Approach — self-join on consecutive dates
Pair each day (w1) with the day before it (w2) by matching w1.recordDate to
w2.recordDate + 1 day, then keep pairs where today is warmer.

```sql
SELECT w1.id
FROM Weather w1
JOIN Weather w2 ON w1.recordDate = DATE(w2.recordDate, '+1 day')
WHERE w1.temperature > w2.temperature;
```

Why it works
- DATE(w2.recordDate, '+1 day') yields the calendar day after w2 as text
  'YYYY-MM-DD', which compares directly to w1.recordDate.
- Anchoring on the actual date (not id) is essential — ids aren't guaranteed to
  be in date order, and dates can have gaps.

MySQL vs SQLite
On LeetCode you'd write `DATEDIFF(w1.recordDate, w2.recordDate) = 1`. SQLite has
no DATEDIFF, hence the DATE(..., '+1 day') form here.

Complexity: O(n) with an index on recordDate.
"""

_ARTICLE_VIEWS_EDITORIAL = _AI_BANNER + """\
Goal: find all authors who viewed at least one of their own articles, returned
as a column `id`, sorted ascending and de-duplicated.

Approach — filter where author equals viewer

```sql
SELECT DISTINCT author_id AS id
FROM Views
WHERE author_id = viewer_id
ORDER BY id;
```

Why it works
- author_id = viewer_id means the viewer is the author — a self-view.
- DISTINCT collapses an author who self-viewed multiple times to one row.
- ORDER BY id is required: this problem specifies the result order, so it must be
  sorted (unlike the others, which allow any order).

Watch the alias and the sort
The output column must be named id, and the rows must be ascending — both are
graded.

Complexity: O(n log n) due to the sort.
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
    "employees-earning-more-than-their-managers": {
        "id": 181,
        "title": "Employees Earning More Than Their Managers",
        "slug": "employees-earning-more-than-their-managers",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Employee\n"
            "  id (int, primary key), name (varchar), salary (int), managerId (int)\n\n"
            "Write a solution to find the employees who earn more than their "
            "managers.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output column: Employee"
        ),
        "sql_schema": _EMP_MANAGERS_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "A manager is just another row in the same table — join Employee to "
            "itself on e.managerId = m.id.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT e.name AS Employee\n"
            "FROM Employee e\n"
            "JOIN Employee m ON e.managerId = m.id\n"
            "WHERE e.salary > m.salary;"
        ),
        "editorial": _EMP_MANAGERS_EDITORIAL,
    },
    "customers-who-never-order": {
        "id": 183,
        "title": "Customers Who Never Order",
        "slug": "customers-who-never-order",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Customers\n"
            "  id (int, primary key), name (varchar)\n\n"
            "Table: Orders\n"
            "  id (int, primary key), customerId (int)\n\n"
            "Write a solution to find all customers who never order anything.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output column: Customers"
        ),
        "sql_schema": _CUSTOMERS_NEVER_ORDER_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "Collect the customerIds that appear in Orders, then keep customers "
            "whose id is NOT IN that set (or use a LEFT JOIN ... IS NULL).",
        ],
        "has_solution": True,
        "reference": (
            "SELECT name AS Customers\n"
            "FROM Customers\n"
            "WHERE id NOT IN (SELECT customerId FROM Orders);"
        ),
        "editorial": _CUSTOMERS_NEVER_ORDER_EDITORIAL,
    },
    "find-customer-referee": {
        "id": 584,
        "title": "Find Customer Referee",
        "slug": "find-customer-referee",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Customer\n"
            "  id (int, primary key), name (varchar), referee_id (int, nullable)\n\n"
            "Find the names of the customers that are NOT referred by the customer "
            "with id = 2.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output column: name"
        ),
        "sql_schema": _CUSTOMER_REFEREE_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "referee_id is nullable. `referee_id != 2` is UNKNOWN for NULLs, so add "
            "an explicit `OR referee_id IS NULL`.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT name\n"
            "FROM Customer\n"
            "WHERE referee_id IS NULL OR referee_id != 2;"
        ),
        "editorial": _CUSTOMER_REFEREE_EDITORIAL,
    },
    "big-countries": {
        "id": 595,
        "title": "Big Countries",
        "slug": "big-countries",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: World\n"
            "  name (varchar, primary key), continent (varchar), area (int), "
            "population (int), gdp (bigint)\n\n"
            "A country is big if it has an area of at least 3,000,000 km² OR a "
            "population of at least 25,000,000.\n\n"
            "Write a solution to report the name, population, and area of the big "
            "countries.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output columns: name, population, area"
        ),
        "sql_schema": _BIG_COUNTRIES_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "The two size criteria are independent — combine them with OR.",
            "Mind the requested column order: name, population, area.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT name, population, area\n"
            "FROM World\n"
            "WHERE area >= 3000000 OR population >= 25000000;"
        ),
        "editorial": _BIG_COUNTRIES_EDITORIAL,
    },
    "classes-more-than-5-students": {
        "id": 596,
        "title": "Classes More Than 5 Students",
        "slug": "classes-more-than-5-students",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Courses\n"
            "  student (varchar), class (varchar)  — (student, class) is unique\n\n"
            "Write a solution to find all the classes that have at least five "
            "students.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output column: class"
        ),
        "sql_schema": _CLASSES_5_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "GROUP BY class, then HAVING COUNT(student) >= 5.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT class\n"
            "FROM Courses\n"
            "GROUP BY class\n"
            "HAVING COUNT(student) >= 5;"
        ),
        "editorial": _CLASSES_5_EDITORIAL,
    },
    "rising-temperature": {
        "id": 197,
        "title": "Rising Temperature",
        "slug": "rising-temperature",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Weather\n"
            "  id (int, primary key), recordDate (date), temperature (int)\n\n"
            "Write a solution to find all dates' id with higher temperature compared "
            "to the previous day (yesterday).\n\n"
            "NOTE: this runs on SQLite — use SQLite date functions such as "
            "DATE(recordDate, '+1 day'), not MySQL's DATEDIFF.\n\n"
            "Return the result table in **any order**.\n\n"
            "Output column: id"
        ),
        "sql_schema": _RISING_TEMP_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "Self-join Weather to itself, pairing each day with the day before via "
            "w1.recordDate = DATE(w2.recordDate, '+1 day').",
            "Anchor on the date, not the id — ids may not follow date order.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT w1.id\n"
            "FROM Weather w1\n"
            "JOIN Weather w2 ON w1.recordDate = DATE(w2.recordDate, '+1 day')\n"
            "WHERE w1.temperature > w2.temperature;"
        ),
        "editorial": _RISING_TEMP_EDITORIAL,
    },
    "article-views-i": {
        "id": 1148,
        "title": "Article Views I",
        "slug": "article-views-i",
        "difficulty": "Easy",
        "lang": "sql",
        "content_text": (
            "Table: Views\n"
            "  article_id (int), author_id (int), viewer_id (int), view_date (date)\n\n"
            "Write a solution to find all the authors that viewed at least one of "
            "their own articles.\n\n"
            "Return the result table sorted by id in **ascending order**.\n\n"
            "Output column: id"
        ),
        "sql_schema": _ARTICLE_VIEWS_SCHEMA.strip(),
        "sql_snippet": "-- Write your SQL query statement below",
        "topic_tags": ["Database"],
        "hints": [
            "A self-view is a row where author_id = viewer_id.",
            "De-duplicate with DISTINCT and remember ORDER BY id — this one is "
            "order-sensitive.",
        ],
        "has_solution": True,
        "reference": (
            "SELECT DISTINCT author_id AS id\n"
            "FROM Views\n"
            "WHERE author_id = viewer_id\n"
            "ORDER BY id;"
        ),
        "editorial": _ARTICLE_VIEWS_EDITORIAL,
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
        {
            "schema": _COMBINE_TWO_TABLES_SCHEMA_2,
            "expected_cols": ["firstName", "lastName", "city", "state"],
            "expected_rows": [
                ["Carol", "Smith", "Austin", "Texas"],
                ["David", "Jones", "Reno", "Nevada"],
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
        {
            # No duplicates → empty result set.
            "schema": _DUPLICATE_EMAILS_SCHEMA_2,
            "expected_cols": ["Email"],
            "expected_rows": [],
            "ordered": False,
        },
        {
            # Two distinct duplicated addresses.
            "schema": _DUPLICATE_EMAILS_SCHEMA_3,
            "expected_cols": ["Email"],
            "expected_rows": [["a@b.com"], ["c@d.com"]],
            "ordered": False,
        },
    ],
    "employees-earning-more-than-their-managers": [
        {
            "schema": _EMP_MANAGERS_SCHEMA,
            "expected_cols": ["Employee"],
            "expected_rows": [["Joe"]],
            "ordered": False,
        },
    ],
    "customers-who-never-order": [
        {
            "schema": _CUSTOMERS_NEVER_ORDER_SCHEMA,
            "expected_cols": ["Customers"],
            "expected_rows": [["Henry"], ["Max"]],
            "ordered": False,
        },
    ],
    "find-customer-referee": [
        {
            "schema": _CUSTOMER_REFEREE_SCHEMA,
            "expected_cols": ["name"],
            "expected_rows": [["Will"], ["Jane"], ["Bill"], ["Zack"]],
            "ordered": False,
        },
    ],
    "big-countries": [
        {
            "schema": _BIG_COUNTRIES_SCHEMA,
            "expected_cols": ["name", "population", "area"],
            "expected_rows": [
                ["Afghanistan", 25500100, 652230],
                ["Algeria", 37100000, 2381741],
            ],
            "ordered": False,
        },
    ],
    "classes-more-than-5-students": [
        {
            "schema": _CLASSES_5_SCHEMA,
            "expected_cols": ["class"],
            "expected_rows": [["Math"]],
            "ordered": False,
        },
    ],
    "rising-temperature": [
        {
            "schema": _RISING_TEMP_SCHEMA,
            "expected_cols": ["id"],
            "expected_rows": [[2], [4]],
            "ordered": False,
        },
    ],
    "article-views-i": [
        {
            "schema": _ARTICLE_VIEWS_SCHEMA,
            "expected_cols": ["id"],
            "expected_rows": [[4], [7]],
            "ordered": True,
        },
    ],
}


def is_sql_slug(slug: str) -> bool:
    return slug in SQL_PROBLEMS
