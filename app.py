import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Your Crypto Dashboard", layout="wide")

# XT3020 Banner
st.markdown("""
<div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; padding: 18px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
    <h2>🚀 Trade on XT.com — Code <strong>XT3020</strong></h2>
    <p><strong>50% Cashback on my commissions for first 30 days!</strong> Transparent via official dashboard.<br>
    <a href="https://www.xt.com/en/register?ref=XT3020" target="_blank" style="color:#ffd700; font-weight:bold;">Register Now with XT3020 →</a></p>
</div>
""", unsafe_allow_html=True)

st.title("🚀 Your Personal Crypto Info Dashboard")
st.markdown("**Prices • Supplies • Charts • Trader Tools** | CoinGecko")

# Controls
col1, col2 = st.columns([4, 1])
with col1:
    vs_currency = st.selectbox("Currency", ["usd", "eur", "gbp", "jpy", "inr", "brl", "aud", "cad", "chf", "cny", "try", "rub"], index=0)
with col2:
    if st.button("🌙 Toggle Dark/Light"):
        if "theme" not in st.session_state:
            st.session_state.theme = "light"
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

per_page = st.slider("Coins to show", 10, 250, 150, step=10)

@st.cache_data(ttl=60)
def get_crypto_data(currency):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency, "order": "market_cap_desc",
        "per_page": per_page, "page": 1, "sparkline": False, "price_change_percentage": "24h"
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        return pd.DataFrame(r.json()) if r.status_code == 200 else pd.DataFrame()
    except:
        st.error("Rate limit — click Refresh")
        return pd.DataFrame()

df = get_crypto_data(vs_currency)

# Watchlist (persistent during session)
if "watchlist" not in st.session_state:
    st.session_state.watchlist = set()

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📋 All Coins", "🔥 Top Gainers", "📉 Top Losers"])

    def make_display_df(data):
        disp = data[["id", "name", "symbol", "current_price", "price_change_percentage_24h",
                     "market_cap", "total_volume", "circulating_supply", "total_supply", "max_supply", "ath"]].copy()
        disp = disp.rename(columns={
            "current_price": "Price", "price_change_percentage_24h": "24h %",
            "market_cap": "Market Cap", "total_volume": "24h Volume",
            "circulating_supply": "Circulating", "total_supply": "Total",
            "max_supply": "Max Supply", "ath": "ATH"
        })
        disp["In Watchlist"] = disp["id"].apply(lambda x: "⭐" if x in st.session_state.watchlist else "☆")
        return disp

    def show_table(data):
        disp = make_display_df(data)
        st.dataframe(
            disp.style.format({
                "Price": f"${{:,.4f}}", "24h %": "{:+.2f}%",
                "Market Cap": "${:,.0f}", "24h Volume": "${:,.0f}"
            }).map(lambda x: "color:green;font-weight:bold" if isinstance(x, float) and x > 0 else "color:red;font-weight:bold", subset=["24h %"]),
            width="stretch", height=600
        )
        # Watchlist management
        st.subheader("Add/Remove from Watchlist")
        selected_coins = st.multiselect("Select coins to toggle in watchlist", 
                                      options=data["name"].tolist(), 
                                      default=[row["name"] for _, row in data.iterrows() if row["id"] in st.session_state.watchlist][:10])
        if st.button("Update Watchlist"):
            st.session_state.watchlist = {row["id"] for _, row in data.iterrows() if row["name"] in selected_coins}
            st.success("Watchlist updated!")

    with tab1:
        st.subheader(f"All Coins ({vs_currency.upper()})")
        search = st.text_input("🔍 Search", key="search_all")
        filtered = df
        if search:
            filtered = df[df["name"].str.contains(search, case=False) | df["symbol"].str.contains(search, case=False)]
        show_table(filtered)

    with tab2:
        st.subheader("🔥 Top Gainers 24h")
        show_table(df.nlargest(30, "price_change_percentage_24h"))

    with tab3:
        st.subheader("📉 Top Losers 24h")
        show_table(df.nsmallest(30, "price_change_percentage_24h"))

    # Watchlist Tab Content
    st.subheader("⭐ Your Watchlist")
    if st.session_state.watchlist:
        watch_df = df[df["id"].isin(st.session_state.watchlist)]
        if not watch_df.empty:
            show_table(watch_df)
    else:
        st.info("Use the multiselect above to add coins to your watchlist")

    # Charts
    st.subheader("📈 Price History")
    selected_name = st.selectbox("Select coin", df["name"].tolist())
    coin_data = df[df["name"] == selected_name].iloc[0]
    coin_id = coin_data["id"]

    timeframe = st.selectbox("Timeframe", ["1", "7", "30", "90", "365", "max"], index=2)

    @st.cache_data(ttl=300)
    def get_history(coin_id, days, vs_currency):
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": vs_currency, "days": days, "interval": "daily" if days != "1" else "hourly"}
        try:
            r = requests.get(url, params=params)
            prices = pd.DataFrame(r.json()["prices"], columns=["timestamp", "price"])
            prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit="ms")
            return prices
        except:
            return pd.DataFrame()

    hist = get_history(coin_id, timeframe, vs_currency)
    if not hist.empty:
        fig = px.line(hist, x="timestamp", y="price", title=f"{selected_name} Price Chart")
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh All Data"):
    st.rerun()

st.caption("💡 Share this link with your XT3020 network!")
