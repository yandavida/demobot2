# Layer: ui
import streamlit as st
from datetime import date, timedelta


def build_market_sidebar():
    st.sidebar.subheader("Market Inputs")

    spot = st.sidebar.number_input("Spot Price", value=500.0, step=1.0)
    r = st.sidebar.number_input("Interest Rate (r)", value=0.05, step=0.01)
    q = st.sidebar.number_input("Dividend Yield (q)", value=0.00, step=0.01)
    iv = st.sidebar.number_input("IV (vol)", value=0.20, step=0.01)

    expiry = st.sidebar.date_input(
        "Expiration Date", value=date.today() + timedelta(days=30)
    )

    return spot, r, q, iv, expiry
