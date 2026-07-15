# SharePoint Dashboard Version

## File To Upload

Upload this file to SharePoint:

```text
sharepoint/manufacturing_report_sharepoint.html
```

This is a static, self-contained dashboard copy. The data, logo, styles, and chart code are embedded in the HTML file.

## What Works In SharePoint

- Dashboard filters
- Interactive charts
- Hover labels
- Print / PDF output
- Embedded source data from the latest rebuild

## What Is Disabled

The local `Refresh Data` button is removed from the SharePoint version because SharePoint cannot run the local rebuild server or read the Excel workbook from your desktop.

To update the SharePoint dashboard after spreadsheet changes:

1. Update the workbook in `Input/Codex Manufacturing Data v1.2.xlsx`.
2. Run the local dashboard refresh or rebuild the report.
3. Upload the updated `sharepoint/manufacturing_report_sharepoint.html` file to SharePoint again.

## Sharing

After upload, use SharePoint's normal **Copy link** or **Share** option. The link will be controlled by your organization's SharePoint permissions rather than pointing back to GitHub.
