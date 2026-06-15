import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import time

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

st.title("🚀 Your Personal Crypto Dashboard")
st.markdown("**CoinGecko Data** | Real-time Prices + Historical Charts")

# Sidebar
with st.sidebar:
    st.header("Controls")
    vs_currency = st.selectbox("Currency", ["usd", "eur", "gbp", "jpy", "inr", "brl", "aud", "cad", "chf", "cny", "try", "rub"], index=0)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

@st.cache_data(ttl=45)
def get_crypto_data(currency):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": 150,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 200:
                return pd.DataFrame(r.json())
        except:
            time.sleep(1)
    st.error("CoinGecko is busy. Please click Manual Refresh.")
    return pd.DataFrame()

df = get_crypto_data(vs_currency)

if not df.empty:
    # Add Rank
    df = df.sort_values("market_cap", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))

    tab1, tab2, tab3 = st.tabs(["📋 All Coins", "🔥 Top Gainers", "📉 Top Losers"])

    def show_table(data, title):
        st.subheader(title)
        disp = data[["Rank", "name", "symbol", "current_price", "price_change_percentage_24h",
                     "market_cap", "total_volume", "circulating_supply", "max_supply"]].copy()
        disp = disp.rename(columns={
            "current_price": "Price", "price_change_percentage_24h": "24h %",
            "market_cap": "Market Cap", "total_volume": "24h Volume"
        })
        st.dataframe(
            disp.style.format({
                "Price": "${:,.6f}", "24h %": "{:+.2f}%",
                "Market Cap": "${:,.0f}", "24h Volume": "${:,.0f}"
            }).map(lambda x: "color:#00cc00;font-weight:bold" if isinstance(x, float) and x > 0 else "color:#ff4444;font-weight:bold", subset=["24h %"]),
            use_container_width=True, height=480
        )

    with tab1:
        show_table(df, "All Coins")
    with tab2:
        show_table(df.nlargest(30, "price_change_percentage_24h"), "Top Gainers")
    with tab3:
        show_table(df.nsmallest(30, "price_change_percentage_24h"), "Top Losers")

    # Historical Chart
    st.subheader("📈 Historical Price Chart")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_name = st.selectbox("Select Coin", df["name"].tolist(), index=0)
    with col2:
        days = st.selectbox("Timeframe", ["1", "7", "30", "90", "365", "max"], index=2)

    @st.cache_data(ttl=300)
    def get_history(coin_id, days, currency):
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": currency, "days": days}
        try:
            r = requests.get(url, params=params, timeout=15)
            prices = pd.DataFrame(r.json()["prices"], columns=["timestamp", "price"])
            prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit="ms")
            return prices
        except:
            return pd.DataFrame()

    coin_id = df[df["name"] == selected_name]["id"].iloc[0]
    hist = get_history(coin_id, days, vs_currency)

    if not hist.empty:
        fig = px.line(hist, x="timestamp", y="price", title=f"{selected_name} Price History")
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)

if auto_refresh:
    st.caption("🔄 Auto-refreshing every 60 seconds...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
