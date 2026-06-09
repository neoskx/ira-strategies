"""Generate matplotlib charts and return base64-encoded PNG strings."""

import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def equity_curve_chart(results: list[dict], title: str = "Equity Curves ($100K start)") -> str:
    fig, ax = plt.subplots(figsize=(12, 6))
    for r in results:
        eq = r["equity"]
        ax.plot(eq.index, eq.values / 1000, label=r["label"], linewidth=1.5)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel("Portfolio Value ($K)")
    ax.set_xlabel("Date")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:.0f}K"))
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    return _fig_to_base64(fig)


def drawdown_chart(results: list[dict], title: str = "Drawdown") -> str:
    fig, ax = plt.subplots(figsize=(12, 5))
    for r in results:
        eq = r["equity"]
        rolling_max = eq.cummax()
        dd = (eq - rolling_max) / rolling_max * 100
        ax.plot(dd.index, dd.values, label=r["label"], linewidth=1.2)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel("Drawdown (%)")
    ax.set_xlabel("Date")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.fill_between(results[0]["equity"].index, 0, 0, alpha=0)  # baseline
    return _fig_to_base64(fig)


def annual_returns_heatmap(results: list[dict]) -> str:
    data = {}
    for r in results:
        ar = r["metrics"].get("annual_returns", {})
        data[r["label"]] = ar

    if not data:
        return ""

    all_years = sorted(set(y for d in data.values() for y in d))
    labels = list(data.keys())
    matrix = np.zeros((len(labels), len(all_years)))

    for i, label in enumerate(labels):
        for j, year in enumerate(all_years):
            matrix[i, j] = data[label].get(year, np.nan) * 100

    fig, ax = plt.subplots(figsize=(max(10, len(all_years) * 1.2), max(4, len(labels) * 0.5 + 1)))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=-40, vmax=60)
    ax.set_xticks(range(len(all_years)))
    ax.set_xticklabels(all_years, fontsize=9)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([l[:40] for l in labels], fontsize=7)
    ax.set_title("Annual Returns Heatmap (%)", fontsize=13, fontweight="bold")

    for i in range(len(labels)):
        for j in range(len(all_years)):
            val = matrix[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=6,
                        color="white" if abs(val) > 25 else "black")

    fig.colorbar(im, ax=ax, label="Return (%)")
    return _fig_to_base64(fig)


def sharpe_bar_chart(results: list[dict]) -> str:
    sorted_r = sorted(results, key=lambda r: r["metrics"]["sharpe"], reverse=True)
    labels = [r["label"][:35] for r in sorted_r]
    sharpes = [r["metrics"]["sharpe"] for r in sorted_r]
    colors = ["#2ecc71" if s > 1.0 else "#f39c12" if s > 0.5 else "#e74c3c" for s in sharpes]

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.4 + 1)))
    bars = ax.barh(labels, sharpes, color=colors)
    ax.set_xlabel("Sharpe Ratio")
    ax.set_title("Sharpe Ratio by Strategy (higher = better risk-adjusted)", fontsize=12, fontweight="bold")
    ax.axvline(x=1.0, color="gray", linestyle="--", alpha=0.5, label="Sharpe=1.0")
    for bar, val in zip(bars, sharpes):
        ax.text(val + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=8)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="x")
    return _fig_to_base64(fig)
