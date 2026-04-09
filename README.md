# AI Invoice Processor

A Streamlit app for extracting text from invoices and documents using OCR and AI extraction.

## Overview

This project reads PDF and image files, extracts text, and saves parsed invoice data in a local SQLite database and Excel file.

## Features

- Upload PDF and image files (`jpg`, `jpeg`, `png`, `bmp`, `pdf`)
- Extract text using OCR
- Parse invoice fields with AI extraction
- Save results to SQLite and Excel
- Dashboard and history views

## Requirements

- Python 3.10+ recommended
- Tesseract OCR installed on the host machine
- Optional: Poppler if you want full `pdf2image` support for older PDF workflows

## Python dependencies

Install dependencies in a virtual environment:

```bash
python -m venv venv
venv\Scripts\Activate.ps1  # PowerShell
# or venv\Scripts\activate.bat for CMD
pip install --upgrade pip
pip install -r requirements.txt
```

## Required external tools

### Tesseract OCR

This app uses `pytesseract` for OCR, so Tesseract must be installed and available in PATH.

- Windows: install from https://github.com/tesseract-ocr/tesseract/releases
- Linux/macOS: install via package manager

Verify installation:

```bash
tesseract --version
```

### Poppler (optional)

The app attempts to use `PyMuPDF` for PDF processing. If you run into PDF conversion issues, install Poppler:

- Windows: install Poppler and add `poppler/bin` to PATH
- Linux: `sudo apt install poppler-utils`

## Run the app

```bash
streamlit run app.py
```

## Output files

- `documents.xlsx` is created in the project root
- `outputs/` directory is used for generated output files
- SQLite DB is stored in a temp folder via `tempfile.gettempdir()`

## Notes

- Make sure the environment has access to Tesseract.
- If OCR fails, try using a clearer scan or image.
- The app is designed for English UI and invoice processing.

## Suggested next steps for production

- Improve error handling and notifications for missing external tools
- Add tests for data extraction and file handling
- Add a `requirements.lock` or pinned dependency file for stability

## Lock file

A pinned dependency file is included:

- `requirements.lock`

Install from it if you want an exact environment match:

```bash
pip install -r requirements.lock
```

## Docker support

A `Dockerfile` is included for containerized deployment.

Build the container:

```bash
docker build -t ai-invoice-processor .
```

Run it locally:

```bash
docker run -p 8501:8501 ai-invoice-processor
```

Then open:

```text
http://localhost:8501
```
