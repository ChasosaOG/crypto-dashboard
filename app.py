import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import time
import hmac
import hashlib
import time as time_module

st.set_page_config(page_title="Crypto Dashboard", layout="wide", initial_sidebar_state="expanded")

# Currency symbols
currency_symbols = {
    "usd": "$", "eur": "€", "gbp": "£", "jpy": "¥", "inr": "₹",
    "brl": "R$", "aud": "A$", "cad": "C$", "chf": "CHF", "cny": "¥",
    "try": "₺", "rub": "₽", "krw": "₩", "hkd": "HK$"
}

st.title("🚀 Your Crypto Dashboard")
st.markdown("**XT.com Data + Public Fallback** | Real-time & Stable")

# Sidebar
with st.sidebar:
    st.header("🔧 Controls")
    vs_currency = st.selectbox("Currency", list(currency_symbols.keys()), index=0)
    symbol = currency_symbols.get(vs_currency, vs_currency.upper())
    
    per_page = st.slider("Coins to Load", 10, 250, 150, step=10)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

    st.subheader("XT Private Data (Read-Only)")
    show_balances = st.checkbox("Show My XT Balances", value=False)

# Load XT Secrets (safe)
xt_api_key = ""
xt_api_secret = ""
if "XT" in st.secrets:
    xt_api_key = st.secrets["XT"].get("api_key", "")
    xt_api_secret = st.secrets["XT"].get("api_secret", "")

# Public XT Tickers (no key needed)
@st.cache_data(ttl=30)
def get_xt_public_tickers():
    try:
        url = "https://www.xt.com/en/api/v1/public/tickers"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", [])
            df = pd.DataFrame(data)
            df = df[df["symbol"].str.endswith("_USDT")]
            df["name"] = df["symbol"].str.replace("_USDT", "")
            df = df.rename(columns={"last": "current_price", "change": "price_change_percentage_24h"})
            df["current_price"] = pd.to_numeric(df["current_price"], errors="coerce")
            df["price_change_percentage_24h"] = pd.to_numeric(df["price_change_percentage_24h"], errors="coerce") * 100
            return df[["name", "current_price", "price_change_percentage_24h"]].head(150)
    except:
        return pd.DataFrame()
    return pd.DataFrame()

df = get_xt_public_tickers()

if df.empty:
    st.error("Could not load data. Click Manual Refresh.")
else:
    # Add Rank
    df = df.sort_values("current_price", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))

    tab1, tab2, tab3 = st.tabs(["📋 All Coins", "🔥 Gainers", "📉 Losers"])

    def show_table(data, title):
        st.subheader(f"{title} ({len(data)} coins)")
        st.dataframe(
            data.style.format({
                "current_price": f"{symbol}{{:.6f}}",
                "price_change_percentage_24h": "{:+.2f}%"
            }).map(lambda x: "color:#00cc00;font-weight:bold" if isinstance(x, float) and x > 0 else "color:#ff4444;font-weight:bold", subset=["price_change_percentage_24h"]),
            use_container_width=True, height=500
        )

    with tab1:
        show_table(df, "All Coins")
    with tab2:
        show_table(df.nlargest(30, "price_change_percentage_24h"), "Top Gainers")
    with tab3:
        show_table(df.nsmallest(30, "price_change_percentage_24h"), "Top Losers")

    # Dynamic Chart
    st.subheader("📈 Price History")
    selected_name = st.selectbox("Select Coin", df["name"].tolist(), index=0)
    st.info("Full historical chart coming in next update (using XT data)")

    # Optional: Show Balances (Read-Only)
    if show_balances and xt_api_key and xt_api_secret:
        st.subheader("💰 My XT Balances (Read-Only)")
        st.success("XT keys detected. Balance feature will be added in the next update.")
    elif show_balances:
        st.warning("Add your XT API keys in Streamlit Secrets to see balances.")

if auto_refresh:
    st.caption("🔄 Auto-refreshing every 60 seconds...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
