import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
import numpy as np

plt.rc('font', family='Times New Roman')
base_dir = "./rawdata"
hm_files = glob.glob(os.path.join(base_dir, "*_HM_coverage.xlsx"))
service_names = [os.path.basename(f).split("_HM_coverage.xlsx")[0] for f in hm_files]

def sparse_indices(length, dense=10, sparse_step=20):
    idx = list(range(min(dense, length)))
    idx += list(range(dense, length, sparse_step))
    return sorted(set(idx))

# 固定4行2列
rows, cols = 2, 4

fig, axes = plt.subplots(rows, cols, figsize=(cols*5, rows*5), dpi=200)
axes = axes.flatten()

for i, service_name in enumerate(service_names):
    if i >= rows * cols:
        break  # 最多只画8个
    hm_path = os.path.join(base_dir, f"{service_name}_HM_coverage.xlsx")
    bm_path = os.path.join(base_dir, f"{service_name}_BM_coverage.xlsx")
    if not (os.path.exists(hm_path) and os.path.exists(bm_path)):
        continue

    df_hm = pd.read_excel(hm_path)
    df_bm = pd.read_excel(bm_path)

    hm_idx = sparse_indices(len(df_hm), dense=10, sparse_step=20)
    bm_idx = sparse_indices(len(df_bm), dense=10, sparse_step=20)

    x_hm = ((df_hm.index[hm_idx] + 1) * 50)
    y_hm = df_hm['branch_coverage'].iloc[hm_idx]
    x_bm = ((df_bm.index[bm_idx] + 1) * 50)
    y_bm = df_bm['branch_coverage'].iloc[bm_idx]

    ax = axes[i]
    ax.plot(x_hm, y_hm, color="#00bfc4", marker='^', markersize=4,
            markerfacecolor='#424242', markeredgecolor='#424242', linewidth=2, label='HiREST', antialiased=True)
    ax.plot(x_bm, y_bm, color='#f98a82', marker='o', markersize=3,
            markerfacecolor='#424242', markeredgecolor='#424242', linewidth=2, label='HiREST-BM', antialiased=True)

    ax.set_title(f'{service_name}', fontsize=14, color='#424242', fontname='Times New Roman')
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
    ax.legend(fontsize=10)

# 去除多余的子图
for j in range(i+1, len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
plt.savefig('all_services_branch_coverage.png', dpi=200, bbox_inches='tight')
plt.close()
