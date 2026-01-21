#!/usr/bin/env bash
set -euo pipefail

# --- CONFIG ---
PY_SCRIPT="pdf_pub_highlight.py"
TEXT_FRAGMENT1=""  # EYEFUL-UAH
TEXT_FRAGMENT2=""  # EYEFUL-URJC
TEXT_FRAGMENT3=""  # EYEFUL
TEXT_FRAGMENT4="PID2020-113118RB-C31/C33"
TEXT_FRAGMENT5="PID2020-113118RB-C31"
TEXT_FRAGMENT6="PID2020-113118RB-C33"
TEXT_FRAGMENT7="MCIN/AEI/10.13039/501100011033"
TEXT_FRAGMENT8="MCINN/AEI/10.13039/501100011033"
TEXT_FRAGMENT9="MICINN/AEI/10.13039/501100011033"
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
  python "$PY_SCRIPT" -t "$TEXT_FRAGMENT1" "$TEXT_FRAGMENT2" "$TEXT_FRAGMENT3" "$TEXT_FRAGMENT4" "$TEXT_FRAGMENT5" "$TEXT_FRAGMENT6" "$TEXT_FRAGMENT7" "$TEXT_FRAGMENT8" "$TEXT_FRAGMENT9" -- "$pdf"
done

