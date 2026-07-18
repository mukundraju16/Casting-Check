"""Streamlit app for financial casting and rounding validation."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import streamlit as st

from casting_check.file_loader import load_tables
from casting_check.report_generator import build_validation_results, generate_excel_report

st.set_page_config(page_title="Financial Validation Tool", layout="wide")
st.title("Financial Statement Decimal Validation")
st.caption("Detect decimal casting and rounding differences in Excel/PDF statements.")

uploaded_file = st.file_uploader("Upload financial statement", type=["xlsx", "xls", "pdf"])
tolerance = st.number_input("Rounding tolerance", min_value=0.0, value=0.01, step=0.01, format="%.4f")

if uploaded_file:
    suffix = Path(uploaded_file.name).suffix
    with TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / f"input{suffix}"
        input_path.write_bytes(uploaded_file.getbuffer())

        with st.spinner("Extracting tables and validating totals..."):
            tables = load_tables(str(input_path))
            details, summary = build_validation_results(tables, tolerance=tolerance)

        if not tables:
            st.warning("No tables detected. Please verify file quality (especially scanned PDFs).")
        else:
            st.success(f"Detected {len(tables)} table(s).")

            st.subheader("Summary Report")
            st.dataframe(summary, use_container_width=True)

            flagged = summary[summary["Status"].isin(["Casting Error", "Decimal Rounding Difference"])]
            if not flagged.empty:
                st.subheader("Flagged Errors")
                st.dataframe(flagged, use_container_width=True)

            st.subheader("Extracted Tables")
            for table, validated_df in details:
                with st.expander(f"{table.table_name} ({table.source_name})", expanded=False):
                    st.dataframe(validated_df, use_container_width=True)

            output_path = Path(tmpdir) / "validation_report.xlsx"
            generate_excel_report(str(output_path), tables, tolerance=tolerance)
            st.download_button(
                label="Download corrected Excel report",
                data=output_path.read_bytes(),
                file_name="validation_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.info("Optional PDF annotation is not yet implemented in this version.")
