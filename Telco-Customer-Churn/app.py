"""Streamlit churn prediction demo.

Run::

    # First time — train the model once:
    python -m telco_churn.model path/to/Telco-Customer-Churn.csv

    # Then launch the app:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from telco_churn.model import load_model, predict_churn  # noqa: E402


st.set_page_config(page_title="Telco Churn Risk", page_icon="📞", layout="centered")

st.title("📞 Telco Customer Churn Risk")
st.caption(
    "Enter a customer's profile on the left — the model returns their churn "
    "probability and a suggested retention play based on which risk bucket "
    "they fall into."
)

try:
    model = load_model()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# ─── Sidebar: customer profile inputs ───────────────────────────────────────

with st.sidebar:
    st.header("Customer profile")

    tenure = st.slider("Tenure (months)", 0, 72, 12)
    monthly = st.slider("Monthly charges ($)", 15.0, 130.0, 70.0, step=0.5)
    total = st.number_input("Total charges ($)", min_value=0.0, value=float(monthly * tenure))

    contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
    payment = st.selectbox(
        "Payment method",
        ["Electronic check", "Mailed check",
         "Bank transfer (automatic)", "Credit card (automatic)"],
    )
    paperless = st.selectbox("Paperless billing", ["Yes", "No"])

    st.divider()
    gender = st.selectbox("Gender", ["Male", "Female"])
    senior = st.selectbox("Senior citizen", [0, 1])
    partner = st.selectbox("Has partner", ["Yes", "No"])
    dependents = st.selectbox("Has dependents", ["Yes", "No"])

    st.divider()
    phone = st.selectbox("Phone service", ["Yes", "No"])
    multiple = st.selectbox("Multiple lines", ["Yes", "No", "No phone service"])
    internet = st.selectbox("Internet service", ["DSL", "Fiber optic", "No"])
    online_sec = st.selectbox("Online security", ["Yes", "No", "No internet service"])
    online_bak = st.selectbox("Online backup", ["Yes", "No", "No internet service"])
    device_prot = st.selectbox("Device protection", ["Yes", "No", "No internet service"])
    tech_sup = st.selectbox("Tech support", ["Yes", "No", "No internet service"])
    stream_tv = st.selectbox("Streaming TV", ["Yes", "No", "No internet service"])
    stream_mov = st.selectbox("Streaming movies", ["Yes", "No", "No internet service"])

customer = {
    "gender": gender, "SeniorCitizen": senior, "Partner": partner, "Dependents": dependents,
    "tenure": tenure, "PhoneService": phone, "MultipleLines": multiple,
    "InternetService": internet, "OnlineSecurity": online_sec, "OnlineBackup": online_bak,
    "DeviceProtection": device_prot, "TechSupport": tech_sup,
    "StreamingTV": stream_tv, "StreamingMovies": stream_mov,
    "Contract": contract, "PaperlessBilling": paperless, "PaymentMethod": payment,
    "MonthlyCharges": float(monthly), "TotalCharges": float(total),
}

proba = predict_churn(model, customer)

# ─── Main panel: risk readout + recommended action ──────────────────────────

col1, col2 = st.columns([2, 1])
with col1:
    st.metric("Churn probability", f"{proba:.0%}")
    st.progress(proba)

with col2:
    if proba >= 0.7:
        st.error("🚨 High risk")
    elif proba >= 0.4:
        st.warning("⚠️  Moderate risk")
    else:
        st.success("✅ Low risk")

st.subheader("Recommended retention play")

plays: list[tuple[str, str]] = []
if contract == "Month-to-month":
    plays.append((
        "Offer annual contract with 10–15% discount",
        "Month-to-month customers churn at ~43% vs. 3% on two-year contracts "
        "— the 15× gap means a 15% discount almost always pays back.",
    ))
if payment == "Electronic check":
    plays.append((
        "Offer $5–10 credit to switch to auto-pay",
        "Electronic-check users churn at ~45%. Auto-pay removes the monthly "
        "'decide to stay' moment and typically pays the credit back within a quarter.",
    ))
if tenure < 4:
    plays.append((
        "Enrol in Day-7 / Day-30 / Day-90 check-in workflow",
        "Most churn happens in the first 90 days. Lightweight outreach "
        "('How's it going? Anything we can help with?') recovers 3–5% of "
        "at-risk new customers.",
    ))
if internet == "Fiber optic" and online_sec == "No":
    plays.append((
        "Bundle Online Security add-on (first 3 months free)",
        "Fiber-optic customers without security add-ons show elevated churn "
        "— the add-on increases perceived value and add-on count is a known "
        "retention feature.",
    ))

if not plays:
    st.info("No automated play triggers for this profile. Keep in monitoring bucket.")
else:
    for title, rationale in plays:
        with st.expander(f"➡️  {title}"):
            st.write(rationale)

with st.expander("Why this prediction? (model internals)"):
    st.markdown(
        """
        The model is a **Gradient Boosting classifier** trained on 7,043 customer
        records from the IBM Telco Customer Churn dataset. Inputs are
        standardised (numerics) and one-hot encoded (categoricals) through a
        `ColumnTransformer` pipeline.

        Key churn drivers from feature importance:
        1. **Contract type** (month-to-month vs. 1y / 2y)
        2. **Tenure** (first 90 days are the danger zone)
        3. **Payment method** (electronic check stands out)
        4. **Total add-ons** (more services = stickier)
        5. **Monthly charges** (pricing pressure correlates with churn)

        The probability shown is the model's raw output at the 0.5 threshold
        boundary. For production you'd sweep the threshold against the cost of
        false positives (unnecessary retention spend) vs. false negatives
        (missed churner) — see `notebooks/02_modeling.ipynb`.
        """
    )
