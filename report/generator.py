"""Generate the HTML backtest report for GitHub Pages."""

import os
from datetime import date
from tabulate import tabulate
from report.charts import equity_curve_chart, drawdown_chart, annual_returns_heatmap, sharpe_bar_chart
from config import OUTPUT_DIR, CHARTS_DIR, REPORT_FILE, INITIAL_CAPITAL, RISK_FREE_RATE, START_DATE, END_DATE


def generate_report(results: list[dict]):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)

    print("  [report] Generating charts...")
    chart_equity = equity_curve_chart(results)
    chart_dd = drawdown_chart(results)
    chart_heatmap = annual_returns_heatmap(results)
    chart_sharpe = sharpe_bar_chart(results)

    html = _build_html(results, chart_equity, chart_dd, chart_heatmap, chart_sharpe)

    with open(REPORT_FILE, "w") as f:
        f.write(html)

    print(f"  [report] Written to {REPORT_FILE}")


def _fmt(val, kind="pct"):
    if val is None:
        return "N/A"
    if kind == "pct":
        return f"{val * 100:.1f}%"
    if kind == "float":
        return f"{val:.2f}"
    if kind == "int":
        return f"{int(val)}" if val is not None else "N/A"
    if kind == "dollar":
        return f"${val:,.0f}"
    return str(val)


def _build_html(results, chart_equity, chart_dd, chart_heatmap, chart_sharpe) -> str:
    ranked = sorted(results, key=lambda r: r["metrics"]["sharpe"], reverse=True)

    rows = []
    for r in ranked:
        m = r["metrics"]
        final_val = r["equity"].iloc[-1]
        rows.append([
            r["label"],
            _fmt(m["cagr"]),
            _fmt(m["total_return"]),
            _fmt(final_val, "dollar"),
            _fmt(m["volatility"]),
            _fmt(m["sharpe"], "float"),
            _fmt(m["sortino"], "float"),
            _fmt(m["max_drawdown"]),
            _fmt(m["calmar"], "float"),
            _fmt(m.get("return_2022")),
            _fmt(m.get("covid_crash")),
            _fmt(m["rebalance_count"], "int"),
        ])

    headers = [
        "Strategy | Rebalance", "CAGR", "Total Return", f"${INITIAL_CAPITAL/1000:.0f}K → ",
        "Volatility", "Sharpe", "Sortino", "Max DD", "Calmar",
        "2022", "COVID Drop", "# Rebalances"
    ]

    table_html = _table_to_html(headers, rows)

    # Annual returns per strategy
    annual_sections = ""
    for r in ranked[:5]:  # top 5 by Sharpe
        ar = r["metrics"].get("annual_returns", {})
        if ar:
            yr_rows = [[str(y), _fmt(v)] for y, v in sorted(ar.items())]
            annual_sections += f"""
            <h3>{r['label']}</h3>
            {_table_to_html(['Year', 'Return'], yr_rows)}
            """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IRA Strategy Backtest Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           max-width: 1400px; margin: 0 auto; padding: 24px; background: #f8f9fa; color: #212529; }}
    h1 {{ color: #1a1a2e; border-bottom: 3px solid #4361ee; padding-bottom: 8px; }}
    h2 {{ color: #4361ee; margin-top: 40px; }}
    h3 {{ color: #495057; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th {{ background: #4361ee; color: white; padding: 8px 12px; text-align: left; }}
    td {{ padding: 7px 12px; border-bottom: 1px solid #dee2e6; }}
    tr:nth-child(even) {{ background: #f1f3f5; }}
    tr:hover {{ background: #e8f4fd; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; }}
    .green {{ background: #d4edda; color: #155724; }}
    .red {{ background: #f8d7da; color: #721c24; }}
    .meta {{ color: #6c757d; font-size: 13px; margin-bottom: 24px; }}
    img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 12px 0; }}
    .card {{ background: white; border-radius: 12px; padding: 24px; margin: 20px 0;
             box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .disclaimer {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px 16px;
                   border-radius: 4px; font-size: 13px; margin-top: 40px; }}
  </style>
</head>
<body>
  <h1>IRA Strategy Backtest Report</h1>
  <p class="meta">
    Generated: {date.today()} &nbsp;|&nbsp;
    Backtest: {START_DATE} – {END_DATE} &nbsp;|&nbsp;
    Starting capital: ${INITIAL_CAPITAL:,.0f} &nbsp;|&nbsp;
    Risk-free rate: {RISK_FREE_RATE:.1%} &nbsp;|&nbsp;
    Rebalancing: zero cost (tax-advantaged account)
  </p>

  <div class="card">
    <h2>Executive Summary — All Strategies (ranked by Sharpe)</h2>
    {table_html}
  </div>

  <div class="card">
    <h2>Equity Curves</h2>
    <img src="data:image/png;base64,{chart_equity}" alt="Equity Curves">
  </div>

  <div class="card">
    <h2>Drawdown</h2>
    <img src="data:image/png;base64,{chart_dd}" alt="Drawdown">
  </div>

  <div class="card">
    <h2>Sharpe Ratio Comparison</h2>
    <img src="data:image/png;base64,{chart_sharpe}" alt="Sharpe Ratios">
  </div>

  <div class="card">
    <h2>Annual Returns Heatmap</h2>
    <img src="data:image/png;base64,{chart_heatmap}" alt="Annual Returns Heatmap">
  </div>

  <div class="card">
    <h2>Annual Returns — Top 5 Strategies (by Sharpe)</h2>
    {annual_sections}
  </div>

  <div class="disclaimer">
    <strong>Disclaimer:</strong> Backtests are hypothetical and based on historical data.
    Past performance does not guarantee future results. This tool is for educational and
    research purposes only — not financial advice. All strategies assume zero transaction costs,
    which is appropriate for tax-advantaged self-directed accounts (IRA/Roth IRA) but may not
    apply in taxable accounts.
  </div>
</body>
</html>"""


def _table_to_html(headers, rows) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        tds = "".join(f"<td>{cell}</td>" for cell in row)
        body += f"<tr>{tds}</tr>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"
