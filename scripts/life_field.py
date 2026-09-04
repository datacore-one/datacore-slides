#!/usr/bin/env python3
"""life_field.py — a Conway's Game of Life ground for PLUR decks, as inline SVG.

WHY THIS EXISTS, AND WHY IT IS NOT GENERATED
--------------------------------------------
`render_cover_slide.py` already argued the point for a single cover and it holds for a
whole deck: the product is memory, so the ground should be a trace of what came before
rather than a picture of nothing. An image model will happily draw a plausible grid that
is not actually Life — on a deck about records you can verify, that is a poor joke. This
computes it. Same seed, same rules (B3/S23), same pixels every run.

WHAT MAKES IT THE PLUR GROUND RATHER THAN GENERIC LIFE
------------------------------------------------------
The mark is nine dots on a grid, four of which fire. This field is the same sentence at
page scale: the CSS ghost lattice is the resting grid, and a live cell is a fired node
sitting exactly on one of its dots. Pitch and offset are shared with the CSS
(`background-size:34px 34px; background-position:17px 17px`) so the two layers register
rather than merely coexist. Nothing here is outside the brand's dot-and-bar vocabulary.

ONE ORGANISM, NOT SIXTEEN PICTURES
-----------------------------------
A deck calls `DeckField` once and advances it between slides. Every slide shows a later
moment of the same simulation, so the backgrounds are unique per slide and obviously one
family — which is the thing a folder of independently generated plates can never be.

Where the argument earns it, a slide INJECTS a pattern into the running field instead of
restarting it: an r-pentomino where the copy says memory fires ungoverned, a glider where
it says a pattern persists and travels, blocks where it says what survives. The organism
keeps living; the argument perturbs it.

USAGE
-----
    from life_field import DeckField
    deck = DeckField(seed="plur", settle=40)
    svg = deck.slide_svg(trail=3, opacity=0.06)      # first slide
    deck.advance(6)                                   # between slides
    deck.inject("r-pentomino")                        # where the copy earns it

CLI (preview a field as a standalone SVG):
    python3 life_field.py --seed plur --settle 40 --advance 12 --out field.svg
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

# Geometry shared with the deck CSS ghost lattice — do not change one without the other.
PITCH = 34
OFFSET = 17
COLS = 57
ROWS = 32
LIVE_R = 9.0          # a fired node: the mark fires at 3x its resting radius, and so does this
CANVAS = (1920, 1080)

# Named seeds. Coordinates are cell offsets from the pattern's own origin.
PATTERNS: dict[str, list[tuple[int, int]]] = {
    # The mark's home path [0,4,5,8] on its 3x3 — the brand's own tetromino, sown as a seed.
    "home-path": [(0, 0), (1, 1), (2, 1), (2, 2)],
    # The classic chaos seed: five cells that will not settle for a thousand generations.
    "r-pentomino": [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)],
    # A pattern that persists AND travels — memory that moves.
    "glider": [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
    # Still lifes: what survives when everything else stops.
    "block": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "beehive": [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)],
    # An oscillator — the thing that recurs.
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
    """One Life simulation, walked through a deck.

    COMPOSED, NOT RANDOM. A dense random seed settles into scattered debris, which reads
    as noise at background opacity — tried it, it looks like dust. Instead the field is
    seeded with a curated cast, each member of which means something the deck is already
    arguing:

        still lifes (block, beehive)  what persists unchanged
        blinkers                      what recurs
        gliders                       a pattern that persists AND travels
        r-pentomino                   growth nobody governs

    The trail is sampled at a STRIDE rather than at consecutive generations. A glider
    moves one cell every four generations, so three consecutive frames are visually
    identical; sampling every fifth generation gives it a wake you can actually see, and
    the wake is the point — the ground shows where something came from.

    A soft left mask keeps the field out of the text column without breaking the
    simulation: the cells are still alive and still evolving, they are simply drawn
    faint where type sits.
    """

    HISTORY = 48

    def __init__(self, seed: str = "plur", settle: int = 24):
        rng = random.Random(seed)
        self.rng = rng
        live: set[tuple[int, int]] = set()

        def place(name: str, x: int, y: int) -> None:
            for (dx, dy) in PATTERNS[name]:
                live.add(((x + dx) % COLS, (y + dy) % ROWS))

        # The cast, placed in the right two thirds where type is not.
        for name, x, y in (("block", 46, 3), ("beehive", 51, 22), ("block", 33, 28),
                           ("blinker", 41, 9), ("blinker", 54, 14)):
            place(name, x, y)
        # Gliders travel down-right one cell per four generations; start them upper-left
        # of their region so they sweep across the frame over the length of the deck.
        for x, y in ((30, 2), (37, 16), (25, 24)):
            place("glider", x, y)
        # The mark's own tetromino, sown twice — the brand's shape, left to evolve.
        for x, y in ((44, 12), (29, 9)):
            place("home-path", x, y)

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

        A cell with `crowd` or more live neighbours is in an overcrowded, churning
        region — the debris an r-pentomino leaves behind. Stable structures are quieter
        by construction: every cell of a block has exactly three neighbours, a blinker's
        have one or two. So removing the crowded cells prunes the chaos and leaves what
        persists, which is the same sentence the deck is arguing on the slide where this
        is called. Returns how many cells were retired.

        Without this the deck gets BUSIER as it goes: the injections at the problem and
        fleet slides grow for the rest of the run and the closer — the slide that should
        be calmest — ends up the loudest. An argument that says governance is the answer
        should not have an ungoverned ground.
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
        """Keep the text column clear.

        Near-silent across the left half, where every slide's headline and body sit,
        rising to full only in the right third. The cells are still alive and still
        evolving there — they are simply drawn faint, so the simulation stays whole.
        """
        t = x / (COLS - 1)
        if t >= 0.66:
            return 1.0
        return 0.05 + 0.95 * max(0.0, (t - 0.16) / 0.50) ** 2.0

    def slide_svg(self, trail: int = 3, stride: int = 5, opacity: float = 0.22,
                  accent: str | None = None) -> str:
        """Inline SVG for one slide's ground.

        `accent` names a CSS var for the newest generation only, so a slide keeps its
        single accent and the trail reads as decay rather than as a second colour.

        Cell radius is NOT set here. It is one CSS rule in the consuming stylesheet
        (`.life circle{r:9px}`) — scoped by class, because an unscoped `circle{r:...}`
        inside an inline SVG leaks to the whole HTML document and would resize the
        mark's own nodes.
        """
        layers: list[tuple[set[tuple[int, int]], float, bool]] = []
        for i in range(trail, 0, -1):
            idx = -i * stride
            if len(self.history) >= i * stride:
                fade = 0.16 + 0.30 * ((trail - i) / trail)
                layers.append((self.history[idx], opacity * fade, False))
        layers.append((self.live, opacity, True))

        out = [f'<svg class="life" viewBox="0 0 {CANVAS[0]} {CANVAS[1]}" '
               f'preserveAspectRatio="xMidYMid slice" aria-hidden="true">']
        for cells, op, newest in layers:
            fill = f"var(--{accent})" if (newest and accent) else "currentColor"
            # Group by mask band so opacity varies across the frame without one <g> per cell.
            bands: dict[int, list[tuple[int, int]]] = {}
            for (x, y) in cells:
                bands.setdefault(int(self._mask(x) * 8), []).append((x, y))
            body = []
            for band, pts in sorted(bands.items()):
                m = (band + 0.5) / 8
                dots = "".join(f'<circle cx="{OFFSET + x * PITCH}" cy="{OFFSET + y * PITCH}"/>'
                               for (x, y) in sorted(pts))
                body.append(f'<g fill-opacity="{op * m:.4f}">{dots}</g>')
            out.append(f'<g fill="{fill}">{"".join(body)}</g>')
        out.append("</svg>")
        return "".join(out)

    def population(self) -> int:
        return len(self.live)


def main() -> int:
    ap = argparse.ArgumentParser(description="Preview a PLUR Life ground as SVG")
    ap.add_argument("--seed", default="plur")
    ap.add_argument("--settle", type=int, default=24)
    ap.add_argument("--advance", type=int, default=0)
    ap.add_argument("--inject", action="append", default=[], choices=list(PATTERNS))
    ap.add_argument("--trail", type=int, default=3)
    ap.add_argument("--opacity", type=float, default=0.13)
    ap.add_argument("--out", default="life-field.svg")
    a = ap.parse_args()

    f = DeckField(seed=a.seed, settle=a.settle)
    for p in a.inject:
        f.inject(p)
    if a.advance:
        f.advance(a.advance)
    svg = f.slide_svg(trail=a.trail, opacity=a.opacity)
    Path(a.out).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS[0]}" height="{CANVAS[1]}" '
        f'viewBox="0 0 {CANVAS[0]} {CANVAS[1]}" style="background:#0e0f14;color:#f0f0f2">'
        + svg[svg.index(">") + 1:])
    print(f"{a.out}  generation {f.generation}  population {f.population()}  "
          f"{len(svg) // 1024} KB inline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
