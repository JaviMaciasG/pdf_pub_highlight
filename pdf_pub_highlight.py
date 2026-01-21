#!/usr/bin/env python3
"""
Create <file>-pub.pdf containing only pages where any given text fragment appears,
and highlight all matches in yellow.

Requires: PyMuPDF (pymupdf)
"""

from __future__ import annotations

import argparse
import os
import sys
import fitz  # PyMuPDF


def build_output_name(input_path: str, suffix: str = "-pub") -> str:
    base, ext = os.path.splitext(input_path)
    if ext.lower() != ".pdf":
        # Keep original extension logic simple; still output as .pdf
        return f"{input_path}{suffix}.pdf"
    return f"{base}{suffix}.pdf"


def highlight_rects_on_page(page: fitz.Page, rects: list[fitz.Rect], opacity: float = 0.35) -> int:
    """
    Add yellow highlight annotations for a list of rectangles on the given page.
    Returns number of highlight annotations added.
    """
    count = 0
    for r in rects:
        # Highlight annotation (visually a marker-like overlay).
        annot = page.add_highlight_annot(r)
        # Yellow
        annot.set_colors(stroke=(1, 1, 0))
        annot.set_opacity(opacity)
        annot.update()
        count += 1
    return count


def process_pdf(input_pdf: str, fragments: list[str], *, case_sensitive: bool, whole_words: bool) -> tuple[str, int, int]:
    """
    Returns (output_pdf, pages_written, total_highlights).
    """
    if not os.path.exists(input_pdf):
        raise FileNotFoundError(input_pdf)

    # Search flags
    flags = 0
    if not case_sensitive:
        flags |= fitz.TEXT_DEHYPHENATE  # doesn't control case; dehyphenate helps matching across line breaks
    # PyMuPDF search flags are a bit nuanced; for case-insensitive matching we use the built-in:
    # search_for has a 'flags' parameter, but case-insensitive is handled by 'page.search_for' via 'flags=fitz.TEXT_IGNORECASE'
    # when available. We'll set it if present.
    if hasattr(fitz, "TEXT_IGNORECASE") and not case_sensitive:
        flags |= fitz.TEXT_IGNORECASE
    if hasattr(fitz, "TEXT_PRESERVE_LIGATURES"):
        flags |= fitz.TEXT_PRESERVE_LIGATURES

    if hasattr(fitz, "TEXT_WORDS") and whole_words:
        flags |= fitz.TEXT_WORDS

    src = fitz.open(input_pdf)
    out = fitz.open()  # new empty PDF

    pages_written = 0
    total_highlights = 0

    # Iterate pages, collect matches, copy matching pages to output, apply highlights there
    for page_index in range(src.page_count):
        page = src.load_page(page_index)

        page_rects: list[fitz.Rect] = []
        for frag in fragments:
            # Find all occurrences of fragment on this page
            rects = page.search_for(frag, flags=flags)
            if rects:
                page_rects.extend(rects)

        if page_rects:
            # Copy this page into output
            out.insert_pdf(src, from_page=page_index, to_page=page_index)
            out_page = out.load_page(pages_written)

            # Highlight matches on the copied page (same coordinates)
            total_highlights += highlight_rects_on_page(out_page, page_rects)
            pages_written += 1

    output_pdf = build_output_name(input_pdf, suffix="-pub")

    # If nothing matched, still create a valid PDF with 0 pages? Many tools dislike that.
    # We'll only save if at least one page was written; otherwise we skip and report.
    if pages_written > 0:
        out.save(output_pdf, garbage=4, deflate=True)
    out.close()
    src.close()

    return output_pdf, pages_written, total_highlights


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Extract pages containing any of the given text fragments and highlight matches in yellow."
    )
    p.add_argument(
        "inputs",
        nargs="+",
        help="Input PDF files (one or more).",
    )
    p.add_argument(
        "-t",
        "--text",
        nargs="+",
        required=True,
        help="Text fragments to search for (one or more). Use quotes for fragments with spaces.",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Make searches case-sensitive (default: case-insensitive if supported).",
    )
    p.add_argument(
        "--whole-words",
        action="store_true",
        help="Try to match whole words only (best-effort, depends on PyMuPDF flags support).",
    )
    args = p.parse_args(argv)

    fragments = args.text
    any_errors = False

    for pdf in args.inputs:
        try:
            out_pdf, pages_written, highlights = process_pdf(
                pdf,
                fragments,
                case_sensitive=args.case_sensitive,
                whole_words=args.whole_words,
            )
            if pages_written == 0:
                print(f"[{pdf}] No matches found. No output created.")
            else:
                print(f"[{pdf}] -> {out_pdf} | pages: {pages_written} | highlights: {highlights}")
        except Exception as e:
            any_errors = True
            print(f"[{pdf}] ERROR: {e}", file=sys.stderr)

    return 1 if any_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

