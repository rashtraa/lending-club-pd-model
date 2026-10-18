# Credit Risk & PD Engine — Lending Club, 2007–2018

**An application scorecard, a master rating scale, lifetime PD estimation, and what
a three-point calibration miss costs in dollars.**

---

## Summary

Built on 2.26M Lending Club consumer loan originations, this project produces a
ten-variable WOE scorecard, a seven-grade rating scale, lifetime PD estimates for
vintages that have not finished resolving, and a loss quantification of the model's
own error.

Four results, each of which contradicted the expectation held before it was computed:

| | |
|---|---|
| **The scorecard matches the lender's own risk grade** | Test AUC 0.7076 against Lending Club's proprietary `sub_grade` at 0.7100, using public borrower attributes only |
| **A PD-anchored rating scale ties the lender's, with better tails** | 0.7007 vs 0.7008 at equal resolution; 14.8× default spread vs their 9.8× |
| **Kaplan-Meier overstates lifetime default by 111%** | 34.27% against a known truth of 16.22%; the competing-risks estimator returns 16.22% exactly |
| **The 2015 calibration gap cost $115m** | On $5.50bn exposure at 65% LGD, with 47% of stressed loss in 24% of exposure |

The through-line is that each finding came from testing a belief rather than
defending it, and in four cases out of four the belief lost.

---

## 1. The gap, and what it cost

### The setup

The target is binary default, defined as `Charged Off`, `Default`, or the
`Does not meet the credit policy` variant. Loans that have not resolved carry no
usable label, so the modelling pool is the 1,348,099 resolved loans.

The split is out-of-time, not random. Random splitting on loan data leaks: two loans
originated the same month share macro conditions and underwriting policy, so a
randomly held-out loan is not independent of its training neighbours. Vintages
2007–2014 train (453,780 loans, 17.03% bad); vintage 2015 tests (375,546 loans,
20.19% bad). 2016–2018 are set aside — their resolution rates are too low for the
label to carry meaning.

The scorecard uses ten WOE-binned characteristics in a logistic regression, scaled to
points at PDO 20, base score 600, base odds 50:1.

| | Train | Test (2015) |
|---|---|---|
| AUC | 0.6848 | **0.7076** |
| Gini | — | 0.4152 |
| KS | — | 0.2986 |
| Mean predicted PD | — | 0.1720 |
| Actual bad rate | 0.1703 | **0.2019** |

Test AUC exceeds train AUC, which is unusual and worth stating rather than glossing:
2015 has a wider risk spread than the pooled training years, so the same model
separates it more cleanly. It is not a sign of leakage — the split is strictly
forward in time.

### The gap

Predicted 17.20%, realised 20.19%. **The model under-predicts 2015 default by 2.99
percentage points.** A Platt slope of 1.1671 confirms the miss is systematic rather
than noise.

Three explanations are available, and Sections 2 and 3 kill two of them.

### The cost

Attaching exposure (`loan_amnt`) to the rated 2015 book gives $5.50bn. Loss
follows EAD × PD × LGD. There is no recovery data in this dataset, so LGD is an
assumption, stated as one and run at three levels.

| | LGD 50% | LGD 65% | LGD 80% |
|---|---|---|---|
| Expected loss, model PD | $493m | $641m | $789m |
| Expected loss, realised PD | $582m | $757m | $931m |
| **Unexpected loss** | **$89m** | **$115m** | **$142m** |

At the middle assumption the calibration gap is **$115m, roughly 2.1% of
exposure.** That is the cost of the model being three points wrong, and it is the
only result here that needs no statistical vocabulary to land.

Two structural facts sharpen it.

**Exposure is not distributed like loan count.** Average loan size is U-shaped
across the risk scale — $15,075 at grade A, bottoming at $13,037 at D, rising to
$17,997 at G. Riskier borrowers take larger loans, largely a term effect. So the
dollar-weighted default rate is 21.17% against the count-weighted 20.19%, and every
count-weighted default rate in this project understates the loss.

**Deterioration is not parallel.** The predicted-versus-realised gap widens
monotonically down the scale: −0.59pp at A, +1.95pp at D, +9.82pp at G. A stress
test applying a uniform +3.01pp shock understates the loss increment by 7.4%
relative to applying the observed grade-specific shape. Small, but it points the
same way as the exposure weighting, and both are invisible if you look only at the
portfolio average.

The concentration this produces is the practical conclusion:

