#!/usr/bin/env node
/**
 * Report generator agent — builds an interactive HTML report from backtest results.
 *
 * Reads data/results/*.json and writes docs/index.html with:
 * - Live progress bar (auto-refresh until --final)
 * - Interactive Chart.js equity curves for top 5 strategies
 * - Sortable results table with all metrics
 * - Summary cards for top 3
 *
 * Usage:
 *   node generate_report.js --results-dir data/results --total 17
 *   node generate_report.js --results-dir data/results --total 17 --final
 *   node generate_report.js --results-dir data/results --total 17 --final --output docs/index.html
 */
'use strict';

const fs = require('fs');
const path = require('path');

// ── CLI args ──────────────────────────────────────────────────────────────────

function parseArgs() {
  const argv = process.argv.slice(2);
  const opts = {
    resultsDir: 'data/results',
    total: 0,
    final: false,
    output: 'docs/index.html',
  };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case '--results-dir': opts.resultsDir = argv[++i]; break;
      case '--total':       opts.total = parseInt(argv[++i], 10); break;
      case '--final':       opts.final = true; break;
      case '--output':      opts.output = argv[++i]; break;
    }
  }
  return opts;
}

// ── Data loading ──────────────────────────────────────────────────────────────

function loadResults(resultsDir) {
  if (!fs.existsSync(resultsDir)) return [];
  return fs.readdirSync(resultsDir)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      try { return JSON.parse(fs.readFileSync(path.join(resultsDir, f), 'utf8')); }
      catch { return null; }
    })
    .filter(Boolean)
    .sort((a, b) => (b.metrics.sharpe || 0) - (a.metrics.sharpe || 0));
}

// ── Formatting helpers ────────────────────────────────────────────────────────

const fmt = {
  pct:   v => v == null || isNaN(v) ? '—' : (v * 100).toFixed(1) + '%',
  num:   v => v == null || isNaN(v) ? '—' : v.toFixed(2),
  money: v => v == null || isNaN(v) ? '—' : '$' + Math.round(v).toLocaleString(),
};

// ── Chart data ────────────────────────────────────────────────────────────────

const PALETTE = ['#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#f44336'];

function buildChartDatasets(results) {
  return results.slice(0, 5).map((r, i) => ({
    label: r.label,
    data: r.equity_dates.map((d, j) => ({ x: d, y: r.equity_values[j] })),
    borderColor: PALETTE[i],
    backgroundColor: 'transparent',
    borderWidth: 2,
    pointRadius: 0,
    tension: 0.1,
  }));
}

// ── HTML generation ───────────────────────────────────────────────────────────

function summaryCards(results) {
  if (results.length === 0) return '';
  const medals = ['🥇', '🥈', '🥉'];
  return `
  <div class="cards">
    ${results.slice(0, 3).map((r, i) => {
      const m = r.metrics;
      return `
    <div class="card">
      <div class="card-rank">${medals[i]}</div>
      <div class="card-sharpe">${fmt.num(m.sharpe)}<span class="card-unit"> Sharpe</span></div>
      <div class="card-label">${r.label}</div>
      <div class="card-metrics">
        CAGR&nbsp;${fmt.pct(m.cagr)} &nbsp;·&nbsp; MaxDD&nbsp;${fmt.pct(m.max_drawdown)}
      </div>
    </div>`;
    }).join('')}
  </div>`;
}

function equityChart(results) {
  if (results.length === 0 || !results[0].equity_dates?.length) return '';
  const datasets = JSON.stringify(buildChartDatasets(results));
  return `
  <div class="chart-card">
    <h2>Top ${Math.min(results.length, 5)} — Equity Curves</h2>
    <div class="chart-wrap"><canvas id="equityChart"></canvas></div>
  </div>
  <script>
  (function() {
    const ctx = document.getElementById('equityChart').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: { datasets: ${datasets} },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        interaction: { mode: 'index', intersect: false },
        scales: {
          x: { type: 'time', time: { unit: 'year' },
               grid: { color: '#f0f2f5' }, ticks: { color: '#888', maxTicksLimit: 10 } },
          y: { grid: { color: '#f0f2f5' }, ticks: { color: '#888',
               callback: v => '$' + (v / 1000).toFixed(0) + 'k' } }
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: { callbacks: {
            label: c => ' ' + c.dataset.label + ': $' + Math.round(c.raw.y).toLocaleString()
          }}
        }
      }
    });
  })();
  </script>`;
}

