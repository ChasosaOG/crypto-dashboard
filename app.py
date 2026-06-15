import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

st.title("🚀 Multi-Exchange Crypto Dashboard")
st.markdown("**Public Data from XT.com + MEXC + BitMEX** | No API Keys Needed")

# Sidebar
with st.sidebar:
    st.header("Controls")
    exchange = st.selectbox("Select Exchange", ["XT.com", "MEXC", "BitMEX"], index=0)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

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

@st.cache_data(ttl=30)
def get_bitmex_public():
    try:
        r = requests.get("https://www.bitmex.com/api/v1/instrument", timeout=15)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df = df[df.get("quoteCurrency") == "USD"]
            df = df.rename(columns={"symbol": "name", "lastPrice": "Price", "lastChangePcnt": "24h %"})
            df["Price"] = pd.to_numeric(df["Price"], errors='coerce')
            df["24h %"] = pd.to_numeric(df["24h %"], errors='coerce') * 100
            return df[["name", "Price", "24h %"]].head(100).dropna()
    except:
        return pd.DataFrame()

# Get data
if exchange == "XT.com":
    df = get_xt_public()
elif exchange == "MEXC":
    df = get_mexc_public()
else:
    df = get_bitmex_public()

# Safety check
if df is None or df.empty:
    st.error("❌ Failed to load data from this exchange. Please try another exchange or click Manual Refresh.")
    df = pd.DataFrame()  # prevent further errors
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

    # Chart
    st.subheader("📈 Price History")
    selected = st.selectbox("Select Coin", df["name"].tolist(), index=0)
    st.info(f"Selected: {selected} from {exchange} — Full chart support coming soon.")

if auto_refresh:
    st.caption("🔄 Auto-refreshing every 60 seconds...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
