"""
make_figures.py — regenerates the three figures used in README.md and WRITEUP.md.

Run from the repo root:  python figures/make_figures.py
Reads:  data/processed/master_scale.csv       (notebook 07, Block F)
        data/processed/loss_concentration.csv (notebook 08, Block C)
Writes: figures/fig1_lifetime_pd.png
        figures/fig2_calibration_by_grade.png
        figures/fig3_loss_concentration.png

Matplotlib only — no extra dependency beyond what the notebooks already use.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, 'data', 'processed')

# Muted, print-safe, and distinguishable in greyscale.
INK, GREY, BLUE, RED, AMBER = '#22222e', '#9a9aa6', '#2f5d8a', '#a63a3a', '#c98a2b'

plt.rcParams.update({
    'figure.dpi': 150, 'savefig.dpi': 150, 'savefig.bbox': 'tight',
    'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': GREY, 'axes.labelcolor': INK, 'text.color': INK,
    'xtick.color': INK, 'ytick.color': INK, 'figure.facecolor': 'white',
})


def annotate_bars(ax, bars, fmt='{:.1f}', dy=0.4, **kw):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy,
                fmt.format(b.get_height()), ha='center', va='bottom',
                fontsize=8, **kw)


# ---------------------------------------------------------------- figure 1
def fig_lifetime_pd():
    """Kaplan-Meier vs Aalen-Johansen against known ground truth.

    Reads data/processed/lifetime_pd.csv if notebook 06 has written it
    (index = vintage; columns = resolved_only, aalen_johansen, kaplan_meier).
    Falls back to the values as of the final nb 06 run, and says so loudly —
    hardcoded numbers in a figures script go stale silently otherwise.
    """
    path = os.path.join(PROC, 'lifetime_pd.csv')
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0)
    else:
        print('  ! lifetime_pd.csv not found — using hardcoded fallback.\n'
              '    Add a to_csv in notebook 06 to make this figure live.')
        df = pd.DataFrame({
            'resolved_only': [16.22, 18.10, 18.66, 15.61],
            'aalen_johansen': [16.22, 18.56, 19.87, 17.94],
            'kaplan_meier': [34.27, 36.24, 31.02, 23.97],
        }, index=[2013, 2014, 2015, 2016])

    x = np.arange(len(df))
    w = 0.26
    fig, ax = plt.subplots(figsize=(8, 4.6))

    b1 = ax.bar(x - w, df['resolved_only'], w, label='Resolved loans only',
                color=GREY)
    b2 = ax.bar(x, df['aalen_johansen'], w, label='Aalen-Johansen (competing risks)',
                color=BLUE)
    b3 = ax.bar(x + w, df['kaplan_meier'], w, label='Kaplan-Meier',
                color=RED)
    for bars in (b1, b2, b3):
        annotate_bars(ax, bars, '{:.2f}')

    # 2013 is fully resolved: the grey bar IS the truth.
    # xy targets the top-right corner of the 2013 Aalen-Johansen bar so the
    # arrow lands on the bar it describes, not in the gap next to 2014.
    ax.annotate('2013 is fully resolved — the true rate is\n'
                'knowable, and Aalen-Johansen matches it exactly',
                xy=(0.14, 16.6), xytext=(0.42, 24.5), fontsize=8.5,
                ha='left', va='bottom',
                arrowprops=dict(arrowstyle='->', color=INK, lw=0.9,
                                shrinkA=2, shrinkB=2))

    ax.set_xticks(x)
    ax.set_xticklabels(df.index)
    ax.set_xlabel('Origination vintage')
    ax.set_ylabel('Lifetime default rate (%)')
    ax.set_title('Treating repayment as censoring overstates lifetime default by 111%',
                 loc='left', pad=14)
    ax.set_ylim(0, 41)
    ax.legend(frameon=False, loc='upper right', fontsize=9)
    ax.grid(axis='y', color=GREY, alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)

    out = os.path.join(HERE, 'fig1_lifetime_pd.png')
    fig.savefig(out)
    plt.close(fig)
    print('wrote', out)


# ---------------------------------------------------------------- figure 2
def fig_calibration_by_grade():
    """Predicted vs realised PD by grade — the gap widens down the scale."""
    ms = pd.read_csv(os.path.join(PROC, 'master_scale.csv'), index_col=0)
    pred = ms['pred_PD'] * 100
    real = ms['realised_PD'] * 100
    x = np.arange(len(ms))

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.fill_between(x, pred, real, color=RED, alpha=0.13, zorder=1)
    ax.plot(x, pred, 'o-', color=BLUE, lw=1.8, ms=5, label='Predicted PD', zorder=3)
    ax.plot(x, real, 'o-', color=RED, lw=1.8, ms=5, label='Realised PD (2015)', zorder=3)

    for i, (p, r) in enumerate(zip(pred, real)):
        gap = r - p
        ax.annotate(f'{gap:+.2f}pp', xy=(i, max(p, r)), xytext=(0, 7),
                    textcoords='offset points', ha='center', fontsize=8,
                    color=RED if gap > 0 else BLUE)

    ax.set_xticks(x)
    ax.set_xticklabels(ms.index)
    ax.set_xlabel('Rating grade')
    ax.set_ylabel('Default probability (%)')
    ax.set_title('The calibration gap is not a level shift — it concentrates in the '
                 'riskiest grades', loc='left', pad=14)
    ax.legend(frameon=False, loc='upper left', fontsize=9)
    ax.grid(axis='y', color=GREY, alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(real) * 1.18)

    out = os.path.join(HERE, 'fig2_calibration_by_grade.png')
    fig.savefig(out)
    plt.close(fig)
    print('wrote', out)


# ---------------------------------------------------------------- figure 3
def fig_loss_concentration():
    """Share of exposure vs share of stressed loss, by grade."""
    lc = pd.read_csv(os.path.join(PROC, 'loss_concentration.csv'), index_col=0)
    y = np.arange(len(lc))
    h = 0.36

    fig, ax = plt.subplots(figsize=(8, 4.6))
    b1 = ax.barh(y + h / 2, lc['pct_of_ead'], h, label='Share of exposure',
                 color=GREY)
    b2 = ax.barh(y - h / 2, lc['pct_of_loss'], h, label='Share of stressed loss',
                 color=AMBER)
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_width() + 0.4, b.get_y() + b.get_height() / 2,
                    f'{b.get_width():.1f}%', va='center', fontsize=8)

    fg_ead = lc.loc[['F', 'G'], 'pct_of_ead'].sum()
    fg_loss = lc.loc[['F', 'G'], 'pct_of_loss'].sum()
    ax.axhspan(len(lc) - 2.5, len(lc) - 0.5, color=AMBER, alpha=0.07, zorder=0)
    # Callout and legend both go top-right: the F/G band is the region the eye
    # should land on, so nothing overlays it.
    ax.text(0.98, 0.80,
            f'Grades F+G: {fg_ead:.1f}% of exposure, {fg_loss:.1f}% of loss',
            transform=ax.transAxes, ha='right', fontsize=9, color=INK)

    ax.set_yticks(y)
    ax.set_yticklabels(lc.index)
    ax.invert_yaxis()
    ax.set_xlabel('Share of 2015 book (%)')
    ax.set_ylabel('Rating grade')
    ax.set_title('Nearly half of stressed loss sits in a quarter of exposure',
                 loc='left', pad=14)
    ax.legend(frameon=False, loc='upper right', fontsize=9)
    ax.grid(axis='x', color=GREY, alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(lc.max()) * 1.15)

    out = os.path.join(HERE, 'fig3_loss_concentration.png')
    fig.savefig(out)
    plt.close(fig)
    print('wrote', out)


if __name__ == '__main__':
    fig_lifetime_pd()
    fig_calibration_by_grade()
    fig_loss_concentration()
    print('done — 3 figures in', HERE)
