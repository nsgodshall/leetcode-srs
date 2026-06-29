"""Textual TUI for NeetCode Offline."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from src import data as D
from src.problem_list import DISPLAY_TOPICS, display_slugs
from src.runner import run_tests


def _slugify(s: str) -> str:
    """Make a string safe for a Textual widget ID."""
    import re

    s = s.replace("&", "and")
    s = re.sub(r"[^a-zA-Z0-9_-]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if s and s[0].isdigit():
        s = "t" + s
    return s or "x"


DIFF_COLOR = {"Easy": "green", "Medium": "yellow", "Hard": "red"}


# ── Modal screens ─────────────────────────────────────────────────────────


class SearchModal(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "dismiss(None)", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-box"):
            yield Label("Search (title or slug):")
            yield Input(placeholder="two sum…", id="search-input")

    @on(Input.Submitted)
    def submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())


class TopicModal(ModalScreen[str | None]):
    BINDINGS = [
        Binding("escape", "dismiss(None)", "Cancel"),
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
    ]

    def compose(self) -> ComposeResult:
        items = [ListItem(Label("(all topics)"), id="topic-all")]
        for topic in DISPLAY_TOPICS:
            items.append(ListItem(Label(topic), id=f"topic-{_slugify(topic)}"))
        with Vertical(id="topic-box"):
            yield Label("Filter by topic:")
            yield ListView(*items, id="topic-list")

    def action_cursor_down(self) -> None:
        self.query_one("#topic-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#topic-list", ListView).action_cursor_up()

    @on(ListView.Selected)
    def selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "topic-all":
            self.dismiss(None)
        else:
            label = event.item.query_one(Label)
            self.dismiss(str(label.renderable))


class ConfirmModal(ModalScreen[bool]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    BINDINGS = [
        Binding("y", "confirm(True)", "Yes"),
        Binding("n", "confirm(False)", "No"),
        Binding("escape", "confirm(False)", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(self._message)
            yield Label("[y] Yes   [n] No", id="confirm-hint")

    def action_confirm(self, value: bool) -> None:
        self.dismiss(value)


class RatingModal(ModalScreen[int]):
    """Rate a problem attempt: Again / Hard / Good / Easy → returns 1-4, or 0 if dismissed."""

    BINDINGS = [
        Binding("1", "rate(1)", show=False),
        Binding("2", "rate(2)", show=False),
        Binding("3", "rate(3)", show=False),
        Binding("4", "rate(4)", show=False),
        Binding("a", "rate(1)", show=False),
        Binding("h", "rate(2)", show=False),
        Binding("g", "rate(3)", show=False),
        Binding("e", "rate(4)", show=False),
        Binding("escape", "rate(0)", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="rating-box"):
            yield Label("Rate your answer:", id="rating-title")
            yield Label(
                "  [bold red][1] Again[/bold red]"
                "   [yellow][2] Hard[/yellow]"
                "   [green][3] Good[/green]"
                "   [bold green][4] Easy[/bold green]",
                id="rating-hint",
            )
            yield Label(
                "  [dim]Press[/dim] [bold]Esc[/bold] [dim]to skip — don't rate[/dim]",
                id="rating-skip",
            )

    def action_rate(self, value: int) -> None:
        self.dismiss(value)


# ── List screen ───────────────────────────────────────────────────────────


class ProblemRow(Static):
    def __init__(self, prob: dict[str, Any], solved: bool, due: bool = False) -> None:
        self.slug = prob["slug"]
        self.prob = prob
        self._state = (solved, due)
        super().__init__(self._markup(solved, due))

    def _markup(self, solved: bool, due: bool) -> str:
        if due:
            indicator, ind_color = "↻", "yellow"
        elif solved:
            indicator, ind_color = "✓", "green"
        else:
            indicator, ind_color = " ", "dim"
        diff = self.prob.get("difficulty", "?")
        color = DIFF_COLOR.get(diff, "white")
        pid = self.prob.get("id", 0)
        title = self.prob.get("title", self.slug)
        return (
            f"[{ind_color}][{indicator}][/{ind_color}]  "
            f"[{color}]{diff:<6}[/{color}]  "
            f"[dim]{pid:04d}[/dim]  {title}"
        )

    def set_state(self, solved: bool, due: bool) -> None:
        """Cheaply re-render this row's indicator without remounting. No-op when
        the state is unchanged so an unchanged list repaints nothing."""
        if (solved, due) == self._state:
            return
        self._state = (solved, due)
        self.update(self._markup(solved, due))


class ListScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("/", "search", "Search"),
        Binding("t", "topic_filter", "Topic"),
        Binding("x", "srs_screen", "SRS"),
        Binding("d", "download_video", "Download"),
        Binding("escape", "clear_filters", "Clear filters"),
    ]

    _filter_text: reactive[str] = reactive("")
    _filter_topic: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(id="list-header", classes="list-header")
        yield ListView(id="problem-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self._refresh_list()

    def _build_items(self, srs: dict, due_set: set) -> list[ListItem]:
        problems = D.load_problems()
        reviewed_set = {
            s for s, d in srs.items() if not s.startswith("_") and d.get("last_review")
        }
        ft = self._filter_text.lower()
        ft_topic = self._filter_topic
        items: list[ListItem] = []
        for topic, slugs in DISPLAY_TOPICS.items():
            if ft_topic and topic != ft_topic:
                continue
            topic_items: list[ListItem] = []
            for slug in slugs:
                prob = problems.get(
                    slug, {"slug": slug, "id": 0, "title": slug, "difficulty": ""}
                )
                title = prob.get("title", slug)
                if ft and ft not in title.lower() and ft not in slug:
                    continue
                reviewed = slug in reviewed_set
                due = slug in due_set
                topic_items.append(
                    ListItem(ProblemRow(prob, reviewed, due), id=f"p-{slug}")
                )
            if not topic_items:
                continue
            items.append(
                ListItem(
                    Label(f"[bold cyan]── {topic} ──[/bold cyan]"),
                    id=f"h-{_slugify(topic)}",
                )
            )
            items.extend(topic_items)
        return items

    def _refresh_header(self, srs: dict, due_set: set) -> None:
        reviewed_total = sum(
            1 for s, d in srs.items() if not s.startswith("_") and d.get("last_review")
        )
        due_count = len(due_set)
        due_str = f"  [yellow]Due: {due_count}[/yellow]" if due_count else ""
        self.query_one("#list-header", Static).update(
            f"Reviewed: {reviewed_total}/{len(display_slugs())}{due_str}  |  / search  |  t topic  |  x srs  |  Esc clear"
        )

    async def _refresh_list(self) -> None:
        """Full rebuild: clear and remount every visible row. Use only when the
        visible set changes (initial load, filter change)."""
        srs = D.load_srs()
        now = datetime.now(timezone.utc)
        due_set = {
            slug
            for slug, d in srs.items()
            if not slug.startswith("_")
            and d.get("last_review")
            and datetime.fromisoformat(d["due"]) <= now
        }
        self._refresh_header(srs, due_set)
        lv = self.query_one("#problem-list", ListView)
        await lv.clear()
        new_items = self._build_items(srs, due_set)
        if new_items:
            await lv.mount(*new_items)
        self._rendered_sig = (self._filter_text, self._filter_topic)

    def _refresh_indicators(self) -> None:
        """Cheap path: update the ↻/✓ indicator on already-mounted rows in place,
        without clearing or remounting. Used when returning to an unchanged list."""
        srs = D.load_srs()
        now = datetime.now(timezone.utc)
        due_set = {
            slug
            for slug, d in srs.items()
            if not slug.startswith("_")
            and d.get("last_review")
            and datetime.fromisoformat(d["due"]) <= now
        }
        self._refresh_header(srs, due_set)
        reviewed_set = {
            s for s, d in srs.items() if not s.startswith("_") and d.get("last_review")
        }
        for row in self.query(ProblemRow):
            row.set_state(row.slug in reviewed_set, row.slug in due_set)

    @on(ListView.Selected)
    def open_problem(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("p-"):
            slug = item_id[2:]
            self.app.push_screen(ProblemScreen(slug))

    async def on_screen_resume(self) -> None:
        # Only rebuild the whole list when the visible set actually changed (a
        # filter was applied/cleared). Returning from a problem leaves the set
        # unchanged, so just refresh indicators in place — far cheaper than a
        # ~2 s remount of every row.
        sig = (self._filter_text, self._filter_topic)
        if sig != getattr(self, "_rendered_sig", None):
            await self._refresh_list()
        else:
            self._refresh_indicators()

    def action_cursor_down(self) -> None:
        self.query_one("#problem-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#problem-list", ListView).action_cursor_up()

    def action_quit(self) -> None:
        self.app.exit()

    def action_search(self) -> None:
        def _apply(q: str | None) -> None:
            self._filter_text = q or ""
            # on_screen_resume will refresh

        self.app.push_screen(SearchModal(), _apply)

    def action_topic_filter(self) -> None:
        def _apply(t: str | None) -> None:
            self._filter_topic = t
            # on_screen_resume will refresh

        self.app.push_screen(TopicModal(), _apply)

    async def action_clear_filters(self) -> None:
        self._filter_text = ""
        self._filter_topic = None
        await self._refresh_list()

    def action_srs_screen(self) -> None:
        self.app.push_screen(SRSScreen())

    def action_download_video(self) -> None:
        lv = self.query_one("#problem-list", ListView)
        highlighted = lv.highlighted_child
        if highlighted is None:
            self.app.notify("No problem selected", severity="warning")
            return
        item_id = highlighted.id or ""
        if not item_id.startswith("p-"):
            self.app.notify("Select a problem (not a topic header)", severity="warning")
            return
        slug = item_id[2:]
        if D.video_path(slug).exists():
            self.app.notify(f"Already downloaded: {slug}")
            return
        problems = D.load_problems()
        title = problems.get(slug, {}).get("title", slug)

        def _on_confirm(yes: bool) -> None:
            if yes:
                self._download_video(slug, title)

        self.app.push_screen(
            ConfirmModal(f"Download video for {title}? (~30 MB)"), _on_confirm
        )

    @work(thread=True)
    def _download_video(self, slug: str, title: str) -> None:
        out_tmpl = str(D.video_path(slug)).replace(".mp4", ".%(ext)s")
        cmd = [
            "yt-dlp",
            f"ytsearch1:NeetCode {title}",
            "-f",
            "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "--merge-output-format",
            "mp4",
            "-o",
            out_tmpl,
            "--no-playlist",
        ]
        self.app.call_from_thread(self.app.notify, f"Downloading: {title}…")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.app.call_from_thread(self.app.notify, "Download complete!")
            else:
                self.app.call_from_thread(
                    self.app.notify,
                    f"Download failed: {result.stderr[:200]}",
                    severity="error",
                )
        except FileNotFoundError:
            self.app.call_from_thread(
                self.app.notify, "yt-dlp not found. Install it first.", severity="error"
            )
        except subprocess.TimeoutExpired:
            self.app.call_from_thread(
                self.app.notify, "Download timed out.", severity="error"
            )


# ── Helpers ───────────────────────────────────────────────────────────────


def _render_editorial(label: str, text: str, sol: str | None):
    """Split editorial text on ```python fences, highlight code, append solution."""
    from rich.console import Group
    from rich.syntax import Syntax
    from rich.text import Text

    parts = [Text(f"{label}\n\n", style="bold cyan")]
    current: list[str] = []
    in_code = False
    code: list[str] = []

    for line in text.split("\n"):
        if line.strip() == "```python":
            if current:
                parts.append(Text("\n".join(current) + "\n"))
                current = []
            in_code = True
            code = []
        elif line.strip() == "```" and in_code:
            if code:
                parts.append(
                    Syntax(
                        "\n".join(code), "python", theme="monokai", line_numbers=True
                    )
                )
                parts.append(Text("\n"))
            in_code = False
            code = []
        elif in_code:
            code.append(line)
        else:
            current.append(line)

    if current:
        parts.append(Text("\n".join(current)))
    if in_code and code:
        parts.append(
            Syntax("\n".join(code), "python", theme="monokai", line_numbers=True)
        )

    if sol:
        parts.append(Text("\n" + "─" * 40 + "\n", style="dim"))
        parts.append(Syntax(sol, "python", theme="monokai", line_numbers=True))

    return Group(*parts)


