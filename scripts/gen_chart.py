"""ROI comparison chart - horizontal bars, charts.md compliant (no top/right spines, values labeled, no grid)."""
import matplotlib
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

labels = [
    'Commercial AI scribes\n(high estimate, 2026)',
    'Commercial AI scribes\n(low estimate, 2026)',
    'Willow open stack\n(self-hosted, estimated)',
]
values = [7200, 2500, 1200]
colors = ['#b7d3c5', '#556e62', '#298959']

fig, ax = plt.subplots(figsize=(7.2, 2.9), dpi=220, constrained_layout=True)
bars = ax.barh(labels, values, color=colors, height=0.58, edgecolor='none', zorder=3)

# Value labels at bar ends
for bar, v in zip(bars, values):
    ax.text(v + 130, bar.get_y() + bar.get_height() / 2,
            f'${v:,.0f}', va='center', ha='left', fontsize=11.5,
            color='#232725', fontweight='bold')

# Spine cleanup: delete top/right; keep bottom thin gray baseline
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#9aa8a0')
ax.spines['bottom'].set_linewidth(0.8)

# Values are labeled directly -> no grid (charts.md rule)
ax.grid(False)
ax.set_xticks([])
ax.set_xlim(0, 8600)
ax.tick_params(axis='y', length=0, labelsize=10.5, colors='#232725')
ax.set_xlabel('Annual documentation-AI cost per clinician (USD)', fontsize=10.5, color='#556e62', labelpad=8)

fig.savefig('/home/z/my-project/scripts/assets/chart_roi.png', facecolor='white')
print('OK chart_roi.png')
