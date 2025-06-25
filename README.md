# PDF Tools

A lightweight collection of PDF-related utilities built with [FastMCP](https://github.com/Modular-ML/fastmcp). It exposes a handful of tools for reading, cropping and rasterising PDF files that can be called programmatically or through the FastMCP CLI.

## Features

- **read_pdf** – extract raw text from a PDF and (optionally) write it to disk
- **get_page_rect** – return a dictionary describing the common rectangle (size) of all pages
- **crop_pdf** – crop a rectangular area on a specific page and return the cropped markdown text
- **get_pdf_image** – convert a page to a Pillow `Image`
- **get_cropped_pdf_image** – convert a cropped region on a page to a Pillow `Image`

All heavy-lifting is delegated to [`pymupdf`](https://pymupdf.readthedocs.io/) (aka **fitz**) and [`pymupdf4llm`](https://github.com/linusboyle/pymupdf4llm).

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)

The exact dependency versions are pinned in `pyproject.toml` and `uv.lock`.

## Installation

```bash
# clone the repo
$ git clone https://github.com/Toyo-Keizai/mcp-pdf.git
$ cd mcp-pdf

# 1️⃣ create a virtual environment (optional but recommended)
$ uv venv
$ .venv/bin/activate # Powershell: .venv\Scripts\Activate.ps1

# 2️⃣ install Python dependencies
$ uv sync
```

## Debug / Test

```bash
# launch the FastMCP runtime
$ fastmcp dev main.py
```

## Make it avaiable to Claude

```bash
$ fastmcp install main.py
```

## License

This project is distributed under the **GNU Affero General Public License v3.0**. See `LICENSE` for full details.
