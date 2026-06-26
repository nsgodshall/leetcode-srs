"""Online fetchers for problem statements, reference solutions, and transcripts."""

import re
import subprocess
import sys
import tempfile
import time
from html import unescape
from pathlib import Path
from typing import Any

import requests

from src.problem_list import SLUG_IDS

_GRAPHQL_URL = "https://leetcode.com/graphql"
_FALLBACK_URL = "https://alfa-leetcode-api.onrender.com/select"
_GITHUB_RAW = (
    "https://raw.githubusercontent.com/neetcode-gh/leetcode/main/python/{id:04d}-{slug}.py"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com/",
    "Origin": "https://leetcode.com",
}

_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    titleSlug
    difficulty
    content
    exampleTestcases
    codeSnippets { lang code }
    topicTags { name }
    hints
  }
}
"""


def _strip_html(html: str) -> str:
    """Convert HTML to plain text without BeautifulSoup."""
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", html, flags=re.DOTALL)
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<li>", "\n• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_problem(slug: str) -> dict[str, Any] | None:
    """Fetch problem data from LeetCode GraphQL, with fallback."""
    data = _fetch_graphql(slug)
    if data is None:
        data = _fetch_fallback(slug)
    return data


def _fetch_graphql(slug: str) -> dict[str, Any] | None:
    try:
        resp = requests.post(
            _GRAPHQL_URL,
            headers=_HEADERS,
            json={"query": _QUERY, "variables": {"titleSlug": slug}},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        q = resp.json().get("data", {}).get("question")
        if not q:
            return None
        return _normalize_graphql(q)
    except Exception:
        return None


def _normalize_graphql(q: dict[str, Any]) -> dict[str, Any]:
    snippet = next(
        (s["code"] for s in (q.get("codeSnippets") or []) if s["lang"] == "Python3"),
        "",
    )
    return {
        "id": int(q.get("questionId") or 0),
        "title": q.get("title", ""),
        "slug": q.get("titleSlug", ""),
        "difficulty": q.get("difficulty", ""),
        "content_text": _strip_html(q.get("content") or ""),
        "example_testcases": q.get("exampleTestcases") or "",
        "python_snippet": snippet,
        "topic_tags": [t["name"] for t in (q.get("topicTags") or [])],
        "hints": q.get("hints") or [],
        "has_solution": False,
    }


def _fetch_fallback(slug: str) -> dict[str, Any] | None:
    try:
        resp = requests.get(
            _FALLBACK_URL,
            params={"titleSlug": slug},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        d = resp.json()
        if not d:
            return None
        snippet = next(
            (s["code"] for s in (d.get("codeSnippets") or []) if s.get("lang") == "Python3"),
            "",
        )
        return {
            "id": int(d.get("questionFrontendId") or SLUG_IDS.get(slug, 0)),
            "title": d.get("title", slug),
            "slug": slug,
            "difficulty": d.get("difficulty", ""),
            "content_text": _strip_html(d.get("content") or d.get("question") or ""),
            "example_testcases": d.get("exampleTestcases") or "",
            "python_snippet": snippet,
            "topic_tags": [t["name"] for t in (d.get("topicTags") or [])],
            "hints": d.get("hints") or [],
            "has_solution": False,
        }
    except Exception:
        return None


def fetch_solution(slug: str) -> str | None:
    """Fetch reference Python solution from neetcode-gh/leetcode on GitHub."""
    problem_id = SLUG_IDS.get(slug, 0)
    url = _GITHUB_RAW.format(id=problem_id, slug=slug)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None


def fetch_transcript(slug: str, title: str) -> str | None:
    """
    Download the auto-generated YouTube transcript for a NeetCode video.

    Uses yt-dlp to search for "NeetCode <title>" and downloads only the
    subtitle VTT file (no video).  Returns cleaned plain text, or None on
    failure.
    """
    ytdlp = _find_ytdlp()
    if not ytdlp:
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        query = f"ytsearch1:NeetCode {title} solution"
        cmd = [
            ytdlp,
            query,
            "--write-auto-sub",
            "--skip-download",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "-o", f"{tmpdir}/%(id)s",
            "--no-playlist",
            "-q",
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=45)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

        vtt_file = next(Path(tmpdir).glob("*.vtt"), None)
        if not vtt_file:
            return None
        return _parse_vtt(vtt_file.read_text(encoding="utf-8", errors="replace"))


def _find_ytdlp() -> str | None:
    """Return the path to yt-dlp, checking venv and PATH."""
    # Prefer venv-installed yt-dlp
    venv_bin = Path(sys.executable).parent / "yt-dlp"
    if venv_bin.exists():
        return str(venv_bin)
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=5)
        return "yt-dlp"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _parse_vtt(text: str) -> str:
    """Convert a YouTube auto-caption VTT file to readable plain text."""
    lines: list[str] = []
    prev = ""
    seen: set[str] = set()

    for line in text.splitlines():
        # Skip header, timestamps, blank lines, and word-timed cues
        if (
            not line.strip()
            or line.startswith("WEBVTT")
            or "-->" in line
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or "<c>" in line
        ):
            continue

        # Strip inline VTT timing tags  e.g. <00:00:01.000>
        clean = re.sub(r"<[^>]+>", "", line).strip()
        clean = unescape(clean)  # &amp; -> &  etc.
        if not clean:
            continue

        # Auto-captions repeat the running segment in each cue block;
        # skip exact repeats but reset the dedup window at each repeat
        # so we catch legitimately repeated phrases.
        if clean == prev:
            continue
        if clean in seen:
            seen = {clean}
        else:
            seen.add(clean)
            lines.append(clean)
        prev = clean

    raw = " ".join(lines)
    # Add paragraph breaks at sentence endings for readability
    raw = re.sub(r"([.!?])\s+([A-Z])", r"\1\n\n\2", raw)
    return raw.strip()


# ── NeetCode editorial scraping (Playwright) ──────────────────────────────

_LANG_TABS = {"Python", "Java", "C++", "JavaScript", "C#", "Go", "Kotlin", "Swift", "Rust"}
_SKIP_LINES = {"Expand", "View on Youtube", "Video Explanation"}


def _clean_editorial(raw: str) -> str:
    """Clean raw .solutions-tab inner_text into readable plain text with fenced code blocks."""
    lines = raw.split("\n")

    # Skip nav-link noise at top; find real "Prerequisites" header
    start = 0
    prereq_hits = [i for i, ln in enumerate(lines) if ln.strip() == "Prerequisites"]
    if len(prereq_hits) >= 2:
        start = prereq_hits[1]
    elif prereq_hits:
        start = prereq_hits[0]
    lines = lines[start:]

    result: list[str] = []
    skip_anim = False
    in_code = False
    # After seeing "Python" tab, wait for the actual code to begin
    # (other lang tabs like Java/C++ follow Python in the tab row and must be skipped)
    pending_code = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect animation block: next line matches "Step N / M"
        if (not skip_anim and i + 1 < len(lines)
                and re.match(r"Step \d+ / \d+$", lines[i + 1].strip())):
            if in_code:
                result.append("```")
                in_code = False
            pending_code = False
            skip_anim = True
            i += 1
            continue

        if skip_anim:
            if stripped == "Python":
                skip_anim = False
                pending_code = True
            i += 1
            continue

        # Language tabs: "Python" arms pending_code; all tabs are skipped
        if stripped in _LANG_TABS:
            if stripped == "Python":
                if in_code:
                    result.append("```")
                    in_code = False
                pending_code = True
            i += 1
            continue

        if stripped in _SKIP_LINES:
            pending_code = False
            i += 1
            continue

        # Skip pure-unicode math symbol lines (single chars like math-O, math-n, etc.)
        if stripped and all(ord(c) > 127 or c in "()+-/ " for c in stripped):
            i += 1
            continue

        # Merge "Time/Space complexity: " with the clean O(...) that follows
        if re.search(r"complexity:\s*$", stripped):
            if in_code:
                result.append("```")
                in_code = False
            pending_code = False
            j, val = i + 1, ""
            while j < len(lines) and j < i + 15:
                cand = lines[j].strip()
                if re.match(r"O\(", cand):
                    val = cand
                    break
                j += 1
            if val:
                result.append(f"{stripped} {val}")
                i = j + 1
                continue

        # Skip "Where ..." footnote lines (mixed unicode + plain text)
        if re.match(r"Where\s*$", stripped):
            i += 1
            continue
        if stripped and ord(stripped[0]) > 127 and "is the" in stripped:
            i += 1
            continue

        # First non-tab, non-skip content after "Python" tab: open the fence
        if pending_code:
            result.append("```python")
            in_code = True
            pending_code = False

        result.append(line)
        i += 1

    if in_code:
        result.append("```")

    text = "\n".join(result)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _scrape_editorial_page(page: Any, nc_slug: str, first: bool = False) -> str | None:
    """Navigate an existing Playwright page to an editorial and extract text."""
    url = f"https://neetcode.io/problems/{nc_slug}/solution"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(".solutions-tab", timeout=20000)
        # Wait until the editorial body has real content (not just the skeleton)
        page.wait_for_function(
            "() => { const el = document.querySelector('.solutions-tab'); "
            "return el && el.innerText.length > 200; }",
            timeout=15000,
        )
        # Small extra buffer on first load for Angular hydration
        if first:
            time.sleep(0.5)
        sol_tab = page.query_selector(".solutions-tab")
        raw = sol_tab.inner_text() if sol_tab else ""
        return _clean_editorial(raw) if raw else None
    except Exception:
        return None


def fetch_editorial(nc_slug: str) -> str | None:
    """
    Scrape a single NeetCode editorial using a fresh Playwright browser.
    For bulk fetching, prepare.py calls fetch_editorials() to reuse one browser.
    Returns None if playwright is not installed or the page fails to load.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            pg = browser.new_page()
            result = _scrape_editorial_page(pg, nc_slug, first=True)
            browser.close()
        return result
    except Exception:
        return None


def fetch_all(slugs: list[str], delay: float = 0.6) -> dict[str, dict[str, Any]]:
    """Fetch all problems, returning slug -> problem dict."""
    results: dict[str, dict[str, Any]] = {}
    total = len(slugs)
    for i, slug in enumerate(slugs, 1):
        print(f"  [{i}/{total}] {slug}", flush=True)
        data = fetch_problem(slug)
        if data:
            results[slug] = data
        else:
            print(f"    WARNING: could not fetch {slug}")
        if i < total:
            time.sleep(delay)
    return results