| | Share of exposure | Share of stressed loss |
|---|---|---|
| Grades A–B | 14.7% | 4.1% |
| Grades C–E | 61.0% | 49.0% |
| **Grades F–G** | **24.3%** | **46.9%** |

---

## 2. Did the applicants change, or did the outcomes?

The comfortable explanation for a calibration gap is population drift: the 2015
applicants were worse, so the model trained on 2007–2014 was scoring a different
book. It is comfortable because it implicates nobody's model.

It is also false here.

**Population Stability Index on the score distribution is 0.0005.** The
conventional threshold for "stable" is 0.10. At the characteristic level the worst
single feature is `dti_bin` at 0.0581, and all ten are stable. The applicant pool
did not move.

A second, independent check via the rating scale (Section 4). Decomposing the
+3.16pp change in default rate between train and test into a mix effect and a
within-grade effect:

| | |
|---|---|
| Mix effect — 2015's grade distribution at 2007–14 grade-level PDs | **+0.14pp** |
| Within-grade effect — same grades defaulting more | **+3.01pp** |

**Ninety-five per cent of the deterioration is within-grade.** Borrowers the model
scored identically defaulted more often in 2015 than they had before.

One caveat that must be stated, because it is the first objection a careful reader
will raise: grades are assigned by the model, so "mix" means mix *as this model
measures it*. Any change along a dimension the model does not observe lands in the
within-grade bucket by construction. What is shown is that the shift is not in the
ten characteristics being scored — not that the borrowers were identical in every
respect. Macro conditions, unobserved underwriting loosening, and servicing changes
remain live candidates and cannot be separated with this data.

Walk-forward validation confirms the model itself is stable while the outcomes move:

| Test year | Train n | Test n | Test bad rate | AUC |
|---|---|---|---|---|
| 2012 | 42,506 | 53,367 | 0.162 | 0.6712 |
| 2013 | 95,873 | 134,804 | 0.156 | 0.6693 |
| 2014 | 230,677 | 223,103 | 0.184 | 0.6889 |
| 2015 | 453,780 | 375,546 | 0.202 | 0.7076 |

Discrimination holds or improves as the book deteriorates. The model still ranks
correctly; it is the level that is wrong.

---

## 3. Lifetime PD, and an error worth 111%

The third explanation for the gap is the most technical and the hardest to dismiss
by argument: **maturity bias.** Defaults resolve faster than repayments — a loan
that charges off in month 14 is labelled long before a 36-month loan that pays to
term. Dropping unresolved loans therefore keeps a sample skewed toward bad
outcomes, and the observed 20.19% may be inflated by the exclusion rather than real.

Testing this requires estimating what a vintage's default rate *will* be, not what
has resolved so far — a survival problem, and one where 1.37M loans from 2016–2018
re-enter as censored observations instead of being discarded.

### The error

The default choice is Kaplan-Meier. On 2013 it returns a lifetime default rate of
**34.27%**.

2013 is fully resolved. The true answer is knowable: **16.22%**.

Kaplan-Meier is wrong by 111%, and the reason is conceptual. KM treats every non-event
exit as censoring — as a loan that left the sample early and might still have
defaulted had it stayed. But a repaid loan has not left early. It has exited
permanently and can never default. Repayment is a **competing risk**, not censoring,
and treating it as censoring shrinks the at-risk denominator and inflates the hazard
at every subsequent duration.

The Aalen-Johansen estimator handles competing risks correctly. On the same data it
returns **16.22%** — exact to two decimals against known ground truth.

| Vintage | n | Resolved-only | **Aalen-Johansen** | Kaplan-Meier |
|---|---|---|---|---|
| 2013 | 17,883 | 16.22 | **16.22** | 34.27 |
| 2014 | 31,298 | 18.10 | **18.56** | 36.24 |
| 2015 | 55,934 | 18.66 | **19.87** | 31.02 |
| 2016 | 60,461 | 15.61 | **17.94** | 23.97 |

The correction over the naive rate grows monotonically with censoring — +0.00,
+0.46, +1.21, +2.33 — which is the shape the method predicts and evidence it is
doing real work rather than fitting noise. The censored share behaves the same way:
0.0% through 2012, 1.6% for 2013, rising to 95.5% for 2018.

Getting there took three attempts at classifying exit type, and the final bug was
conceptual rather than technical: an early rule labelled only *early* payoffs as
competing events, leaving loans that ran to full term classified as censored. A loan
that reaches maturity and repays has exited exactly as definitively as one that
prepaid.

### The answer

**2015's true lifetime default rate is 19.87%.** The observed 20.19% was inflated by
0.32 points — essentially nothing.