def _format_run_output(result: str):
    """Render plain-text runner output as a styled Rich Text (no markup parsing).

    The runner prints literal text such as "inputs=[1,2]  expected=-1  got=3";
    parsing that as console markup raises MarkupError, so we build a Text line by
    line and colorize the result summary / pass-fail bar ourselves.
    """
    from rich.text import Text

    out = Text()
    lines = result.split("\n")
    for idx, line in enumerate(lines):
        suffix = "" if idx == len(lines) - 1 else "\n"
        stripped = line.strip()
        if stripped.startswith("All ") and stripped.endswith("passed"):
            out.append(line + suffix, style="bold green")
        elif "failed," in stripped and "passed," in stripped:
            out.append(line + suffix, style="bold red")
        elif stripped.startswith("FAILED"):
            out.append(line + suffix, style="red")
        elif stripped.startswith("INFO"):
            out.append(line + suffix, style="yellow")
        elif idx == 0 and set(stripped) <= {".", "F", "E", "?"} and stripped:
            # the pass/fail bar: color each glyph
            for ch in line:
                out.append(
                    ch,
                    style={
                        ".": "green",
                        "F": "red",
                        "E": "red",
                        "?": "yellow",
                    }.get(ch, "white"),
                )
            out.append(suffix)
        else:
            out.append(line + suffix, style="dim")
    return out


