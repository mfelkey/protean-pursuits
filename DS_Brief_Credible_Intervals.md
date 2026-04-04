# DS Brief — Posterior Credible Interval Extraction
## Project: wc2026_predictions_v2 Uncertainty Bands
**Brief ID:** DS-CI-001  
**Date:** 2026-04-02  
**Team:** DS  
**Project ID:** PROJ-PARALLAXEDGE

---

## 1. Objective

Extract 90% credible intervals from the hierarchical Bayesian Dixon-Coles posterior
samples stored in `ds/models/bayesian_hier_idata.nc` and store them as 6 new columns
on `wc2026_predictions_v2`. These intervals will power uncertainty band visualizations
in the FixtureRow UI component (Sharp+ tier subscribers only).

---

## 2. Background

The Bayesian model (MODEL_VERSION='bayesian', commit 59b92df) currently stores only
posterior mean probabilities in `wc2026_predictions_v2`:
- `prob_home_win`, `prob_draw`, `prob_away_win`

The posterior samples (thousands of MCMC draws) are stored in `bayesian_hier_idata.nc`
via ArviZ InferenceData format. These samples contain the full posterior predictive
distribution per fixture — the credible intervals are computable from them.

Current gap: the DB table does not store credible interval bounds. The UI component
(FixtureRow.tsx) is gated pending these columns — see DESIGN-SC-001 §4.

---

## 3. Required Deliverables

### 3.1 DB Schema Migration

Add 6 columns to `wc2026_predictions_v2`:

```sql
ALTER TABLE wc2026_predictions_v2
  ADD COLUMN prob_home_win_lo  DECIMAL(6,4),
  ADD COLUMN prob_home_win_hi  DECIMAL(6,4),
  ADD COLUMN prob_draw_lo      DECIMAL(6,4),
  ADD COLUMN prob_draw_hi      DECIMAL(6,4),
  ADD COLUMN prob_away_win_lo  DECIMAL(6,4),
  ADD COLUMN prob_away_win_hi  DECIMAL(6,4),
  ADD COLUMN credible_interval DECIMAL(3,2) DEFAULT 0.90;
```

All columns nullable — rows populated by MLE model will have NULL interval columns.
Only rows with `model_version = 'bayesian_hier_xg'` will be populated.

### 3.2 Pipeline Script: `03j_credible_intervals.py`

New script at `ds/pipelines/03j_credible_intervals.py`:

1. Load `ds/models/bayesian_hier_idata.nc` via `arviz.from_netcdf()`
2. Load all 72 WC2026 fixtures from `wc2026_predictions_v2` where `model_version = 'bayesian_hier_xg'`
3. For each fixture, extract the posterior predictive distribution from the idata object
4. Compute 5th and 95th percentiles (90% credible interval) for each outcome:
   - `prob_home_win_lo` = 5th percentile of home win posterior
   - `prob_home_win_hi` = 95th percentile of home win posterior
   - Same for draw and away win
5. Upsert results to `wc2026_predictions_v2` via ON CONFLICT on `(home_team, away_team, model_version)`
6. Log summary: number of rows updated, mean interval widths per outcome

### 3.3 Update `03i_select_model.py`

After generating posterior mean predictions, call `03j_credible_intervals.py` inline
(or refactor the interval extraction into `03i` directly). The nightly pipeline must
populate intervals on every run — not a one-off migration.

### 3.4 Upload Artifact (if needed)

If `03j` requires any additional model artifacts beyond `bayesian_hier_idata.nc` and
`bayesian_hier_team_index.csv`, update `upload_model_artifacts.py` to include them.
Current artifacts in R2: `bayesian_hier_idata.nc`, `bayesian_hier_team_index.csv`.

---

## 4. Technical Constraints

- **ArviZ version:** latest (installed in DS environment)
- **Python version:** 3.11
- **DB:** Railway PostgreSQL — use `psycopg2`, `sslmode='require'`
- **Secrets:** `infisical run --env=prod --` pattern
- **Posterior format:** ArviZ InferenceData netCDF4 — posterior group contains
  MCMC samples. The relevant variable names depend on how `03c_train_bayesian_hierarchical.py`
  named them — check the idata object's `posterior` group variable names first.
- **Interval width gate (UI):** Only render uncertainty bands when
  `(hi - lo) > 0.05` (5 percentage points). This gate is implemented in the UI,
  not the pipeline — the pipeline always stores the intervals.

---

## 5. Acceptance Criteria

- [ ] All 72 `bayesian_hier_xg` rows in `wc2026_predictions_v2` have non-null interval columns
- [ ] `prob_home_win_lo + prob_draw_lo + prob_away_win_lo` approximately sums to a value
      consistent with the posteriors (not a hard constraint — intervals are per-outcome)
- [ ] `prob_home_win_hi >= prob_home_win_lo` for all rows (no inverted intervals)
- [ ] `credible_interval = 0.90` for all Bayesian rows
- [ ] Nightly pipeline (`03i_select_model.py` via GitHub Actions) populates intervals on each run
- [ ] MLE rows (`model_version = 'mle'`) retain NULL interval columns

---

## 6. UI Gate (for Dev team reference — not DS deliverable)

Once columns are populated, the Dev team will implement in `FixtureRow.tsx`:
- Uncertainty band beneath each probability bar (DESIGN-SC-001 §4)
- Primary bar: posterior mean at full opacity
- Extension: `hi - lo` width at 25% opacity (teal)
- Tooltip: "90% credible interval: X%–Y%"
- Only render if interval width > 5pp
- Sharp+ subscribers only (blur gate applies)

---

## 7. Reference Files

- `ds/pipelines/03i_select_model.py` — current prediction generation script
- `ds/pipelines/03c_train_bayesian_hierarchical.py` — model training (idata structure)
- `ds/models/bayesian_hier_idata.nc` — posterior samples (also in R2)
- `ds/models/bayesian_hier_team_index.csv` — team index
- `docs/DESIGN-SC-001-signal-card-spec.md` §4 — UI spec for uncertainty bands
- `docs/Parallax_PRD_v1_13.md` §7.1 — model inputs/outputs interface contract
