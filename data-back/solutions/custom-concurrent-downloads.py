"""Concurrently download an arbitrary list of URLs (one per line in a file).

I/O-bound work, so a bounded ThreadPoolExecutor + requests is the right tool:
threads release the GIL while blocked on the network, the pool caps open
sockets, and per-URL try/except keeps one bad link from killing the batch.

An asyncio + aiohttp variant is sketched at the bottom for very high fan-out.
"""

import concurrent.futures as cf
import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


def read_urls(path):
    """Yield cleaned URLs: strip whitespace, skip blanks, add a scheme."""
    for line in Path(path).read_text().splitlines():
        url = line.strip()
        if not url:
            continue
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        yield url


def output_name(url, out_dir):
    """Collision-proof local filename: host + short URL hash + basename."""
    parsed = urlparse(url)
    stem = Path(parsed.path).name or "index"
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return Path(out_dir) / f"{parsed.netloc}_{digest}_{stem}"


def download(url, out_dir, timeout=30):
    dest = output_name(url, out_dir)
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                f.write(chunk)
    return dest


def download_all(url_file, out_dir="downloads", max_workers=8):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    urls = list(read_urls(url_file))
    results = {}
    with cf.ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_url = {pool.submit(download, u, out_dir): u for u in urls}
        for fut in cf.as_completed(future_to_url):
            url = future_to_url[fut]
            try:
                results[url] = ("ok", str(fut.result()))
            except Exception as e:  # isolate failures; keep the batch alive
                results[url] = ("error", repr(e))
    return results


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "urls.txt"
    for url, (status, detail) in download_all(path).items():
        print(f"[{status:>5}] {url} -> {detail}")


# ── asyncio + aiohttp sketch (for thousands of concurrent requests) ─────────
#
# import asyncio, aiohttp
#
# async def fetch(session, url, out_dir, sem):
#     async with sem:                       # bound concurrency
#         async with session.get(url) as r:
#             r.raise_for_status()
#             dest = output_name(url, out_dir)
#             with open(dest, "wb") as f:
#                 async for chunk in r.content.iter_chunked(64 * 1024):
#                     f.write(chunk)
#             return dest
#
# async def download_all_async(urls, out_dir="downloads", limit=50):
#     sem = asyncio.Semaphore(limit)
#     async with aiohttp.ClientSession() as session:
#         tasks = [fetch(session, u, out_dir, sem) for u in urls]
#         return await asyncio.gather(*tasks, return_exceptions=True)
