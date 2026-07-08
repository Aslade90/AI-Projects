# Rebuilding the Manufacturing Report

This report is a static HTML file. It does not read the Excel workbook every time the HTML address is opened. Instead, the builder script reads the spreadsheet and embeds a fresh data snapshot into the HTML file.

## Files

- Source spreadsheet: `C:\Users\sladeand\Desktop\Codex Manufacturing Data.xlsx`
- Report builder: `C:\Users\sladeand\Desktop\Reporting Apps\Manufacturing Report Dashboard\tools\build_html_report.py`
- Generated report: `C:\Users\sladeand\Desktop\Reporting Apps\Manufacturing Report Dashboard\report\manufacturing_report.html`

## Rebuild Workflow

1. Update the spreadsheet.

   Make changes in:

   ```text
   C:\Users\sladeand\Desktop\Codex Manufacturing Data.xlsx
   ```

2. Save and close, or at least save, the spreadsheet.

3. Open PowerShell in the project folder:

   ```powershell
   cd 'C:\Users\sladeand\Desktop\Reporting Apps\Manufacturing Report Dashboard'
   ```

4. Run the builder:

   ```powershell
   & 'C:\Users\sladeand\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools\build_html_report.py
   ```

5. Refresh the report in the browser.

   Report address:

   ```text
   file:///C:/Users/sladeand/Desktop/Reporting%20Apps/Manufacturing%20Report%20Dashboard/report/manufacturing_report.html
   ```

## What Updates

Running the builder replaces `report\manufacturing_report.html` with a fresh version based on the current spreadsheet data.

The report reads from the `Long Format` sheet. The current graph set excludes QC-12 rows, and the live/viability line charts exclude day-zero data.

## Saving Versions

After a rebuild looks correct, save the project to GitHub so there is a version to return to later.

In Codex, ask:

```text
save this to github
```
