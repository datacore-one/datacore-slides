#!/usr/bin/env python3
"""
Render a refined two-pager markdown file to a faithful A4 PDF.

This is the FIDELITY-FIRST companion to render_dubai_entity_twopager.py.

That renderer drives both .md and .pdf from a rigid per-entity SPECS dict — great
when the content fits the template. But once a refined .md is produced by an
evaluator/consensus loop, its free-form content no longer fits SPECS, and running
the SPECS renderer would OVERWRITE the refined .md with stale template content.

This script does the opposite: it takes the refined .md as the source of truth and
renders the PDF from it verbatim (markup syntax stripped; no paraphrase). It uses
ReportLab Platypus for automatic pagination, so length is not constrained to two
pages of a fixed layout — fidelity of the refined text is the priority.

Supported markdown subset (sufficient for the Dubai two-pagers):
  - YAML frontmatter (skipped for body; not rendered)
  - # / ## / ### headings
  - paragraphs
  - > blockquotes (incl. multi-line)
  - - unordered lists
  - N. ordered lists
  - GFM pipe tables
  - --- horizontal rules
  - **bold** and *italic* inline (converted to <b>/<i>)

Datafund light aesthetic: charcoal text, pure-blue (#0066FF) accents, generous
whitespace, fine rules. Page numbers in the footer.

Usage:
    python3 render_md_twopager.py FILE.md [FILE2.md ...]
    # PDF is written next to each .md (same stem, .pdf extension)
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Palette (matches render_dubai_entity_twopager.py)
# ---------------------------------------------------------------------------
CHARCOAL_DARK = colors.HexColor("#1A1A1A")
CHARCOAL_BODY = colors.HexColor("#333333")
CHARCOAL_MID = colors.HexColor("#555555")
MUTED_GREY = colors.HexColor("#888888")
PALE_GREY = colors.HexColor("#E8E8E8")
BLUE = colors.HexColor("#0066FF")
BLUE_PALE = colors.HexColor("#DCE9F8")
HEADER_GREY = colors.HexColor("#F4F6FA")


def register_font():
    """Register Helvetica Neue if present, with bold/italic faces. Fallback Helvetica."""
    base = "Helvetica"
    bold = "Helvetica-Bold"
    italic = "Helvetica-Oblique"
    bolditalic = "Helvetica-BoldOblique"
    # Try the macOS Helvetica Neue collection for a closer-to-brand look.
    candidates = [
        ("HelN", "/System/Library/Fonts/HelveticaNeue.ttc", 0),
        ("HelN-Bold", "/System/Library/Fonts/HelveticaNeue.ttc", 1),
    ]
    ok = True
    for name, path, idx in candidates:
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
        except Exception:
            ok = False
            break
    if ok:
        # Map regular/bold to Helvetica Neue; keep platform Oblique faces for italics
        # (HelveticaNeue.ttc italic subfont index varies; use core Oblique for safety).
        base, bold = "HelN", "HelN-Bold"
    return base, bold, italic, bolditalic


FONT, FONT_BOLD, FONT_ITALIC, FONT_BOLDITALIC = register_font()


# ---------------------------------------------------------------------------
# Inline markdown -> ReportLab mini-HTML
# ---------------------------------------------------------------------------
def inline(text: str) -> str:
    """Convert a markdown inline string to ReportLab paragraph markup.

    Order matters: escape HTML first, then apply bold (**), then italic (*).
    Text is preserved verbatim; only the markup characters are consumed.
    """
    text = html.escape(text, quote=False)
    # Bold: **...**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.S)
    # Italic: *...*  (single asterisks not adjacent to another asterisk)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text, flags=re.S)
    return text


# ---------------------------------------------------------------------------
# Block parser
# ---------------------------------------------------------------------------
def parse_blocks(md: str):
    """Yield (kind, payload) blocks from markdown body (frontmatter already stripped)."""
    lines = md.split("\n")
    i = 0
    n = len(lines)
    blocks = []

    def is_table_row(s):
        return s.lstrip().startswith("|")

    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # blank
        if not stripped:
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}", stripped):
            blocks.append(("hr", None))
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            blocks.append(("h", (level, m.group(2).strip())))
            i += 1
            continue

        # table (a row, followed by a separator row of dashes/pipes)
        if is_table_row(line) and i + 1 < n and re.search(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]):
            tbl = []
            while i < n and is_table_row(lines[i]):
                tbl.append(lines[i].strip())
                i += 1
            blocks.append(("table", tbl))
            continue

        # blockquote (consume consecutive > lines; join with spaces unless blank > )
        if stripped.startswith(">"):
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                content = re.sub(r"^\s*>\s?", "", lines[i])
                quote_lines.append(content.rstrip())
                i += 1
            # collapse into paragraphs separated by blank quote lines
            chunks = []
            cur = []
            for q in quote_lines:
                if q.strip() == "":
                    if cur:
                        chunks.append(" ".join(cur))
                        cur = []
                else:
                    cur.append(q.strip())
            if cur:
                chunks.append(" ".join(cur))
            blocks.append(("quote", chunks))
            continue

        # unordered list
        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i].strip()))
                i += 1
            blocks.append(("ul", items))
            continue

        # ordered list
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append(("ol", items))
            continue

        # paragraph (consume until blank / block boundary)
        para = []
        while i < n:
            cur = lines[i]
            cs = cur.strip()
            if (not cs or cs.startswith(("#", ">", "|"))
                    or re.fullmatch(r"-{3,}", cs)
                    or re.match(r"^\s*[-*]\s+", cur)
                    or re.match(r"^\s*\d+\.\s+", cur)):
                break
            para.append(cs)
            i += 1
        blocks.append(("p", " ".join(para)))

    return blocks


def split_frontmatter(text: str):
    if text.startswith("---"):
        parts = text.split("\n")
        # find closing --- after line 0
        for idx in range(1, len(parts)):
            if parts[idx].strip() == "---":
                return "\n".join(parts[idx + 1:])
    return text


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def build_styles():
    ss = getSampleStyleSheet()
    styles = {}
    styles["h1"] = ParagraphStyle(
        "h1", parent=ss["Normal"], fontName=FONT_BOLD, fontSize=17, leading=20,
        textColor=CHARCOAL_DARK, spaceBefore=0, spaceAfter=4)
    styles["h2"] = ParagraphStyle(
        "h2", parent=ss["Normal"], fontName=FONT_BOLD, fontSize=11.5, leading=13.5,
        textColor=CHARCOAL_DARK, spaceBefore=5, spaceAfter=2)
    styles["h3"] = ParagraphStyle(
        "h3", parent=ss["Normal"], fontName=FONT_BOLD, fontSize=9.6, leading=12,
        textColor=BLUE, spaceBefore=4.5, spaceAfter=1.5)
    styles["body"] = ParagraphStyle(
        "body", parent=ss["Normal"], fontName=FONT, fontSize=7.6, leading=9.8,
        textColor=CHARCOAL_BODY, spaceAfter=2.0, alignment=TA_LEFT)
    styles["subtitle"] = ParagraphStyle(
        "subtitle", parent=ss["Normal"], fontName=FONT_BOLD, fontSize=9, leading=11.8,
        textColor=CHARCOAL_DARK, spaceAfter=3.5)
    styles["quote"] = ParagraphStyle(
        "quote", parent=ss["Normal"], fontName=FONT, fontSize=7.6, leading=10.2,
        textColor=CHARCOAL_MID, leftIndent=6, spaceAfter=2.5)
    styles["bullet"] = ParagraphStyle(
        "bullet", parent=ss["Normal"], fontName=FONT, fontSize=7.7, leading=10.0,
        textColor=CHARCOAL_BODY, leftIndent=10, bulletIndent=1, spaceAfter=1.5)
    styles["cell"] = ParagraphStyle(
        "cell", parent=ss["Normal"], fontName=FONT, fontSize=7.0, leading=9.2,
        textColor=CHARCOAL_BODY)
    styles["cellhead"] = ParagraphStyle(
        "cellhead", parent=ss["Normal"], fontName=FONT_BOLD, fontSize=7.1, leading=9.4,
        textColor=CHARCOAL_DARK)
    styles["footer"] = ParagraphStyle(
        "footer", parent=ss["Normal"], fontName=FONT, fontSize=7.2, leading=9.5,
        textColor=MUTED_GREY)
    return styles


# ---------------------------------------------------------------------------
# Build flowables
# ---------------------------------------------------------------------------
def parse_table_cells(row: str):
    s = row.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def build_story(blocks, styles, content_width):
    story = []
    first_h1_done = False

    for kind, payload in blocks:
        if kind == "hr":
            story.append(HRFlowable(width="100%", thickness=0.5, color=PALE_GREY,
                                    spaceBefore=1.5, spaceAfter=3))
        elif kind == "h":
            level, text = payload
            if level == 1:
                story.append(Paragraph(inline(text), styles["h1"]))
                first_h1_done = True
            elif level == 2:
                story.append(Paragraph(inline(text), styles["h2"]))
            else:
                story.append(Paragraph(inline(text), styles["h3"]))
        elif kind == "p":
            # The first standalone bold paragraph after H1 acts as the subtitle.
            txt = payload
            if first_h1_done and re.fullmatch(r"\*\*.+\*\*", txt.strip(), flags=re.S):
                story.append(Paragraph(inline(txt), styles["subtitle"]))
                first_h1_done = False
            else:
                story.append(Paragraph(inline(txt), styles["body"]))
        elif kind == "quote":
            for chunk in payload:
                story.append(_quote_flowable(chunk, styles, content_width))
        elif kind == "ul":
            for it in payload:
                story.append(Paragraph(inline(it), styles["bullet"],
                                       bulletText="▪"))
        elif kind == "ol":
            for idx, it in enumerate(payload, 1):
                story.append(Paragraph(inline(it), styles["bullet"],
                                       bulletText=f"{idx}."))
        elif kind == "table":
            story.append(_table_flowable(payload, styles, content_width))
            story.append(Spacer(1, 2))

    return story


def _quote_flowable(text, styles, content_width):
    """A blockquote rendered as a pale-blue left-bar callout."""
    p = Paragraph(inline(text), styles["quote"])
    t = Table([[p]], colWidths=[content_width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_PALE),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _table_flowable(rows, styles, content_width):
    parsed = [parse_table_cells(r) for r in rows]
    header = parsed[0]
    # drop the separator row (row 1)
    body = parsed[2:] if len(parsed) > 2 else []
    ncols = len(header)

    # Column widths: if first column is an empty header (matrix tables), make it narrow.
    if header and header[0] == "":
        first = content_width * 0.16
        rest = (content_width - first) / (ncols - 1) if ncols > 1 else content_width
        col_widths = [first] + [rest] * (ncols - 1)
    else:
        col_widths = [content_width / ncols] * ncols

    def cellpara(txt, is_header, is_firstcol):
        style = styles["cellhead"] if (is_header or is_firstcol) else styles["cell"]
        return Paragraph(inline(txt) if txt else "", style)

    data = []
    data.append([cellpara(c, True, False) for c in header])
    for r in body:
        # pad/truncate to ncols
        r = (r + [""] * ncols)[:ncols]
        data.append([cellpara(c, False, j == 0) for j, c in enumerate(r)])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_GREY),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, BLUE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, PALE_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


# ---------------------------------------------------------------------------
# Page furniture
# ---------------------------------------------------------------------------
def make_page_decorator(title):
    def on_page(canvas, doc):
        canvas.saveState()
        page_w, page_h = A4
        mx = 18 * mm
        # top rule + masthead
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(MUTED_GREY)
        canvas.drawString(mx, page_h - 13 * mm, "PLUR by Datafund  ·  2026")
        canvas.drawRightString(page_w - mx, page_h - 13 * mm, f"Page {doc.page}")
        canvas.setStrokeColor(PALE_GREY)
        canvas.setLineWidth(0.4)
        canvas.line(mx, page_h - 15 * mm, page_w - mx, page_h - 15 * mm)
        # bottom rule + footer
        canvas.line(mx, 14 * mm, page_w - mx, 14 * mm)
        canvas.setFont(FONT, 6.8)
        canvas.setFillColor(MUTED_GREY)
        canvas.drawString(mx, 10 * mm, title)
        canvas.drawRightString(page_w - mx, 10 * mm, "Institutional Memory for Sovereign AI")
        canvas.restoreState()
    return on_page


def render(md_path: Path, out_path: Path | None = None):
    text = md_path.read_text(encoding="utf-8")
    body = split_frontmatter(text)
    blocks = parse_blocks(body)
    styles = build_styles()

    page_w, page_h = A4
    mx = 15 * mm
    top = 17 * mm
    bottom = 14 * mm
    content_width = page_w - 2 * mx

    pdf_path = out_path if out_path is not None else md_path.with_suffix(".pdf")

    # Derive a short footer title from the H1.
    title = md_path.stem
    for kind, payload in blocks:
        if kind == "h" and payload[0] == 1:
            title = payload[1]
            break

    doc = BaseDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=mx, rightMargin=mx, topMargin=top, bottomMargin=bottom,
        title=title, author="Gregor Zavcer, Datafund",
    )
    frame = Frame(mx, bottom, content_width, page_h - top - bottom,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="main", frames=[frame], onPage=make_page_decorator(title)),
    ])

    story = build_story(blocks, styles, content_width)
    doc.build(story)
    return pdf_path


def main():
    args = sys.argv[1:]
    if not args:
        print("usage: render_md_twopager.py FILE.md [FILE2.md ...]")
        print("       render_md_twopager.py --out OUT.pdf FILE.md   (single file, explicit output)")
        sys.exit(1)
    # Explicit single-file output: --out OUT.pdf INPUT.md
    if args[0] == "--out":
        out_path = Path(args[1]).expanduser().resolve()
        in_path = Path(args[2]).expanduser().resolve()
        out = render(in_path, out_path)
        print(f"  {in_path.name} -> {out}  ({out.stat().st_size:,} bytes)")
        return
    for a in args:
        p = Path(a).expanduser().resolve()
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        out = render(p)
        size = out.stat().st_size
        print(f"  {p.name} -> {out.name}  ({size:,} bytes)")


if __name__ == "__main__":
    main()
