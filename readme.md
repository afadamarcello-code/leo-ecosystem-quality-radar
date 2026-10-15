# 🚨 LEO Ecosystem Quality Radar
### AI-powered Cost-of-Poor-Quality, Root-Cause & Forecasting Engine
**HVIA Data & AI Solutions — Task 02: EL-SHARNOUBY GROUP Challenge**
*From Data to Decisions. From Operations to Intelligence.*

> One refunded pajama → traced to its stitch defect → its factory line → its fabric
> supplier → and a reorder plan for next month. That is this product.

---

## 🎯 The idea in one sentence
When quality fails, money leaks in three places (refunds, factory scrap, printing
waste). This engine quantifies the leak, traces it to its root cause across the
ecosystem, forecasts next month's operational risk, and prescribes the action —
in a web app a non-technical manager can feed and use.

## 💰 Headline results (from challenge training data)
| Finding | Value |
|---|---|
| Total Cost of Poor Quality | **EGP 20,787,702 / year** |
| — Factory scrap (QC loss) | 16,322,914 |
| — Customer quality refunds | 2,509,899 (2,457 returns) |
| — Printing waste (rework + wasted ink) | 1,954,889 |
| Concentration | **71%** of refund money in Pajamas/Homewear |
| Statistical suspects | 2 SKUs (z = 3.75, 2.73); high-volume normal items correctly NOT flagged |
| Root cause chain | Stitch/size defects → Sewing & Finishing bottleneck → **Supplier 11 (742,764 rejected units)** |
| Service insight | Tickets >48h → **79.74%** low CSAT; topic irrelevant |
| Stockout forecaster | **ROC-AUC 0.95** on unseen future months (time-based split) |
| Live warnings | 667 items with cover < lead time; 202 items >70% risk next month + reorder qty |
| Hidden waste | Normal months average **343 days of cover** (frozen capital) |

## 🧱 Architecture (5 layers)
1. **Evidence layer** — Power BI (4 pages): Service Overview, Monthly Trends,
   Retention Risk, Wholesale Pipeline. The voice of the customer.
2. **Diagnostic layer** — CPQ accounting + deterministic root-cause trace
   (Sales → Quality → Production → BOM → Purchase Orders → Suppliers).
3. **Intelligence layer** — z-score anomaly detection (product return rates)
   + Random Forest stockout forecaster with lagged features (no leakage).
4. **Prescription layer** — reorder quantities, supplier audit targets,
   48-hour escalation rule.
5. **Product layer** — Streamlit app with guided per-tab CSV upload
   (`session_state` shared memory), live status sidebar, one-click reset.

## 📊 Power BI companion (`Power/`)
The BI suite lives in this repo as a **Power BI Project (PBIP)** — the
Git-friendly format:
- `02_Service_Intelligence.SemanticModel/` — star schema, `_Measures` table, DAX.
- `02_Service_Intelligence.Report/` — 4 pages (p2–p5): Service Overview,
  Monthly Trends, Retention Risk, Wholesale Pipeline.
Open with Power BI Desktop ≥ May 2024 (PBIP support) and point it at `Data/Raw/`.

## 🧠 Honesty appendix (models that failed and were retired)
| Experiment | Result | Decision |
|---|---|---|
| Ticket low-CSAT classifier (LR/DT/RF) | ROC-AUC ≈ 0.53 | Archived — early signals carry no outcome signal |
| Per-sale quality-return predictor | ROC-AUC 0.58, precision 1.7% | Archived — signal lives in aggregates, not rows |
| K-Means customer segmentation | Collapsed onto consent/type columns | Demoted to validation/scoring only |
| CPQ v1 (included normal ink cost) | Overstated loss | Corrected to wasted-ink-only |

*Every shipped model beat a `DummyClassifier` baseline on a time-aware split.*

## 📁 Repository structure (matches the actual project folder)
```
├── app.py                           # Streamlit decision app (5 tabs + guided upload)
├── requirements.txt
├── README.md
├── .gitignore
├── Data/
│   └── Raw/                         # 20 challenge CSVs (modeled / anonymized)
├── Notebooks/
│   ├── 01_data_overview.ipynb       # tickets & customers profiling + quality reports
│   ├── 02_problem_discovery.ipynb   # 6 evidence cuts (48h rule, buckets)
│   ├── 03_ml_training.ipynb         # supervised experiments → honest null results
│   ├── 05_ecosystem_links.ipynb     # referential integrity + CPQ + pajama detective
│   ├── 06_train_test.ipynb          # stockout detector vs dummy baseline
│   ├── 07_anomaly_and_rules.ipynb   # z-score suspects + early-warning rule
│   └── 08_future_forecast.ipynb     # lagged-feature forecaster (ROC-AUC 0.95)
├── models/
│   ├── stockout_forecast_model.pkl  # next-month stockout brain (lagged Random Forest)
│   └── stockout_model.pkl           # present-state detector
├── Power/
│   ├── 02_Service_Intelligence.Report/        # PBIP report (4 pages)
│   └── 02_Service_Intelligence.SemanticModel/ # star schema + DAX measures
├── reports/                         # exported CSVs (quality report, issue summary…)
├── screenshots/                     # Power BI + Streamlit captures  ← create now
└── slides/                          # final_deck.pdf                 ← create now
```
> **Data note:** all files are modeled/anonymized challenge data
> (`Data_Class` column confirms: "not actual personal data"), so they are safe
> to publish. If your challenge rules say otherwise, add `Data/Raw/` to
> `.gitignore` and ship a `Data/sample/` subset instead.

## ▶️ Run it yourself
```bash
git clone <your-repo-url>
cd <repo>
python -m venv venv && venv\Scripts\activate     # Windows
pip install -r requirements.txt
streamlit run app.py
```
Open the **🔮 AI Forecast** tab, expand the uploader, drop
`Inventory_History.csv` — watch every dependent tab recalculate.


** Live demo:** https://leo-ecosystem-quality-radar.streamlit.app/

## 🛠️ Tech stack
Python · Pandas · Scikit-learn · Streamlit · Power BI (DAX, PBIP) · joblib · Git

## 📜 License & credits
Built for the HVIA Data & AI Solutions internship challenge (EL-SHARNOUBY GROUP
brief). Figures derive from modeled training data. Thanks to my mentors and the
HVIA team for pushing beyond template dashboards.