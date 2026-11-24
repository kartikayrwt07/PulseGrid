# PulseGrid — 5-Minute Live Pitch & Demo Script

**Setup Checklist Before Going on Stage**
1. Open **http://127.0.0.1:4173** (Faculty Dashboard loaded with signed demo JWT).
2. Have `data/messy_sample.xlsx` ready to drop into the **CSV / XLSX Upload** tab.
3. Verify top bar status pill reads `Week 9 / 14 · 240 Students` in emerald green.

---

## 0:00 – 0:45 | The Problem & Thesis
> *"Universities only catch struggling students after finals, when attendance cliffs or cumulative deficits are already mathematically impossible to fix. Generic pass/fail thresholds either fire late or spam false alerts after one tough midterm. PulseGrid replaces static thresholds with cohort-calibrated statistical process control, per-subject Point-of-No-Return deadlines, and minimum-effort counterfactual recovery plans — running 100% locally with zero external LLM APIs."*

- **Point at KPI Strip (Faculty Dashboard):** 240 students, real-time At-Risk/Critical counts, CUSUM Silent Slippers, and Root-Cause Traps.

---

## 0:45 – 1:45 | Hero 1 — `STU-001` Aarav Kulkarni (Catching the "Silent Slipper")
1. In the search box, type **`Aarav`**. Click **Aarav Kulkarni**.
2. **Say:** *"Aarav had an 89% baseline in Weeks 1–4. Static 60% rules still miss high performers sliding quietly—until weeks later. Notice our **Cohort Z-Score Trajectory chart** suppresses the Week 5 tough-exam dip across the class, then fires a red **CUSUM Shift line right at Week 7**."*
3. Point to the **SHAP Root-Cause Attribution** bars: `CUSUM Drop Magnitude`, `CUSUM Shift Detected`, and `EWMA Flagged Weeks` explain *why* he moved to `AT_RISK`.

---

## 1:45 – 2:30 | Hero 2 — `STU-002` Meera Nair ("Assignment Comfort Trap")
1. Click **`Meera`** in the quick Hero Persona pill strip at top-right.
2. **Say:** *"Meera scores ~94% on take-home assignments and attends 86% of classes—she looks fine on paper. But closed-book internals sit near 39%. Our **Assignment–Internal Divergence Index (`+3.27σ`)** exposes `PASSIVE_COPIER_CONCEPT_GAP`, flagging her `CRITICAL` even though attendance is healthy."*
3. Scroll down to **Mentor Alert Digest** and click **Copy Mentor Alert** (1-click ready text for Slack/email), then click **Print Brief** to show the clean 1-page printable PDF view.

---

## 2:30 – 3:30 | Hero 3 — `STU-003` Rohan Deshmukh (Student Mode + PONR + What-If Simulator)
1. Click **Student** in the top-right **Role Switcher** (issues a real student-scoped JWT; backend enforces `403` isolation against other students' data), then select **`STU-003 — Rohan Deshmukh`**.
2. **Say:** *"Rohan passes every theory class (~85%), so his overall average looks safe. Look at the amber alert banner: his 2-hour/week **CN Lab (`CS301L`)** is `WINDOW CLOSING` at 66.7%. Under the 75% rule, out of 10 remaining labs he must attend at least 9 — his **bunk budget is exactly 1 session**."*
3. Click **Open What-If Recovery Simulator** and drag the attendance/internal sliders up to `95%`. Point out how the predicted score delta and SHAP waterfall recompute live (using `AbortController` debouncing).

---

## 3:30 – 4:30 | Hero 4 & Judge Differentiators (Faculty Triage, Messy XLSX, Interventions & Audit)
1. Switch back to **Faculty** in the Role Switcher.
2. Click **Triage Matrix** → *"All 240 students plotted by Urgency vs. Solver Rescueability across 4 actionable quadrants."*
3. Click **Interventions** → Point to **STU-004 Priya Sharma**: *"Her Week 7 Remedial Mentoring intervention displays the **`LIFT IMPROVED`** badge (`AT_RISK → SAFE`, rising toward 94%)."*
4. Click **CSV / XLSX Upload** → Drop `data/messy_sample.xlsx` (*`Take-Home Assn (%)`*, *`Midterm Internal Marks`*, *`Wk`*): our `difflib` fuzzy mapper aligns every messy header automatically with confidence scores and data-health alerts.
5. Click **Model Audit** → Show real holdout metrics (`train=180`, `holdout=60` on Weeks 1–8 → predicting Weeks 10–12: `LogisticRegression` selected with `95.7%` At-Risk Recall, `0.903` ROC AUC, confusion matrix, and zero-leakage global feature importances).

---

## 4:30 – 5:00 | Quick Judge Q&A Cheat Sheet
- **Data Leakage?** *"Strict temporal cutoff (`week <= 8`) + allowlisted observational columns only. Our automated `test_anti_leakage.py` mutates Weeks 9–12 scores and verifies Weeks 1–8 feature vectors remain bit-for-bit identical."*
- **Why LogisticRegression beat trees here?** *"Our model selector benchmarks 3 classifiers on unseen holdout data and picks the highest At-Risk Recall (`95.7%`), tie-broken by Macro-F1 (`0.691`), rather than hardcoding a heavy model."*
- **Cost / Privacy / Offline?** *"100% local SQLite + scikit-learn/SHAP/SciPy; zero paid APIs or external data exfiltration."*
