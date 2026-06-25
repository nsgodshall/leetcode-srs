"""CRUD helpers over the data/ directory."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BASE = Path(__file__).parent.parent / "data"
_PROBLEMS_FILE = _BASE / "problems.json"
_SRS_FILE = _BASE / "srs.json"
_SOLUTIONS_DIR = _BASE / "solutions"
_VIDEOS_DIR = _BASE / "videos"
_ATTEMPTS_DIR = _BASE / "attempts"
_EXPLANATIONS_DIR = _BASE / "explanations"
_EDITORIALS_DIR = _BASE / "editorials"
_SRS_BACKUP_DIR = _BASE / "srs_backups"
_SRS_BACKUP_KEEP = 30  # number of timestamped srs.json snapshots to retain


def _ensure_dirs() -> None:
    for d in (_SOLUTIONS_DIR, _VIDEOS_DIR, _ATTEMPTS_DIR, _EXPLANATIONS_DIR,
              _EDITORIALS_DIR, _SRS_BACKUP_DIR):
        d.mkdir(parents=True, exist_ok=True)


_ensure_dirs()


# ── Problems ──────────────────────────────────────────────────────────────

_problems_cache: dict[str, Any] | None = None


def load_problems() -> dict[str, Any]:
    """Return the problems dict keyed by slug.

    problems.json is static at runtime (only prepare.py writes it), so the parsed
    result is cached in-process to avoid re-parsing the ~240 KB file on every
    list refresh and problem-screen render.
    """
    global _problems_cache
    if _problems_cache is None:
        if _PROBLEMS_FILE.exists():
            _problems_cache = json.loads(_PROBLEMS_FILE.read_text(encoding="utf-8"))
        else:
            _problems_cache = {}
    return _problems_cache


def save_problems(problems: dict[str, Any]) -> None:
    global _problems_cache
    _PROBLEMS_FILE.write_text(
        json.dumps(problems, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _problems_cache = problems


# ── Reference solutions ───────────────────────────────────────────────────

def reference_solution(slug: str) -> str | None:
    path = _SOLUTIONS_DIR / f"{slug}.py"
    return path.read_text(encoding="utf-8") if path.exists() else None


def save_solution(slug: str, code: str) -> None:
    (_SOLUTIONS_DIR / f"{slug}.py").write_text(code, encoding="utf-8")


# ── Attempts ──────────────────────────────────────────────────────────────

def attempt_path(slug: str) -> Path:
    return _ATTEMPTS_DIR / f"{slug}.py"


def load_attempt(slug: str) -> str | None:
    p = attempt_path(slug)
    return p.read_text(encoding="utf-8") if p.exists() else None


def save_attempt(slug: str, code: str) -> None:
    attempt_path(slug).write_text(code, encoding="utf-8")


def starter_code(slug: str, problems: dict[str, Any]) -> str:
    """Return a starter template for the given problem."""
    prob = problems.get(slug, {})
    title = prob.get("title", slug)
    difficulty = prob.get("difficulty", "")
    snippet = prob.get("python_snippet", "")
    content = prob.get("content_text", "").strip()

    prompt_block = f"\n\n{content}" if content else ""
    header = f'"""\n{title}  [{difficulty}]\nhttps://leetcode.com/problems/{slug}/{prompt_block}\n"""\n\n'

    typing_import = "from typing import List, Optional, Dict, Tuple, Set\n\n"

    if snippet:
        body = snippet + "\n        # Your code here\n        pass\n"
    else:
        body = "class Solution:\n    def solve(self):\n        # Your code here\n        pass\n"

    return header + typing_import + body


# ── Explanations (YouTube transcript) ────────────────────────────────────

def explanation_path(slug: str) -> Path:
    return _EXPLANATIONS_DIR / f"{slug}.txt"


def load_explanation(slug: str) -> str | None:
    p = explanation_path(slug)
    return p.read_text(encoding="utf-8") if p.exists() else None


def save_explanation(slug: str, text: str) -> None:
    explanation_path(slug).write_text(text, encoding="utf-8")


# ── Editorials (NeetCode structured editorial) ────────────────────────────

def editorial_path(slug: str) -> Path:
    return _EDITORIALS_DIR / f"{slug}.txt"