function resultsTable(results) {
  if (results.length === 0) {
    return '<p class="empty">Waiting for first result…</p>';
  }
  const rows = results.map((r, i) => {
    const m = r.metrics;
    const rank = i + 1;
    return `
    <tr class="rank-${rank <= 3 ? rank : 'other'}">
      <td class="td-rank">${rank}</td>
      <td class="td-label" title="${r.strategy}">${r.label}</td>
      <td>${fmt.pct(m.cagr)}</td>
      <td><strong>${fmt.num(m.sharpe)}</strong></td>
      <td>${fmt.num(m.sortino)}</td>
      <td>${fmt.pct(m.max_drawdown)}</td>
      <td>${fmt.num(m.calmar)}</td>
      <td>${fmt.pct(m.volatility)}</td>
      <td>${m.recovery_months != null ? m.recovery_months + 'mo' : '—'}</td>
      <td>${fmt.pct(m.return_2022)}</td>
      <td>${fmt.pct(m.covid_crash)}</td>
    </tr>`;
  }).join('');
  return `
  <table id="resultsTable">
    <thead>
      <tr>
        <th>#</th>
        <th>Strategy | Rule</th>
        <th>CAGR</th>
        <th>Sharpe</th>
        <th>Sortino</th>
        <th>Max&nbsp;DD</th>
        <th>Calmar</th>
        <th>Vol</th>
        <th>Recovery</th>
        <th>2022</th>
        <th>COVID</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function generateHtml(results, total, isFinal) {
  const completed = results.length;
  const pct = Math.round(100 * completed / Math.max(total, 1));
  const isDone = isFinal || completed >= total;
  const refreshTag = isDone ? '' : '<meta http-equiv="refresh" content="5">';
  const statusMsg = isDone ? 'Complete' : `Running… auto-refreshing every 5 s`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  ${refreshTag}
  <title>401k Strategy Backtest${isDone ? '' : ' — Live'}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           background: #f0f2f5; color: #1a1a2e; min-height: 100vh; }
    .container { max-width: 1240px; margin: 0 auto; padding: 2rem 1.5rem; }
    h1 { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.2rem; }
    .subtitle { color: #666; font-size: 0.9rem; margin-bottom: 2rem; }

    /* Progress */
    .progress-card { background: white; border-radius: 14px; padding: 1.25rem 1.5rem;
                     box-shadow: 0 1px 3px rgba(0,0,0,0.07); margin-bottom: 1.5rem; }
    .progress-header { display: flex; justify-content: space-between;
                       font-size: 0.82rem; color: #777; margin-bottom: 0.75rem; }
    .progress-bar-bg { height: 8px; background: #e4e8ee; border-radius: 4px; overflow: hidden; }
    .progress-bar-fill { height: 100%; border-radius: 4px;
                         background: ${isDone ? '#4caf50' : '#2196f3'};
                         width: ${pct}%; transition: width 0.5s ease; }

    /* Summary cards */
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
             gap: 1rem; margin-bottom: 1.5rem; }
    .card { background: white; border-radius: 14px; padding: 1.25rem 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.07); }
    .card-rank { font-size: 1.4rem; margin-bottom: 0.4rem; }
    .card-sharpe { font-size: 2rem; font-weight: 700; line-height: 1; }
    .card-unit { font-size: 0.9rem; font-weight: 400; color: #888; }
    .card-label { font-size: 0.8rem; color: #444; margin: 0.4rem 0 0.5rem;
                  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .card-metrics { font-size: 0.78rem; color: #4caf50; }

    /* Chart */
    .chart-card { background: white; border-radius: 14px; padding: 1.5rem;
                  box-shadow: 0 1px 3px rgba(0,0,0,0.07); margin-bottom: 1.5rem; }
    .chart-card h2 { font-size: 0.9rem; font-weight: 600; color: #444;
                     text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; }
    .chart-wrap { position: relative; height: 320px; }

    /* Table */
    .table-card { background: white; border-radius: 14px; padding: 1.5rem;
                  box-shadow: 0 1px 3px rgba(0,0,0,0.07); overflow-x: auto; }
    .table-card h2 { font-size: 0.9rem; font-weight: 600; color: #444;
                     text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.855rem; }
    thead tr { border-bottom: 2px solid #eef0f4; }
    th { padding: 8px 10px; text-align: left; font-size: 0.75rem; color: #888;
         text-transform: uppercase; letter-spacing: 0.04em; white-space: nowrap; cursor: pointer; }
    th:hover { color: #2196f3; }
    td { padding: 9px 10px; border-bottom: 1px solid #f2f4f7; white-space: nowrap; }
    .td-rank { font-weight: 600; color: #888; width: 2rem; }
    .td-label { max-width: 280px; overflow: hidden; text-overflow: ellipsis;
                font-weight: 500; color: #1a1a2e; }
    tr.rank-1 td { background: #fffde7; }
    tr.rank-2 td { background: #fafafa; }
    tr.rank-3 td { background: #fff8f5; }
    tr:hover td { background: #eef4ff !important; }
    .empty { text-align: center; color: #aaa; padding: 3rem; font-size: 0.9rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>401k Strategy Backtest</h1>
    <p class="subtitle">${statusMsg} &nbsp;&middot;&nbsp; ${completed}&thinsp;/&thinsp;${total} strategies complete</p>

    <div class="progress-card">
      <div class="progress-header"><span>Progress</span><span>${pct}%</span></div>
      <div class="progress-bar-bg"><div class="progress-bar-fill"></div></div>
    </div>

    ${summaryCards(results)}
    ${equityChart(results)}

    <div class="table-card">
      <h2>All Strategies &mdash; Ranked by Sharpe</h2>
      ${resultsTable(results)}
    </div>
  </div>
</body>
</html>`;
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
  const opts = parseArgs();
  const results = loadResults(opts.resultsDir);
  const total = opts.total || results.length;
  const html = generateHtml(results, total, opts.final);

  const outPath = path.resolve(opts.output);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, html, 'utf8');

  console.log(`[report-generator] ${results.length}/${total} complete → ${opts.output}`);
}

main();
