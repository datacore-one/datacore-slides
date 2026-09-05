#!/usr/bin/env python3
"""life_field.py — a Conway's Game of Life ground for PLUR decks, as inline SVG.

WHY LIFE, AND WHY COMPUTED
--------------------------
The product is memory, so the ground should be a trace of what came before rather than a
picture of nothing: each slide layers past generations behind the current one, oldest
faintest. And an image model draws a plausible grid that is not actually Life — on a deck
about records you can verify, that would be a poor joke. `render_cover_slide.py` made the
argument first and it holds for a whole deck. Same seed, same B3/S23 rules, same pixels.

SCALE IS THE WHOLE DESIGN DECISION
----------------------------------
The first version ran 57x32 cells of 9px dots. It was, correctly, called noise — and it
was noise by definition: uniform high-frequency detail with no low-frequency structure,
scattered evenly, in one colour at an opacity too low to read as colour at all.

This runs 13x8. A live cell is a 52px disc in the slide's accent, and adjacent live cells
are joined by a bar carrying the gradient between their colours. A slide's ground is eight
or fifteen large connected forms, not four hundred specks — and it is the mark's own
construction (nodes joined by round-capped bars) at the size of the page, which is exactly
what the mark already is at the size of a logo.

Fewer, larger, connected, and in colour. That is the difference between a ground and dust.

ONE ORGANISM, NOT SIXTEEN PICTURES
-----------------------------------
A deck seeds the field once and advances it between slides, so every ground is unique and
obviously the same creature. `inject()` perturbs it where the copy earns it; `govern()`
retires overcrowded cells, which prunes churn and leaves what persists.

USAGE
-----
    from life_field import DeckField
    deck = DeckField(seed="plur")
    svg = deck.slide_svg(accent="cyan", accent_next="amber", opacity=0.16)
    deck.advance(1)

CLI:
    python3 life_field.py --advance 3 --out field.svg
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

CANVAS = (1920, 1080)
COLS, ROWS = 13, 8
PITCH = 150
NODE_R = 52          # a fired node at page scale
TRAIL_R = 30         # an afterimage is smaller as well as fainter
BAR_W = 15           # the mark's bar is 11 at viewBox 200; this is that weight here

# Centre the lattice on the canvas.
OX = (CANVAS[0] - (COLS - 1) * PITCH) // 2
OY = (CANVAS[1] - (ROWS - 1) * PITCH) // 2

PATTERNS: dict[str, list[tuple[int, int]]] = {
    "home-path": [(0, 0), (1, 1), (2, 1), (2, 2)],   # the mark's own four fired nodes
    "r-pentomino": [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)],
    "glider": [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
    "block": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "blinker": [(0, 0), (1, 0), (2, 0)],
}


def step(live: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """One generation of B3/S23 on a torus, so nothing escapes the frame."""
    counts: dict[tuple[int, int], int] = {}
    for (x, y) in live:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    n = ((x + dx) % COLS, (y + dy) % ROWS)
                    counts[n] = counts.get(n, 0) + 1
    return {c for c, n in counts.items() if n == 3 or (n == 2 and c in live)}


class DeckField:
    """One Life simulation, walked through a deck at page scale."""

    HISTORY = 12

    def __init__(self, seed: str = "plur", settle: int = 3):
        self.rng = random.Random(seed)
        live: set[tuple[int, int]] = set()

        def place(name: str, x: int, y: int) -> None:
            for (dx, dy) in PATTERNS[name]:
                live.add(((x + dx) % COLS, (y + dy) % ROWS))

        # A small world needs a deliberate cast; a random scatter here either dies in two
        # generations or fills the frame, and neither is a composition.
        place("home-path", 8, 1)      # the mark, sown, and left to evolve
        place("block", 11, 5)         # what persists unchanged
        place("blinker", 6, 6)        # what recurs
        place("glider", 2, 2)         # what persists AND travels
        place("home-path", 4, 4)

        self.live = live
        self.history: list[set[tuple[int, int]]] = []
        self.generation = 0
        self.advance(settle)

    def advance(self, n: int = 1) -> None:
        for _ in range(n):
            self.history.append(self.live)
            self.live = step(self.live)
            self.generation += 1
        self.history = self.history[-self.HISTORY:]

    def inject(self, pattern: str, at: tuple[int, int] | None = None) -> None:
        """Perturb the running field where the argument earns it. Seeded, so reproducible."""
        ox, oy = at or (self.rng.randrange(COLS), self.rng.randrange(ROWS))
        for (dx, dy) in PATTERNS[pattern]:
            self.live.add(((ox + dx) % COLS, (oy + dy) % ROWS))

    def govern(self, crowd: int = 4) -> int:
        """Retire the ungoverned parts of the field, and only those.

        A cell with `crowd` or more live neighbours sits in a churning region — the debris
        an r-pentomino leaves. Stable structures are quieter by construction: every cell of
        a block has exactly three neighbours. So this prunes chaos and leaves what persists,
        which is the sentence the deck is arguing on the slide where it is called. Without
        it the deck grows busier as it runs and the closer becomes its loudest page.
        """
        counts: dict[tuple[int, int], int] = {}
        for (x, y) in self.live:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx or dy:
                        n = ((x + dx) % COLS, (y + dy) % ROWS)
                        counts[n] = counts.get(n, 0) + 1
        before = len(self.live)
        self.live = {c for c in self.live if counts.get(c, 0) < crowd}
        return before - len(self.live)

    # ── rendering ────────────────────────────────────────────────────────
    @staticmethod
    def _mask(x: int) -> float:
        """Keep the type column quiet. Near-silent left, full by two thirds across."""
        t = x / (COLS - 1)
        if t >= 0.66:
            return 1.0
        return 0.10 + 0.90 * max(0.0, (t - 0.15) / 0.51) ** 1.8

    def _px(self, x: int, y: int) -> tuple[int, int]:
        return OX + x * PITCH, OY + y * PITCH

    def _bars(self, cells: set[tuple[int, int]], a: str, b: str, op: float, uid: str) -> str:
        """Join adjacent live cells, gradient between their accents.

        This is the one gradient the brand owns — inside a bar, between the two nodes it
        connects — and it is what turns a set of discs into the mark's own construction.
        Wrapped pairs are skipped: a bar that leaves one edge and reappears at the other
        reads as a mistake rather than as a torus.
        """
        out, defs, n = [], [], 0
        for (x, y) in sorted(cells):
            for (dx, dy) in ((1, 0), (0, 1)):
                nx, ny = x + dx, y + dy
                if nx >= COLS or ny >= ROWS or (nx, ny) not in cells:
                    continue
                x1, y1 = self._px(x, y)
                x2, y2 = self._px(nx, ny)
                gid = f"{uid}b{n}"
                n += 1
                defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
                            f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
                            f'<stop offset="0" stop-color="var(--{a})"/>'
                            f'<stop offset="1" stop-color="var(--{b})"/></linearGradient>')
                m = min(self._mask(x), self._mask(nx))
                out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="url(#{gid})" '
                           f'stroke-width="{BAR_W}" stroke-linecap="round" '
                           f'stroke-opacity="{op * m:.4f}"/>')
        return f'<defs>{"".join(defs)}</defs>{"".join(out)}'

    def slide_svg(self, accent: str = "cyan", accent_next: str = "amber",
                  opacity: float = 0.16, trail: int = 2, uid: str = "f") -> str:
        """Inline SVG for one slide's ground.

        One accent per slide, as the brand requires; the bars carry the licensed gradient
        toward the next accent in the positional sequence, so the deck traverses the whole
        palette across its length without any single page wearing four colours.
        """
        parts = [f'<svg class="life" viewBox="0 0 {CANVAS[0]} {CANVAS[1]}" '
                 f'preserveAspectRatio="xMidYMid slice" aria-hidden="true">']

        # Afterimages first, behind: smaller and much fainter, the trace of what was here.
        for i, gen in enumerate(self.history[-trail:] if trail else []):
            f = 0.20 + 0.22 * (i / max(trail, 1))
            dots = "".join(
                f'<circle cx="{self._px(x, y)[0]}" cy="{self._px(x, y)[1]}" r="{TRAIL_R}" '
                f'fill-opacity="{opacity * f * self._mask(x):.4f}"/>' for (x, y) in sorted(gen))
            parts.append(f'<g fill="var(--{accent})">{dots}</g>')

        parts.append(self._bars(self.live, accent, accent_next, opacity * 0.72, uid))
        dots = "".join(
            f'<circle cx="{self._px(x, y)[0]}" cy="{self._px(x, y)[1]}" r="{NODE_R}" '
            f'fill-opacity="{opacity * self._mask(x):.4f}"/>' for (x, y) in sorted(self.live))
        parts.append(f'<g fill="var(--{accent})">{dots}</g>')
        parts.append("</svg>")
        return "".join(parts)

    def population(self) -> int:
        return len(self.live)


def main() -> int:
    ap = argparse.ArgumentParser(description="Preview a PLUR Life ground as SVG")
    ap.add_argument("--seed", default="plur")
    ap.add_argument("--settle", type=int, default=3)
    ap.add_argument("--advance", type=int, default=0)
    ap.add_argument("--inject", action="append", default=[], choices=list(PATTERNS))
    ap.add_argument("--opacity", type=float, default=0.16)
    ap.add_argument("--out", default="life-field.svg")
    a = ap.parse_args()

    f = DeckField(seed=a.seed, settle=a.settle)
    for p in a.inject:
        f.inject(p)
    if a.advance:
        f.advance(a.advance)
    body = f.slide_svg(opacity=a.opacity)
    Path(a.out).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS[0]}" height="{CANVAS[1]}" '
        f'viewBox="0 0 {CANVAS[0]} {CANVAS[1]}" style="background:#0e0f14">'
        f'<style>:root{{--cyan:#22d3ee;--amber:#f0a050}}</style>'
        + body[body.index(">") + 1:])
    print(f"{a.out}  generation {f.generation}  population {f.population()}  "
          f"{len(body) // 1024} KB inline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