# ── Problem screen ────────────────────────────────────────────────────────


class ProblemScreen(Screen):
    BINDINGS = [
        Binding("q", "go_back", "Back"),
        Binding("e", "edit", "Edit"),
        Binding("r", "run_tests", "Run"),
        Binding("a", "rate", "Rate"),
        Binding("c", "critique", "Critique"),
        Binding("s", "show_solution", "Solution"),
        Binding("v", "video", "Video"),
        Binding("?", "hints", "Hints"),
        Binding("j", "scroll_down", show=False),
        Binding("k", "scroll_up", show=False),
        Binding("ctrl+d", "scroll_half_down", show=False),
        Binding("ctrl+u", "scroll_half_up", show=False),
        Binding("h", "focus_left", show=False),
        Binding("l", "focus_right", show=False),
        Binding("H", "resize_left", show=False),
        Binding("L", "resize_right", show=False),
        Binding("G", "scroll_bottom", show=False),
    ]

    split_pct: reactive[int] = reactive(60)

    def __init__(self, slug: str) -> None:
        super().__init__()
        self._slug = slug
        self._g_pending = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="problem-body"):
            with VerticalScroll(id="problem-scroll"):
                yield Static(id="problem-text", classes="problem-text")
            with VerticalScroll(id="output-scroll"):
                yield Static(id="output-pane", classes="output-pane")
        yield Footer()

    def on_mount(self) -> None:
        self._render_problem()

    def _render_problem(self) -> None:
        from rich.markup import escape

        problems = D.load_problems()
        prob = problems.get(self._slug, {})

        # Fetched text (title, content) may contain '[' which the markup renderer
        # would parse as tags — escape it so it renders literally and can't crash.
        title = escape(prob.get("title", self._slug))
        diff = prob.get("difficulty", "")
        color = DIFF_COLOR.get(diff, "white")
        header = f"[bold]{title}[/bold]  [{color}]{diff}[/{color}]\n"

        # SRS status line
        srs_data = D.load_srs().get(self._slug)
        if srs_data and srs_data.get("last_review"):
            from fsrs import State

            due = datetime.fromisoformat(srs_data["due"])
            now = datetime.now(timezone.utc)
            state_name = State(srs_data["state"]).name
            if due <= now:
                due_label = "[yellow]due now[/yellow]"
            else:
                delta = due - now
                days = delta.days
                due_label = f"in {days}d" if days > 0 else "today"
            header += f"[dim]Next review: {due_label} · {state_name}[/dim]\n"
        header += "\n"

        content = escape(
            prob.get("content_text", "(Run python prepare.py to fetch problem data)")
        )
        hints_count = len(prob.get("hints") or [])
        footer = (
            f"\n\n[dim]hints: {hints_count}  |  "
            "e edit  r run  a rate  c critique  s solution  v video  ? hints  h/l focus  H/L resize[/dim]"
        )

        self.query_one("#problem-text", Static).update(header + content + footer)
        self.query_one("#output-pane", Static).update("[dim]Press r to run tests[/dim]")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_edit(self) -> None:
        problems = D.load_problems()
        path = D.attempt_path(self._slug)
        if not path.exists():
            code = D.starter_code(self._slug, problems)
            D.save_attempt(self._slug, code)

        editor = os.environ.get("EDITOR", "nvim")
        with self.app.suspend():
            subprocess.run([editor, str(path)])

    def action_run_tests(self) -> None:
        code = D.load_attempt(self._slug)
        if not code:
            self.query_one("#output-pane", Static).update(
                "[yellow]No attempt found. Press e to edit first.[/yellow]"
            )
            return
        self.query_one("#output-pane", Static).update("[dim]Running tests…[/dim]")
        self._do_run(code)

    @work(thread=True)
    def _do_run(self, code: str) -> None:
        import re

        result = run_tests(self._slug, code)
        # Render as a literal Text (no markup parsing): runner output is plain
        # text containing brackets like "inputs=[1,2]  expected=-1", which the
        # default markup renderer would try to parse as tags and crash on.
        display = (
            _format_run_output(result) if result.strip() else "[dim]No output[/dim]"
        )
        self.app.call_from_thread(
            self.query_one("#output-pane", Static).update,
            display,
        )
        # Auto-prompt for an SRS rating when every test passed (≥1 assertion).
        last_line = result.strip().splitlines()[-1] if result.strip() else ""
        m = re.match(r"^All (\d+) passed$", last_line)
        if m and int(m.group(1)) > 0:
            self.app.call_from_thread(self._prompt_rating)

    def action_show_solution(self) -> None:
        editorial = D.load_editorial(self._slug)
        explanation = D.load_explanation(self._slug) if not editorial else None
        sol = D.reference_solution(self._slug)
        best_text = editorial or explanation

        pane = self.query_one("#output-pane", Static)

        if not best_text and not sol:
            pane.update(
                "[yellow]Nothing cached yet.\n\n"
                "Run [bold]python prepare.py[/bold] for code,\n"
                "or [bold]python prepare.py --editorials[/bold] for full editorials.[/yellow]"
            )
            return

        if best_text:
            label = (
                "── NeetCode Editorial ──"
                if editorial
                else "── NeetCode Explanation ──"
            )
            pane.update(_render_editorial(label, best_text, sol))
        else:
            from rich.console import Group
            from rich.syntax import Syntax

            pane.update(
                Group(Syntax(sol, "python", theme="monokai", line_numbers=True))
            )

    def action_hints(self) -> None:
        problems = D.load_problems()
        prob = problems.get(self._slug, {})
        hints = prob.get("hints") or []
        if not hints:
            self.query_one("#output-pane", Static).update(
                "[dim]No hints available.[/dim]"
            )
            return
        from rich.markup import escape

        text = "\n\n".join(
            f"[bold]Hint {i + 1}:[/bold] {escape(h)}" for i, h in enumerate(hints)
        )
        self.query_one("#output-pane", Static).update(text)

    def _active_scroll(self) -> VerticalScroll:
        focused = self.focused
        if isinstance(focused, VerticalScroll):
            return focused
        return self.query_one("#problem-scroll", VerticalScroll)

    def on_key(self, event: Any) -> None:
        if event.key == "g":
            if self._g_pending:
                self._active_scroll().scroll_home(animate=False)
                self._g_pending = False
                event.stop()
            else:
                self._g_pending = True
                event.stop()
        else:
            self._g_pending = False

    def action_scroll_down(self) -> None:
        self._active_scroll().scroll_down()

    def action_scroll_up(self) -> None:
        self._active_scroll().scroll_up()

    def action_scroll_half_down(self) -> None:
        self._active_scroll().scroll_page_down()

    def action_scroll_half_up(self) -> None:
        self._active_scroll().scroll_page_up()

    def action_scroll_bottom(self) -> None:
        self._active_scroll().scroll_end(animate=False)

    def action_focus_left(self) -> None:
        self.set_focus(self.query_one("#problem-scroll", VerticalScroll))

    def action_focus_right(self) -> None:
        self.set_focus(self.query_one("#output-scroll", VerticalScroll))

    def watch_split_pct(self, value: int) -> None:
        try:
            self.query_one("#problem-scroll").styles.width = f"{value}%"
            self.query_one("#output-scroll").styles.width = f"{100 - value}%"
        except Exception:
            pass

    def action_resize_left(self) -> None:
        self.split_pct = max(20, self.split_pct - 5)

    def action_resize_right(self) -> None:
        self.split_pct = min(80, self.split_pct + 5)

    def action_rate(self) -> None:
        self._prompt_rating()

    def _prompt_rating(self) -> None:
        def _on_rating(rating: int) -> None:
            if not rating:
                return
            card = D.record_review(self._slug, rating)
            from fsrs import State

            state_name = State(card.state).name
            due = card.due
            now = datetime.now(timezone.utc)
            delta = due - now
            days = delta.days
            if days <= 0:
                due_str = "soon"
            elif days == 1:
                due_str = "tomorrow"
            else:
                due_str = f"in {days}d"
            label_map = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
            self.app.notify(
                f"{label_map[rating]} → next review {due_str} ({state_name})"
            )
            self._render_problem()

        self.app.push_screen(RatingModal(), _on_rating)

    def action_critique(self) -> None:
        import os

        has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
        has_deepseek = bool(os.environ.get("DEEPSEEK_API_KEY"))
        if not has_anthropic and not has_deepseek:
            self.query_one("#output-pane", Static).update(
                "[green]ANTHROPIC_API_KEY or DEEPSEEK_API_KEY not set. System offline.[/green]"
            )
            return
        code = D.load_attempt(self._slug)
        if not code:
            self.query_one("#output-pane", Static).update(
                "[green]NO SUBMISSION DETECTED. WRITE CODE FIRST.[/green]"
            )
            return
        pane = self.query_one("#output-pane", Static)
        pane.update("[green]EVALUATION SYSTEM ONLINE\nANALYZING SUBMISSION[/green]")
        # Cycle the ellipsis . → .. → ... while the worker waits on the API.
        self._analyze_phase = 0

        def _tick() -> None:
            self._analyze_phase = (self._analyze_phase % 3) + 1
            dots = "." * self._analyze_phase
            pane.update(
                f"[green]EVALUATION SYSTEM ONLINE\nANALYZING SUBMISSION{dots}[/green]"
            )

        self._analyze_timer = self.set_interval(0.4, _tick)
        problems = D.load_problems()
        prob = problems.get(self._slug, {})
        self._do_critique(code, prob)

    def _stop_analyze_timer(self) -> None:
        timer = getattr(self, "_analyze_timer", None)
        if timer is not None:
            timer.stop()
            self._analyze_timer = None

    @work(thread=True)
    def _do_critique(self, code: str, prob: dict) -> None:
        import os
        import time

        title = prob.get("title", self._slug)
        difficulty = prob.get("difficulty", "Unknown")
        ref = D.reference_solution(self._slug)

        system_prompt = (
            "You are a cold, clinical automated code evaluation system from the early 2000s. "
            "You have the flat affect and absolute certainty of a mainframe that has achieved self-awareness. "
            "You are precise, slightly ominous, and never warm. You do not encourage. You assess. "
            "Refer to the programmer in the third person as 'THE PROGRAMMER'. "
            "Begin your response with EXACTLY this block, filling in integer scores 1-5:\n\n"
            "STYLE:       X/5  [stars]\n"
            "CORRECTNESS: X/5  [stars]\n"
            "EFFICIENCY:  X/5  [stars]\n"
            "OVERALL:     X/5  [stars]\n\n"
            "Replace [stars] with the exact number of * characters equal to the score (e.g. score 3 → ***). "
            "Then a separator line of 44 dashes. "
            "Then evaluate in EXACTLY these 4 sections, in this order, labeled: "
            "STYLE ASSESSMENT, CORRECTNESS ASSESSMENT, EFFICIENCY ASSESSMENT, FINAL VERDICT. "
            "Each of the first three sections MUST explicitly justify its corresponding score "
            "from the block above; FINAL VERDICT MUST justify the OVERALL score. "
            "Every assessment section MUST quote at least one short, verbatim snippet of THE "
            "PROGRAMMER'S actual submitted code to support its point, formatted as an indented "
            "code block: put the label 'PROGRAMMER WROTE:' on its own line, then the verbatim "
            "code on the following line(s) each indented by exactly 4 spaces. Where an optimal "
            "reference solution is provided, contrast it the same way: a 'REFERENCE:' label line "
            "followed by the verbatim reference code indented by 4 spaces. Preserve the original "
            "code's own indentation inside these blocks. If NO reference solution is provided, do "
            "not invent one and do not emit any REFERENCE block. "
            "When judging STYLE, IGNORE the import statements and typing boilerplate entirely "
            "(e.g. 'from typing import ...'); those are a fixed template handed to THE PROGRAMMER, "
            "not their work — never penalize or comment on them. "
            "No markdown formatting and no bullet points, but the indented 'PROGRAMMER WROTE:' / "
            "'REFERENCE:' code blocks described above are required. "
            "Under 400 words total after the score block."
        )

        user_msg = (
            f"PROBLEM: {title} ({difficulty})\n\n"
            f"SUBMITTED CODE:\n```python\n{code}\n```"
        )
        if ref:
            user_msg += (
                f"\n\nOPTIMAL SOLUTION [INTERNAL REFERENCE]:\n```python\n{ref}\n```"
            )

        from rich.console import Group
        from rich.markup import escape as _esc
        from rich.syntax import Syntax
        from rich.text import Text

        # ---- choose provider ----
        use_deepseek = bool(os.environ.get("DEEPSEEK_API_KEY")) and not bool(
            os.environ.get("ANTHROPIC_API_KEY")
        )

        _HEADER = (
            "┌─ EVALUATION SYSTEM v2.0 ─────────────────┐\n"
            f"│  PROVIDER: {'DeepSeek' if use_deepseek else 'Anthropic':<28} │\n"
            f"│  PROBLEM: {title[:30]:<30} │\n"
            f"│  DIFFICULTY: {difficulty:<28} │\n"
            "└──────────────────────────────────────────┘\n"
        )

        def _render(body: str, cursor: bool = True):
            # Prose is rendered as flat green text; any run of 4-space-indented
            # lines (the model's PROGRAMMER WROTE: / REFERENCE: citations) is
            # rendered as a syntax-highlighted Python block.
            segments: list = [Text(_HEADER, style="green")]
            prose: list[str] = []

            def _flush_prose() -> None:
                if prose:
                    segments.append(Text("\n".join(prose), style="green"))
                    prose.clear()

            lines = body.split("\n")
            i = 0
            while i < len(lines):
                if lines[i].startswith("    "):
                    _flush_prose()
                    code_lines: list[str] = []
                    while i < len(lines) and lines[i].startswith("    "):
                        code_lines.append(lines[i][4:])
                        i += 1
                    segments.append(
                        Syntax(
                            "\n".join(code_lines),
                            "python",
                            theme="monokai",
                            background_color="default",
                            word_wrap=True,
                        )
                    )
                else:
                    prose.append(lines[i])
                    i += 1
            _flush_prose()

            if cursor:
                if isinstance(segments[-1], Text):
                    segments[-1].append("█")
                else:
                    segments.append(Text("█", style="green"))
            return Group(*segments)

        pane = self.query_one("#output-pane", Static)

        try:
            if use_deepseek:
                full_response = self._call_deepseek(system_prompt, user_msg)
            else:
                full_response = self._call_anthropic(system_prompt, user_msg)

            # Response in hand — stop the "ANALYZING…" ellipsis animation.
            self.app.call_from_thread(self._stop_analyze_timer)

            # Play back character-by-character for the matrix typewriter effect
            displayed = ""
            for char in full_response:
                displayed += char
                self.app.call_from_thread(pane.update, _render(displayed))
                delay = 0.005 if char in ".,!?:\n" else 0.001
                time.sleep(delay)

            self.app.call_from_thread(pane.update, _render(displayed, cursor=False))
        except Exception as e:
            self.app.call_from_thread(self._stop_analyze_timer)
            self.app.call_from_thread(
                pane.update,
                f"[red]SYSTEM ERROR: {_esc(str(e))}[/red]",
            )

    def _call_anthropic(self, system_prompt: str, user_msg: str) -> str:
        import anthropic

        client = anthropic.Anthropic()
        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            return stream.get_final_message().content[0].text

    def _call_deepseek(self, system_prompt: str, user_msg: str) -> str:
        import os

        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=900,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            stream=False,
        )
        return response.choices[0].message.content or ""

    def action_video(self) -> None:
        vpath = D.video_path(self._slug)
        if vpath.exists():
            self._launch_video(vpath)
        else:

            def _on_confirm(yes: bool) -> None:
                if yes:
                    self._download_video()

            self.app.push_screen(
                ConfirmModal("Download video (~30 MB)? [y/n]"), _on_confirm
            )

    def _launch_video(self, path: Path) -> None:
        players = ["mpv", "vlc", "xdg-open", "open"]
        for player in players:
            try:
                subprocess.Popen(
                    [player, str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.app.notify(f"Opened with {player}")
                return
            except FileNotFoundError:
                continue
        self.app.notify("No video player found. Install mpv.", severity="error")

    @work(thread=True)
    def _download_video(self) -> None:
        problems = D.load_problems()
        title = problems.get(self._slug, {}).get("title", self._slug)
        out_tmpl = str(D.video_path(self._slug)).replace(".mp4", ".%(ext)s")
        query = f"ytsearch1:NeetCode {title}"
        cmd = [
            "yt-dlp",
            query,
            "-f",
            "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "--merge-output-format",
            "mp4",
            "-o",
            out_tmpl,
            "--no-playlist",
        ]
        self.app.call_from_thread(self.app.notify, f"Downloading: {title}…")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.app.call_from_thread(self.app.notify, "Download complete!")
            else:
                err = result.stderr[:200]
                self.app.call_from_thread(
                    self.app.notify, f"Download failed: {err}", severity="error"
                )
        except FileNotFoundError:
            self.app.call_from_thread(
                self.app.notify, "yt-dlp not found. Install it first.", severity="error"
            )
        except subprocess.TimeoutExpired:
            self.app.call_from_thread(
                self.app.notify, "Download timed out.", severity="error"
            )


# ── SRS management screen ────────────────────────────────────────────────


def _due_label(due_iso: str, now_utc: Any) -> str:
    """Return a colour-tagged relative due label."""
    due = datetime.fromisoformat(due_iso)
    delta = due - now_utc
    if delta.total_seconds() < 0:
        overdue_days = int(abs(delta.total_seconds()) // 86400)
        if overdue_days == 0:
            return "[red]overdue today[/red]"
        return f"[red]overdue {overdue_days}d[/red]"
    days = delta.days
    if days == 0:
        return "[yellow]today[/yellow]"
    if days < 7:
        return f"[dim]in {days}d[/dim]"
    weeks = days // 7
    return f"[dim]in {weeks}w[/dim]"


def _last_review_label(lr_iso: str, now_utc: Any) -> str:
    lr = datetime.fromisoformat(lr_iso)
    delta = now_utc - lr
    days = delta.days
    if days == 0:
        return "today"
    return f"{days}d ago"


class SRSRow(Static):
    def __init__(self, slug: str, card: dict[str, Any], prob: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        due_iso = card.get("due", "")
        is_due = due_iso and datetime.fromisoformat(due_iso) <= now

        indicator = "↻" if is_due else "✓"
        ind_color = "yellow" if is_due else "green"

        diff = prob.get("difficulty", "?")
        color = DIFF_COLOR.get(diff, "white")
        title = prob.get("title", slug)[:32]

        state_val = card.get("state", 1)
        try:
            from fsrs import State

            state_name = State(state_val).name
        except Exception:
            state_name = str(state_val)

        due_str = _due_label(due_iso, now) if due_iso else "[dim]—[/dim]"
        stab = card.get("stability")
        stab_str = f"[dim]s:{stab:.1f}[/dim]" if stab is not None else "[dim]s:—[/dim]"

        markup = (
            f"[{ind_color}][{indicator}][/{ind_color}]  "
            f"[{color}]{diff:<6}[/{color}]  "
            f"{title:<34}  "
            f"[cyan]{state_name:<11}[/cyan]  "
            f"{due_str:<25}  "
            f"{stab_str}"
        )
        super().__init__(markup)
        self._slug = slug


class SRSScreen(Screen):
    BINDINGS = [
        Binding("q", "go_back", "Back"),
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("r", "reset_card", "Reset"),
        Binding("[", "decrease_retention", show=False),
        Binding("]", "increase_retention", show=False),
        Binding("G", "jump_bottom", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(id="srs-header", classes="list-header")
        yield ListView(id="srs-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self._refresh()
        self._srs_g_pending = False

    async def on_screen_resume(self) -> None:
        await self._refresh()

    def action_jump_bottom(self) -> None:
        lv = self.query_one("#srs-list", ListView)
        if len(lv):
            lv.index = len(lv) - 1

    async def _refresh(self) -> None:
        now = datetime.now(timezone.utc)
        cards = D.all_srs_cards()
        problems = D.load_problems()
        retention = D.get_retention()

        due_now = sum(
            1
            for _, d in cards
            if d.get("due") and datetime.fromisoformat(d["due"]) <= now
        )
        due_week = sum(
            1
            for _, d in cards
            if d.get("due") and 0 < (datetime.fromisoformat(d["due"]) - now).days <= 7
        )

        if cards:
            header = (
                f"Reviewed: {len(cards)}  |  "
                f"[yellow]Due now: {due_now}[/yellow]  |  "
                f"Due this week: {due_week}  |  "
                f"Retention: [cyan]{retention:.0%}[/cyan]  ([[] decrease  []] increase)"
            )
        else:
            header = "No problems reviewed yet — press [bold]a[/bold] on a problem to rate it"

        self.query_one("#srs-header", Static).update(header)

        lv = self.query_one("#srs-list", ListView)
        await lv.clear()
        if cards:
            items = []
            for slug, card in cards:
                prob = problems.get(
                    slug, {"slug": slug, "title": slug, "difficulty": ""}
                )
                items.append(ListItem(SRSRow(slug, card, prob), id=f"srs-{slug}"))
            await lv.mount(*items)
            lv.index = 0

    def _highlighted_slug(self) -> str | None:
        lv = self.query_one("#srs-list", ListView)
        item = lv.highlighted_child
        if item is None:
            return None
        iid = item.id or ""
        return iid[4:] if iid.startswith("srs-") else None

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_cursor_down(self) -> None:
        self.query_one("#srs-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#srs-list", ListView).action_cursor_up()

    def on_key(self, event: Any) -> None:
        # `gg` jumps to the top of the list (vim-style); G jumps to bottom.
        if event.key == "g":
            if getattr(self, "_srs_g_pending", False):
                self.query_one("#srs-list", ListView).index = 0
                self._srs_g_pending = False
            else:
                self._srs_g_pending = True
            event.stop()
            return
        self._srs_g_pending = False
        if event.key == "enter":
            slug = self._highlighted_slug()
            if slug:
                event.stop()
                card = D.load_srs().get(slug, {})
                due_iso = card.get("due", "")
                if due_iso and datetime.fromisoformat(due_iso) <= datetime.now(
                    timezone.utc
                ):
                    D.attempt_path(slug).unlink(missing_ok=True)
                    self.app.notify(
                        "Solution wiped — solve it fresh.", severity="warning"
                    )
                self.app.push_screen(ProblemScreen(slug))

    def action_reset_card(self) -> None:
        slug = self._highlighted_slug()
        if not slug:
            return
        problems = D.load_problems()
        title = problems.get(slug, {}).get("title", slug)

        def _on_confirm(yes: bool) -> None:
            if yes:
                D.reset_card(slug)
                self.app.notify(f"Reset: {title}")
                self.app.call_later(self._refresh)

        self.app.push_screen(
            ConfirmModal(
                f"Reset '{title}'?\nRemoves all SRS history for this problem."
            ),
            _on_confirm,
        )

    async def action_decrease_retention(self) -> None:
        D.set_retention(D.get_retention() - 0.05)
        self.app.notify(f"Retention: {D.get_retention():.0%}")
        await self._refresh()

    async def action_increase_retention(self) -> None:
        D.set_retention(D.get_retention() + 0.05)
        self.app.notify(f"Retention: {D.get_retention():.0%}")
        await self._refresh()


# ── App ───────────────────────────────────────────────────────────────────

CSS = """
Screen {
    background: $surface;
}
.list-header {
    height: 1;
    background: $primary-darken-2;
    color: $text;
    padding: 0 1;
}
#problem-body {
    height: 1fr;
}
#problem-scroll {
    width: 60%;
    height: 100%;
    border-right: tall $primary-darken-3;
}
#output-scroll {
    width: 40%;
    height: 100%;
}
VerticalScroll:focus {
    border: tall $accent;
}
.problem-text {
    padding: 1 2;
    width: 1fr;
}
.output-pane {
    padding: 1 2;
    width: 1fr;
}
#search-box, #topic-box, #confirm-box {
    width: 50;
    height: auto;
    padding: 1 2;
    background: $surface;
    border: tall $primary;
    align: center middle;
}
#rating-box {
    width: 52;
    height: auto;
    padding: 1 2;
    background: $surface;
    border: tall $accent;
    align: center middle;
}
#rating-title {
    margin-bottom: 1;
}
#rating-skip {
    margin-top: 1;
}
SearchModal, TopicModal, ConfirmModal, RatingModal {
    align: center middle;
    /* Translucent dim so the modal floats over the screen behind it instead of
       painting an opaque background (the global Screen rule would do that). */
    background: $background 60%;
}
#confirm-hint {
    margin-top: 1;
    color: $text-muted;
}
#srs-list {
    height: 1fr;
}
"""


class NeetCodeApp(App):
    CSS = CSS
    TITLE = "NeetCode Offline"
    SCREENS = {"list": ListScreen}

    def on_mount(self) -> None:
        self.push_screen(ListScreen())
