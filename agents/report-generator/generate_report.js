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

const fs = require('fs');
const path = require('path');

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

// ── Domain knowledge ──────────────────────────────────────────────────────────

const ASSET_UNIVERSE = [
  { ticker: 'QQQ',     category: 'Broad ETF',        desc: 'Nasdaq-100 — top 100 non-financial US tech stocks' },
  { ticker: 'VOO',     category: 'Broad ETF',        desc: 'S&P 500 (Vanguard) — 500 largest US companies' },
  { ticker: 'SPY',     category: 'Broad ETF',        desc: 'S&P 500 (SPDR) — most liquid US equity ETF' },
  { ticker: 'VTI',     category: 'Broad ETF',        desc: 'Total US market — large, mid, and small cap' },
  { ticker: 'VXUS',    category: 'Broad ETF',        desc: 'International ex-US — developed + emerging markets' },
  { ticker: 'EEM',     category: 'Broad ETF',        desc: 'Emerging markets — China, India, Brazil, etc.' },
  { ticker: 'IWM',     category: 'Broad ETF',        desc: 'Russell 2000 — US small-cap stocks' },
  { ticker: 'SPMO',    category: 'Factor ETF',       desc: 'S&P 500 momentum — strongest recent performers' },
  { ticker: 'SCHG',    category: 'Factor ETF',       desc: 'US large-cap growth — high-growth large companies' },
  { ticker: 'VBR',     category: 'Factor ETF',       desc: 'US small-cap value — cheap small companies' },
  { ticker: 'VGT',     category: 'Sector ETF',       desc: 'Information technology sector' },
  { ticker: 'SOXX',    category: 'Sector ETF',       desc: 'Semiconductors sector' },
  { ticker: 'XLE',     category: 'Sector ETF',       desc: 'Energy sector — oil, gas, pipelines' },
  { ticker: 'XLV',     category: 'Sector ETF',       desc: 'Healthcare sector — pharma, biotech, insurance' },
  { ticker: 'XLF',     category: 'Sector ETF',       desc: 'Financials sector — banks, insurance, asset managers' },
  { ticker: 'TQQQ',    category: 'Leveraged ETF',    desc: '3× Nasdaq-100 — high risk, high reward' },
  { ticker: 'UPRO',    category: 'Leveraged ETF',    desc: '3× S&P 500 — high risk, high reward' },
  { ticker: 'TMF',     category: 'Leveraged ETF',    desc: '3× 20-yr Treasuries — inverse of rate hikes' },
  { ticker: 'GLD',     category: 'Alternative',      desc: 'Gold — inflation hedge and safe haven' },
  { ticker: 'VNQ',     category: 'Alternative',      desc: 'US REITs — real estate income' },
  { ticker: 'DBC',     category: 'Alternative',      desc: 'Broad commodities — oil, metals, agriculture basket' },
  { ticker: 'BTC-USD', category: 'Alternative',      desc: 'Bitcoin — high-volatility digital asset' },
  { ticker: 'BND',     category: 'Fixed Income',     desc: 'Total bond market — investment-grade US bonds' },
  { ticker: 'HYG',     category: 'Fixed Income',     desc: 'High-yield bonds — junk bonds, equity-like risk' },
  { ticker: 'TIP',     category: 'Fixed Income',     desc: 'TIPS — Treasury bonds indexed to inflation' },
  { ticker: 'TLT',     category: 'Fixed Income',     desc: '20-yr Treasuries — rate-sensitive long bonds' },
  { ticker: 'SHY',     category: 'Fixed Income',     desc: '1-3 yr Treasuries — near-cash, minimal rate risk' },
  { ticker: 'AAPL',    category: 'Mega-Cap Stock',   desc: 'Apple' },
  { ticker: 'MSFT',    category: 'Mega-Cap Stock',   desc: 'Microsoft' },
  { ticker: 'NVDA',    category: 'Mega-Cap Stock',   desc: 'Nvidia' },
  { ticker: 'AMZN',    category: 'Mega-Cap Stock',   desc: 'Amazon' },
  { ticker: 'GOOGL',   category: 'Mega-Cap Stock',   desc: 'Alphabet' },
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

function profileContextCard(profile) {
  const fields = [];
  if (profile?.accountType) fields.push(['Account', profile.accountType.toUpperCase()]);
  if (profile?.age) fields.push(['Age', profile.age]);
  if (profile?.yearsToRetirement) fields.push(['Horizon', profile.yearsToRetirement + ' years']);
  if (profile?.riskTolerance) fields.push(['Risk', profile.riskTolerance.charAt(0).toUpperCase() + profile.riskTolerance.slice(1)]);
  if (profile?.minBacktestYears) fields.push(['Backtest', profile.minBacktestYears + ' yr history']);

  const grouped = {};
  for (const a of ASSET_UNIVERSE) {
    if (!grouped[a.category]) grouped[a.category] = [];
    grouped[a.category].push(a);
  }

  return `
  <div class="context-card">
    <div class="context-section">
      <div class="context-heading">Investor Profile</div>
      <div class="profile-grid">
        ${fields.map(([k, v]) => `<div class="pf-item"><span class="pf-label">${k}</span><span class="pf-val">${v}</span></div>`).join('')}
      </div>
    </div>
    <div class="context-section context-section--wide">
      <div class="context-heading">Asset Universe (${ASSET_UNIVERSE.length} instruments)</div>
      <div class="universe-groups">
        ${Object.entries(grouped).map(([cat, assets]) => `
        <div class="asset-group">
          <span class="asset-cat">${cat}</span>
          ${assets.map(a => `<span class="chip" title="${a.desc}">${a.ticker}</span>`).join('')}
        </div>`).join('')}
      </div>
    </div>
  </div>`;
}

const TICKER_NAMES = {
  'QQQ': 'Nasdaq-100 ETF', 'VOO': 'S&P 500 ETF (Vanguard)', 'SPY': 'S&P 500 ETF (SPDR)',
  'VTI': 'Total US Market ETF', 'VXUS': 'International ex-US ETF',
  'SPMO': 'S&P 500 Momentum ETF', 'SCHG': 'Large-Cap Growth ETF', 'VBR': 'Small-Cap Value ETF',
  'VGT': 'Technology Sector ETF', 'SOXX': 'Semiconductor ETF',
  'TQQQ': '3× Nasdaq-100 (leveraged)', 'UPRO': '3× S&P 500 (leveraged)', 'TMF': '3× 20-yr Treasury (leveraged)',
  'GLD': 'Gold ETF', 'VNQ': 'US REIT ETF', 'BTC-USD': 'Bitcoin',
  'BND': 'Total Bond Market ETF', 'TLT': '20-yr Treasury ETF', 'SHY': 'Short-Term Treasury ETF',
  'AAPL': 'Apple', 'MSFT': 'Microsoft', 'NVDA': 'Nvidia', 'AMZN': 'Amazon', 'GOOGL': 'Alphabet',
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
  const n = ASSET_UNIVERSE.length;

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
    const m = strategyName.match(/\((\d+) assets\)/);
    const count = m ? parseInt(m[1]) : n;
    const eachPct = (100 / count).toFixed(1);
    return {
      universe: { label: `All ${count} instruments — every one held simultaneously`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `Divide your account equally: ${eachPct}% in each of the ${count} funds in the universe.`,
        `Rebalance ${freq}: bring every fund back to ${eachPct}%. Sell what is over, buy what is under.`,
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
      universe: { label: `Selects from all ${n} instruments — holds top ${top} at any given time`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, look up the 12-month total return for every fund in the universe (${n} funds).`,
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
      universe: { label: `Optimizes across all ${n} instruments — actual holdings vary by quarter`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `At the start of each quarter, download the past 36 months of price data for all ${n} funds.`,
        'Run a mean-variance optimization (e.g., in Python or a spreadsheet) to find the portfolio weights that maximize the Sharpe ratio.',
        'Rebalance your account to those computed weights. The output changes each quarter based on the rolling 3-year history.',
      ],
      when: rebalanceRule,
      effort: 'High — requires an optimization tool or spreadsheet with solver',
    };
  }

  if (strategyName.startsWith('MinVariance')) {
    return {
      universe: { label: `Optimizes across all ${n} instruments — typically concentrates in low-volatility assets`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `At the start of each quarter, download the past 36 months of price data for all ${n} funds.`,
        'Run a minimum-variance optimization to find the weight mix that minimizes total portfolio volatility (regardless of return).',
        'Rebalance to those weights. Expect heavy allocation to low-volatility assets like bonds and gold.',
      ],
      when: rebalanceRule,
      effort: 'High — requires an optimization tool or spreadsheet with solver',
    };
  }

  if (strategyName.startsWith('RiskParity')) {
    return {
      universe: { label: `All ${n} instruments held simultaneously, sized by inverse volatility`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, calculate the 3-month return volatility (std dev of daily returns) for each fund.`,
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
      universe: { label: `Selects from all ${n} instruments — holds top ${top} by risk-adjusted momentum`, chips: universeChips(ASSET_UNIVERSE.map(a => a.ticker)) },
      steps: [
        `${freq.charAt(0).toUpperCase() + freq.slice(1)}, compute a score for each fund: score = (12-month return) ÷ (3-month volatility). Only funds with positive 12-month momentum qualify.`,
        `Keep the top ${top} highest-scoring funds. Set each fund's weight proportional to 1 ÷ its 3-month volatility (lower volatility → bigger share). Normalize weights to 100%.`,
        `Sell all funds not in the top ${top}. Rebalance to the new weights. If fewer than ${top} funds have positive momentum, hold ${tickerLabel('SHY')} for the missing slots.`,
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

function strategyGuide(results) {
  if (results.length === 0) return '';
  const medals = ['🥇', '🥈', '🥉'];
  return `
  <div class="guide-card">
    <h2>Implementation Guide — Ranked by Sharpe</h2>
    <p class="guide-intro">Expand each strategy below to see exactly what to buy, when to act, and how to make each trade decision. Strategies are ordered by Sharpe ratio (best risk-adjusted performance first).</p>
    ${results.map((r, i) => {
      const rank = i + 1;
      const m = r.metrics;
      const instr = buildInstructions(r.strategy, r.rebalance_rule);
      const isTop = rank <= 3;
      const medal = medals[i] || '';
      return `
    <details class="guide-strategy" ${isTop ? 'open' : ''}>
      <summary class="guide-summary">
        <div class="guide-summary-left">
          <span class="guide-rank-badge rank-${rank <= 3 ? rank : 'other'}">${medal || '#' + rank}</span>
          <div>
            <div class="guide-strategy-name">${r.label}</div>
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
        ${instr.what ? `
        <div class="guide-section-label">Fixed holdings</div>
        <div class="guide-alloc-row">
          ${instr.what.map(a => `
          <div class="guide-alloc-item">
            <div class="guide-alloc-pct">${a.pct}%</div>
            <div class="guide-alloc-ticker">${a.ticker}</div>
            <div class="guide-alloc-name">${TICKER_NAMES[a.ticker] || ''}</div>
          </div>`).join('')}
        </div>` : ''}
        ${instr.universe ? `
        <div class="guide-section-label">Eligible universe</div>
        <div class="guide-universe">
          <span class="guide-universe-label">${instr.universe.label}</span>
          <div class="guide-universe-chips">${instr.universe.chips}</div>
        </div>` : ''}
        <div class="guide-section-label">Step-by-step</div>
        <ol class="guide-steps">
          ${instr.steps.map(s => `<li>${s}</li>`).join('')}
        </ol>
        ${r.rebalance_log && r.rebalance_log.length > 0 ? `
        <div class="guide-section-label">Trade history (${r.rebalance_log.length} rebalances over backtest period)</div>
        <div class="trade-log-wrap">
          <table class="trade-log">
            <thead><tr><th>Date</th><th>Portfolio value</th><th>Holdings after rebalance</th></tr></thead>
            <tbody>
              ${r.rebalance_log.map(e => `
              <tr>
                <td class="tl-date">${e.date}</td>
                <td class="tl-val">${fmt.money(e.portfolio_value)}</td>
                <td class="tl-holdings">${Object.entries(e.weights).sort((a,b)=>b[1]-a[1]).map(([t,w])=>`<span class="tl-chip" title="${TICKER_NAMES[t]||t}">${t}&nbsp;${(w*100).toFixed(0)}%</span>`).join(' ')}</td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>` : `
        <div class="trade-log-empty">Trade history available after next backtest run.</div>`}
        <div class="guide-meta-row">
          <span class="guide-meta-item"><span class="guide-meta-label">Rebalance frequency</span> ${r.rebalance_rule.replace('Calendar(', '').replace(')', '')}</span>
          <span class="guide-meta-item"><span class="guide-meta-label">Implementation effort</span> ${instr.effort}</span>
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
      <td class="td-label" data-val="${r.label}" title="${getStrategyNotes(r.strategy) || r.strategy}">${r.label}</td>
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

function generateHtml(results, total, isFinal, profile) {
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

    /* Implementation guide */
    .guide-card { background: white; border-radius: 14px; padding: 1.5rem;
                  box-shadow: 0 1px 3px rgba(0,0,0,0.07); margin-top: 1.5rem; }
    .guide-card h2 { font-size: 0.9rem; font-weight: 600; color: #444;
                     text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem; }
    .guide-intro { font-size: 0.82rem; color: #888; margin-bottom: 1.25rem; line-height: 1.5; }
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
    .tl-holdings { display: flex; flex-wrap: wrap; gap: 0.25rem; }
    .tl-chip { display: inline-block; background: #eef4ff; color: #1565c0; border-radius: 4px;
               padding: 1px 5px; font-size: 0.7rem; font-weight: 500; white-space: nowrap; }
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

    ${profileContextCard(profile)}
    ${summaryCards(results)}
    ${equityChart(results)}

    <div class="table-card">
      <h2>All Strategies &mdash; Ranked by Sharpe</h2>
      ${resultsTable(results)}
    </div>

    ${strategyGuide(results)}
  </div>
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
  const html = generateHtml(results, total, opts.final, profile);

  const outPath = path.resolve(opts.output);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, html, 'utf8');

  console.log(`[report-generator] ${results.length}/${total} complete → ${opts.output}`);
}

main();
