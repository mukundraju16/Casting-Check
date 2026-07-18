# Casting Check - Financial Decimal Validation Tool

Production-grade Python tool for identifying:
- **Decimal casting differences** (incorrect subtotal/total arithmetic)
- **Decimal rounding differences** (small differences within configurable tolerance)

Supports **Excel (.xlsx, .xls)** and **PDF** statements (text-based + scanned OCR fallback), and provides a **Streamlit UI**.

## Project structure

- `casting_check/file_loader.py` - input dispatch for Excel/PDF
- `casting_check/excel_processor.py` - read all Excel sheets, detect tables
- `casting_check/pdf_extractor.py` - Camelot primary, pdfplumber fallback, OCR fallback
- `casting_check/data_cleaner.py` - cleaning numbers, empty rows/columns, header normalization
- `casting_check/validator.py` - casting checks, rounding checks, classification
- `casting_check/report_generator.py` - summary + detailed Excel report with highlighting
- `app.py` - Streamlit app

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### System dependencies (PDF/OCR)

For full PDF support install:
- `ghostscript` (Camelot)
- `tesseract-ocr` (OCR)
- `poppler-utils` (pdf2image)

## Run app

```bash
streamlit run app.py
```

## How validation works

1. Detect candidate tables in sheets/pages.
2. Clean number formats (commas, bracket negatives, OCR symbols).
3. Detect total rows using keywords:
   - `Total`, `Subtotal`, `Grand Total`, `Net Total`
4. Recompute numeric-column totals from line items.
5. Compare reported vs computed totals and classify:
   - `OK`
   - `Decimal Rounding Difference`
   - `Casting Error`

Default tolerance is `0.01` and configurable in UI.

## Output

Generated Excel report includes:
- **Sheet 1: Summary Report**
- **Sheet 2+: Detail_N** with original data + computed fields (`computed_total`, `difference`, `status`)

Highlighting:
- **Casting Error** = red
- **Decimal Rounding Difference** = yellow

## Example test files

A helper script generates a sample Excel file:

```bash
python examples/generate_sample_files.py
```

This creates `examples/sample_statement.xlsx` with deliberate rounding/casting differences.

## Notes

- PDF annotation is marked optional and not implemented in this baseline.
- OCR extraction is heuristic and may need document-specific tuning.
