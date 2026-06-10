#!/usr/bin/env node
/**
 * Report generator agent — builds an interactive HTML report from backtest results.
 *
 * Reads data/results/*.json and writes data/reports/index.html with:
 * - Live progress bar (auto-refresh until --final)
 * - Interactive Chart.js equity curves for top 5 strategies
 * - Sortable results table with all metrics
 * - Summary cards for top 3
 *
 * Usage:
 *   node generate_report.js --results-dir data/results --total 17
 *   node generate_report.js --results-dir data/results --total 17 --final
 *   node generate_report.js --results-dir data/results --total 17 --final --output data/reports/index.html
 */
'use strict';

const fs   = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ── CLI args ──────────────────────────────────────────────────────────────────

function parseArgs() {
  const argv = process.argv.slice(2);
  const opts = {
    resultsDir: 'data/results',
    total: 0,
    final: false,
    output: 'data/reports/index.html',
    profile: null,
  };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case '--results-dir': opts.resultsDir = argv[++i]; break;
      case '--total':       opts.total = parseInt(argv[++i], 10); break;
      case '--final':       opts.final = true; break;
      case '--output':      opts.output = argv[++i]; break;
      case '--profile':     opts.profile = argv[++i]; break;
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

// ── Profile loader ────────────────────────────────────────────────────────────

function loadProfile(profilePath) {
  if (!profilePath || !fs.existsSync(profilePath)) return null;
  const text = fs.readFileSync(profilePath, 'utf8');
  const get = key => {
    const m = text.match(new RegExp(`^\\s*${key}:\\s*(.+)$`, 'm'));
    return m ? m[1].trim().replace(/['"]/g, '') : null;
  };
  return {
    accountType:       get('account_type'),
    age:               get('age'),
    yearsToRetirement: get('years_to_retirement'),
    riskTolerance:     get('risk_tolerance'),
    horizon:           get('investment_horizon'),
    minBacktestYears:  get('min_backtest_years'),
  };
}

// ── Strategy MD loader ────────────────────────────────────────────────────────

function loadStrategyMdMap(strategiesDir) {
  const map = {}; // strategy name → { folder, description, logic }
  if (!fs.existsSync(strategiesDir)) return map;
  for (const folder of fs.readdirSync(strategiesDir)) {
    const mdPath = path.join(strategiesDir, folder, 'strategy.md');
    if (!fs.existsSync(mdPath)) continue;
    try {
      const content = fs.readFileSync(mdPath, 'utf8');
      const nameMatch = content.match(/^name:\s*["']?(.+?)["']?\s*$/m);
      if (!nameMatch) continue;
      const name = nameMatch[1].trim();
      const section = key => {
        const m = content.match(new RegExp(`## ${key}\\n+([\\s\\S]*?)(?=\\n## |\\n---\\s*$|$)`));
        return m ? m[1].trim() : '';
      };
      map[name] = { folder, description: section('Description'), logic: section('Logic') };
    } catch { /* skip malformed files */ }
  }
  return map;
}

function getRepoUrl() {
  try {
    const remote = execSync('git remote get-url origin 2>/dev/null', { encoding: 'utf8' }).trim();
    return remote.replace(/^git@github\.com:/, 'https://github.com/').replace(/\.git$/, '');
  } catch { return ''; }
}

function renderLogicMd(logic) {
  if (!logic) return '<li>See the strategy spec for details.</li>';
  return logic.split('\n')
    .map(l => l.trim())
    .filter(Boolean)
    .map(l => `<li>${l.replace(/^\d+\.\s*/, '').replace(/^[-*]\s*/, '')}</li>`)
    .join('');
}

// ── Domain knowledge ──────────────────────────────────────────────────────────

const ASSET_UNIVERSE = [
  { ticker: 'QQQ',     category: 'Broad ETF',        desc: 'Nasdaq-100 — top 100 non-financial US tech stocks' },
  { ticker: 'VOO',     category: 'Broad ETF',        desc: 'S&P 500 (Vanguard) — 500 largest US companies' },
  { ticker: 'SPY',     category: 'Broad ETF',        desc: 'S&P 500 (SPDR) — most liquid US equity ETF' },
  { ticker: 'VTI',     category: 'Broad ETF',        desc: 'Total US market — large, mid, and small cap' },
  { ticker: 'DIA',     category: 'Broad ETF',        desc: 'Dow Jones Industrial Average — 30 large US blue chips' },
  { ticker: 'IWF',     category: 'Broad ETF',        desc: 'Russell 1000 growth — large-cap growth tilt' },
  { ticker: 'IWD',     category: 'Broad ETF',        desc: 'Russell 1000 value — large-cap value tilt' },
  { ticker: 'IVE',     category: 'Broad ETF',        desc: 'S&P 500 value — large-cap value exposure' },
  { ticker: 'IJR',     category: 'Broad ETF',        desc: 'S&P 600 small-cap — US small companies' },
  { ticker: 'VXUS',    category: 'Broad ETF',        desc: 'International ex-US — developed + emerging markets' },
  { ticker: 'EEM',     category: 'Broad ETF',        desc: 'Emerging markets — China, India, Brazil, etc.' },
  { ticker: 'IWM',     category: 'Broad ETF',        desc: 'Russell 2000 — US small-cap stocks' },
  { ticker: 'VEA',     category: 'Broad ETF',        desc: 'Developed markets outside the US' },
  { ticker: 'VWO',     category: 'Broad ETF',        desc: 'Emerging markets — broad, low-cost exposure' },
  { ticker: 'IEMG',    category: 'Broad ETF',        desc: 'Emerging markets — broad, liquid ETF' },
  { ticker: 'EFA',     category: 'Broad ETF',        desc: 'Developed international equities' },
  { ticker: 'EWJ',     category: 'Broad ETF',        desc: 'Japan equities' },
  { ticker: 'EWG',     category: 'Broad ETF',        desc: 'Germany equities' },
  { ticker: 'EWU',     category: 'Broad ETF',        desc: 'United Kingdom equities' },
  { ticker: 'INDA',    category: 'Broad ETF',        desc: 'India equities' },
  { ticker: 'SPMO',    category: 'Factor ETF',       desc: 'S&P 500 momentum — strongest recent performers' },
  { ticker: 'SCHG',    category: 'Factor ETF',       desc: 'US large-cap growth — high-growth large companies' },
  { ticker: 'VBR',     category: 'Factor ETF',       desc: 'US small-cap value — cheap small companies' },
  { ticker: 'VIG',     category: 'Factor ETF',       desc: 'Dividend appreciation — quality dividend growers' },
  { ticker: 'SCHD',    category: 'Factor ETF',       desc: 'High dividend US equities' },
  { ticker: 'QUAL',    category: 'Factor ETF',       desc: 'Quality factor ETF' },
  { ticker: 'MTUM',    category: 'Factor ETF',       desc: 'Momentum factor ETF' },
  { ticker: 'USMV',    category: 'Factor ETF',       desc: 'Min volatility US equities' },
  { ticker: 'MDY',     category: 'Broad ETF',        desc: 'S&P MidCap 400 — US mid-cap stocks' },
  { ticker: 'IJH',     category: 'Broad ETF',        desc: 'S&P MidCap 400 — US mid-cap stocks' },
  { ticker: 'IWO',     category: 'Broad ETF',        desc: 'Russell 2000 growth — small-cap growth tilt' },
  { ticker: 'IWN',     category: 'Broad ETF',        desc: 'Russell 2000 value — small-cap value tilt' },
  { ticker: 'VGT',     category: 'Sector ETF',       desc: 'Information technology sector' },
  { ticker: 'SOXX',    category: 'Sector ETF',       desc: 'Semiconductors sector' },
  { ticker: 'XLE',     category: 'Sector ETF',       desc: 'Energy sector — oil, gas, pipelines' },
  { ticker: 'XLB',     category: 'Sector ETF',       desc: 'Materials sector — chemicals, mining, paper' },
  { ticker: 'XLI',     category: 'Sector ETF',       desc: 'Industrials sector — aerospace, machinery, transport' },
  { ticker: 'XLP',     category: 'Sector ETF',       desc: 'Consumer staples sector — groceries, household goods' },
  { ticker: 'XLV',     category: 'Sector ETF',       desc: 'Healthcare sector — pharma, biotech, insurance' },
  { ticker: 'XLF',     category: 'Sector ETF',       desc: 'Financials sector — banks, insurance, asset managers' },
  { ticker: 'XLK',     category: 'Sector ETF',       desc: 'Technology sector — software, hardware, services' },
  { ticker: 'XLU',     category: 'Sector ETF',       desc: 'Utilities sector — electric, water, gas' },
  { ticker: 'XLY',     category: 'Sector ETF',       desc: 'Consumer discretionary sector — retail, autos, travel' },
  { ticker: 'XLRE',    category: 'Sector ETF',       desc: 'Real estate sector' },
  { ticker: 'SMH',     category: 'Sector ETF',       desc: 'Semiconductor sector — pure-play chips' },
  { ticker: 'XBI',     category: 'Sector ETF',       desc: 'Biotechnology sector' },
  { ticker: 'TQQQ',    category: 'Leveraged ETF',    desc: '3× Nasdaq-100 — high risk, high reward' },
  { ticker: 'UPRO',    category: 'Leveraged ETF',    desc: '3× S&P 500 — high risk, high reward' },
  { ticker: 'TMF',     category: 'Leveraged ETF',    desc: '3× 20-yr Treasuries — inverse of rate hikes' },
  { ticker: 'GLD',     category: 'Alternative',      desc: 'Gold — inflation hedge and safe haven' },
  { ticker: 'IAU',     category: 'Alternative',      desc: 'Gold bullion trust — lower-fee gold exposure' },
  { ticker: 'SLV',     category: 'Alternative',      desc: 'Silver — precious metal with higher volatility' },
  { ticker: 'VNQ',     category: 'Alternative',      desc: 'US REITs — real estate income' },
  { ticker: 'DBC',     category: 'Alternative',      desc: 'Broad commodities — oil, metals, agriculture basket' },
  { ticker: 'USO',     category: 'Alternative',      desc: 'US oil fund — crude oil futures exposure' },
  { ticker: 'UNG',     category: 'Alternative',      desc: 'US natural gas fund' },
  { ticker: 'BTC-USD', category: 'Alternative',      desc: 'Bitcoin — high-volatility digital asset' },
  { ticker: 'BND',     category: 'Fixed Income',     desc: 'Total bond market — investment-grade US bonds' },
  { ticker: 'AGG',     category: 'Fixed Income',     desc: 'Aggregate bond market — broad investment-grade bonds' },
  { ticker: 'IEF',     category: 'Fixed Income',     desc: '7-10 year Treasuries — intermediate duration' },
  { ticker: 'HYG',     category: 'Fixed Income',     desc: 'High-yield bonds — junk bonds, equity-like risk' },
  { ticker: 'LQD',     category: 'Fixed Income',     desc: 'Investment-grade corporate bonds' },
  { ticker: 'MUB',     category: 'Fixed Income',     desc: 'Municipal bonds — tax-efficient bond exposure' },
  { ticker: 'BSV',     category: 'Fixed Income',     desc: 'Short-term investment-grade bonds' },
  { ticker: 'VCIT',    category: 'Fixed Income',     desc: 'Intermediate-term corporate bonds' },
  { ticker: 'EMB',     category: 'Fixed Income',     desc: 'Emerging markets sovereign debt' },
  { ticker: 'BIL',     category: 'Fixed Income',     desc: '1-3 month Treasury bills — cash proxy' },
  { ticker: 'TIP',     category: 'Fixed Income',     desc: 'TIPS — Treasury bonds indexed to inflation' },
  { ticker: 'TLT',     category: 'Fixed Income',     desc: '20-yr Treasuries — rate-sensitive long bonds' },
  { ticker: 'SHY',     category: 'Fixed Income',     desc: '1-3 yr Treasuries — near-cash, minimal rate risk' },
  { ticker: 'SHV',     category: 'Fixed Income',     desc: 'Short Treasury ETF — near-cash, ultra-low duration' },
  { ticker: 'AAPL',    category: 'Mega-Cap Stock',   desc: 'Apple' },
  { ticker: 'MSFT',    category: 'Mega-Cap Stock',   desc: 'Microsoft' },
  { ticker: 'NVDA',    category: 'Mega-Cap Stock',   desc: 'Nvidia' },
  { ticker: 'AMZN',    category: 'Mega-Cap Stock',   desc: 'Amazon' },
  { ticker: 'GOOGL',   category: 'Mega-Cap Stock',   desc: 'Alphabet' },
  { ticker: 'META',    category: 'Mega-Cap Stock',   desc: 'Meta Platforms' },
  { ticker: 'TSLA',    category: 'Mega-Cap Stock',   desc: 'Tesla' },
  { ticker: 'JPM',     category: 'Mega-Cap Stock',   desc: 'JPMorgan Chase' },
  { ticker: 'UNH',     category: 'Mega-Cap Stock',   desc: 'UnitedHealth Group' },
  { ticker: 'BRK-B',   category: 'Mega-Cap Stock',   desc: 'Berkshire Hathaway Class B' },
];

const STRATEGY_NOTES = {
  'FixedWeight':        'Holds a fixed allocation, rebalanced on schedule. Simple, low-cost, and easy to understand. No active decisions after setup.',
  'EqualWeight':        '1/N diversification across all assets in the universe. No market view required — every asset gets an equal slice, rebalanced monthly.',
  'MomentumRotation':   'Ranks assets by 12-month price return and holds the top N. Rotates monthly. Performs well in trending markets; can lag in choppy sideways periods.',
  'DualMomentum':       'Combines relative momentum (which equity wins?) with absolute momentum (are equities beating cash?). Defensively switches to bonds when trend is down.',
  'TrendFollowing':     '200-day moving average filter: holds equities above the trend line, shifts to bonds below it. Reduces crash exposure at the cost of whipsaws.',
  'MaxSharpe':          'Mean-variance optimization: finds the portfolio weight mix that maximizes the Sharpe ratio over a 36-month lookback. Model-dependent; sensitive to estimation error.',
  'MinVariance':        'Minimizes portfolio volatility regardless of return. Capital preservation first. Suits conservative investors; lower absolute return than equity-heavy strategies.',
  'RiskParity':         'Sizes positions so each asset contributes equal risk (volatility). Bridgewater All-Weather style. High Sharpe ratio, lower absolute return than pure equity.',
  'AdaptiveAA':         'Selects top N assets by risk-adjusted momentum (momentum ÷ volatility), then sizes them with inverse-volatility weighting. Research-backed combination of two proven factors.',
  'QqqVooSpyAdaptive':  'Constrained to QQQ, VOO, and SPY. Picks the strongest index ETF by risk-adjusted momentum each month. Splits 50/50 between VOO and SPY when an S&P 500 ETF wins.',
};

function getStrategyNotes(strategyName) {
  for (const [prefix, notes] of Object.entries(STRATEGY_NOTES)) {
    if (strategyName.startsWith(prefix)) return notes;
  }
  return null;
}

// ── Formatting helpers ────────────────────────────────────────────────────────

const fmt = {
  pct:   v => v == null || isNaN(v) ? '—' : (v * 100).toFixed(1) + '%',
  num:   v => v == null || isNaN(v) ? '—' : v.toFixed(2),
  money: v => v == null || isNaN(v) ? '—' : '$' + Math.round(v).toLocaleString(),
  money2: v => v == null || isNaN(v) ? '—' : '$' + Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
};

function colorClass(v) {
  if (v == null || isNaN(v)) return '';
  return v >= 0 ? ' class="pos"' : ' class="neg"';
}

function pctCell(v, dataVal) {
  const dv = dataVal !== undefined ? dataVal : v;
  return `<td${colorClass(v)} data-val="${dv ?? ''}">${fmt.pct(v)}</td>`;
}

function numCell(v) {
  return `<td data-val="${v ?? ''}">${fmt.num(v)}</td>`;
}

function toAnchorId(label) {
  return 'guide-' + label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function yahooHistoryUrl(ticker, dateText) {
  const start = Math.floor(new Date(`${dateText}T00:00:00Z`).getTime() / 1000);
  const end = start + 24 * 60 * 60;
  return `https://finance.yahoo.com/quote/${encodeURIComponent(ticker)}/history?period1=${start}&period2=${end}&interval=1d&filter=history&frequency=1d`;
}

function yahooQuoteUrl(ticker) {
  return `https://finance.yahoo.com/quote/${encodeURIComponent(ticker)}`;
}

function renderTradeHoldings(entry) {
  if (Array.isArray(entry.holdings) && entry.holdings.length > 0) {
    return entry.holdings
      .slice()
      .sort((a, b) => (b.weight || 0) - (a.weight || 0))
      .map(h => {
        const ticker = h.ticker;
        const url = yahooHistoryUrl(ticker, entry.date);
        const title = `${TICKER_NAMES[ticker] || ticker} adjusted-close backtest value for ${entry.date}`;
        const adj = h.price;
        const raw = h.raw_close;
        const rawDiffers = raw != null && Math.abs(Number(raw) - Number(adj)) > 0.005;
        const priceHtml = rawDiffers
          ? `<span class="tl-price tl-price--diff" title="adjusted close differs from raw close">${fmt.money2(adj)}</span>`
          : `<span class="tl-price tl-price--same" title="adjusted close matches raw close">${fmt.money2(adj)}</span>`;
        return `<span class="tl-chip tl-chip--detail" title="${title}">
          <a href="${url}" target="_blank" rel="noopener">${ticker}&nbsp;${((h.weight || 0) * 100).toFixed(0)}%</a>
          <span class="tl-cost">${priceHtml} = ${fmt.money2(h.market_value)}</span>
        </span>`;
      })
      .join(' ');
  }

  return Object.entries(entry.weights || {})
    .sort((a, b) => b[1] - a[1])
    .map(([t, w]) => `<span class="tl-chip" title="${TICKER_NAMES[t] || t}">${t}&nbsp;${(w * 100).toFixed(0)}%</span>`)
    .join(' ');
}

// ── Chart data ────────────────────────────────────────────────────────────────

const PALETTE = ['#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#f44336'];
const BENCHMARK_PALETTE = ['#111827', '#4b5563', '#9ca3af'];

function compactChartLabel(label) {
  return label
    .replace(' | Calendar(monthly)', ' monthly')
    .replace(' | Calendar(quarterly)', ' quarterly')
    .replace(' | Calendar(annual)', ' annual')
    .replace('AdaptiveAA(', 'AdaptiveAA ')
    .replace('MomentumRotation(', 'Momentum ')
    .replace('MaxSharpe(', 'MaxSharpe ')
    .replace('MinVariance(', 'MinVar ')
    .replace('QqqVooSpyAdaptive(', 'QVS ')
    .replace('TrendFollowing(', 'Trend ')
    .replace('DualMomentum(', 'DualMom ')
    .replace(/\)/g, '')
    .replace(/, 12m mom, 3m vol/g, '')
    .replace(/, 12m/g, '')
    .replace(/, 36m lookback/g, '')
    .replace(/200d MA/g, '200d')
    .replace(/\s+/g, ' ')
    .trim();
}

function buildChartDatasets(results) {
  const strategyDatasets = results.slice(0, 5).map((r, i) => ({
    label: compactChartLabel(r.label),
    fullLabel: r.label,
    data: r.equity_dates.map((d, j) => ({ x: d, y: r.equity_values[j] })),
    borderColor: PALETTE[i],
    backgroundColor: 'transparent',
    borderWidth: 2,
    pointRadius: 0,
    tension: 0.1,
  }));
  const benchmarkDatasets = collectBenchmarkDatasets(results);
  return [...strategyDatasets, ...benchmarkDatasets];
}

function collectBenchmarkDatasets(results) {
  const seen = new Map();
  for (const r of results) {
    for (const b of r.benchmarks || []) {
      if (!b || !b.ticker || seen.has(b.ticker)) continue;
      seen.set(b.ticker, b);
    }
  }
  return Array.from(seen.values()).map((b, i) => ({
    label: b.label,
    fullLabel: `${b.label} (${b.price_type === 'adjusted_close' ? 'adjusted close' : b.price_type})`,
    data: (b.dates || []).map((d, j) => ({ x: d, y: b.values[j] })),
    borderColor: BENCHMARK_PALETTE[i % BENCHMARK_PALETTE.length],
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderDash: [7, 4],
    pointRadius: 0,
    tension: 0.1,
    order: -1,
  }));
}

function chartLegend(results) {
  return `
    <div class="chart-legend">
      ${buildChartDatasets(results).map(d => `
        <span class="chart-legend-item" title="${d.fullLabel}">
          <span class="chart-legend-swatch" style="border-color: ${d.borderColor};"></span>
          <span class="chart-legend-label">${d.label}</span>
        </span>`).join('')}
    </div>`;
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
      <div class="card-total">$10k → ${fmt.money(10000 * (1 + (m.total_return || 0)))}</div>
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
    <div class="chart-note">Benchmark lines are always shown. They use buy-and-hold with the same starting value as the backtest. QQQ is black, SPY is dark gray, and VOO is light gray. All use adjusted close and dashed lines.</div>
    ${chartLegend(results)}
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
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          x: { type: 'time', time: { unit: 'year' },
               grid: { color: '#f0f2f5' }, ticks: { color: '#888', maxTicksLimit: 10 } },
          y: { grid: { color: '#f0f2f5' }, ticks: { color: '#888',
               callback: v => '$' + (v / 1000).toFixed(0) + 'k' } }
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: {
            label: c => ' ' + (c.dataset.fullLabel || c.dataset.label) + ': $' + Math.round(c.raw.y).toLocaleString()
          }}
        }
      }
    });
  })();
  </script>`;
}

function profileContextCard(profile) {
  const grouped = {};
  for (const a of ASSET_UNIVERSE) {
    if (!grouped[a.category]) grouped[a.category] = [];
    grouped[a.category].push(a);
  }

  return `
  <div class="context-card">
    <div class="context-section context-section--wide">
      <div class="context-heading">Asset Universe (${ASSET_UNIVERSE.length} instruments)</div>
      <div class="context-note">All trades in this report are constrained to this fixed preselected asset list. Strategies do not search the whole market; they rank or filter only these instruments, then rebalance into the winners. The benchmark lines below always show QQQ, SPY, and VOO buy-and-hold with the same starting capital.</div>
      <div class="universe-groups">
        ${Object.entries(grouped).map(([cat, assets]) => `
        <div class="asset-group">
          <span class="asset-cat">${cat}</span>
          ${assets.map(a => `<a class="chip chip--link" href="${yahooQuoteUrl(a.ticker)}" target="_blank" rel="noopener" title="${a.desc}">${a.ticker}</a>`).join('')}
        </div>`).join('')}
      </div>
    </div>
  </div>`;
}

const TICKER_NAMES = {
  'QQQ': 'Nasdaq-100 ETF', 'VOO': 'S&P 500 ETF (Vanguard)', 'SPY': 'S&P 500 ETF (SPDR)',
  'VTI': 'Total US Market ETF', 'DIA': 'Dow Jones Industrial Average ETF',
  'IWF': 'Russell 1000 Growth ETF', 'IWD': 'Russell 1000 Value ETF', 'IVE': 'S&P 500 Value ETF', 'IJR': 'S&P SmallCap 600 ETF',
  'VXUS': 'International ex-US ETF', 'EEM': 'Emerging Markets ETF', 'IWM': 'Russell 2000 ETF',
  'VEA': 'Developed ex-US ETF', 'VWO': 'Emerging Markets ETF', 'IEMG': 'Emerging Markets ETF', 'EFA': 'Developed Markets ETF',
  'EWJ': 'Japan ETF', 'EWG': 'Germany ETF', 'EWU': 'United Kingdom ETF', 'INDA': 'India ETF',
  'SPMO': 'S&P 500 Momentum ETF', 'SCHG': 'Large-Cap Growth ETF', 'VBR': 'Small-Cap Value ETF', 'VIG': 'Dividend Appreciation ETF',
  'SCHD': 'Dividend Equity ETF', 'QUAL': 'Quality Factor ETF', 'MTUM': 'Momentum Factor ETF', 'USMV': 'Min Volatility ETF',
  'MDY': 'S&P MidCap 400 ETF', 'IJH': 'S&P MidCap 400 ETF', 'IWO': 'Russell 2000 Growth ETF', 'IWN': 'Russell 2000 Value ETF',
  'VGT': 'Technology Sector ETF', 'SOXX': 'Semiconductor ETF', 'XLE': 'Energy Sector ETF', 'XLB': 'Materials Sector ETF',
  'XLI': 'Industrials Sector ETF', 'XLP': 'Consumer Staples Sector ETF', 'XLV': 'Healthcare Sector ETF', 'XLF': 'Financials Sector ETF',
  'XLK': 'Technology Sector ETF', 'XLU': 'Utilities Sector ETF', 'XLY': 'Consumer Discretionary Sector ETF', 'XLRE': 'Real Estate Sector ETF',
  'SMH': 'Semiconductor ETF', 'XBI': 'Biotechnology ETF',
  'TQQQ': '3× Nasdaq-100 (leveraged)', 'UPRO': '3× S&P 500 (leveraged)', 'TMF': '3× 20-yr Treasury (leveraged)',
  'GLD': 'Gold ETF', 'IAU': 'Gold Trust ETF', 'SLV': 'Silver ETF', 'VNQ': 'US REIT ETF',
  'DBC': 'Broad Commodities ETF', 'USO': 'US Oil Fund', 'UNG': 'Natural Gas ETF', 'BTC-USD': 'Bitcoin',
  'BND': 'Total Bond Market ETF', 'AGG': 'Aggregate Bond ETF', 'IEF': '7-10 Year Treasury ETF', 'HYG': 'High Yield Bond ETF',
  'LQD': 'Investment Grade Corporate Bond ETF', 'MUB': 'Municipal Bond ETF', 'BSV': 'Short-Term Bond ETF',
  'VCIT': 'Intermediate Corporate Bond ETF', 'EMB': 'Emerging Market Bond ETF', 'BIL': 'Treasury Bill ETF',
  'TIP': 'TIPS ETF', 'TLT': '20-yr Treasury ETF', 'SHY': 'Short-Term Treasury ETF', 'SHV': 'Short Treasury ETF',
  'AAPL': 'Apple', 'MSFT': 'Microsoft', 'NVDA': 'Nvidia', 'AMZN': 'Amazon', 'GOOGL': 'Alphabet',
  'META': 'Meta Platforms', 'TSLA': 'Tesla', 'JPM': 'JPMorgan Chase', 'UNH': 'UnitedHealth Group', 'BRK-B': 'Berkshire Hathaway B',
};

function tickerLabel(t) {
  return TICKER_NAMES[t] ? `<strong>${t}</strong> <span class="ticker-desc">(${TICKER_NAMES[t]})</span>` : `<strong>${t}</strong>`;
}

function rebalanceFreq(rule) {
  if (rule.includes('monthly'))   return 'on the 1st business day of each month';
  if (rule.includes('quarterly')) return 'on the 1st business day of Jan, Apr, Jul, and Oct';
  return 'once a year (e.g., every January 1st)';
}

function universeChips(tickers) {
  return tickers.map(t => `<span class="chip chip--sm" title="${TICKER_NAMES[t] || t}">${t}</span>`).join(' ');
}

function buildInstructions(strategyName, rebalanceRule) {
  const freq = rebalanceFreq(rebalanceRule);

  if (strategyName.startsWith('FixedWeight')) {
    const allocs = [...strategyName.matchAll(/([A-Z0-9\-]+):([\d.]+)%/g)]
      .map(([, t, p]) => ({ ticker: t, pct: parseFloat(p) }));
    const holdList = allocs.map(a => `${a.pct}% in ${tickerLabel(a.ticker)}`).join(', ');
    const tickers = allocs.map(a => a.ticker);
    return {
      what: allocs.map(a => ({ ticker: a.ticker, pct: a.pct })),
      universe: { label: `Fixed — only these ${tickers.length} funds`, chips: universeChips(tickers) },
      steps: [
        `Set your 401k fund allocations to: ${holdList}.`,
        `Check your balance ${freq}. If any fund has drifted more than 5 percentage points from its target, rebalance it back.`,
        'Hold through all market conditions — no other action needed.',
      ],
      when: rebalanceRule,
      effort: 'Low — one action per rebalance period, no ongoing monitoring',
    };
  }

  if (strategyName.startsWith('EqualWeight')) {
    return {
      universe: { label: 'All assets in the universe — every one held simultaneously', chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        'Divide your account equally across all assets in the universe.',
        `Rebalance ${freq}: bring every asset back to equal weight. Sell what is over, buy what is under.`,
        'No signals or calculations required — simple equal weighting every period.',
      ],
      when: rebalanceRule,
      effort: 'Low — no calculations, just restore equal weights each period',
    };
  }

  if (strategyName.startsWith('MomentumRotation')) {
    const top = strategyName.match(/top(\d+)/i)?.[1] || '?';
    const eachPct = (100 / parseInt(top)).toFixed(0);
    return {
      universe: { label: `Selects from all assets in the universe — holds top ${top} at any given time`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, look up the 12-month total return for every asset in the universe.`,
        `Rank them. Buy the top ${top} by equal weight (${eachPct}% each). Sell anything not in the top ${top}.`,
        `If a fund has fewer than 12 months of data, skip it. Fill missing slots with ${tickerLabel('SHY')} as a cash proxy.`,
      ],
      when: rebalanceRule,
      effort: 'Medium — requires pulling 12-month return data every month',
    };
  }

  if (strategyName.startsWith('DualMomentum')) {
    return {
      universe: { label: 'Chooses between 2 equity ETFs; falls back to bonds', chips: universeChips(['QQQ', 'VXUS', 'BND', 'SHY']) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, compare the 12-month total return of ${tickerLabel('QQQ')} vs ${tickerLabel('VXUS')}.`,
        `The winner is whichever beat the other. Now compare that winner's 12-month return vs ${tickerLabel('SHY')} (cash proxy).`,
        `If the equity winner beats SHY → put 100% into that ETF. If it doesn't → put 100% into ${tickerLabel('BND')} (bonds). Repeat each month.`,
      ],
      when: rebalanceRule,
      effort: 'Medium — two 12-month return comparisons per month, one fund to hold',
    };
  }

  if (strategyName.startsWith('TrendFollowing')) {
    const riskyTickers = ['QQQ', 'VOO', 'SPY', 'VTI', 'VXUS', 'SPMO', 'SCHG', 'VBR', 'VGT', 'SOXX'];
    return {
      universe: { label: `Monitors ${riskyTickers.length} risky ETFs; shifts to BND below trend`, chips: universeChips([...riskyTickers, 'BND']) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, look up the 200-day moving average for each risky ETF in the universe.`,
        `Hold each ETF that is currently <em>above</em> its 200-day MA in equal weight. For any ETF trading <em>below</em> its 200-day MA, hold ${tickerLabel('BND')} in its place.`,
        'When an ETF crosses back above its 200-day MA next month, switch it back from BND to the ETF.',
      ],
      when: rebalanceRule,
      effort: 'Medium — need 200-day MA for each fund monthly',
    };
  }

  if (strategyName.startsWith('MaxSharpe')) {
    return {
      universe: { label: 'Optimizes across all assets in the universe — actual holdings vary by quarter', chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        'At the start of each quarter, download the past 36 months of price data for all assets in the universe.',
        'Run a mean-variance optimization (e.g., in Python or a spreadsheet) to find the portfolio weights that maximize the Sharpe ratio.',
        'Rebalance your account to those computed weights. The output changes each quarter based on the rolling 3-year history.',
      ],
      when: rebalanceRule,
      effort: 'High — requires an optimization tool or spreadsheet with solver',
    };
  }

  if (strategyName.startsWith('MinVariance')) {
    return {
      universe: { label: 'Optimizes across all assets in the universe — typically concentrates in low-volatility assets', chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        'At the start of each quarter, download the past 36 months of price data for all assets in the universe.',
        'Run a minimum-variance optimization to find the weight mix that minimizes total portfolio volatility (regardless of return).',
        'Rebalance to those weights. Expect heavy allocation to low-volatility assets like bonds and gold.',
      ],
      when: rebalanceRule,
      effort: 'High — requires an optimization tool or spreadsheet with solver',
    };
  }

  if (strategyName.startsWith('RiskParity')) {
    return {
      universe: { label: 'All assets in the universe held simultaneously, sized by inverse volatility', chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, calculate the 3-month return volatility (std dev of daily returns) for each asset in the universe.`,
        'Set each fund\'s weight proportional to 1 ÷ its volatility, then normalize so all weights sum to 100%.',
        'Rebalance to those weights. Low-volatility assets (bonds, gold) will receive a higher weight than high-volatility ones (equities, crypto).',
      ],
      when: rebalanceRule,
      effort: 'Medium — needs 3-month volatility calculation per fund monthly',
    };
  }

  if (strategyName.startsWith('AdaptiveAA')) {
    const top = strategyName.match(/top(\d+)/i)?.[1] || '?';
    return {
      universe: { label: `Selects from all assets in the universe — holds top ${top} by risk-adjusted momentum`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, compute a score for each asset: score = (12-month return) ÷ (3-month volatility). Only assets with positive 12-month momentum qualify.`,
        `Keep the top ${top} highest-scoring assets. Set each asset's weight proportional to 1 ÷ its 3-month volatility (lower volatility → bigger share). Normalize weights to 100%.`,
        `Sell all assets not in the top ${top}. Rebalance to the new weights. If fewer than ${top} assets have positive momentum, hold ${tickerLabel('SHY')} for the missing slots.`,
      ],
      when: rebalanceRule,
      effort: 'Medium-High — needs 12-month return and 3-month volatility per fund monthly',
    };
  }

  if (strategyName.startsWith('QqqVooSpyAdaptive')) {
    return {
      universe: { label: 'Fixed 3-fund shortlist — only these ETFs are ever considered', chips: universeChips(['QQQ', 'VOO', 'SPY']) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, compute a score for each of the three funds: score = (12-month return) ÷ (3-month volatility).`,
        `Identify the highest-scoring fund. If it is ${tickerLabel('QQQ')}: hold 100% QQQ.`,
        `If ${tickerLabel('VOO')} or ${tickerLabel('SPY')} has the highest score: hold 50% VOO + 50% SPY (split S&P 500 exposure between both to reduce fund-specific risk).`,
      ],
      when: rebalanceRule,
      effort: 'Low — only 3 funds to score, one monthly decision',
    };
  }

  return { steps: ['Refer to strategy documentation for implementation details.'], when: rebalanceRule, effort: 'Unknown' };
}

function backtestMethodCard() {
  return `
  <div class="method-card">
    <div class="method-heading">Backtest Method</div>
    <div class="method-copy">The backtest walks forward one trading day at a time. On each rebalance date it computes signals using only price history up to that day, then allocates the portfolio across the selected assets from the fixed universe. Prices are tracked with adjusted close for total-return accounting, and raw close is shown in the trade log when it differs.</div>
  </div>`;
}

function strategyGuide(results, mdMap, repoUrl) {
  if (results.length === 0) return '';
  const medals = ['🥇', '🥈', '🥉'];
  return `
  <div class="guide-card">
    <h2>Implementation Guide — Ranked by Sharpe</h2>
    <p class="guide-intro">Expand each strategy to see what it does, the exact rebalance rule, and its trade history from the fixed preselected asset universe. Ranked by Sharpe ratio.</p>
    <div class="guide-price-key"><span class="guide-price-key-item"><span class="guide-price-swatch guide-price-swatch--same"></span> Blue: adjusted close matches raw close</span><span class="guide-price-key-item"><span class="guide-price-swatch guide-price-swatch--diff"></span> Yellow: adjusted close differs from raw close</span></div>
    ${results.map((r, i) => {
      const rank = i + 1;
      const m = r.metrics;
      const md = mdMap[r.strategy] || {};
      const mdLink = (md.folder && repoUrl)
        ? `${repoUrl}/blob/main/data/strategies/${md.folder}/strategy.md`
        : '';
      const isTop = rank <= 3;
      const medal = medals[i] || '';
      return `
    <details class="guide-strategy" id="${toAnchorId(r.label)}" ${isTop ? 'open' : ''}>
      <summary class="guide-summary">
        <div class="guide-summary-left">
          <span class="guide-rank-badge rank-${rank <= 3 ? rank : 'other'}">${medal || '#' + rank}</span>
          <div>
            <div class="guide-strategy-name">
              ${r.label}
              ${mdLink ? `<a class="guide-md-link" href="${mdLink}" target="_blank" title="View strategy spec">spec&nbsp;↗</a>` : ''}
            </div>
            <div class="guide-summary-metrics">
              Sharpe&nbsp;<strong>${fmt.num(m.sharpe)}</strong>
              &nbsp;·&nbsp; CAGR&nbsp;<strong class="${m.cagr >= 0 ? 'pos' : 'neg'}">${fmt.pct(m.cagr)}</strong>
              &nbsp;·&nbsp; Max&nbsp;DD&nbsp;<strong class="neg">${fmt.pct(m.max_drawdown)}</strong>
              &nbsp;·&nbsp; $10k&nbsp;→&nbsp;<strong>${fmt.money(10000 * (1 + (m.total_return || 0)))}</strong>
            </div>
          </div>
        </div>
        <span class="guide-chevron">›</span>
      </summary>
      <div class="guide-body">
        ${md.description ? `
        <div class="guide-section-label">What it does</div>
        <p class="guide-description">${md.description}</p>` : ''}
        <div class="guide-section-label">Step-by-step</div>
        <ol class="guide-steps">
          ${renderLogicMd(md.logic)}
        </ol>
        ${r.rebalance_log && r.rebalance_log.length > 0 ? `
        <div class="guide-section-label">Trade history (${r.rebalance_log.length} rebalances over backtest period)</div>
        <div class="trade-log-note">Backtest accounting uses adjusted close. The price color tells you whether the adjusted close matches the raw market close (blue) or differs from it (yellow).</div>
        <div class="trade-log-wrap">
          <table class="trade-log">
            <thead><tr><th>Date</th><th>Portfolio value</th><th>Holdings after rebalance (adjusted-close backtest accounting)</th></tr></thead>
            <tbody>
              ${r.rebalance_log.map(e => `
              <tr>
                <td class="tl-date">${e.date}</td>
                <td class="tl-val">${fmt.money(e.portfolio_value)}</td>
                <td class="tl-holdings">${renderTradeHoldings(e)}</td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>` : `
        <div class="trade-log-empty">Trade history available after next backtest run.</div>`}
        <div class="guide-meta-row">
          <span class="guide-meta-item"><span class="guide-meta-label">Rebalance</span> ${r.rebalance_rule.replace('Calendar(', '').replace(')', '')}</span>
        </div>
      </div>
    </details>`;
    }).join('')}
  </div>`;
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
      <td class="td-rank" data-val="${rank}">${rank}</td>
      <td class="td-label" data-val="${r.label}" title="${getStrategyNotes(r.strategy) || r.strategy}"><a class="strategy-anchor" href="#${toAnchorId(r.label)}">${r.label}</a></td>
      ${pctCell(m.cagr)}
      <td data-val="${m.sharpe ?? ''}"><strong>${fmt.num(m.sharpe)}</strong></td>
      ${numCell(m.sortino)}
      ${pctCell(m.max_drawdown)}
      ${numCell(m.calmar)}
      ${pctCell(m.volatility)}
      <td data-val="${m.recovery_months ?? 9999}">${m.recovery_months != null ? m.recovery_months + 'mo' : '—'}</td>
      ${pctCell(m.best_year)}
      ${pctCell(m.worst_year)}
      ${pctCell(m.return_2022)}
      ${pctCell(m.covid_crash)}
    </tr>`;
  }).join('');
  return `
  <table id="resultsTable">
    <thead>
      <tr>
        <th data-col="0">#</th>
        <th data-col="1">Strategy | Rule</th>
        <th data-col="2">CAGR</th>
        <th data-col="3">Sharpe</th>
        <th data-col="4">Sortino</th>
        <th data-col="5">Max&nbsp;DD</th>
        <th data-col="6">Calmar</th>
        <th data-col="7">Vol</th>
        <th data-col="8">Recovery</th>
        <th data-col="9">Best&nbsp;Yr</th>
        <th data-col="10">Worst&nbsp;Yr</th>
        <th data-col="11">2022</th>
        <th data-col="12">COVID</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function generateHtml(results, total, isFinal, profile, mdMap, repoUrl) {
  const completed = results.length;
  const pct = Math.round(100 * completed / Math.max(total, 1));
  const isDone = isFinal || completed >= total;
  const refreshTag = isDone ? '' : '<meta http-equiv="refresh" content="5">';
  const statusMsg = isDone ? 'Complete' : `Running… auto-refreshing every 5 s`;
  const generatedAt = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

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
                  box-shadow: 0 1px 3px rgba(0,0,0,0.07); margin-bottom: 1.5rem;
                  overflow: hidden; }
    .chart-card h2 { font-size: 0.9rem; font-weight: 600; color: #444;
                     text-transform: uppercase; letter-spacing: 0.05em;
                     margin-bottom: 1rem; }
    .chart-note { font-size: 0.76rem; color: #666; margin: -0.4rem 0 0.7rem; line-height: 1.4; }
    .chart-wrap { position: relative; height: 640px; }
    .method-card { background: white; border-radius: 14px; padding: 1.25rem 1.5rem;
                   box-shadow: 0 1px 3px rgba(0,0,0,0.07); margin-bottom: 1.5rem; }
    .method-heading { font-size: 0.75rem; font-weight: 600; color: #888;
                      text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
    .method-copy { font-size: 0.82rem; color: #555; line-height: 1.55; }

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
    .strategy-anchor { color: inherit; text-decoration: none; }
    .strategy-anchor:hover { color: #2196f3; text-decoration: underline; }
    html { scroll-behavior: smooth; }
    tr.rank-1 td { background: #fffde7; }
    tr.rank-2 td { background: #fafafa; }
    tr.rank-3 td { background: #fff8f5; }
    tr:hover td { background: #eef4ff !important; }
    .empty { text-align: center; color: #aaa; padding: 3rem; font-size: 0.9rem; }
    .pos { color: #2e7d32; }
    .neg { color: #c62828; }
    .card-total { font-size: 0.78rem; color: #888; margin-top: 0.25rem; }
    th { position: relative; }
    th.sort-asc::after { content: ' ▲'; font-size: 0.65em; color: #2196f3; }
    th.sort-desc::after { content: ' ▼'; font-size: 0.65em; color: #2196f3; }

    /* Context card */
    .context-card { background: white; border-radius: 14px; padding: 1.25rem 1.5rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.07); margin-bottom: 1.5rem;
                    display: flex; gap: 2rem; flex-wrap: wrap; }
    .context-section { flex: 0 0 auto; }
    .context-section--wide { flex: 1 1 auto; }
    .context-heading { font-size: 0.75rem; font-weight: 600; color: #888;
                       text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem; }
    .context-note { font-size: 0.78rem; color: #555; line-height: 1.5; margin-bottom: 0.75rem; max-width: 920px; }
    .profile-grid { display: flex; gap: 1.25rem; flex-wrap: wrap; }
    .pf-item { display: flex; flex-direction: column; gap: 0.1rem; }
    .pf-label { font-size: 0.7rem; color: #aaa; text-transform: uppercase; letter-spacing: 0.04em; }
    .pf-val { font-size: 1rem; font-weight: 600; color: #1a1a2e; }

    /* Asset universe */
    .universe-groups { display: flex; flex-direction: column; gap: 0.5rem; }
    .asset-group { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }
    .asset-cat { font-size: 0.68rem; color: #aaa; text-transform: uppercase;
                 letter-spacing: 0.04em; min-width: 110px; flex-shrink: 0; }
    .chip { display: inline-block; padding: 2px 7px; background: #eef4ff; border-radius: 99px;
            font-size: 0.72rem; font-weight: 500; color: #1565c0; cursor: default; }
    .chip--link { text-decoration: none; }
    .chip--link:hover { background: #dbeafe; }

    /* Implementation guide */
    .guide-card { background: white; border-radius: 14px; padding: 1.5rem;
                  box-shadow: 0 1px 3px rgba(0,0,0,0.07); margin-top: 1.5rem; }
    .guide-card h2 { font-size: 0.9rem; font-weight: 600; color: #444;
                     text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem; }
    .guide-intro { font-size: 0.82rem; color: #888; margin-bottom: 1.25rem; line-height: 1.5; }
    .guide-price-key { display: flex; flex-wrap: wrap; gap: 0.75rem 1rem; margin: -0.5rem 0 1rem; font-size: 0.75rem; color: #666; }
    .guide-price-key-item { display: inline-flex; align-items: center; gap: 0.4rem; }
    .guide-price-swatch { width: 0.65rem; height: 0.65rem; border-radius: 2px; flex: 0 0 auto; }
    .guide-price-swatch--same { background: #1565c0; }
    .guide-price-swatch--diff { background: #b8860b; }
    .guide-strategy { border: 1px solid #eef0f4; border-radius: 10px; margin-bottom: 0.5rem; overflow: hidden; }
    .guide-strategy[open] { border-color: #c8deff; }
    .guide-summary { display: flex; align-items: center; justify-content: space-between;
                     padding: 0.85rem 1rem; cursor: pointer; list-style: none; gap: 1rem;
                     background: #fafbfc; }
    .guide-strategy[open] .guide-summary { background: #eef4ff; }
    .guide-summary::-webkit-details-marker { display: none; }
    .guide-summary-left { display: flex; align-items: center; gap: 0.85rem; flex: 1; min-width: 0; }
    .guide-rank-badge { flex-shrink: 0; font-size: 1.2rem; width: 2.2rem; text-align: center; }
    .rank-1 { color: #f9a825; } .rank-2 { color: #90a4ae; } .rank-3 { color: #a1887f; }
    .rank-other { font-size: 0.8rem; font-weight: 700; color: #aaa; }
    .guide-strategy-name { font-size: 0.85rem; font-weight: 600; color: #1a1a2e; white-space: nowrap;
                           overflow: hidden; text-overflow: ellipsis; }
    .guide-summary-metrics { font-size: 0.75rem; color: #777; margin-top: 0.1rem; }
    .guide-chevron { color: #aaa; font-size: 1.2rem; flex-shrink: 0;
                     transition: transform 0.2s; }
    .guide-strategy[open] .guide-chevron { transform: rotate(90deg); }
    .guide-body { padding: 1rem 1.25rem 1.25rem; border-top: 1px solid #eef0f4; }
    .guide-section-label { font-size: 0.7rem; font-weight: 700; color: #aaa;
                           text-transform: uppercase; letter-spacing: 0.06em; margin: 1rem 0 0.5rem; }
    .guide-section-label:first-child { margin-top: 0; }
    .guide-alloc-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.25rem; }
    .guide-alloc-item { background: #eef4ff; border-radius: 8px; padding: 0.5rem 0.75rem;
                        text-align: center; min-width: 80px; }
    .guide-alloc-pct { font-size: 1.1rem; font-weight: 800; color: #1565c0; }
    .guide-alloc-ticker { font-size: 0.78rem; font-weight: 700; color: #1a1a2e; }
    .guide-alloc-name { font-size: 0.68rem; color: #888; margin-top: 0.1rem; }
    .guide-steps { margin: 0; padding-left: 1.4rem; display: flex; flex-direction: column; gap: 0.45rem; }
    .guide-steps li { font-size: 0.82rem; color: #333; line-height: 1.55; }
    .ticker-desc { color: #888; font-weight: 400; }
    .guide-meta-row { display: flex; gap: 2rem; flex-wrap: wrap; margin-top: 1rem;
                      padding-top: 0.75rem; border-top: 1px solid #f0f2f5; }
    .guide-meta-item { font-size: 0.75rem; color: #666; }
    .guide-meta-label { font-weight: 600; color: #aaa; text-transform: uppercase;
                        font-size: 0.68rem; letter-spacing: 0.04em; display: block; margin-bottom: 0.1rem; }
    .guide-description { font-size: 0.82rem; color: #555; line-height: 1.6; margin-bottom: 0.25rem; }
    .guide-md-link { font-size: 0.68rem; font-weight: 500; color: #2196f3; text-decoration: none;
                     margin-left: 0.5rem; padding: 1px 5px; border: 1px solid #c8deff;
                     border-radius: 4px; vertical-align: middle; }
    .guide-md-link:hover { background: #eef4ff; }
    .chart-legend { display: flex; flex-wrap: wrap; gap: 0.55rem 1rem; margin: 0.25rem 0 0.9rem; }
    .chart-legend-item { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.72rem; color: #666; line-height: 1.2; }
    .chart-legend-swatch { width: 0.8rem; height: 0.8rem; border: 2px solid currentColor; border-radius: 2px; flex: 0 0 auto; }
    .chart-legend-label { white-space: nowrap; }
    .guide-universe { margin-bottom: 0.25rem; }
    .guide-universe-label { font-size: 0.76rem; color: #555; display: block; margin-bottom: 0.4rem; font-style: italic; }
    .guide-universe-chips { display: flex; flex-wrap: wrap; gap: 0.3rem; }
    .chip--sm { font-size: 0.65rem; padding: 1px 5px; }
    .trade-log-wrap { max-height: 260px; overflow-y: auto; border: 1px solid #eef0f4;
                      border-radius: 8px; font-size: 0.76rem; }
    .trade-log { width: 100%; border-collapse: collapse; }
    .trade-log thead { position: sticky; top: 0; background: #f8f9fc; }
    .trade-log th { padding: 6px 10px; text-align: left; font-size: 0.68rem; color: #888;
                    text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid #eef0f4; }
    .trade-log td { padding: 5px 10px; border-bottom: 1px solid #f5f6f8; vertical-align: top; }
    .trade-log tr:last-child td { border-bottom: none; }
    .tl-date { white-space: nowrap; color: #666; font-variant-numeric: tabular-nums; width: 90px; }
    .tl-val { white-space: nowrap; color: #1a1a2e; font-weight: 600; width: 90px; }
    .tl-holdings { display: flex; flex-wrap: wrap; gap: 0.25rem; min-width: 260px; }
    .tl-chip { display: inline-block; background: #eef4ff; color: #1565c0; border-radius: 4px;
               padding: 1px 5px; font-size: 0.7rem; font-weight: 500; white-space: nowrap; }
    .tl-chip a { color: #1565c0; text-decoration: none; }
    .tl-chip a:hover { text-decoration: underline; }
    .tl-chip--detail { display: inline-flex; align-items: baseline; gap: 0.35rem; }
    .tl-cost { color: #445; font-weight: 500; font-variant-numeric: tabular-nums; }
    .tl-price { font-variant-numeric: tabular-nums; }
    .tl-price--same { color: #1565c0; font-weight: 600; }
    .tl-price--diff { color: #b8860b; font-weight: 600; }
    .trade-log-note { font-size: 0.76rem; color: #666; margin: 0.15rem 0 0.5rem; }
    .trade-log-empty { font-size: 0.78rem; color: #aaa; font-style: italic; padding: 0.5rem 0; }
  </style>
</head>
<body>
  <div class="container">
    <h1>401k Strategy Backtest</h1>
    <p class="subtitle">${statusMsg} &nbsp;&middot;&nbsp; ${completed}&thinsp;/&thinsp;${total} strategies complete &nbsp;&middot;&nbsp; ${generatedAt}</p>

    <div class="progress-card">
      <div class="progress-header"><span>Progress</span><span>${pct}%</span></div>
      <div class="progress-bar-bg"><div class="progress-bar-fill"></div></div>
    </div>

    ${summaryCards(results)}
    ${equityChart(results)}
    ${backtestMethodCard()}
    ${profileContextCard(profile)}

    <div class="table-card">
      <h2>All Strategies &mdash; Ranked by Sharpe</h2>
      ${resultsTable(results)}
    </div>

    ${strategyGuide(results, mdMap, repoUrl)}
  </div>
  <script>
  // Open the target <details> card when navigating via anchor link
  (function() {
    function openTarget() {
      const id = location.hash.slice(1);
      if (!id) return;
      const el = document.getElementById(id);
      if (el && el.tagName === 'DETAILS') el.open = true;
    }
    openTarget();
    window.addEventListener('hashchange', openTarget);
    document.querySelectorAll('a.strategy-anchor').forEach(a => {
      a.addEventListener('click', () => setTimeout(openTarget, 50));
    });
  })();
  </script>
  <script>
  (function() {
    const table = document.getElementById('resultsTable');
    if (!table) return;
    let sortCol = 3, sortAsc = false;
    function sortTable(col, asc) {
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.rows);
      rows.sort((a, b) => {
        const av = parseFloat(a.cells[col]?.dataset?.val) || 0;
        const bv = parseFloat(b.cells[col]?.dataset?.val) || 0;
        return asc ? av - bv : bv - av;
      });
      rows.forEach(r => tbody.appendChild(r));
      table.querySelectorAll('th').forEach((th, i) => {
        th.classList.toggle('sort-asc', i === col && asc);
        th.classList.toggle('sort-desc', i === col && !asc);
      });
    }
    table.querySelectorAll('th').forEach((th, col) => {
      th.addEventListener('click', () => {
        if (sortCol === col) sortAsc = !sortAsc;
        else { sortCol = col; sortAsc = col <= 1; }
        sortTable(sortCol, sortAsc);
      });
    });
    sortTable(sortCol, sortAsc);
  })();
  </script>
</body>
</html>`;
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
  const opts = parseArgs();
  const results = loadResults(opts.resultsDir);
  const total = opts.total || results.length;
  const profile = loadProfile(opts.profile);
  const strategiesDir = path.resolve(path.dirname(opts.output), '..', 'strategies');
  const mdMap = loadStrategyMdMap(strategiesDir);
  const repoUrl = getRepoUrl();
  const html = generateHtml(results, total, opts.final, profile, mdMap, repoUrl);

  const outPath = path.resolve(opts.output);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, html, 'utf8');

  console.log(`[report-generator] ${results.length}/${total} complete → ${opts.output}`);
}

main();
