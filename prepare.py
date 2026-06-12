"""
One-time online preparation script.

Usage:
    python setup.py                  # fetch problem statements + reference solutions
    python setup.py --editorials     # also scrape full NeetCode editorials (needs playwright)
    python setup.py --explanations   # also download NeetCode video transcripts (needs yt-dlp)
    python setup.py --videos         # also download all videos (large!)
    python setup.py --all            # everything above
"""

import sys
import subprocess
import time
from pathlib import Path

# Ensure src/ is importable when run directly
sys.path.insert(0, str(Path(__file__).parent))

from src.problem_list import TOPICS, SLUG_IDS, LC_TO_NC_SLUG, all_slugs
from src import fetch as F
from src import data as D


def fetch_problems() -> None:
    slugs = all_slugs()
    print(f"Fetching {len(slugs)} problems...")
    existing = D.load_problems()
    total = len(slugs)

    for i, slug in enumerate(slugs, 1):
        if slug in existing:
            print(f"  [{i}/{total}] {slug} (cached)")
            continue
        print(f"  [{i}/{total}] {slug}", end="", flush=True)
        data = F.fetch_problem(slug)
        if data:
            existing[slug] = data
            print(f"  ✓ {data.get('title', slug)}")
        else:
            print(f"  ✗ failed")
        if i < total:
            time.sleep(0.6)

    D.save_problems(existing)
    print(f"\nSaved {len(existing)} problems to data/problems.json")


def fetch_solutions() -> None:
    problems = D.load_problems()
    slugs = all_slugs()
    total = len(slugs)
    saved = 0

    print(f"\nFetching reference solutions...")
    for i, slug in enumerate(slugs, 1):
        sol_path = D.attempt_path(slug).parent.parent / "solutions" / f"{slug}.py"
        # Use data module path
        from src.data import _SOLUTIONS_DIR
        sol_file = _SOLUTIONS_DIR / f"{slug}.py"
        if sol_file.exists():
            print(f"  [{i}/{total}] {slug} (cached)")
            continue

        print(f"  [{i}/{total}] {slug}", end="", flush=True)
        sol = F.fetch_solution(slug)
        if sol:
            D.save_solution(slug, sol)
            saved += 1
            print(f"  ✓")
            prob = problems.get(slug, {})
            prob["has_solution"] = True
            problems[slug] = prob
        else:
            print(f"  – (not found)")
        if i < total:
            time.sleep(0.3)

    D.save_problems(problems)
    print(f"Saved {saved} solutions")


def fetch_editorials() -> None:
    """Scrape structured NeetCode editorials (prerequisites, approaches, pitfalls) via Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ERROR: playwright not installed.")
        print("  Run: uv pip install playwright && .venv/bin/playwright install chromium")
        return

    slugs = all_slugs()
    to_fetch = [s for s in slugs if not D.editorial_path(s).exists()]
    cached = len(slugs) - len(to_fetch)
    saved = 0

    print(f"\nScraping NeetCode editorials ({cached} cached, {len(to_fetch)} remaining)...")
    print("(reusing one browser — ~6-8s per problem, ~16 min for all 150)\n")

    if not to_fetch:
        print("All editorials already cached.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        first = True

        for i, slug in enumerate(to_fetch, 1):
            nc_slug = LC_TO_NC_SLUG.get(slug, slug)
            print(f"  [{i}/{len(to_fetch)}] {slug}...", end="", flush=True)
            text = F._scrape_editorial_page(page, nc_slug, first=first)
            first = False
            if text:
                D.save_editorial(slug, text)
                saved += 1
                print(f" ok ({len(text)} chars)")
            else:
                print(" – (failed)")

        browser.close()

    print(f"\nSaved {saved} editorials to data/editorials/")


def fetch_explanations() -> None:
    """Download NeetCode YouTube transcripts for all problems."""
    ytdlp = F._find_ytdlp()
    if not ytdlp:
        print("  ERROR: yt-dlp not found. Install: uv pip install yt-dlp")
        return

    problems = D.load_problems()
    slugs = all_slugs()
    total = len(slugs)
    saved = 0

    print(f"\nFetching NeetCode transcripts for {total} problems...")
    print("(each takes ~5 seconds — total ~12 min)\n")

    for i, slug in enumerate(slugs, 1):
        if D.explanation_path(slug).exists():
            print(f"  [{i}/{total}] {slug} (cached)")
            continue

        title = problems.get(slug, {}).get("title", slug)
        print(f"  [{i}/{total}] {title}...", end="", flush=True)
        text = F.fetch_transcript(slug, title)
        if text:
            D.save_explanation(slug, text)
            saved += 1
            print(f" ✓ ({len(text)} chars)")
        else:
            print(" – (not found)")

    print(f"\nSaved {saved} transcripts to data/explanations/")


def download_all_videos() -> None:
    problems = D.load_problems()
    slugs = all_slugs()
    print(f"\nDownloading videos for {len(slugs)} problems (this will take a long time!)...")

    for i, slug in enumerate(slugs, 1):
        vpath = D.video_path(slug)
        if vpath.exists():
            print(f"  [{i}/{len(slugs)}] {slug} (exists)")
            continue

        title = problems.get(slug, {}).get("title", slug)
        out_tmpl = str(vpath).replace(".mp4", ".%(ext)s")
        query = f"ytsearch1:NeetCode {title}"
        cmd = [
            "yt-dlp", query,
            "-f", "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "--merge-output-format", "mp4",
            "-o", out_tmpl,
            "--no-playlist",
            "-q",
        ]
        print(f"  [{i}/{len(slugs)}] {title}...", end="", flush=True)
        try:
            result = subprocess.run(cmd, timeout=120)
            print(" ✓" if result.returncode == 0 else " ✗")
        except FileNotFoundError:
            print("\nERROR: yt-dlp not found. Install it: pip install yt-dlp")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print(" timed out")


if __name__ == "__main__":
    args = set(sys.argv[1:])
    do_videos = "--videos" in args or "--all" in args
    do_explanations = "--explanations" in args or "--all" in args
    do_editorials = "--editorials" in args or "--all" in args

    if do_videos:
        print("WARNING: Downloading all videos will use several GB of disk space.")
        resp = input("Continue? [y/N] ").strip().lower()
        if resp != "y":
            print("Aborted.")
            sys.exit(0)

    fetch_problems()
    fetch_solutions()

    if do_editorials:
        fetch_editorials()

    if do_explanations:
        fetch_explanations()

    if do_videos:
        download_all_videos()

    print("\nSetup complete!")
