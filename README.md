# PDF Publisher Pages Extractor + Highlighter

This repository contains a small command-line toolset to **prepare “publication-ready” PDF subsets** from one or more input PDFs where the requirement is to contain only pages with given text fragments.

Given a list of **text fragments**, the tool:

- Scans each PDF
- Detects pages where **any fragment appears**
- Creates a new output PDF called: `<original-file>-pub.pdf`

- The output contains:
  - **(Optionally) the first page always**
  - **Only the pages where matches are found**
- Every match is **highlighted in yellow** (PDF highlight annotation)

It is especially useful for quickly producing “public” versions of documents by keeping only the pages that contain required **funding acknowledgements**, **grant codes**, or **institutional boilerplate**. In my case this was to support the generation of justification documents that show proper publicity of funding sources.



## Contents

- `pdf_pub_highlight.py`  
  Main Python script that performs page selection and highlighting.

- `go.process-all.sh` (example)  
  A Bash helper script that runs the Python tool over multiple PDFs safely (including filenames with spaces).



## Requirements

- Python **3.9+** (recommended)
- [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`)

Install dependencies:

```bash
python -m pip install pymupdf
```



## Usage (Python)

+ Basic usage:

```bash
python pdf_pub_highlight.py -t "Towards" myfile.pdf
```

+ Multiple PDFs:

```bash
python pdf_pub_highlight.py -t "Towards" file1.pdf file2.pdf
```

+ Multiple text fragments:

```bash
python pdf_pub_highlight.py -t "grant code" "MCIN/AEI/10.13039/501100011033" report.pdf
```



### Always include the first page

Sometimes you want the cover page / title page included even if it does not contain any matching text.

Use:

```bash
python pdf_pub_highlight.py --always-add-first-page -t "PID2020-113118RB-C31" myfile.pdf
```

This forces the output PDF to always contain page 1 (index 0).



## Output files

For each input PDF:

- Input: `art.pdf`

- Output: `art-pub.pdf`

If no fragments are found, **no output file is created** and you will see:

```
[art.pdf] No matches found. No output created.
```



## Bash helper script (batch processing)

Example script (provided by the user) to process multiple PDFs:

```bash
bash go.process-all.sh *.pdf
```

or using an absolute path (globs expanded by the shell):

```bash
bash go.process-all.sh /path/to/folder/*.pdf
```

If filenames with spaces exist in your list of files to process, my recommendation is to do:

``` bash
$ SAVEIFS=$IFS
$ IFS=$(echo -en "\n\b")
$
  ... do your processing ...
$ IFS=$SAVEIFS
```



## Notes and limitations

### 1. Scanned PDFs (no selectable text)

This tool searches **text content** inside the PDF.  
If the PDF is scanned images (no embedded text), it will not match anything unless you run OCR first.

### 2. Text split across lines

The script includes a fallback mechanism for cases where the fragment may span across line breaks or PDF word layout boundaries (using a word-stream search). This may be slower on some PDFs, but it greatly improves matching robustness.

### 3. Highlight appearance

Highlights are added as **PDF highlight annotations** (yellow, semi-transparent). Most PDF viewers show them as a yellow marker background.



## Repository workflow

Typical workflow:

1. Install dependencies  
   ```bash
   python -m pip install pymupdf
   ```

2. Run on a single file  
   ```bash
   python pdf_pub_highlight.py --always-add-first-page -t "MCIN/AEI/10.13039/501100011033" report.pdf
   ```

3. Run on many files  
   ```bash
   bash go.process-all.sh *.pdf
   ```


### IA usage

The `pdf_pub_highlight.py` and `go.process-all.sh` scripts and associated `README.md` have been generated and adapted from an original version by ChatGPT 5.2.


## License

This code is distributed under the GPL v3 license. 
