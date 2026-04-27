"""Generate sample test files for quick validation."""

from pathlib import Path

import pandas as pd


def main() -> None:
    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        {
            "Line Item": ["Revenue A", "Revenue B", "Subtotal", "Cost", "Grand Total"],
            "Amount": ["500.00", "499.98", "1000.00", "(250.00)", "749.99"],
        }
    )
    path = out_dir / "sample_statement.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Statement", index=False)

    print(f"Created {path}")


if __name__ == "__main__":
    main()
