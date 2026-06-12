# NeetCode Offline TUI

Study NeetCode 150 on a plane — no internet required after setup.

## Quick Start

```bash
# 1. Create and activate virtual environment
uv venv
source .venv/bin/activate

# 2. Install dependencies
uv pip install -e .
uv pip install yt-dlp   # optional, only needed for video downloads

# 3. Fetch problem data while online (takes ~2 min)
python prepare.py

# 4. Launch the TUI
python run.py
```

## Editor Setup

The TUI opens your system `$EDITOR` for coding. Set it in your shell rc:

```bash
# ~/.bashrc or ~/.zshrc
export EDITOR=nvim    # or vim, nano, etc.
```

Vim-style navigation is provided via the external editor — there is no
in-TUI editor. The TUI suspends while you code, then resumes when you quit
the editor.

## Keybindings

### List Screen

| Key | Action |
|-----|--------|
| `↑` / `↓` or `j` / `k` | Navigate |
| `Enter` | Open problem |
| `/` | Search by title or slug |
| `t` | Filter by topic |
| `Esc` | Clear filters |
| `q` | Quit |

### Problem Screen

| Key | Action |
|-----|--------|
| `e` | Edit your solution (opens `$EDITOR`) |
| `r` | Run tests (hand-curated pass/fail where available) |
| `s` | Show reference solution (syntax-highlighted) |
| `v` | Play video / download on demand |
| `h` | Show hints |
| `m` | Toggle solved mark |
| `q` | Back to list |

## Test Workflow

1. Press `e` on a problem to open your editor with a starter template.
2. Write your `Solution` class.
3. Quit the editor.
4. Press `r` to run tests — hand-curated pass/fail results appear on the
   right pane for the first ~50 problems. For others, LeetCode example
   inputs are shown without expected output.

Example output:
```
✓ PASS  [1] inputs=[[2, 7, 11, 15], 9]
✓ PASS  [2] inputs=[[3, 2, 4], 6]
✓ PASS  [3] inputs=[[3, 3], 6]
Passed 3/3
```

## Video Downloads

Videos are **never downloaded automatically**. Two ways to get them:

**Bulk (before your flight):**
```bash
python prepare.py --videos   # downloads all 150 at 480p (~10–15 GB)
```

**On-demand (from the TUI):**
Press `v` on any problem. If the video is missing you'll be asked to confirm
the download (~30 MB). This runs `yt-dlp` in a background thread so the UI
stays responsive.

Videos are stored in `data/videos/<slug>.mp4` and played with `mpv` (falls
back to `vlc`, `xdg-open`, `open`).

## Project Layout

```
neetcode-offline/
├── pyproject.toml
├── README.md
├── prepare.py        # online prep
├── run.py            # TUI entrypoint
├── src/
│   ├── problem_list.py   # NeetCode 150 slugs
│   ├── fetch.py          # LeetCode API + GitHub fetchers
│   ├── data.py           # disk I/O helpers
│   ├── runner.py         # solution executor
│   ├── tests.py          # hand-curated test cases
│   └── tui.py            # Textual app
└── data/
    ├── problems.json
    ├── solutions/    # reference solutions (.py)
    ├── videos/       # downloaded videos (.mp4)
    ├── attempts/     # your code (.py)
    └── progress.json
```

## Troubleshooting

**LeetCode 403:** The fallback API (`alfa-leetcode-api.onrender.com`) kicks
in automatically. You may see slower fetches.

**`mpv` not found:**
```bash
sudo apt install mpv      # Debian/Ubuntu
sudo pacman -S mpv        # Arch
brew install mpv          # macOS
```

**Textual rendering glitches over SSH:**
```bash
export TERM=xterm-256color
```

**Import errors:** Make sure you activated the venv with
`source .venv/bin/activate` before running.
