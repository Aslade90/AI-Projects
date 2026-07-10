# Cell Therapy CAR-T Manufacturing Reporting

Standalone HTML reporting assets for Gates manufacturing data.

## Contents

- `report/manufacturing_report.html` - self-contained generated report.
- `tools/build_html_report.py` - rebuilds the HTML report from the workbook's `Long Format` sheet.
- `tools/inspect_workbook.py` - helper script for inspecting workbook structure.

The report currently excludes QC-12 rows from the active graph set and excludes blank or day-zero values from live/viability trend charts.