So maturity bias is not the explanation either. The gap is real. Combined with
Section 2, the conclusion is that the applicant population did not shift, the
observed rate was not an artefact of censoring, and the same-looking borrowers simply
defaulted more.

The hazard structure explains why the censoring correction matters at all: default
hazard peaks at **months 12–18 at 4.64% marginal** and declines after. Recent
vintages have not yet lived through their own risk peak, which is precisely why
their resolved-only rates understate.

---

## 4. The rating scale

A rating is a claim that a grade means a *fixed default probability*. Cutting the
score distribution into seven equal buckets would produce grades whose meaning drifts
with every population shift, which defeats the purpose. Boundaries here are anchored
to PD bands, fit on train and applied to test unchanged.

Because PD is a monotone transform of score, the PD bands *are* score bands — the
scale is implementable as a lookup on points alone.

| Grade | Score | PD band | % of book | Predicted PD | Realised PD (2015) |
|---|---|---|---|---|---|
| A | 572+ | 0–5% | 4.0 | 3.94% | 3.34% |
| B | 558–572 | 5–8% | 10.4 | 6.64% | 6.94% |
| C | 545–558 | 8–12% | 20.2 | 10.06% | 11.22% |
| D | 533–545 | 12–17% | 24.4 | 14.40% | 16.35% |
| E | 520–533 | 17–24% | 20.8 | 20.05% | 23.35% |
| F | 508–520 | 24–33% | 11.8 | 27.95% | 34.41% |
| G | <508 | 33%+ | 8.4 | 39.78% | 49.60% |

Realised default is monotonic across all seven grades with no inversions, and the
book spreads across the scale rather than piling into the middle.

### Against the lender's own scale

Lending Club publishes its own A–G grade. Same loans, same number of grades, direct
comparison:

| | Test AUC |
|---|---|
| Scorecard, continuous PD | 0.7076 |
| **This scale, 7 grades** | **0.7007** |
| **LC grade, 7 grades** | **0.7008** |
| This scale, 35 sub-grades | 0.7073 |
| LC `sub_grade`, 35 grades | 0.7100 |

At seven grades it is a dead heat — 0.0001 apart. The scales are shaped very
differently, though. LC puts 19.1% of the book in A at a 5.54% default rate; this
scale's A is 4.0% of the book at 3.34%. At the bottom, LC's F and G differ by only
2.7 points across 2.7% of the book, while F and G here are 34.4% and 49.6% on 20.2%
of the book. Equal AUC comes from LC discriminating well in the crowded middle while
spending little resolution at the tails.

At 35 grades LC wins by 0.0027. Their proprietary data and underwriting history buy
a real if modest advantage at equal resolution, and the honest summary is that the
tie holds at seven grades and not at thirty-five.

### The cost of a letter

Collapsing continuous PD to seven grades costs **0.0069 AUC**. Splitting into 35
sub-grades recovers **0.0066** of it.

That number is worth holding next to Section 5.

---

## 5. The price of interpretability

XGBoost on 20 raw features, early-stopped on 2014 (never on the 2015 test set):

| | Scorecard | XGBoost | LC `sub_grade` |
|---|---|---|---|
| Features | 10 binned | 20 raw | 1 |
| Train AUC | 0.6848 | 0.7180 | — |
| Test AUC | 0.7076 | 0.7165 | 0.7100 |
| Gini | 0.4152 | 0.4330 | 0.4200 |
| KS | 0.2986 | 0.3147 | — |
| Platt slope | 1.1671 | 1.1470 | — |
| Deployable by hand | Yes — points table | No | Proprietary |

A train–test gap of 0.0015 says the scorecard is not overfit; it is constrained. The
raw uplift is +0.0089.

### Where the uplift comes from, and where it doesn't

SHAP on a 20k test sample ranks `term_months` (0.356), `annual_inc` (0.262),
`fico_range_low` (0.247), and `installment` (0.194) highest. The highest-value
features *absent* from the scorecard are `installment`, `open_acc`, `addr_state`,
`revol_util`, `revol_bal`, and `total_acc` — that is, revolving-credit depth and
geography. The uplift is a different information set, not curvature the WOE bins
could not bend to.

`installment` raised a concern. It is a deterministic function of loan amount, term,
and interest rate, and both loan amount and term are in the feature set. So the tree
could in principle invert the annuity formula, recover `int_rate` — Lending Club's
own price, a monotone transform of `sub_grade` — and smuggle the lender's risk
assessment into a model built to exclude it. The scorecard maintains that firewall
explicitly; XGBoost did not.

