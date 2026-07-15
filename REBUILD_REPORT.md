# Rebuilding the Manufacturing Report

This report is a static HTML file. It does not read the Excel workbook every time the HTML address is opened. Instead, the builder script reads the spreadsheet and embeds a fresh data snapshot into the HTML file.

## Files

- Source spreadsheet: `C:\Users\sladeand\Desktop\Reporting Apps\GBF\CT In-Process Manufacturing Dashboard\Input\Codex Manufacturing Data v1.2.xlsx`
- Report builder: `C:\Users\sladeand\Desktop\Reporting Apps\GBF\CT In-Process Manufacturing Dashboard\tools\build_html_report.py`
- Generated report: `C:\Users\sladeand\Desktop\Reporting Apps\GBF\CT In-Process Manufacturing Dashboard\report\manufacturing_report.html`

## Rebuild Workflow

### Option A: Refresh From the Dashboard

1. Start the local report server by double-clicking:

   ```text
   C:\Users\sladeand\Desktop\Reporting Apps\GBF\CT In-Process Manufacturing Dashboard\Start Report Server.cmd
   ```

2. Open the report at:

   ```text
   http://127.0.0.1:8765/report/manufacturing_report.html
   ```

   You can also open `Open Manufacturing Report.url` after the server is running.

3. Update and save the spreadsheet:

   ```text
   C:\Users\sladeand\Desktop\Reporting Apps\GBF\CT In-Process Manufacturing Dashboard\Input\Codex Manufacturing Data v1.2.xlsx
   ```

4. In the dashboard, click `Refresh Data`.

The button first syncs populated batch-sheet rows into `Long Format`, then rebuilds `report\manufacturing_report.html` from `Long Format`, then reloads the dashboard.

### Option B: Manual Rebuild

1. Update the spreadsheet.

   Make changes in:

   ```text
   C:\Users\sladeand\Desktop\Reporting Apps\GBF\CT In-Process Manufacturing Dashboard\Input\Codex Manufacturing Data v1.2.xlsx
   ```

2. Save and close, or at least save, the spreadsheet.

3. Open PowerShell in the project folder:

   ```powershell
   cd 'C:\Users\sladeand\Desktop\Reporting Apps\GBF\CT In-Process Manufacturing Dashboard'
   ```

4. Sync the batch sheets into `Long Format`:

   ```powershell
   & 'C:\Users\sladeand\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools\sync_batch_sheets_to_long_format.py
   ```

5. Run the builder:

   ```powershell
   & 'C:\Users\sladeand\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools\build_html_report.py
   ```

6. Refresh the report in the browser.

   Report address:

   ```text
   http://127.0.0.1:8765/report/manufacturing_report.html
   ```

## What Updates

Running the builder replaces `report\manufacturing_report.html` with a fresh version based on the current spreadsheet data.

The sync script finds batch-entry sheets by looking for the expected headers: `Batch`, `Day`, `Category`, `Measurement Type`, `Value`, and `Construct`. It skips `Long Format`, `New Batch Entry Template`, and `Specs`. It only syncs rows with a value in column E, updates existing `Batch` + `Measurement Type` combinations, adds new combinations, and skips duplicates automatically.

The report reads from the `Long Format` sheet. The current graph set excludes QC-12 rows, and the live/viability line charts exclude day-zero data.

## Saving Versions

After a rebuild looks correct, save the project to GitHub so there is a version to return to later.

In Codex, ask:

```text
save this to github
```
