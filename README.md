# PDF Stamper

Lightweight tools to place handwritten-style **initials on every page** and **full signatures on specific pages** of a PDF. Includes a no-frills Qt GUI and a CLI script.

## Requirements
- Python 3
- PyMuPDF (`python3-fitz`) for PDF/image stamping
- PyQt5 for the GUI

Install on Debian/Ubuntu:
```bash
sudo apt-get install -y python3-fitz python3-pyqt5
```

## Files

### `stamp_pdf.py` — CLI stamper
Command-line script to stamp initials on all pages and optionally place a full signature at given coordinates (points).

**Positional args**
- `input_pdf` — source PDF
- `output_pdf` — destination PDF

**Options**
- `--initials PATH` (required) — initials PNG
- `--initials-width FLOAT` — initials width in points (default 72)
- `--initials-margin FLOAT` — margin from page edges in points (default 12)
- `--signature PATH` — signature PNG
- `--signature-width FLOAT` — signature width in points (default 180)
- `--sig-page INT` — 0-based page for the signature
- `--sig-x FLOAT` / `--sig-y FLOAT` — left/top coordinates (points) for the signature
- `--fullsig XxY` — convenience for `--sig-x`/`--sig-y` (e.g. `548x300`)
- `--onpage INT` — 1-based page for the signature; defaults to last page if omitted

**Examples**
```bash
# Initials on all pages, no full signature
python3 stamp_pdf.py in.pdf out.pdf --initials initials.png

# Add a full signature on page 13 at (548,300) pts
python3 stamp_pdf.py in.pdf out.pdf --initials initials.png \
  --signature fullsig.png --fullsig 548x300 --onpage 13
```

### `stamp_gui.py` — Qt GUI stamper
Interactive viewer that lets you **open a PDF**, **add draggable boxes** for:
- **Initials (all pages):** place once; on save they’re applied to every page at the same relative spot/size.
- **Full signature (per-page):** add one or more boxes; each is tied to the page it was placed on and only shows on that page.
- **Other stamp (per-page):** e.g. a QR, watermark. Also page-specific.

It provides chevron navigation (≪ ‹ › ≫), live image previews inside boxes, and “Save as…” to write a stamped PDF. Window is tall by default and the PDF view fits to the page with aspect preserved.

**Run**
```bash
python3 stamp_gui.py
```

**Workflow**
1. **Open PDF** → choose your file.  
2. **Add initials (all pages)** → pick PNG → drag/size the box.  
3. **Add full signature** → pick PNG → on any page, add/drag/size one or more boxes (each stays on that page only).  
4. (Optional) **Add other stamp** similarly.  
5. **Save as…** → write stamped PDF.

**UI tips**
- Double-click a box to pick/replace its image.
- “Remove …” buttons delete all boxes of that type.
- Chevrons navigate; “Last page” (≫) is handy for end-page signing.

## Shell scripts

- `setup.sh` — installation/initial setup helper (not documented here; inspect script for details).  
- `stamp.sh` — wrapper script to run the CLI stamper (not documented here; inspect script for details).

## Licence
MIT 
