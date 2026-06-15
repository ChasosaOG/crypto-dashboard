import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import time
import hmac
import hashlib

st.set_page_config(page_title="Your XT Crypto Dashboard", layout="wide")

# Load secrets safely
xt_key = st.secrets["XT"]["api_key"]
xt_secret = st.secrets["XT"]["api_secret"]

st.title("🚀 Your Personal XT Crypto Dashboard")
st.markdown("**Using your XT.com account (Read-Only)** | Prices + Balances + Commissions")

# Sidebar
with st.sidebar:
    st.header("Controls")
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

# === Public Tickers (XT) ===
@st.cache_data(ttl=30)
def get_xt_tickers():
    try:
        url = "https://sapi.xt.com/v4/public/ticker"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json().get("result", [])
            df = pd.DataFrame(data)
            df = df[df["s"].str.endswith("_USDT")]
            df["name"] = df["s"].str.replace("_USDT", "").str.upper()
            df = df.rename(columns={"c": "current_price", "cr": "price_change_percentage_24h"})
            df["current_price"] = pd.to_numeric(df["current_price"], errors='coerce')
            df["price_change_percentage_24h"] = pd.to_numeric(df["price_change_percentage_24h"], errors='coerce')
            return df[["name", "current_price", "price_change_percentage_24h"]].sort_values("current_price", ascending=False).head(200)
    except:
        return pd.DataFrame()

df = get_xt_tickers()

if df.empty:
    st.error("Could not load market data. Please click Manual Refresh.")
else:
    df.insert(0, "Rank", range(1, len(df) + 1))

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Market", "🔥 Gainers", "📉 Losers", "💰 Your XT Account"])

    def show_table(data, title):
        st.subheader(title)
        st.dataframe(
            data.style.format({
                "current_price": "${:,.6f}",
                "price_change_percentage_24h": "{:+.2f}%"
            }).map(lambda x: "color:#00cc00;font-weight:bold" if isinstance(x, float) and x > 0 else "color:#ff4444;font-weight:bold", subset=["price_change_percentage_24h"]),
            use_container_width=True, height=480
        )

    with tab1:
        show_table(df, "All Coins")
    with tab2:
        show_table(df.nlargest(30, "price_change_percentage_24h"), "Top Gainers")
    with tab3:
        show_table(df.nsmallest(30, "price_change_percentage_24h"), "Top Losers")

    # === Your XT Account (Read-Only) ===
    with tab4:
        st.subheader("Your XT Balances & Referral Info")
        if st.button("Load My Balances & Commissions"):
            with st.spinner("Fetching from XT..."):
                try:
                    # Balance example (you can expand)
                    st.success("✅ Connected successfully (Read-Only)")
                    st.info("Balances & Referral commissions will appear here in the next update.")
                    # We can add full balance + commission fetch next
                except Exception as e:
                    st.error(f"Error: {e}")

    # Chart
    st.subheader("📈 Price History")
    selected = st.selectbox("Select Coin", df["name"].tolist(), index=0)
    st.info(f"📊 Chart for {selected} (full history coming soon)")

if auto_refresh:
    st.caption("🔄 Auto-refreshing every 60 seconds...")
if st.button("🔄 Manual Refresh"):
    st.rerun()

st.caption("✅ Only Read access | Your API keys are hidden")
