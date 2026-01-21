#!/usr/bin/env python3
"""
Create <file>-pub.pdf containing only pages where any given text fragment appears,
and highlight all matches in yellow.

Optionally, always include the first page.

Requires: PyMuPDF (pymupdf)
"""

from __future__ import annotations

import argparse
import os
import sys
import fitz  # PyMuPDF

import re
from bisect import bisect_right


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
        annot.set_colors(stroke=(1, 1, 0))  # Yellow
        annot.set_opacity(opacity)
        annot.update()
        count += 1
    return count


def _page_word_stream(page: fitz.Page, *, case_sensitive: bool):
    """
    Build a page-level word stream once:
      - words_sorted: words in reading order with their rects
      - text_cmp: linearized text used for searching (optionally lowercased)
      - starts: list of start char offsets per word in text_cmp
      - ends: list of end char offsets per word in text_cmp (exclusive)
    """
    words = page.get_text("words")
    if not words:
        return [], "", [], []

    # Reading order: block, line, word
    words.sort(key=lambda w: (w[5], w[6], w[7]))

    word_texts = [w[4] for w in words]

    # Build linear text and per-word spans (single space between words)
    pieces = []
    starts = []
    ends = []
    pos = 0
    for wt in word_texts:
        starts.append(pos)
        pieces.append(wt)
        pos += len(wt)
        ends.append(pos)
        pieces.append(" ")
        pos += 1

    linear = "".join(pieces).rstrip()
    # fix last trailing space bookkeeping: adjust last word end if we rstrip()
    if ends:
        # pos has included trailing space; rstrip removes it, so linear length is pos-1
        # ends[-1] already points to end of last word, so it's fine.
        pass

    if not case_sensitive:
        return words, linear.lower(), starts, ends
    return words, linear, starts, ends


def _find_fragment_rects_in_word_stream(
    words_sorted,
    text_cmp: str,
    starts: list[int],
    ends: list[int],
    fragment: str,
    *,
    case_sensitive: bool
) -> list[fitz.Rect]:
    """
    Find fragment inside the precomputed word-stream text_cmp and return rects for overlapping words.
    Uses bisect to map substring ranges -> word indices quickly.
    """
    if not fragment:
        return []

    frag_cmp = fragment if case_sensitive else fragment.lower()
    frag_cmp = re.sub(r"\s+", " ", frag_cmp.strip())  # normalize fragment whitespace

    rects: list[fitz.Rect] = []
    start = 0
    n = len(text_cmp)

    # Fast scan with str.find
    while True:
        idx = text_cmp.find(frag_cmp, start)
        if idx < 0:
            break
        match_start = idx
        match_end = idx + len(frag_cmp)

        # Find first word whose end > match_start
        i0 = bisect_right(ends, match_start)
        # Find last word whose start < match_end
        i1 = bisect_right(starts, match_end - 1) - 1

        if 0 <= i0 <= i1 < len(words_sorted):
            for i in range(i0, i1 + 1):
                x0, y0, x1, y1 = words_sorted[i][0], words_sorted[i][1], words_sorted[i][2], words_sorted[i][3]
                rects.append(fitz.Rect(x0, y0, x1, y1))

        start = idx + 1
        if start >= n:
            break

    return rects



def process_pdf(
    input_pdf: str,
    fragments: list[str],
    *,
    case_sensitive: bool,
    whole_words: bool,
    always_add_first_page: bool,
    include_all_pages: bool,  # <-- NEW
) -> tuple[str, int, int]:
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
    added_pages: set[int] = set()

    # --- NEW: include all pages up-front if requested
    if include_all_pages and src.page_count > 0:
        out.insert_pdf(src)  # copy all pages
        added_pages = set(range(src.page_count))
        pages_written = src.page_count

    # Optionally add first page (page_index = 0) with no highlights
    if (not include_all_pages) and always_add_first_page and src.page_count > 0:
        out.insert_pdf(src, from_page=0, to_page=0)
        added_pages.add(0)
        pages_written += 1

    # Iterate pages, collect matches, copy matching pages to output, apply highlights there
    for page_index in range(src.page_count):
        page = src.load_page(page_index)

        if 0:
            page_rects: list[fitz.Rect] = []
            for frag in fragments:
                # Find all occurrences of fragment on this page
                rects = page.search_for(frag, flags=flags)
                if rects:
                    page_rects.extend(rects)
        else:
            page_rects: list[fitz.Rect] = []

            # Build the word-stream only if we need the fallback on this page
            word_stream_built = False
            words_sorted = []
            text_cmp = ""
            starts = []
            ends = []

            for frag in fragments:
                # 1) Fast path: normal search
                rects = page.search_for(frag, flags=flags)

                # 2) Slow fallback only if needed:
                #    - native search didn't find anything
                #    - fragment likely spans lines/spaces/hyphenation
                if not rects and (" " in frag or "\t" in frag or "-" in frag):
                    if not word_stream_built:
                        words_sorted, text_cmp, starts, ends = _page_word_stream(
                        page,
                        case_sensitive=case_sensitive
                        )
                        word_stream_built = True

                    if text_cmp:
                        rects = _find_fragment_rects_in_word_stream(
                        words_sorted,
                        text_cmp,
                        starts,
                        ends,
                        frag,
                        case_sensitive=case_sensitive
                        )

                if rects:
                    page_rects.extend(rects)

        if page_rects:
            if page_index in added_pages:
                # Already included (e.g., first page, or include-all-pages). Just add highlights onto the existing output page.
                if include_all_pages:
                    out_page = out.load_page(page_index)  # <-- NEW: direct mapping in include-all-pages mode
                else:
                    out_page_index = list(sorted(added_pages)).index(page_index)
                    out_page = out.load_page(out_page_index)
            else:
                out.insert_pdf(src, from_page=page_index, to_page=page_index)
                added_pages.add(page_index)
                out_page = out.load_page(pages_written)
                pages_written += 1

            # Highlight matches on the copied page (same coordinates)
            total_highlights += highlight_rects_on_page(out_page, page_rects)

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
    p.add_argument(
        "--always-add-first-page",
        action="store_true",
        help="Always include the first page in the output PDF, even if it has no matches.",
    )
    p.add_argument(
        "--include-all-pages",
        action="store_true",
        help="Include all pages in the output PDF (still highlights matches).",
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
                always_add_first_page=args.always_add_first_page,
                include_all_pages=args.include_all_pages,
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

