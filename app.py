import streamlit as st
import pandas as pd
import joblib

st.set_page_config(page_title="LEO Quality Radar", layout="wide")

# ==========================================================
# 0. SHARED MEMORY + FILE GUIDE
# ==========================================================
if "tables" not in st.session_state:
    st.session_state.tables = {}

DISK = {
    "sales":    "Data/Raw/Sales_Transactions.csv",
    "inv":      "Data/Raw/Inventory_History.csv",
    "qual":     "Data/Raw/Quality.csv",
    "prod":     "Data/Raw/Production_Orders.csv",
    "printing": "Data/Raw/Printing_Batches.csv",
    "pm":       "Data/Raw/Product_Master.csv",
    "bom":      "Data/Raw/Product_BOM.csv",
    "po":       "Data/Raw/Purchase_Orders.csv",
    "sup":      "Data/Raw/Suppliers.csv",
}

NICE = {
    "sales": "Sales & Returns", "inv": "Inventory", "qual": "QC Inspections",
    "prod": "Production Orders", "printing": "Printing Batches",
    "pm": "Product Master", "bom": "Product BOM (materials recipe)",
    "po": "Purchase Orders", "sup": "Suppliers",
}

def get_table(key):
    if key in st.session_state.tables:
        return st.session_state.tables[key]
    return pd.read_csv(DISK[key], encoding="utf-8-sig")

# CHANGE 1: the guide now shows the EXACT file name from the Raw folder
def ask(key, why, tab_id):
    fname = DISK[key].split("/")[-1]
    st.markdown(f"**📄 {NICE[key]}** — _file name: `{fname}` — {why}_")
    file = st.file_uploader(f"Upload new {fname}", type=["csv"], key="up_" + key + "_" + tab_id)
    if file is not None:
        st.session_state.tables[key] = pd.read_csv(file, encoding="utf-8-sig")
        st.success(f"✅ {file.name} is now live in EVERY tab that uses it.")

def build_suspects(sales, pm):
    sold = sales.groupby("Product_ID").size().rename("sold_qty")
    ret = sales[sales["Quality_Related_Return"] == "Yes"].groupby("Product_ID").agg(
        returned_qty=("Row_ID", "size"), refund_egp=("Refund_Value_EGP", "sum"))
    ps = pd.concat([sold, ret], axis=1).fillna(0).reset_index()
    ps["return_rate"] = ps["returned_qty"] / ps["sold_qty"]
    ps["z_score"] = (ps["return_rate"] - ps["return_rate"].mean()) / ps["return_rate"].std()
    ps["ALARM"] = ps["z_score"] > 2
    ps = ps.merge(pm[["Product_ID", "Product_Name", "Product_Family"]], on="Product_ID", how="left")
    return ps.sort_values("return_rate", ascending=False)

forecast_model = joblib.load("models/stockout_forecast_model.pkl")

# ---------- Sidebar: status + map + reset ----------
st.sidebar.header("🗂 Data Status")
live = [NICE[k] for k in st.session_state.tables]
if live:
    st.sidebar.success("Live from upload: " + ", ".join(live))
else:
    st.sidebar.info("All tables from disk (last saved month).")

# CHANGE 3: permanent map — which file feeds which tab
st.sidebar.markdown("""
**Which file updates which tab?**
- `Sales_Transactions.csv` → Boss View, Detective, Root-Cause
- `Quality.csv` → Boss View, Root-Cause
- `Printing_Batches.csv` → Boss View
- `Inventory_History.csv` → Smoke Detector **+ AI Forecast**
- `Production_Orders.csv`, `Product_BOM.csv`,
  `Purchase_Orders.csv`, `Suppliers.csv` → Root-Cause
""")

if st.sidebar.button("🔄 Reset to files on disk"):
    st.session_state.tables = {}
    st.rerun()

# ==========================================================
# TITLE + TABS
# ==========================================================
st.title("🚨 LEO Ecosystem Quality Radar")
st.markdown("*AI-powered Cost-of-Poor-Quality, Root-Cause & Forecasting Engine*")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 The Boss View (CPQ)",
    "🕵️‍♂️ The Detective (Suspects)",
    "🧬 Root-Cause Trace",
    "🚨 Smoke Detector (Present)",
    "🔮 AI Forecast (Next Month)"
])

