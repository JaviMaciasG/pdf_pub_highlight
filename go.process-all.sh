#!/usr/bin/env bash
set -euo pipefail

# --- CONFIG ---
PY_SCRIPT="pdf_pub_highlight.py"
TEXT_FRAGMENT01="PID2020-113118RB-C31/C33"
TEXT_FRAGMENT02="PID2020-113118RB-C31"
TEXT_FRAGMENT03="PID2020-113118RB-C33"
TEXT_FRAGMENT04="MCIN/AEI/10.13039/501100011033"
TEXT_FRAGMENT05="MCINN/AEI/10.13039/501100011033"
TEXT_FRAGMENT06="MICINN/AEI/10.13039/501100011033"
TEXT_FRAGMENT07="MICINN/AEI/10. 13039/501100011033"
TEXT_FRAGMENT08="Spanish Ministry of Science and Innovation"
TEXT_FRAGMENT09=""
TEXT_FRAGMENT10=""
TEXT_FRAGMENT11=""
TEXT_FRAGMENT12=""
TEXT_FRAGMENT13=""

# --- HELP ---
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <pdf1> [pdf2 ...]"
  echo "Example:"
  echo "  $0 \"My Paper.pdf\" other.pdf"
  exit 1
fi

# --- PROCESS EACH PDF ARGUMENT SAFELY (supports spaces) ---
for pdf in "$@"; do
  if [[ ! -f "$pdf" ]]; then
    echo "ERROR: file not found: $pdf" >&2
    continue
  else
    echo "---------------------------------------------------------------------------"
    echo "Processing file [$pdf]"
  fi

  if [[ "${pdf,,}" != *.pdf ]]; then
    echo "Skipping (not a PDF): $pdf"
    continue
  fi

  echo "Processing: $pdf"
  python "$PY_SCRIPT" --always-add-first-page -t "$TEXT_FRAGMENT01" "$TEXT_FRAGMENT02" "$TEXT_FRAGMENT03" "$TEXT_FRAGMENT04" "$TEXT_FRAGMENT05" "$TEXT_FRAGMENT06" "$TEXT_FRAGMENT07" "$TEXT_FRAGMENT08" "$TEXT_FRAGMENT09" "$TEXT_FRAGMENT10" "$TEXT_FRAGMENT11" "$TEXT_FRAGMENT12" "$TEXT_FRAGMENT13" -- "$pdf"
done

