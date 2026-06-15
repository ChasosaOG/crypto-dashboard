import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

st.title("🚀 Multi-Exchange Crypto Dashboard")
st.markdown("**Public Data from XT + MEXC + BitMEX** | Historical Charts Added")

# Sidebar
with st.sidebar:
    st.header("Controls")
    exchange = st.selectbox("Select Exchange", ["MEXC", "XT.com", "BitMEX"], index=0)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

# Public data functions (same as before)
@st.cache_data(ttl=30)
def get_xt_public():
    try:
        r = requests.get("https://www.xt.com/en/api/v1/public/tickers", timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", [])
            df = pd.DataFrame(data)
            df = df[df["symbol"].str.endswith("_USDT")]
            df["name"] = df["symbol"].str.replace("_USDT", "").str.upper()
            df = df.rename(columns={"last": "Price", "change": "24h %"})
            df["Price"] = pd.to_numeric(df["Price"], errors='coerce')
            df["24h %"] = pd.to_numeric(df["24h %"], errors='coerce') * 100
            return df[["name", "Price", "24h %"]].head(200).dropna()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_mexc_public():
    try:
        r = requests.get("https://api.mexc.com/api/v3/ticker/24hr", timeout=15)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df = df[df["symbol"].str.endswith("USDT")]
            df["name"] = df["symbol"].str.replace("USDT", "")
            df = df.rename(columns={"lastPrice": "Price", "priceChangePercent": "24h %"})
            df["Price"] = pd.to_numeric(df["Price"], errors='coerce')
            df["24h %"] = pd.to_numeric(df["24h %"], errors='coerce')
            return df[["name", "Price", "24h %"]].head(200).dropna()
    except:
        return pd.DataFrame()

# Historical Chart Function (using MEXC - most reliable)
@st.cache_data(ttl=300)
def get_historical_data(symbol, interval="1d", limit=100):
    try:
        url = "https://api.mexc.com/api/v3/klines"
        params = {
            "symbol": f"{symbol}USDT",
            "interval": interval,
            "limit": limit
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["close"] = pd.to_numeric(df["close"])
            return df[["timestamp", "close"]]
    except:
        return pd.DataFrame()

if exchange == "MEXC":
    df = get_mexc_public()
elif exchange == "XT.com":
    df = get_xt_public()
else:
    df = pd.DataFrame()  # BitMEX simplified for now

if df.empty:
    st.error("Failed to load data. Try another exchange or Manual Refresh.")
else:
    df = df.sort_values("Price", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))

    tab1, tab2, tab3 = st.tabs(["📋 All Coins", "🔥 Top Gainers", "📉 Top Losers"])

    def show_table(data, title):
        st.subheader(f"{title} on {exchange} ({len(data)} shown)")
        st.dataframe(
            data.style.format({"Price": "${:,.6f}", "24h %": "{:+.2f}%"})
            .map(lambda x: "color:#00cc00;font-weight:bold" if isinstance(x, float) and x > 0 else "color:#ff4444;font-weight:bold", subset=["24h %"]),
            use_container_width=True, height=500
        )

    with tab1:
        show_table(df, "All Coins")
    with tab2:
        show_table(df.nlargest(30, "24h %"), "Top Gainers")
    with tab3:
        show_table(df.nsmallest(30, "24h %"), "Top Losers")

    # Historical Chart Section
    st.subheader("📈 Historical Price Chart")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox("Select Coin", df["name"].tolist(), index=0)
    with col2:
        interval = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d", "1w"], index=5)

    hist_df = get_historical_data(selected, interval, limit=200)

    if not hist_df.empty:
        fig = px.line(hist_df, x="timestamp", y="close", 
                     title=f"{selected} — {interval} Chart (MEXC Data)")
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical data available for this coin right now.")

if auto_refresh:
    st.caption("🔄 Auto-refreshing...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