# ---------- TAB 1 ----------
with tab1:
    with st.expander("📥 Update the data this tab uses", expanded=True):   # CHANGE 2: open by default
        ask("sales", "customer refunds and quality returns are counted from sales rows.", "tab1")
        ask("qual", "factory scrap loss (Estimated_Loss_EGP) comes from QC inspection records.", "tab1")
        ask("printing", "rework cost and wasted ink are counted from printing batches.", "tab1")
    sales, qual, printing = get_table("sales"), get_table("qual"), get_table("printing")

    total_refund = sales[sales["Quality_Related_Return"] == "Yes"]["Refund_Value_EGP"].sum()
    total_factory_loss = qual["Estimated_Loss_EGP"].sum()
    waste_share = (printing["Rejected_Qty"] + printing["Reprint_Qty"]) / printing["Printed_Qty"]
    printing_loss = printing["Rework_Cost_EGP"].sum() + (printing["Ink_or_Consumable_Cost_EGP"] * waste_share).sum()
    total_cpq = total_refund + total_factory_loss + printing_loss

    st.header("Total Cost of Poor Quality (CPQ)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Customer Refunds", f"{total_refund:,.0f} EGP")
    c2.metric("Factory Scrap Loss", f"{total_factory_loss:,.0f} EGP")
    c3.metric("Printing Waste", f"{printing_loss:,.0f} EGP")
    st.markdown("---")
    st.metric("TOTAL MONEY BLEEDING", f"{total_cpq:,.0f} EGP", delta="Action Required", delta_color="inverse")

# ---------- TAB 2 ----------
with tab2:
    with st.expander("📥 Update the data this tab uses", expanded=True):
        ask("sales", "the suspect list is built from sales + quality-return flags.", "tab2")
        ask("pm", "product names and families come from the Product Master.", "tab2")
    sales, pm = get_table("sales"), get_table("pm")
    suspects = build_suspects(sales, pm)

    st.header("Top 10 Suspect Products (Ranked by Return Rate)")
    st.markdown("*Only products with an abnormally high **rate** (Z-score > 2) trigger the ALARM.*")
    cols = ["Product_Name", "Product_Family", "sold_qty", "returned_qty", "return_rate", "z_score", "refund_egp", "ALARM"]
    st.dataframe(suspects.head(10)[cols])

# ---------- TAB 3 ----------
with tab3:
    with st.expander("📥 Update the data this tab uses", expanded=True):
        ask("sales", "chooses which suspect product to trace.", "tab3")
        ask("qual", "QC defect types and root causes.", "tab3")
        ask("prod", "factory lines and bottlenecks.", "tab3")
        st.markdown("_Master data below rarely changes — upload only if it changed:_")
        ask("bom", "the materials recipe inside each product.", "tab3")
        ask("po", "which supplier sent which material, rejected quantities, lateness.", "tab3")
        ask("sup", "supplier names.", "tab3")
    sales, pm = get_table("sales"), get_table("pm")
    qual, prod = get_table("qual"), get_table("prod")
    bom, po, sup = get_table("bom"), get_table("po"), get_table("sup")
    suspects = build_suspects(sales, pm)

    st.header("🧬 Root-Cause Trace: From Customer Return to Supplier")
    choice = st.selectbox("Choose a suspect product", suspects["Product_Name"].tolist())
    pid = suspects.loc[suspects["Product_Name"] == choice, "Product_ID"].iloc[0]

    q = qual[qual["Product_ID"] == pid]
    defects = q.groupby(["Defect_Type", "Root_Cause"]).agg(
        inspections=("QC_ID", "count"), rejected_units=("Rejected_Qty", "sum"),
        factory_loss_egp=("Estimated_Loss_EGP", "sum")
    ).reset_index().sort_values("rejected_units", ascending=False)
    st.subheader("Step 1 — What QC inspections found"); st.dataframe(defects)

    pr = prod[prod["Product_ID"] == pid]
    lines = pr.groupby(["Line_ID", "Primary_Bottleneck"]).agg(
        orders=("Production_Order_ID", "count"), rejected_units=("Rejected_Qty", "sum"),
        avg_efficiency_pct=("Efficiency_Pct", "mean")
    ).reset_index().sort_values("rejected_units", ascending=False)
    st.subheader("Step 2 — Which factory lines made it"); st.dataframe(lines)

    mats = bom[bom["Product_ID"] == pid][["Material_ID", "Material_Name", "Required_Per_Unit", "Unit"]]
    st.subheader("Step 3 — Materials inside this product"); st.dataframe(mats)

    po_sup = po.merge(sup[["Supplier_ID", "Supplier_Name"]], on="Supplier_ID", how="left")
    po_sup["Late"] = (pd.to_datetime(po_sup["Actual_Receipt_Date"], errors="coerce")
                      > pd.to_datetime(po_sup["Promised_Date"], errors="coerce"))
    sup_trace = po_sup[po_sup["Material_ID"].isin(mats["Material_ID"])].groupby(
        ["Supplier_Name", "Material_Name"]).agg(
        ordered_units=("Ordered_Qty", "sum"), rejected_units=("Rejected_Qty", "sum"),
        late_deliveries=("Late", "sum")
    ).reset_index().sort_values("rejected_units", ascending=False)
    st.subheader("Step 4 — Suppliers who sent those materials"); st.dataframe(sup_trace)

    if len(sup_trace) > 0 and sup_trace["rejected_units"].iloc[0] > 0:
        w = sup_trace.iloc[0]
        st.error(f"🚨 Prime suspect: **{w['Supplier_Name']}** sent {int(w['rejected_units']):,} "
                 f"rejected units of {w['Material_Name']} for this product. Audit this supplier first.")

    st.markdown("---")
    st.subheader("Supplier Risk League Table (all materials, whole company)")
    league = po_sup.groupby("Supplier_Name").agg(
        total_ordered=("Ordered_Qty", "sum"), total_rejected=("Rejected_Qty", "sum"),
        late_deliveries=("Late", "sum"), purchase_orders=("PO_ID", "count")
    ).reset_index()
    league["reject_rate"] = (league["total_rejected"] / league["total_ordered"]).round(4)
    st.dataframe(league.sort_values("total_rejected", ascending=False))