def load_editorial(slug: str) -> str | None:
    p = editorial_path(slug)
    return p.read_text(encoding="utf-8") if p.exists() else None


def save_editorial(slug: str, text: str) -> None:
    editorial_path(slug).write_text(text, encoding="utf-8")


# ── Videos ────────────────────────────────────────────────────────────────

def video_path(slug: str) -> Path:
    return _VIDEOS_DIR / f"{slug}.mp4"


# ── Spaced repetition (FSRS) ──────────────────────────────────────────────

def load_srs() -> dict[str, dict]:
    if not _SRS_FILE.exists():
        return {}
    return json.loads(_SRS_FILE.read_text(encoding="utf-8"))


def _save_srs(srs: dict[str, dict]) -> None:
    payload = json.dumps(srs, indent=2)
    # Write to a temp file then rename — prevents corruption on crash mid-write
    tmp = _SRS_FILE.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(_SRS_FILE)
    # Keep a rolling single backup of the last good state (legacy)
    _SRS_FILE.with_suffix(".json.bak").write_text(payload, encoding="utf-8")
    # And keep a rotating set of timestamped snapshots so an accidental delete
    # is recoverable (the single .bak above gets clobbered on the next save).
    _write_srs_backup(payload)


def _write_srs_backup(payload: str) -> None:
    """Write a timestamped srs snapshot and prune to the most recent N."""
    _SRS_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    (_SRS_BACKUP_DIR / f"srs-{ts}.json").write_text(payload, encoding="utf-8")
    snapshots = sorted(_SRS_BACKUP_DIR.glob("srs-*.json"))
    for old in snapshots[:-_SRS_BACKUP_KEEP]:
        old.unlink(missing_ok=True)


def _card_to_dict(card: Any) -> dict:
    return {
        "card_id": card.card_id,
        "state": card.state.value,
        "step": card.step,
        "stability": card.stability,
        "difficulty": card.difficulty,
        "due": card.due.isoformat(),
        "last_review": card.last_review.isoformat() if card.last_review else None,
    }


def _dict_to_card(d: dict) -> Any:
    from fsrs import Card, State
    card = Card()
    card.card_id = d["card_id"]
    card.state = State(d["state"])
    card.step = d["step"]
    card.stability = d["stability"]
    card.difficulty = d["difficulty"]
    card.due = datetime.fromisoformat(d["due"])
    card.last_review = datetime.fromisoformat(d["last_review"]) if d["last_review"] else None
    return card


def get_card(slug: str) -> Any:
    """Return the FSRS Card for *slug*, or a fresh Card if never reviewed."""
    from fsrs import Card
    srs = load_srs()
    if slug in srs:
        return _dict_to_card(srs[slug])
    return Card()


def record_review(slug: str, rating_int: int) -> Any:
    """Schedule *slug* with the given FSRS rating (1=Again … 4=Easy). Returns updated Card."""
    from fsrs import Scheduler, Rating
    card = get_card(slug)
    updated, _log = Scheduler(desired_retention=get_retention()).review_card(card, Rating(rating_int))
    srs = load_srs()
    srs[slug] = _card_to_dict(updated)
    _save_srs(srs)
    return updated


def all_srs_cards() -> list[tuple[str, dict]]:
    """Return (slug, card_dict) for all reviewed problems, sorted by due date ascending."""
    rows = [
        (slug, d) for slug, d in load_srs().items()
        if not slug.startswith("_") and d.get("last_review") is not None
    ]
    rows.sort(key=lambda x: datetime.fromisoformat(x[1]["due"]))
    return rows


def reset_card(slug: str) -> None:
    """Remove slug's SRS state — card returns to fresh/unreviewed."""
    srs = load_srs()
    srs.pop(slug, None)
    _save_srs(srs)


def get_retention() -> float:
    """Return desired_retention (default 0.9) stored in srs.json config."""
    return float(load_srs().get("_config", {}).get("desired_retention", 0.9))


def set_retention(value: float) -> None:
    """Persist desired_retention (clamped 0.50–0.99) to srs.json."""
    srs = load_srs()
    srs.setdefault("_config", {})["desired_retention"] = round(max(0.5, min(0.99, value)), 2)
    _save_srs(srs)
