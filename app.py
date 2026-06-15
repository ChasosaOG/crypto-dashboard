import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Your Crypto Dashboard", layout="wide")

# Dark mode toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# XT3020 Promo Banner
st.markdown("""
<div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; padding: 18px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
    <h2>🚀 Trade Smart on XT.com — Code <strong>XT3020</strong></h2>
    <p><strong>50% Cashback on my commissions for first 30 days!</strong> Transparent via official XT dashboard.<br>
    <a href="https://www.xt.com/en/register?ref=XT3020" target="_blank" style="color:#ffd700; font-weight:bold;">Register Now with XT3020 →</a></p>
</div>
""", unsafe_allow_html=True)

st.title("🚀 Your Personal Crypto Info Dashboard")
st.markdown("**Prices • Supplies • Charts • Trader Tools** | Powered by CoinGecko")

col1, col2 = st.columns([4, 1])
with col1:
    vs_currency = st.selectbox("Currency", ["usd", "eur", "gbp", "jpy", "inr", "brl", "aud", "cad", "chf", "cny", "try", "rub"], index=0)
with col2:
    st.button("🌙 Dark Mode" if st.session_state.dark_mode else "☀️ Light Mode", on_click=toggle_dark_mode)

per_page = st.slider("Coins to show", 10, 250, 150, step=10)

@st.cache_data(ttl=60)
def get_crypto_data(currency):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
    except:
        st.error("Rate limit — wait and refresh")
        return pd.DataFrame()

df = get_crypto_data(vs_currency)

# Watchlist
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

def toggle_watchlist(coin_id, name):
    if coin_id in st.session_state.watchlist:
        st.session_state.watchlist.remove(coin_id)
    else:
        st.session_state.watchlist.append(coin_id)

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📋 All Coins", "🔥 Top Gainers", "📉 Top Losers"])

    # Helper for table
    def display_table(data):
        df_display = data.copy()
        df_display = df_display.rename(columns={
            "current_price": "Price", "price_change_percentage_24h": "24h %",
            "market_cap": "Market Cap", "total_volume": "24h Volume",
            "circulating_supply": "Circulating", "total_supply": "Total",
            "max_supply": "Max Supply", "ath": "ATH"
        })
        
        # Add star column
        df_display["⭐"] = df_display["id"].apply(
            lambda x: "★" if x in st.session_state.watchlist else "☆"
        )
        
        st.dataframe(
            df_display[["⭐", "name", "symbol", "Price", "24h %", "Market Cap", "24h Volume", "Circulating", "Total", "Max Supply", "ATH"]].style.format({
                "Price": f"${{:,.4f}}", "24h %": "{:+.2f}%", "Market Cap": "${:,.0f}",
                "24h Volume": "${:,.0f}"
            }).map(lambda v: "color: green; font-weight: bold" if isinstance(v, float) and v > 0 else "color: red; font-weight: bold", subset=["24h %"]),
            width="stretch", height=650,
            on_click=lambda row: toggle_watchlist(row["id"], row["name"])  # simplified
        )

    with tab1:
        st.subheader(f"All Coins ({vs_currency.upper()})")
        search = st.text_input("🔍 Search", key="all_search")
        filtered = df
        if search:
            filtered = df[df["name"].str.contains(search, case=False) | df["symbol"].str.contains(search, case=False)]
        display_table(filtered)

    with tab2:
        st.subheader("🔥 Top Gainers (24h)")
        gainers = df.nlargest(30, "price_change_percentage_24h")
        display_table(gainers)

    with tab3:
        st.subheader("📉 Top Losers (24h)")
        losers = df.nsmallest(30, "price_change_percentage_24h")
        display_table(losers)

    # Watchlist Section
    st.subheader("⭐ Your Watchlist")
    if st.session_state.watchlist:
        watch_df = df[df["id"].isin(st.session_state.watchlist)]
        if not watch_df.empty:
            display_table(watch_df)
    else:
        st.info("Star coins in any tab to add them here")

    # Charts Section
    st.subheader("📈 Price History Chart")
    selected_coin = st.selectbox("Select coin for chart", df["name"].tolist(), index=0)
    coin_id = df[df["name"] == selected_coin]["id"].iloc[0]
    coin_symbol = df[df["name"] == selected_coin]["symbol"].iloc[0].upper()

    timeframe = st.selectbox("Timeframe", ["1", "7", "30", "90", "365", "max"], index=2)

    @st.cache_data(ttl=300)
    def get_history(coin_id, days, currency):
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": currency, "days": days, "interval": "daily" if days != "1" else "hourly"}
        try:
            r = requests.get(url, params=params)
            data = r.json()
            prices = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
            prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit='ms')
            return prices
        except:
            return pd.DataFrame()

    history = get_history(coin_id, timeframe, vs_currency)
    if not history.empty:
        fig = px.line(history, x="timestamp", y="price", title=f"{selected_coin} ({coin_symbol}) - {timeframe} days")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh All Data"):
    st.rerun()

st.caption("💡 Pro Tip: Share this dashboard with your XT3020 referrals!")