# ---------- TAB 4 ----------
with tab4:
    with st.expander("📥 Update the data this tab uses", expanded=True):
        ask("inv", "days-of-cover and supplier lead times come from this monthly snapshot.", "tab4")
    inv = get_table("inv")
    inv_copy = inv.copy()
    inv_copy["EARLY_WARNING"] = inv_copy["Days_of_Cover"] < inv_copy["Supplier_Lead_Time_Days"]
    danger = inv_copy[inv_copy["EARLY_WARNING"] == True]
    st.header("Inventory Early-Warning Zone (Present)")
    st.markdown(f"**{len(danger)}** product-location combinations are in the danger zone.")
    st.dataframe(danger[["Location_Name", "Product_ID", "Days_of_Cover", "Supplier_Lead_Time_Days"]].head(20))

# ---------- TAB 5 ----------
with tab5:
    with st.expander("📥 Update the data this tab uses", expanded=True):
        ask("inv", "THIS is the Inventory_History.csv file — it feeds both the Smoke Detector and this AI Forecast.", "tab5")
    inv = get_table("inv")
    st.header("🔮 AI Forecast: Next Month's Stockout Risk")

    inv_sorted = inv.sort_values(["Location_ID", "Product_ID", "Snapshot_Month"]).copy()
    lag_cols = ["Opening_Stock", "Days_of_Cover", "Avg_Daily_Sales_90D", "Sold_Qty"]
    for c in lag_cols:
        inv_sorted["LAST_" + c] = inv_sorted.groupby(["Location_ID", "Product_ID"])[c].shift(1)
    latest = inv_sorted.dropna(subset=["LAST_" + c for c in lag_cols]).copy()
    feats = ["LAST_" + c for c in lag_cols] + ["Supplier_Lead_Time_Days", "Safety_Stock_Units"]
    latest["Risk"] = forecast_model.predict_proba(latest[feats])[:, 1]
    latest["Reorder"] = (latest["LAST_Avg_Daily_Sales_90D"] * (latest["Supplier_Lead_Time_Days"] + 30)
                         + latest["Safety_Stock_Units"] - latest["LAST_Opening_Stock"]).clip(lower=0).round(0)
    high = latest[latest["Risk"] > 0.70].copy()

    if len(high) > 0:
        st.error(f"🚨 CRITICAL: {len(high)} items have a >70% chance of stocking out next month!")
        df = high[["Location_Name", "Product_Name", "LAST_Days_of_Cover",
                   "Supplier_Lead_Time_Days", "Risk", "Reorder"]].copy()
        df["Risk"] = df["Risk"].apply(lambda x: f"{x*100:.1f}%")
        df = df.rename(columns={"LAST_Days_of_Cover": "Current Days of Cover",
                                "Risk": "AI Risk Probability",
                                "Reorder": "Action: Order This Many Units"})
        st.dataframe(df.sort_values("AI Risk Probability", ascending=False).head(50))
    else:
        st.success("✅ No critical stockout risks predicted for next month!")