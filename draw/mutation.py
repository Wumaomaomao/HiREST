import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import math

plt.rc('font', family='Times New Roman')
script_dir = Path(__file__).resolve().parent
base_dir = script_dir / "trend_data"
hm_files = sorted(base_dir.glob("*_trend_coverage_HM.xlsx"))
service_names = [f.name.split("_trend_coverage_HM.xlsx")[0] for f in hm_files]

# Keep service order stable and map internal ids to publication names.
SERVICE_ORDER = [
    "languagetool",
    "ncs",
    "person",
    "restcountries",
    "scs",
    "news",
    "youtube",
    "genome",
    "user",
    "project",
]

SERVICE_DISPLAY_NAME = {
    "languagetool": "Language Tool",
    "ncs": "NCS",
    "person": "Person Controller",
    "restcountries": "Rest Countries",
    "scs": "SCS",
    "news": "News Service",
    "youtube": "Youtube-Mock",
    "genome": "Genome Nexus",
    "user": "User Management",
    "project": "Project Tracking System",
}

paired_services = [
    s for s in SERVICE_ORDER
    if s in service_names and (base_dir / f"{s}_trend_coverage_BM.xlsx").exists()
]


def extract_branch_coverage(df: pd.DataFrame, file_path: Path) -> pd.Series:
    """Extract branch coverage column from mixed excel schemas."""
    normalized = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}

    if "branch_coverage" in normalized:
        series = pd.to_numeric(df[normalized["branch_coverage"]], errors="coerce")
        return series.reset_index(drop=True)

    for norm_name, raw_name in normalized.items():
        if "branch" in norm_name or "bran" in norm_name:
            series = pd.to_numeric(df[raw_name], errors="coerce")
            return series.reset_index(drop=True)

    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        return pd.to_numeric(numeric_df.iloc[:, 0], errors="coerce").reset_index(drop=True)

    # Fallback for files without headers: assume column-1 is branch coverage if present.
    df_no_header = pd.read_excel(file_path, header=None)
    if df_no_header.shape[1] >= 2:
        return pd.to_numeric(df_no_header.iloc[:, 1], errors="coerce").reset_index(drop=True)
    if df_no_header.shape[1] == 1:
        return pd.to_numeric(df_no_header.iloc[:, 0], errors="coerce").reset_index(drop=True)

    raise ValueError(f"Cannot extract branch coverage from {file_path}")

def sparse_indices(length, dense=10, sparse_step=20):
    idx = list(range(min(dense, length)))
    idx += list(range(dense, length, sparse_step))
    return sorted(set(idx))


def request_x_positions(selected_indices, interval=50):
    # Follow original plotting method: request count starts at 50 for the first sample.
    return (np.array(selected_indices) + 1) * interval

service_total = len(paired_services)
cols = 4
rows = max(1, math.ceil(service_total / cols))

fig, axes = plt.subplots(rows, cols, figsize=(cols*5, rows*5), dpi=200)
if isinstance(axes, np.ndarray):
    axes = axes.flatten()
else:
    axes = np.array([axes])

full_rows = service_total // cols
remainder = service_total % cols
slot_indices = []

for r in range(full_rows):
    row_base = r * cols
    slot_indices.extend(row_base + c for c in range(cols))

if remainder:
    row_base = full_rows * cols
    start_col = (cols - remainder) // 2
    slot_indices.extend(row_base + start_col + c for c in range(remainder))

for plot_idx, service_name in enumerate(paired_services):
    hm_path = base_dir / f"{service_name}_trend_coverage_HM.xlsx"
    bm_path = base_dir / f"{service_name}_trend_coverage_BM.xlsx"

    df_hm = pd.read_excel(hm_path)
    df_bm = pd.read_excel(bm_path)

    branch_hm = extract_branch_coverage(df_hm, hm_path)
    branch_bm = extract_branch_coverage(df_bm, bm_path)

    hm_idx = sparse_indices(len(branch_hm), dense=10, sparse_step=20)
    bm_idx = sparse_indices(len(branch_bm), dense=10, sparse_step=20)

    x_hm = request_x_positions(hm_idx, interval=50)
    y_hm = branch_hm.iloc[hm_idx]
    x_bm = request_x_positions(bm_idx, interval=50)
    y_bm = branch_bm.iloc[bm_idx]

    ax = axes[slot_indices[plot_idx]]
    ax.plot(x_bm, y_bm, color='#f98a82', marker='o', markersize=3,
            markerfacecolor='#424242', markeredgecolor='#424242', linewidth=2,
            label='HiREST-BM', antialiased=True, zorder=2)
    ax.plot(x_hm, y_hm, color="#00bfc4", marker='^', markersize=4,
            markerfacecolor='#424242', markeredgecolor='#424242', linewidth=2,
            label='HiREST', antialiased=True, zorder=3)

    title_name = SERVICE_DISPLAY_NAME.get(service_name, service_name)
    ax.set_title(f'{title_name}', fontsize=14, color='#424242', fontname='Times New Roman')
    ax.set_xlabel('Request Count', fontsize=12, color='#424242', fontname='Times New Roman')
    ax.set_ylabel('Branch Coverage (%)', fontsize=12, color='#424242', fontname='Times New Roman')
    ax.set_xscale('log')

    ax.tick_params(axis='x', labelsize=10, colors='#424242')
    ax.tick_params(axis='y', labelsize=10, colors='#424242')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    ax.spines['left'].set_color('#424242')
    ax.spines['bottom'].set_color('#424242')
    handles, labels = ax.get_legend_handles_labels()
    order = []
    if 'HiREST' in labels:
        order.append(labels.index('HiREST'))
    if 'HiREST-BM' in labels:
        order.append(labels.index('HiREST-BM'))
    if order:
        ax.legend([handles[i] for i in order], [labels[i] for i in order], fontsize=10)
    else:
        ax.legend(fontsize=10)

# 去除多余的子图
used_slots = set(slot_indices[:len(paired_services)])
for idx, axis in enumerate(axes):
    if idx not in used_slots:
        fig.delaxes(axis)

if len(paired_services) == 0:
    raise RuntimeError(
        f"No paired HM/BM coverage files found in {base_dir}. "
        "Expected pattern: <service>_trend_coverage_HM.xlsx and <service>_trend_coverage_BM.xlsx"
    )

plt.tight_layout()
plt.savefig('all_services_branch_coverage.png', dpi=200, bbox_inches='tight')
plt.close()
