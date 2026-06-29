"""
One-time online preparation script.

Usage:
    python prepare.py                  # fetch problem statements + reference solutions
    python prepare.py --editorials     # also scrape full NeetCode editorials (needs playwright)
    python prepare.py --explanations   # also download NeetCode video transcripts (needs yt-dlp)
    python prepare.py --videos         # also download all videos (large!)
    python prepare.py --all            # everything above
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.problem_list import LC_TO_NC_SLUG, python_slugs
from src import fetch as F
from src import data as D

_HTTP_CONCURRENCY = 8
_PROC_CONCURRENCY = 5


async def fetch_problems() -> None:
    slugs = python_slugs()
    existing = D.load_problems()
    to_fetch = [s for s in slugs if s not in existing]
    total = len(to_fetch)

    print(f"Fetching {total} problems ({len(slugs) - total} cached)...")
    if not to_fetch:
        return

    sem = asyncio.Semaphore(_HTTP_CONCURRENCY)
    done = 0

    async def fetch_one(slug: str) -> None:
        nonlocal done
        async with sem:
            data = await asyncio.to_thread(F.fetch_problem, slug)
        done += 1
        if data:
            existing[slug] = data
            print(f"  [{done}/{total}] ✓ {data.get('title', slug)}")
        else:
            print(f"  [{done}/{total}] ✗ {slug}")

    await asyncio.gather(*[fetch_one(s) for s in to_fetch])
    D.save_problems(existing)
    print(f"\nSaved {len(existing)} problems to data/problems.json")


async def fetch_solutions() -> None:
    from src.data import _SOLUTIONS_DIR

    problems = D.load_problems()
    all_ = python_slugs()
    to_fetch = [s for s in all_ if not (_SOLUTIONS_DIR / f"{s}.py").exists()]
    total = len(to_fetch)
    saved = 0
    done = 0

    print(f"\nFetching {total} solutions ({len(all_) - total} cached)...")
    if not to_fetch:
        return

    sem = asyncio.Semaphore(_HTTP_CONCURRENCY)

    async def fetch_one(slug: str) -> None:
        nonlocal done, saved
        async with sem:
            sol = await asyncio.to_thread(F.fetch_solution, slug)
        done += 1
        if sol:
            D.save_solution(slug, sol)
            saved += 1
            prob = problems.get(slug, {})
            prob["has_solution"] = True
            problems[slug] = prob
            print(f"  [{done}/{total}] ✓ {slug}")
        else:
            print(f"  [{done}/{total}] – {slug} (not found)")

    await asyncio.gather(*[fetch_one(s) for s in to_fetch])
    D.save_problems(problems)
    print(f"Saved {saved} solutions")


def fetch_editorials() -> None:
    """Scrape NeetCode editorials via Playwright (sequential — single browser page)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ERROR: playwright not installed.")
        print("  Run: uv pip install playwright && .venv/bin/playwright install chromium")
        return

    slugs = python_slugs()
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


async def fetch_explanations() -> None:
    """Download NeetCode YouTube transcripts concurrently."""
    ytdlp = F._find_ytdlp()
    if not ytdlp:
        print("  ERROR: yt-dlp not found. Install: uv pip install yt-dlp")
        return

    problems = D.load_problems()
    all_ = python_slugs()
    to_fetch = [s for s in all_ if not D.explanation_path(s).exists()]
    total = len(to_fetch)
    saved = 0
    done = 0

    print(f"\nFetching {total} transcripts ({len(all_) - total} cached)...")
    if not to_fetch:
        return

    sem = asyncio.Semaphore(_PROC_CONCURRENCY)

    async def fetch_one(slug: str) -> None:
        nonlocal done, saved
        title = problems.get(slug, {}).get("title", slug)
        async with sem:
            text = await asyncio.to_thread(F.fetch_transcript, slug, title)
        done += 1
        if text:
            D.save_explanation(slug, text)
            saved += 1
            print(f"  [{done}/{total}] ✓ {title} ({len(text)} chars)")
        else:
            print(f"  [{done}/{total}] – {title} (not found)")

    await asyncio.gather(*[fetch_one(s) for s in to_fetch])
    print(f"\nSaved {saved} transcripts to data/explanations/")


async def download_all_videos() -> None:
    problems = D.load_problems()
    all_ = python_slugs()
    to_fetch = [s for s in all_ if not D.video_path(s).exists()]
    total = len(to_fetch)
    done = 0

    print(f"\nDownloading {total} videos (this will take a long time!)...")
    if not to_fetch:
        return

    sem = asyncio.Semaphore(3)

    async def download_one(slug: str) -> None:
        nonlocal done
        title = problems.get(slug, {}).get("title", slug)
        vpath = D.video_path(slug)
        out_tmpl = str(vpath).replace(".mp4", ".%(ext)s")
        cmd = [
            "yt-dlp", f"ytsearch1:NeetCode {title}",
            "-f", "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "--merge-output-format", "mp4",
            "-o", out_tmpl,
            "--no-playlist", "-q",
        ]
        async with sem:
            try:
                proc = await asyncio.create_subprocess_exec(*cmd)
                await asyncio.wait_for(proc.wait(), timeout=120)
                done += 1
                print(f"  [{done}/{total}] {'✓' if proc.returncode == 0 else '✗'} {title}")
            except asyncio.TimeoutError:
                proc.kill()
                done += 1
                print(f"  [{done}/{total}] timed out: {title}")
            except FileNotFoundError:
                print("\nERROR: yt-dlp not found. Install it: pip install yt-dlp")
                sys.exit(1)

    await asyncio.gather(*[download_one(s) for s in to_fetch])


async def main() -> None:
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

    await fetch_problems()
    await fetch_solutions()

    if do_editorials:
        # Run in a thread so Playwright's sync API isn't inside the event loop
        await asyncio.to_thread(fetch_editorials)

    if do_explanations:
        await fetch_explanations()

    if do_videos:
        await download_all_videos()

    print("\nSetup complete!")


if __name__ == "__main__":
    asyncio.run(main())
