import csv
from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import numpy as np

# =========================
# 1. 配置
# =========================
CSV_FILENAME = "cov_input.csv"

base_categories = [
    "Language Tool",
    "NCS",
    "Person Controller",
    "REST Countries",
    "SCS",
    "News Service",
    "Youtube-Mock",
    "Genome Nexus",
    "User Management",
    "Project"
]

categories = [*base_categories, "Average"]

tools = ["HiREST", "RESTler", "EvoMaster", "Morest", "ARAT-RL", "AutoRest"]
run_order = ["1000", "1h"]
metric_order = ["Branch", "Line", "Method"]

wrapped_categories = [textwrap.fill(name, width=12) for name in categories]
wrapped_categories = [
    "Youtube\nMock" if name == "Youtube-Mock"
    else "Genome\nNexus" if name == "Genome Nexus"
    else label
    for name, label in zip(categories, wrapped_categories)
]

series_names = [f"{tool}-{run}" for tool in tools for run in run_order]


def load_coverage_from_csv(csv_path: Path):
    required_columns = ["tool", "run", "metric", *base_categories]
    coverage_data = {
        tool: {
            metric: {run: None for run in run_order}
            for metric in metric_order
        }
        for tool in tools
    }

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV header is missing.")

        missing_columns = [col for col in required_columns if col not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"CSV missing required columns: {missing_columns}")

        for row in reader:
            tool = row["tool"].strip()
            run = row["run"].strip()
            metric = row["metric"].strip()

            if tool not in tools:
                raise ValueError(f"Unknown tool in CSV: {tool}")
            if run not in run_order:
                raise ValueError(f"Unknown run type in CSV: {run}")
            if metric not in metric_order:
                raise ValueError(f"Unknown metric in CSV: {metric}")

            values = []
            for service in categories:
                raw = (row.get(service) or "").strip()
                values.append(float(raw) if raw else 0.0)

            coverage_data[tool][metric][run] = np.array(values, dtype=float)

    missing_entries = []
    for tool in tools:
        for metric in metric_order:
            for run in run_order:
                if coverage_data[tool][metric][run] is None:
                    missing_entries.append((tool, metric, run))

    if missing_entries:
        preview = ", ".join(f"{t}/{m}/{r}" for t, m, r in missing_entries[:6])
        raise ValueError(
            "CSV data is incomplete. Missing entries: "
            f"{preview}" + (" ..." if len(missing_entries) > 6 else "")
        )

    metric_series = []
    for metric in metric_order:
        base_data = np.array([coverage_data[tool][metric]["1000"] for tool in tools])
        top_data = np.array([coverage_data[tool][metric]["1h"] for tool in tools])
        metric_series.append((metric, base_data, top_data))

    return metric_series

# =========================
# 2. 颜色
# =========================
colors = [
    "#d96b62", "#bb4a40",   # HiREST (highlighted)
    "#8fadd6", "#6f92c4",   # RESTler
    "#8dbc93", "#6ea47a",   # EvoMaster
    "#a996c4", "#8d75b3",   # Morest
    "#d4a371", "#be8751",   # ARAT-RL
    "#83b7ba", "#619ea2"    # AutoRest
]

# =========================
# 3. 从 CSV 加载数据
# =========================
csv_path = Path(__file__).resolve().with_name(CSV_FILENAME)
metric_series = load_coverage_from_csv(csv_path)

# =========================
# 4. 画图
# =========================

fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(24, 15), dpi=150, sharex=True)

x = np.arange(len(categories))
n_groups = len(tools)
bar_width = 0.143
offsets = (np.arange(n_groups) - (n_groups - 1) / 2) * bar_width

legend_handles = None
legend_labels = None

for ax, (metric_name, metric_base, metric_top) in zip(axes, metric_series):
    for i in range(n_groups):
        xpos = x + offsets[i]

        # Base is the 1000-hit absolute coverage, clipped to valid percent range.
        base_cov = np.clip(metric_base[i], 0.0, 100.0)
        # Top segment only represents positive gain from 1000-hit to 1h.
        top_cov = np.clip(metric_top[i], 0.0, 100.0)
        top_gain = np.clip(top_cov - base_cov, 0.0, 100.0 - base_cov)

        ax.bar(
            xpos, base_cov,
            width=bar_width,
            color=colors[2 * i],
            label=series_names[2 * i],
            edgecolor="none"
        )

        ax.bar(
            xpos, top_gain,
            width=bar_width,
            bottom=base_cov,
            color=colors[2 * i + 1],
            label=series_names[2 * i + 1],
            edgecolor="none"
        )

    ax.set_ylim(0, 100)
    ax.set_ylabel("Coverage (%)", fontsize=16)
    ax.tick_params(axis='y', labelsize=12)
    ax.grid(axis='y', linestyle='--', linewidth=0.8, alpha=0.5)

    ax.text(
        0.02, 0.90, metric_name,
        transform=ax.transAxes,
        fontsize=23,
        fontweight="bold"
    )

    if legend_handles is None:
        legend_handles, legend_labels = ax.get_legend_handles_labels()

# =========================
# 5. 样式设置
# =========================
for ax in axes:
    ax.set_xticks(x)
    ax.set_xticklabels(wrapped_categories, rotation=0, ha="center", fontsize=13)
    ax.tick_params(axis='x', labelbottom=True)

fig.legend(
    legend_handles,
    legend_labels,
    ncol=3,
    loc='upper right',
    bbox_to_anchor=(0.99, 0.99),
    fontsize=15,
    frameon=True,
    handlelength=2.0,
    labelspacing=0.6,
    columnspacing=1.2
)

plt.subplots_adjust(top=0.90, bottom=0.08, hspace=0.28)
plt.tight_layout()
output_path = Path(__file__).resolve().with_name("coverage_comparison.png")
plt.savefig(output_path, bbox_inches="tight")
plt.show()