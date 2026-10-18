"""
patch_notebooks.py — applies the last two mechanical fixes.

Run ONCE from the repo root:  python patch_notebooks.py

What it does
------------
05_validation.ipynb
  * np.percentile(...) -> .tolist()   so pd.cut gets a list, not an ndarray
    (silences 4 Pylance errors; no behaviour change)
  * train['vintage'] -> .astype(int)  in the walk-forward loop
    (silences the Series[Timestamp] < float error)

06_survival.ipynb
  * appends one new cell that recomputes the KM / Aalen-Johansen / naive table
    and writes data/processed/lifetime_pd.csv, so make_figures.py stops using
    hardcoded numbers. You still need to RUN that cell once.

Safety
------
Edits the notebook JSON directly, so your existing cell outputs are untouched —
nothing needs re-running except the one new cell in 06.
Writes .bak copies before touching anything. Idempotent: running it twice is a
no-op and it will tell you so.
"""

import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

NB05 = os.path.join(ROOT, '05_validation.ipynb')
NB06 = os.path.join(ROOT, '06_survival.ipynb')

# ---------------------------------------------------------------- nb 05
REPLACEMENTS_05 = [
    ("edges = np.percentile(train['score'], np.arange(0, 101, 10))",
     "edges = np.percentile(train['score'], np.arange(0, 101, 10)).tolist()"),
    ("tr_f = train[train['vintage'] < yr]",
     "tr_f = train[train['vintage'].astype(int) < yr]"),
    ("te_f = train[train['vintage'] == yr]",
     "te_f = train[train['vintage'].astype(int) == yr]"),
]

# ---------------------------------------------------------------- nb 06
CELL_06 = '''# ============================================================
# BLOCK F — persist the lifetime PD table for figures/make_figures.py
# Recomputes naive / Aalen-Johansen / Kaplan-Meier per vintage so the
# figure reads live numbers instead of hardcoded ones.
# Uses the final exit_type from Block E4.
# ============================================================
from lifelines import KaplanMeierFitter, AalenJohansenFitter

rows = []
for v in [2013, 2014, 2015, 2016]:
    s = surv[surv['vintage'] == v]

    kmf_ = KaplanMeierFitter()
    kmf_.fit(s['duration'], s['event'])
    horizon = min(60, int(s['duration'].max()))
    km = (1 - float(kmf_.survival_function_.loc[:horizon].iloc[-1])) * 100

    ajf_ = AalenJohansenFitter(calculate_variance=False)
    ajf_.fit(s['duration'], s['exit_type'], event_of_interest=1)
    aj = float(ajf_.cumulative_density_.iloc[-1, 0]) * 100

    rows.append({'vintage': v,
                 'resolved_only': round(s['event'].mean() * 100, 2),
                 'aalen_johansen': round(aj, 2),
                 'kaplan_meier': round(km, 2)})

lifetime_pd = pd.DataFrame(rows).set_index('vintage')
lifetime_pd.to_csv('data/processed/lifetime_pd.csv')
print(lifetime_pd.to_string())
print("\\nSaved -> data/processed/lifetime_pd.csv")
'''

MARKER_06 = 'BLOCK F — persist the lifetime PD table'


def load(path):
    if not os.path.exists(path):
        print(f'  ! not found: {os.path.basename(path)} — skipped')
        return None
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def save(path, nb):
    shutil.copy2(path, path + '.bak')
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)
        fh.write('\n')


def patch_05():
    nb = load(NB05)
    if nb is None:
        return
    hits = 0
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        src = ''.join(cell['source'])
        new = src
        for old, repl in REPLACEMENTS_05:
            if old in new and repl not in new:
                new = new.replace(old, repl)
        if new != src:
            # keep the trailing-newline convention nbformat expects
            lines = new.splitlines(keepends=True)
            cell['source'] = lines
            hits += 1
    if hits:
        save(NB05, nb)
        print(f'  05_validation.ipynb  — patched {hits} cell(s), backup written')
    else:
        print('  05_validation.ipynb  — already patched, nothing to do')


def patch_06():
    nb = load(NB06)
    if nb is None:
        return
    if any(MARKER_06 in ''.join(c['source']) for c in nb['cells']):
        print('  06_survival.ipynb    — cell already present, nothing to do')
        return
    nb['cells'].append({
        'cell_type': 'code',
        'execution_count': None,
        'id': 'lifetimepd01',
        'metadata': {},
        'outputs': [],
        'source': CELL_06.splitlines(keepends=True),
    })
    save(NB06, nb)
    print('  06_survival.ipynb    — appended Block F, backup written')
    print('    -> RUN that last cell to write lifetime_pd.csv')


if __name__ == '__main__':
    if not os.path.exists(os.path.join(ROOT, 'data')):
        print('Run this from the repo root (no data/ folder here).')
        sys.exit(1)
    print('Patching notebooks...')
    patch_05()
    patch_06()
    print('Done.')