Refitting without `installment` costs **0.0016**. The door was open and almost
nothing came through it: trees approximate a multiplicative ratio poorly with
axis-aligned splits. Clean uplift over the scorecard is **+0.0073**, and XGBoost
still beats LC's own grade without access to LC's pricing.

The methodological point is the gap between the two diagnostics. `installment`
ranks fourth of twenty by mean |SHAP| — above `dti`, above `inq_last_6mths` — and
removing it costs 0.0016 AUC. These are not in conflict: mean |SHAP| measures how
much a feature moves the output of the model *as fitted*, and says nothing about
whether the same information is available elsewhere. `installment` is roughly
`loan_amnt` scaled by term, so its correlates absorb the loss.

**SHAP importance is not feature necessity.** The only way to tell them apart is to
refit without the feature.

### The number that reframes the comparison

Gradient boosting buys **+0.0073**. Rounding the scorecard's output to a letter grade
costs **−0.0069**.

The entire advantage of the more powerful model class is roughly the same size as
what is thrown away by the last step of the deployment pipeline. Arguments about
model class that ignore how the output is consumed have the priorities backwards.

---

## 6. What the data killed

Five explanations that were plausible when stated, each ended by a specific
calculation rather than by argument:

| Hypothesis | Killed by |
|---|---|
| The 2015 gap is population drift | Score PSI 0.0005; mix effect +0.14pp of +3.16pp |
| The observed 20.19% is inflated by censoring | Aalen-Johansen lifetime PD 19.87% |
| Kaplan-Meier is fine for loan survival | 34.27% against a known 16.22% |
| XGBoost's uplift is `int_rate` leaking via `installment` | Ablation costs 0.0016 of 0.0089 |
| A parallel PD shock is an adequate stress | Shaped shock is 7.4% worse on the increment |

Three of the five were positions held by the analysis at the time, not straw men.
The pattern — state what a belief predicts, then compute the thing that would
falsify it — is the transferable part of this project.

---

## 7. Limitations

**One lender, one cycle.** Lending Club originated very little during 2007–2009 and
changed underwriting continuously afterwards. Nothing here supports a claim about
consumer credit in general, and macro sensitivities are deliberately not estimated —
Section 1's scenarios impose shocks rather than fitting them.

**LGD is assumed.** No recovery data exists in this dataset. The $115m scales
linearly with the assumption, $89m to $142m across the range shown.

**Exit type in the survival model is reconstructed, not observed.** There is no clean
"repaid versus still paying" field, so a loan counts as repaid if it did not default
and stopped paying more than three months before the 2018-12-31 snapshot. This is the
most fragile inference in the project and was wrong twice before it was right.

**Survival runs on a 14% stratified sample** (~300k loans), fixed seed, sampled per
chunk at read time, for memory reasons.

**The Cox model (C-index 0.6363) is not comparable to the scorecard AUC.** It was fit
treating repayment as censoring — the error corrected elsewhere in Section 3. It
should be refit on exit type before the two are quoted together, and until then it is
reported here only for completeness.

**The rating scale mixes two boundary philosophies.** Grade bands are PD-anchored and
therefore stable across populations; the 1–5 sub-grade splits within each band are
quantile-based and drift with the population. At PSI 0.0005 this is immaterial, but
the two layers do not have the same stability properties.

**The mix/within-grade decomposition is observability-limited**, as set out in
Section 2.

---

## 8. Reproducing

```
notebooks/
  01_setup_and_data.ipynb        vintage resolution rates, target definition, split
  02_features_and_woe.ipynb      WOE/IV binning, feature selection
  03_scorecard.ipynb             logistic regression, points scaling, LC benchmark
  04_xgboost_benchmark.ipynb     GBM, SHAP, installment ablation
  05_validation.ipynb            PSI, gains/lift, walk-forward
  06_survival.ipynb              KM, Aalen-Johansen, Cox
  07_rating_system.ipynb         PD-anchored grades, head-to-head vs LC
  08_stress_and_sensitivity.ipynb  EAD, scenarios, loss concentration
```

Run in order — 01 and 02 write the cached parquet frames the rest read. Data comes
from the Kaggle Lending Club release (`accepted_2007_to_2018Q4.csv.gz`) and is not in
the repo.

Stack: `pandas`, `numpy`, `scikit-learn`, `xgboost`, `lifelines`, `statsmodels`,
`shap`, `matplotlib`.
