from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


WORKBOOK = Path(r"C:\Users\sladeand\Desktop\Codex Manufacturing Data.xlsx")
LOGO = Path(r"C:\Users\sladeand\Desktop\Reporting App\v1.0\Logo.jpg")
OUTPUT = Path(r"C:\Users\sladeand\Documents\Gates Manufacturing Reporting\report\manufacturing_report.html")


PROJECTS = ["Z0121-02", "Z0121-03", "P1114-01", "P1114-02"]
CONSTRUCTS = ["CD19", "CD19x22"]
FLOW_PHASES = ["QC-4", "QC-5"]


def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value


def load_input_batch() -> str:
    try:
        input_df = pd.read_excel(WORKBOOK, sheet_name="input")
    except ValueError:
        return ""

    if input_df.empty:
        return ""

    preferred_columns = [
        column
        for column in input_df.columns
        if "batch" in str(column).lower() and "interest" in str(column).lower()
    ]
    columns = preferred_columns or list(input_df.columns)

    for column in columns:
        for value in input_df[column].dropna():
            text = str(value).strip()
            if text:
                return text
    return ""


def load_logo_data_url() -> str:
    data = LOGO.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def flow_metric_sort_key(metric: str) -> tuple[int, str]:
    order = [
        ("CD3+", 0),
        ("CD8+", 1),
        ("CD4+", 2),
    ]
    for marker, rank in order:
        if marker in metric:
            return rank, metric
    return len(order), metric


def build_payload() -> dict:
    long_df = pd.read_excel(WORKBOOK, sheet_name="Long Format")
    required = ["Batch", "Day", "Category", "Measurement Type", "Value", "Construct"]
    missing = [column for column in required if column not in long_df.columns]
    if missing:
        raise ValueError(f"Missing required Long Format columns: {', '.join(missing)}")

    long_df = long_df[required].copy()
    long_df["Batch"] = long_df["Batch"].astype(str).str.strip()
    long_df["Project"] = long_df["Batch"].str.extract(r"^([A-Z]\d{4}-\d{2})")
    long_df["Day"] = pd.to_numeric(long_df["Day"], errors="coerce")
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    long_df = long_df.dropna(subset=["Batch", "Project", "Value", "Construct", "Category", "Measurement Type"])
    long_df = long_df[~long_df["Measurement Type"].astype(str).str.contains("QC-12", regex=False, na=False)]
    long_df = long_df[long_df["Project"].isin(PROJECTS)]
    long_df = long_df[long_df["Construct"].isin(CONSTRUCTS)]

    rows = []
    for row in long_df.to_dict("records"):
        rows.append(
            {
                "batch": clean_value(row["Batch"]),
                "project": clean_value(row["Project"]),
                "day": None if pd.isna(row["Day"]) else float(row["Day"]),
                "category": clean_value(row["Category"]),
                "type": clean_value(row["Measurement Type"]),
                "value": float(row["Value"]),
                "construct": clean_value(row["Construct"]),
            }
        )

    flow_metrics = {}
    for phase in FLOW_PHASES:
        metrics = sorted(
            {
                row["type"]
                for row in rows
                if row["category"] == "Additional Assays" and phase in row["type"]
            },
            key=flow_metric_sort_key,
        )
        flow_metrics[phase] = metrics

    return {
        "sourceWorkbook": str(WORKBOOK),
        "inputSheet": "input",
        "inputBatch": load_input_batch(),
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "projects": PROJECTS,
        "constructs": CONSTRUCTS,
        "rows": rows,
        "flowMetrics": flow_metrics,
    }


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gates Manufacturing Report</title>
  <style>
    :root {
      --cu-black: #000000;
      --cu-gold: #cfb87c;
      --cu-gold-dark: #9c7b35;
      --cu-light-gray: #bcbcbc;
      --cu-dark-gray: #434343;
      --surface: #ffffff;
      --canvas: #f6f5f2;
      --ink-soft: #5d5d5d;
      --line: #d7d3c8;
      --success: #28745f;
      --warning: #8a5d00;
      --band-1: rgba(207, 184, 124, 0.26);
      --band-2: rgba(207, 184, 124, 0.26);
      --band-3: rgba(207, 184, 124, 0.26);
      font-family: Inter, Segoe UI, Roboto, Arial, sans-serif;
      color: var(--cu-black);
      background: var(--canvas);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background:
        linear-gradient(180deg, #ffffff 0, #ffffff 172px, var(--canvas) 172px);
      min-width: 320px;
    }

    .page {
      width: min(1440px, calc(100% - 32px));
      margin: 0 auto;
      padding: 22px 0 48px;
    }

    header {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 28px;
      align-items: start;
      padding: 12px 0 34px;
      border-bottom: 4px solid var(--cu-black);
      background: #ffffff;
    }

    h1 {
      margin: 0 0 8px;
      font-size: clamp(26px, 3.2vw, 44px);
      line-height: 1.05;
      letter-spacing: 0;
    }

    .subtitle {
      max-width: 780px;
      margin: 0;
      color: var(--cu-dark-gray);
      font-size: 15px;
      line-height: 1.55;
    }

    .logo {
      width: min(240px, 26vw);
      max-height: 120px;
      object-fit: contain;
      align-self: start;
      margin-top: -8px;
    }

    .toolbar {
      position: sticky;
      top: 0;
      z-index: 10;
      margin: 18px 0;
      padding: 14px;
      display: grid;
      grid-template-columns: repeat(3, minmax(180px, 1fr)) auto;
      gap: 12px;
      align-items: end;
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.07);
      backdrop-filter: blur(10px);
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--cu-dark-gray);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .04em;
    }

    select {
      width: 100%;
      appearance: none;
      border: 1px solid #9f9b90;
      border-radius: 6px;
      background:
        linear-gradient(45deg, transparent 50%, var(--cu-black) 50%) calc(100% - 17px) 52% / 7px 7px no-repeat,
        linear-gradient(135deg, var(--cu-black) 50%, transparent 50%) calc(100% - 12px) 52% / 7px 7px no-repeat,
        #ffffff;
      color: var(--cu-black);
      font: inherit;
      font-size: 14px;
      padding: 10px 34px 10px 10px;
      min-height: 42px;
    }

    .print-button {
      border: 0;
      border-radius: 6px;
      background: var(--cu-black);
      color: #ffffff;
      font-weight: 800;
      min-height: 42px;
      padding: 0 18px;
      cursor: pointer;
    }

    .print-button:hover { background: #252525; }

    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 18px 0 26px;
    }

    .kpi,
    .panel,
    .note-panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
    }

    .kpi {
      padding: 16px;
      min-height: 104px;
      border-top: 5px solid var(--cu-gold);
    }

    .kpi-title {
      color: var(--cu-dark-gray);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .04em;
      text-transform: uppercase;
    }

    .kpi-value {
      margin-top: 10px;
      font-size: clamp(23px, 2.6vw, 34px);
      font-weight: 850;
      line-height: 1;
    }

    .kpi-foot {
      margin-top: 8px;
      color: var(--ink-soft);
      font-size: 13px;
      line-height: 1.35;
    }

    section {
      margin-top: 26px;
    }

    .section-head {
      display: flex;
      gap: 18px;
      justify-content: space-between;
      align-items: end;
      margin: 0 0 12px;
    }

    h2 {
      margin: 0;
      font-size: clamp(21px, 2.2vw, 30px);
      line-height: 1.15;
      letter-spacing: 0;
    }

    .section-note {
      max-width: 680px;
      margin: 0;
      color: var(--cu-dark-gray);
      font-size: 13px;
      line-height: 1.45;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }

    .panel {
      min-width: 0;
      padding: 16px;
    }

    .panel-head {
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
      margin-bottom: 10px;
    }

    .line-head {
      grid-template-columns: 1fr minmax(160px, 220px);
      align-items: end;
    }

    .flow-head {
      grid-template-columns: 1fr minmax(190px, 280px) minmax(160px, 220px);
      align-items: end;
    }

    h3 {
      margin: 0;
      font-size: 17px;
      line-height: 1.25;
      letter-spacing: 0;
    }

    .chart-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
      color: var(--cu-dark-gray);
      font-size: 12px;
      line-height: 1.35;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 9px;
      background: #faf9f6;
    }

    .chart {
      width: 100%;
      min-height: 390px;
      overflow: hidden;
    }

    svg {
      display: block;
      width: 100%;
      height: auto;
      overflow: visible;
    }

    .axis text,
    .tick-label {
      fill: var(--cu-dark-gray);
      font-size: 11px;
    }

    .axis-title {
      fill: var(--cu-dark-gray);
      font-size: 12px;
      font-weight: 800;
    }

    .grid-line {
      stroke: #e8e4db;
      stroke-width: 1;
    }

    .axis-line {
      stroke: #9f9b90;
      stroke-width: 1;
    }

    .historical-line {
      fill: none;
      stroke: #9b9b9b;
      stroke-width: 1.25;
      stroke-opacity: .46;
    }

    .average-line {
      fill: none;
      stroke: var(--cu-gold-dark);
      stroke-width: 3;
    }

    .selected-line {
      fill: none;
      stroke: var(--cu-black);
      stroke-width: 3.4;
    }

    .sd-line {
      fill: none;
      stroke: var(--cu-dark-gray);
      stroke-width: 1.15;
      stroke-dasharray: 5 5;
      stroke-opacity: .66;
    }

    .sd-label {
      fill: var(--cu-dark-gray);
      font-size: 10px;
      font-weight: 700;
    }

    .hist-bar { fill: #cfcfcf; }
    .selected-bar { fill: var(--cu-black); }

    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 10px 16px;
      margin: 12px 0 0;
      color: var(--cu-dark-gray);
      font-size: 12px;
    }

    .legend-item {
      display: inline-flex;
      align-items: center;
      gap: 7px;
    }

    .swatch {
      width: 22px;
      height: 3px;
      background: var(--cu-black);
      display: inline-block;
    }

    .swatch.gold { background: var(--cu-gold-dark); }
    .swatch.gray { background: #9b9b9b; opacity: .55; }
    .swatch.dotted {
      background: repeating-linear-gradient(90deg, var(--cu-dark-gray) 0 5px, transparent 5px 10px);
    }
    .swatch.band {
      height: 10px;
      background: var(--band-1);
      border: 1px solid rgba(156, 123, 53, .2);
    }

    .note-panel {
      margin-top: 16px;
      padding: 16px;
      color: var(--cu-dark-gray);
      line-height: 1.55;
      font-size: 14px;
    }

    .note-panel strong { color: var(--cu-black); }

    .empty-state {
      min-height: 280px;
      display: grid;
      place-items: center;
      padding: 22px;
      color: var(--cu-dark-gray);
      text-align: center;
      border: 1px dashed var(--cu-light-gray);
      border-radius: 8px;
      background: #fbfaf7;
    }

    footer {
      margin-top: 28px;
      color: var(--cu-dark-gray);
      font-size: 12px;
      line-height: 1.5;
      border-top: 1px solid var(--line);
      padding-top: 14px;
    }

    @media (max-width: 1050px) {
      .grid-2,
      .grid-3,
      .summary {
        grid-template-columns: 1fr;
      }

      .toolbar {
        grid-template-columns: 1fr 1fr;
      }

      .print-button {
        grid-column: 1 / -1;
      }
    }

    @media (max-width: 700px) {
      .page { width: min(100% - 20px, 1440px); }

      header {
        grid-template-columns: 1fr;
      }

      .logo {
        width: min(220px, 70vw);
        margin-top: 0;
      }

      .toolbar,
      .line-head,
      .flow-head {
        grid-template-columns: 1fr;
      }

      .section-head {
        display: grid;
      }
    }

    @media print {
      body { background: #ffffff; }
      .toolbar, .print-button { display: none; }
      .page { width: 100%; padding: 0; }
      .panel, .kpi, .note-panel { break-inside: avoid; }
      .chart { min-height: 300px; }
    }
  </style>
</head>
<body>
  <div class="page">
    <header>
      <div>
        <h1>Gates Manufacturing Report</h1>
        <p class="subtitle">Cell concentration, viability, and flow assay monitoring from the workbook's Long Format sheet. QC-12 rows are excluded from the current graph set. Historical averages and standard-deviation ranges exclude the selected batch when a batch is indicated in the input sheet.</p>
      </div>
      <img class="logo" src="__LOGO_DATA_URL__" alt="University of Colorado Anschutz Gates Biomanufacturing Facility logo">
    </header>

    <div class="toolbar" aria-label="Report filters">
      <label for="constructSelect">Construct
        <select id="constructSelect"></select>
      </label>
      <label for="projectSelect">Project
        <select id="projectSelect"></select>
      </label>
      <label for="batchSelect">Batch of interest
        <select id="batchSelect"></select>
      </label>
      <button class="print-button" type="button" onclick="window.print()">Print / PDF</button>
    </div>

    <div class="summary" aria-label="Current report summary">
      <div class="kpi">
        <div class="kpi-title">Selected Batch</div>
        <div class="kpi-value" id="kpiBatch">-</div>
        <div class="kpi-foot" id="kpiBatchFoot">From input sheet</div>
      </div>
      <div class="kpi">
        <div class="kpi-title">Historical Batches</div>
        <div class="kpi-value" id="kpiHistorical">-</div>
        <div class="kpi-foot">Filtered project and construct, selected batch excluded</div>
      </div>
      <div class="kpi">
        <div class="kpi-title">Live Data Points</div>
        <div class="kpi-value" id="kpiLive">-</div>
        <div class="kpi-foot">Rows used in the live concentration view</div>
      </div>
      <div class="kpi">
        <div class="kpi-title">Viability Data Points</div>
        <div class="kpi-value" id="kpiViability">-</div>
        <div class="kpi-foot">Rows used in the viability view</div>
      </div>
    </div>

    <section aria-labelledby="cellSection">
      <div class="section-head">
        <h2 id="cellSection">Cell Concentration and Viability Data</h2>
      </div>
      <p class="section-note">Gray lines show historical batches. The black line highlights the selected batch. Gold shows the historical average. Each line chart has its own SD range control for the shaded standard-deviation range and matching dotted limits.</p>
      <div class="grid-2">
        <article class="panel">
          <div class="panel-head line-head">
            <div>
              <h3>Live Cell Concentration vs Day</h3>
              <div class="chart-meta" id="liveMeta"></div>
            </div>
            <label for="liveSdSelect">SD range
              <select id="liveSdSelect">
                <option value="0">+/- SD Off</option>
                <option value="1">+/- 1SD</option>
                <option value="2">+/- 2SD</option>
                <option value="3">+/- 3SD</option>
              </select>
            </label>
          </div>
          <div class="chart" id="liveChart"></div>
          <div class="legend" aria-label="Live concentration legend">
            <span class="legend-item"><span class="swatch gray"></span> Historical batches</span>
            <span class="legend-item"><span class="swatch"></span> Selected batch</span>
            <span class="legend-item"><span class="swatch gold"></span> Historical average</span>
            <span class="legend-item"><span class="swatch band"></span> SD range</span>
            <span class="legend-item"><span class="swatch dotted"></span> SD limit</span>
          </div>
        </article>

        <article class="panel">
          <div class="panel-head line-head">
            <div>
              <h3>Viability vs Day</h3>
              <div class="chart-meta" id="viabilityMeta"></div>
            </div>
            <label for="viabilitySdSelect">SD range
              <select id="viabilitySdSelect">
                <option value="0">+/- SD Off</option>
                <option value="1">+/- 1SD</option>
                <option value="2">+/- 2SD</option>
                <option value="3">+/- 3SD</option>
              </select>
            </label>
          </div>
          <div class="chart" id="viabilityChart"></div>
          <div class="legend" aria-label="Viability legend">
            <span class="legend-item"><span class="swatch gray"></span> Historical batches</span>
            <span class="legend-item"><span class="swatch"></span> Selected batch</span>
            <span class="legend-item"><span class="swatch gold"></span> Historical average</span>
            <span class="legend-item"><span class="swatch band"></span> SD range</span>
            <span class="legend-item"><span class="swatch dotted"></span> SD limit</span>
          </div>
        </article>
      </div>
    </section>

    <section aria-labelledby="flowSection">
      <div class="section-head">
        <h2 id="flowSection">Flow Data</h2>
        <p class="section-note">Each chart shows historical batch bars for the selected QC-4 or QC-5 flow measure and the highlighted batch when available. A labeled gold line marks the historical average. Each flow chart has its own SD range control for the dotted horizontal references around that average.</p>
      </div>
      <div class="grid-3">
        <article class="panel">
          <div class="panel-head flow-head">
            <div>
              <h3>QC-4 Flow</h3>
              <div class="chart-meta" id="qc4Meta"></div>
            </div>
            <label for="qc4Metric">Measure
              <select id="qc4Metric"></select>
            </label>
            <label for="qc4SdSelect">SD range
              <select id="qc4SdSelect">
                <option value="0">+/- SD Off</option>
                <option value="1">+/- 1SD</option>
                <option value="2">+/- 2SD</option>
                <option value="3">+/- 3SD</option>
              </select>
            </label>
          </div>
          <div class="chart" id="qc4Chart"></div>
        </article>

        <article class="panel">
          <div class="panel-head flow-head">
            <div>
              <h3>QC-5 Flow</h3>
              <div class="chart-meta" id="qc5Meta"></div>
            </div>
            <label for="qc5Metric">Measure
              <select id="qc5Metric"></select>
            </label>
            <label for="qc5SdSelect">SD range
              <select id="qc5SdSelect">
                <option value="0">+/- SD Off</option>
                <option value="1">+/- 1SD</option>
                <option value="2">+/- 2SD</option>
                <option value="3">+/- 3SD</option>
              </select>
            </label>
          </div>
          <div class="chart" id="qc5Chart"></div>
        </article>
      </div>
    </section>

    <div class="note-panel">
      <strong>Input sheet suggestion:</strong> the current one-cell input sheet works well for a single highlighted batch. If this report grows, a small inputs table with columns for batch of interest, default project, default construct, owner, and refresh date would make the report easier to audit and extend.
    </div>

    <footer>
      Source workbook: <span id="sourceWorkbook"></span><br>
      Generated: <span id="generatedAt"></span>. Standard-deviation lower limits below zero are omitted from the dotted reference lines and noted in each chart when applicable.
    </footer>
  </div>

  <script>
    const DATA = __DATA_JSON__;

    const els = {
      project: document.getElementById("projectSelect"),
      construct: document.getElementById("constructSelect"),
      batch: document.getElementById("batchSelect"),
      liveChart: document.getElementById("liveChart"),
      viabilityChart: document.getElementById("viabilityChart"),
      liveSd: document.getElementById("liveSdSelect"),
      viabilitySd: document.getElementById("viabilitySdSelect"),
      qc4Chart: document.getElementById("qc4Chart"),
      qc5Chart: document.getElementById("qc5Chart"),
      qc4Metric: document.getElementById("qc4Metric"),
      qc5Metric: document.getElementById("qc5Metric"),
      qc4Sd: document.getElementById("qc4SdSelect"),
      qc5Sd: document.getElementById("qc5SdSelect")
    };

    const fmtInt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
    const fmtShort = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
    const fmtPct = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 });
    const fmtNum = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

    function option(select, value, label = value) {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = label;
      select.appendChild(opt);
    }

    function orderedValues(values, preferredOrder = []) {
      const unique = [...new Set(values.filter(Boolean))];
      return unique.sort((a, b) => {
        const ai = preferredOrder.indexOf(a);
        const bi = preferredOrder.indexOf(b);
        if (ai !== -1 || bi !== -1) {
          if (ai === -1) return 1;
          if (bi === -1) return -1;
          return ai - bi;
        }
        return String(a).localeCompare(String(b), undefined, { numeric: true });
      });
    }

    function shortMetric(name) {
      return name
        .replace(" Additional Assays", "")
        .replace("CD19+/CD22+ CAR+", "CD19/CD22 CAR+")
        .replace("Target Flow ", "")
        .replace("Pre-Harvest Flow ", "Pre-Harvest ")
        .replace("Post Cryo ", "Post Cryo ");
    }

    function setupControls() {
      DATA.constructs.forEach(construct => option(els.construct, construct));

      const inputMatch = DATA.inputBatch ? DATA.rows.find(row => row.batch === DATA.inputBatch) : null;
      if (inputMatch) els.construct.value = inputMatch.construct;
      refreshProjectOptions(inputMatch?.project);
      refreshBatchOptions(inputMatch?.batch || DATA.inputBatch);
      refreshFlowMetricOptions();

      els.construct.addEventListener("change", () => {
        refreshProjectOptions();
        refreshBatchOptions();
        render();
      });
      els.project.addEventListener("change", () => {
        refreshBatchOptions();
        render();
      });
      [els.batch, els.liveSd, els.viabilitySd, els.qc4Metric, els.qc5Metric, els.qc4Sd, els.qc5Sd].forEach(control => {
        control.addEventListener("change", render);
      });

      document.getElementById("sourceWorkbook").textContent = DATA.sourceWorkbook;
      document.getElementById("generatedAt").textContent = DATA.generatedAt;
    }

    function refreshProjectOptions(preferredProject) {
      const prior = preferredProject || els.project.value;
      const projects = orderedValues(
        DATA.rows
          .filter(row => row.construct === els.construct.value)
          .map(row => row.project),
        DATA.projects
      );
      els.project.innerHTML = "";
      projects.forEach(project => option(els.project, project));
      if (projects.includes(prior)) {
        els.project.value = prior;
      } else if (projects.length) {
        els.project.value = projects[0];
      }
    }

    function refreshBatchOptions(preferredBatch) {
      const prior = preferredBatch || els.batch.value;
      const batches = orderedValues(
        DATA.rows
          .filter(row => row.construct === els.construct.value && row.project === els.project.value)
          .map(row => row.batch)
      );
      els.batch.innerHTML = "";
      option(els.batch, "", "No batch selected");
      batches.forEach(batch => option(els.batch, batch));
      if (batches.includes(prior)) {
        els.batch.value = prior;
      } else if (batches.length) {
        els.batch.value = batches[0];
      } else {
        els.batch.value = "";
      }
    }

    function refreshFlowMetricOptions() {
      for (const [phase, select] of [["QC-4", els.qc4Metric], ["QC-5", els.qc5Metric]]) {
        const prior = select.value;
        const valid = DATA.flowMetrics[phase].filter(metric => {
          return currentRows().some(row => row.type === metric);
        });
        select.innerHTML = "";
        valid.forEach(metric => option(select, metric, shortMetric(metric)));
        if (valid.includes(prior)) {
          select.value = prior;
        } else if (valid.length) {
          select.value = valid[0];
        }
      }
    }

    function currentRows() {
      return DATA.rows.filter(row => row.project === els.project.value && row.construct === els.construct.value);
    }

    function selectedBatch() {
      return els.batch.value || "";
    }

    function selectedLineSdMultiplier(select) {
      return Number(select.value);
    }

    function roundDay(day) {
      return Number.isInteger(day) ? String(day) : fmtNum.format(day);
    }

    function formatValue(value, unit) {
      if (!Number.isFinite(value)) return "-";
      if (unit === "percent") return fmtPct.format(value);
      if (Math.abs(value) >= 100000) return fmtShort.format(value);
      return fmtNum.format(value);
    }

    function exactValue(value, unit) {
      if (!Number.isFinite(value)) return "-";
      if (unit === "percent") return fmtPct.format(value);
      return fmtInt.format(value);
    }

    function mean(values) {
      const clean = values.filter(Number.isFinite);
      if (!clean.length) return NaN;
      return clean.reduce((sum, value) => sum + value, 0) / clean.length;
    }

    function sampleSd(values) {
      const clean = values.filter(Number.isFinite);
      if (clean.length < 2) return 0;
      const avg = mean(clean);
      const variance = clean.reduce((sum, value) => sum + Math.pow(value - avg, 2), 0) / (clean.length - 1);
      return Math.sqrt(variance);
    }

    function groupedMean(rows, keys) {
      const buckets = new Map();
      rows.forEach(row => {
        const key = keys.map(k => row[k]).join("|");
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(row.value);
      });
      return [...buckets.entries()].map(([key, values]) => {
        const parts = key.split("|");
        const item = { value: mean(values) };
        keys.forEach((name, index) => item[name] = name === "day" ? Number(parts[index]) : parts[index]);
        return item;
      });
    }

    function lineData(category) {
      const selected = selectedBatch();
      const rows = currentRows().filter(row => row.category === category && Number.isFinite(row.day) && row.day > 0);
      const pointRows = groupedMean(rows, ["batch", "day"]);
      const selectedPoints = selected ? pointRows.filter(row => row.batch === selected).sort((a, b) => a.day - b.day) : [];
      const histPoints = pointRows.filter(row => !selected || row.batch !== selected);
      const byBatch = new Map();
      histPoints.forEach(point => {
        if (!byBatch.has(point.batch)) byBatch.set(point.batch, []);
        byBatch.get(point.batch).push(point);
      });
      const historicalSeries = [...byBatch.entries()].map(([batch, points]) => ({
        batch,
        points: points.sort((a, b) => a.day - b.day)
      }));

      const byDay = new Map();
      histPoints.forEach(point => {
        if (!byDay.has(point.day)) byDay.set(point.day, []);
        byDay.get(point.day).push(point.value);
      });
      const stats = [...byDay.entries()].map(([day, values]) => {
        const avg = mean(values);
        const sd = sampleSd(values);
        return { day: Number(day), n: values.length, mean: avg, sd };
      }).sort((a, b) => a.day - b.day);

      return { rows, pointRows, selectedPoints, historicalSeries, stats };
    }

    function flowData(metric) {
      const selected = selectedBatch();
      const rows = currentRows().filter(row => row.type === metric);
      const byBatch = groupedMean(rows, ["batch"]).sort((a, b) => a.batch.localeCompare(b.batch));
      const hist = byBatch.filter(row => !selected || row.batch !== selected);
      const avg = mean(hist.map(row => row.value));
      const sd = sampleSd(hist.map(row => row.value));
      const bars = byBatch.map(row => ({ ...row, kind: row.batch === selected ? "selected" : "historical" }));
      return { rows, bars, hist, avg, sd, selectedBar: byBatch.find(row => row.batch === selected) };
    }

    function svgEl(tag, attrs = {}) {
      const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
      for (const [key, value] of Object.entries(attrs)) {
        if (value !== null && value !== undefined) el.setAttribute(key, value);
      }
      return el;
    }

    function pathFrom(points, x, y) {
      return points.map((point, index) => `${index ? "L" : "M"}${x(point.day).toFixed(2)},${y(point.value).toFixed(2)}`).join(" ");
    }

    function linePath(points, getValue, x, y, options = {}) {
      let path = "";
      let drawing = false;
      const skipBelowZero = Boolean(options.skipBelowZero);
      const maxValue = Number.isFinite(options.maxValue) ? options.maxValue : null;
      points.forEach(point => {
        const value = getValue(point);
        if (!Number.isFinite(value) || (skipBelowZero && value < 0) || (maxValue !== null && value > maxValue)) {
          drawing = false;
          return;
        }
        path += `${drawing ? "L" : "M"}${x(point.day).toFixed(2)},${y(Math.max(0, value)).toFixed(2)} `;
        drawing = true;
      });
      return path.trim();
    }

    function bandPath(stats, multiplier, x, y, options = {}) {
      const maxValue = Number.isFinite(options.maxValue) ? options.maxValue : null;
      const upper = stats
        .filter(point => Number.isFinite(point.mean))
        .map(point => {
          const value = point.mean + point.sd * multiplier;
          return { day: point.day, value: maxValue === null ? value : Math.min(maxValue, value) };
        });
      const lower = stats
        .filter(point => Number.isFinite(point.mean))
        .map(point => ({ day: point.day, value: Math.max(0, point.mean - point.sd * multiplier) }))
        .reverse();
      if (!upper.length || !lower.length) return "";
      return `${pathFrom(upper, x, y)} ${lower.map(point => `L${x(point.day).toFixed(2)},${y(point.value).toFixed(2)}`).join(" ")} Z`;
    }

    function renderEmpty(container, message) {
      container.innerHTML = `<div class="empty-state">${message}</div>`;
    }

    function renderLineChart(container, metaId, title, category, unit, sdSelect) {
      const { rows, selectedPoints, historicalSeries, stats } = lineData(category);
      const selected = selectedBatch();
      const sdMultiplier = selectedLineSdMultiplier(sdSelect);
      const showSd = sdMultiplier > 0;
      const maxDisplayValue = unit === "percent" ? 1 : null;
      const historicalCount = new Set(historicalSeries.map(series => series.batch)).size;
      const below = [];
      const above = [];
      if (showSd) {
        stats.forEach(point => {
          if (point.mean - point.sd * sdMultiplier < 0) below.push(`${sdMultiplier}SD day ${roundDay(point.day)}`);
          if (maxDisplayValue !== null && point.mean + point.sd * sdMultiplier > maxDisplayValue) {
            above.push(`${sdMultiplier}SD day ${roundDay(point.day)}`);
          }
        });
      }

      document.getElementById(metaId).innerHTML = [
        `<span class="pill">${rows.length} source rows</span>`,
        `<span class="pill">${historicalCount} historical batches</span>`,
        selected ? `<span class="pill">Highlighted ${selected}</span>` : `<span class="pill">No batch excluded</span>`,
        showSd
          ? (below.length ? `<span class="pill">${below.length} lower SD limits omitted below zero</span>` : `<span class="pill">No below-zero SD limits</span>`)
          : `<span class="pill">SD guides off</span>`,
        ...(showSd && maxDisplayValue !== null
          ? [above.length ? `<span class="pill">${above.length} upper SD limits omitted above 100%</span>` : `<span class="pill">No above-100% SD limits</span>`]
          : [])
      ].join("");

      if (!rows.length || (!historicalSeries.length && !selectedPoints.length)) {
        renderEmpty(container, `No ${title.toLowerCase()} data is available for the selected filters.`);
        return;
      }

      const width = 760;
      const height = 410;
      const margin = { top: 28, right: 32, bottom: 58, left: 74 };
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;

      const allDays = [...new Set([
        ...rows.map(row => row.day),
        ...stats.map(row => row.day)
      ])].sort((a, b) => a - b);
      const minDay = Math.min(...allDays);
      const maxDay = Math.max(...allDays);
      const upper3SdMax = Math.max(0, ...stats.map(point => point.mean + point.sd * 3).filter(Number.isFinite));
      const selectedMax = Math.max(0, ...selectedPoints.map(point => point.value).filter(Number.isFinite));
      const fallbackValueMax = Math.max(0, ...rows.map(row => row.value).filter(Number.isFinite));
      const axisMax = Math.max(upper3SdMax, selectedMax);
      const yMax = maxDisplayValue !== null ? maxDisplayValue : axisMax > 0 ? axisMax * 1.04 : fallbackValueMax > 0 ? fallbackValueMax * 1.04 : 1;
      const x = day => margin.left + ((day - minDay) / Math.max(1, maxDay - minDay)) * plotW;
      const y = value => {
        const bounded = Math.min(yMax, Math.max(0, value));
        return margin.top + plotH - (bounded / yMax) * plotH;
      };
      const yTicks = 5;

      const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": title });

      for (let i = 0; i <= yTicks; i++) {
        const value = (yMax / yTicks) * i;
        const yy = y(value);
        svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: yy, y2: yy, class: "grid-line" }));
        const label = svgEl("text", { x: margin.left - 10, y: yy + 4, "text-anchor": "end", class: "tick-label" });
        label.textContent = formatValue(value, unit);
        svg.appendChild(label);
      }

      allDays.forEach(day => {
        const xx = x(day);
        svg.appendChild(svgEl("line", { x1: xx, x2: xx, y1: margin.top, y2: height - margin.bottom, class: "grid-line", opacity: "0.35" }));
        const label = svgEl("text", { x: xx, y: height - margin.bottom + 25, "text-anchor": "middle", class: "tick-label" });
        label.textContent = roundDay(day);
        svg.appendChild(label);
      });

      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: height - margin.bottom, y2: height - margin.bottom, class: "axis-line" }));
      svg.appendChild(svgEl("line", { x1: margin.left, x2: margin.left, y1: margin.top, y2: height - margin.bottom, class: "axis-line" }));

      if (showSd) {
        const sdBand = bandPath(stats, sdMultiplier, x, y, { maxValue: maxDisplayValue });
        if (sdBand) svg.appendChild(svgEl("path", { d: sdBand, fill: `var(--band-${sdMultiplier})`, stroke: "none" }));
      }

      historicalSeries.forEach(series => {
        if (series.points.length < 2) return;
        const path = svgEl("path", { d: pathFrom(series.points, x, y), class: "historical-line" });
        path.appendChild(svgEl("title", {})).textContent = series.batch;
        svg.appendChild(path);
      });

      if (showSd) {
        const upper = linePath(stats, point => point.mean + point.sd * sdMultiplier, x, y, { maxValue: maxDisplayValue });
        if (upper) svg.appendChild(svgEl("path", { d: upper, class: "sd-line" }));
        const lower = linePath(stats, point => point.mean - point.sd * sdMultiplier, x, y, { skipBelowZero: true, maxValue: maxDisplayValue });
        if (lower) svg.appendChild(svgEl("path", { d: lower, class: "sd-line" }));
      }

      const avgPath = linePath(stats, point => point.mean, x, y);
      if (avgPath) svg.appendChild(svgEl("path", { d: avgPath, class: "average-line" }));

      if (selectedPoints.length) {
        if (selectedPoints.length > 1) svg.appendChild(svgEl("path", { d: pathFrom(selectedPoints, x, y), class: "selected-line" }));
        selectedPoints.forEach(point => {
          const dot = svgEl("circle", { cx: x(point.day), cy: y(point.value), r: 4.8, fill: "var(--cu-black)", stroke: "#ffffff", "stroke-width": 1.5 });
          dot.appendChild(svgEl("title", {})).textContent = `${selected} day ${roundDay(point.day)}: ${exactValue(point.value, unit)}`;
          svg.appendChild(dot);
        });
      }

      const xTitle = svgEl("text", { x: margin.left + plotW / 2, y: height - 14, "text-anchor": "middle", class: "axis-title" });
      xTitle.textContent = "Day";
      svg.appendChild(xTitle);
      const yTitle = svgEl("text", { x: 15, y: margin.top + plotH / 2, transform: `rotate(-90 15 ${margin.top + plotH / 2})`, "text-anchor": "middle", class: "axis-title" });
      yTitle.textContent = unit === "percent" ? "Viability" : "Live cell concentration";
      svg.appendChild(yTitle);

      container.innerHTML = "";
      container.appendChild(svg);
    }

    function renderFlowChart(container, metaId, metric, unit = "percent", sdSelect) {
      const selected = selectedBatch();
      const { rows, bars, hist, avg, sd, selectedBar } = flowData(metric);
      const sdMultiplier = selectedLineSdMultiplier(sdSelect);
      const showSd = sdMultiplier > 0;
      const below = showSd && Number.isFinite(avg) && avg - sd * sdMultiplier < 0 ? [sdMultiplier] : [];
      document.getElementById(metaId).innerHTML = [
        `<span class="pill">${rows.length} source rows</span>`,
        `<span class="pill">${hist.length} historical batches</span>`,
        selectedBar ? `<span class="pill">Highlighted ${selected}</span>` : `<span class="pill">Selected batch not present</span>`,
        showSd
          ? (below.length ? `<span class="pill">${sdMultiplier}SD lower limit omitted below zero</span>` : `<span class="pill">No below-zero SD limits</span>`)
          : `<span class="pill">SD guides off</span>`
      ].join("");

      if (!metric || !bars.length) {
        renderEmpty(container, "No flow data is available for this phase and filter combination.");
        return;
      }

      const width = 1120;
      const height = 410;
      const margin = { top: 26, right: 26, bottom: 116, left: 58 };
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;
      const refMax = Number.isFinite(avg) ? avg + sd * (showSd ? sdMultiplier : 0) : 0;
      const rawMax = Math.max(0, ...bars.map(bar => bar.value).filter(Number.isFinite), refMax);
      const yMax = unit === "percent" ? Math.min(1, Math.max(0.05, rawMax * 1.14)) : rawMax * 1.1 || 1;
      const step = plotW / Math.max(1, bars.length);
      const barW = Math.min(28, Math.max(9, step * 0.62));
      const x = index => margin.left + step * index + step / 2;
      const y = value => margin.top + plotH - (value / yMax) * plotH;
      const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": shortMetric(metric) });

      for (let i = 0; i <= 5; i++) {
        const value = (yMax / 5) * i;
        const yy = y(value);
        svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: yy, y2: yy, class: "grid-line" }));
        const label = svgEl("text", { x: margin.left - 9, y: yy + 4, "text-anchor": "end", class: "tick-label" });
        label.textContent = formatValue(value, unit);
        svg.appendChild(label);
      }

      if (showSd && Number.isFinite(avg)) {
        [avg + sd * sdMultiplier, avg - sd * sdMultiplier].forEach(value => {
          if (value < 0 || value > yMax) return;
          svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: y(value), y2: y(value), class: "sd-line" }));
        });
      }

      bars.forEach((bar, index) => {
        const xx = x(index);
        const yy = y(bar.value);
        const rect = svgEl("rect", {
          x: xx - barW / 2,
          y: yy,
          width: barW,
          height: Math.max(1, height - margin.bottom - yy),
          rx: 2,
          class: bar.kind === "selected" ? "selected-bar" : "hist-bar"
        });
        rect.appendChild(svgEl("title", {})).textContent = `${bar.batch}: ${exactValue(bar.value, unit)}`;
        svg.appendChild(rect);

        const label = svgEl("text", {
          x: xx,
          y: height - margin.bottom + 15,
          transform: `rotate(-50 ${xx} ${height - margin.bottom + 15})`,
          "text-anchor": "end",
          class: "tick-label"
        });
        label.textContent = bar.batch;
        svg.appendChild(label);
      });

      if (Number.isFinite(avg)) {
        const yy = y(avg);
        svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: yy, y2: yy, stroke: "var(--cu-gold-dark)", "stroke-width": 2.4 }));
        const label = svgEl("text", { x: width - margin.right, y: yy - 6, "text-anchor": "end", class: "sd-label" });
        label.textContent = `Avg ${formatValue(avg, unit)}`;
        svg.appendChild(label);
      }

      svg.appendChild(svgEl("line", { x1: margin.left, x2: width - margin.right, y1: height - margin.bottom, y2: height - margin.bottom, class: "axis-line" }));
      svg.appendChild(svgEl("line", { x1: margin.left, x2: margin.left, y1: margin.top, y2: height - margin.bottom, class: "axis-line" }));

      const yTitle = svgEl("text", { x: 14, y: margin.top + plotH / 2, transform: `rotate(-90 14 ${margin.top + plotH / 2})`, "text-anchor": "middle", class: "axis-title" });
      yTitle.textContent = "Flow result";
      svg.appendChild(yTitle);

      container.innerHTML = "";
      container.appendChild(svg);
    }

    function updateKpis() {
      const selected = selectedBatch();
      const rows = currentRows();
      const historicalBatches = new Set(rows.filter(row => !selected || row.batch !== selected).map(row => row.batch));
      document.getElementById("kpiBatch").textContent = selected || "None";
      document.getElementById("kpiBatchFoot").textContent = selected === DATA.inputBatch ? "From input sheet" : "Changed in report controls";
      document.getElementById("kpiHistorical").textContent = fmtInt.format(historicalBatches.size);
      document.getElementById("kpiLive").textContent = fmtInt.format(rows.filter(row => row.category === "Live Cell Concentration").length);
      document.getElementById("kpiViability").textContent = fmtInt.format(rows.filter(row => row.category === "Viabilities").length);
    }

    function render() {
      refreshFlowMetricOptions();
      updateKpis();
      renderLineChart(els.liveChart, "liveMeta", "Live cell concentration vs day", "Live Cell Concentration", "count", els.liveSd);
      renderLineChart(els.viabilityChart, "viabilityMeta", "Viability vs day", "Viabilities", "percent", els.viabilitySd);
      renderFlowChart(els.qc4Chart, "qc4Meta", els.qc4Metric.value, "percent", els.qc4Sd);
      renderFlowChart(els.qc5Chart, "qc5Meta", els.qc5Metric.value, "percent", els.qc5Sd);
    }

    setupControls();
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    payload = build_payload()
    html = HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(payload, ensure_ascii=False, allow_nan=False))
    html = html.replace("__LOGO_DATA_URL__", load_logo_data_url())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "rows": len(payload["rows"]), "inputBatch": payload["inputBatch"]}, indent=2))


if __name__ == "__main__":
    main()
