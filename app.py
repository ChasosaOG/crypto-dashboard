import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Your Crypto Dashboard", layout="wide")

st.title("🚀 Your Personal Crypto Info Dashboard")
st.markdown("**Real-time Prices • Supplies • Charts • Trader Tools** | CoinGecko Data")

# Sidebar controls
st.sidebar.header("Filters & Settings")
vs_currency = st.sidebar.selectbox("Currency", ["usd", "eur", "gbp", "jpy", "inr", "brl", "aud", "cad", "chf", "cny", "try", "rub"], index=0)
per_page = st.sidebar.slider("Number of coins to show", 10, 250, 150, step=10)

# Dark mode toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if st.sidebar.button("🌙 Toggle Dark / Light Mode"):
    st.session_state.dark_mode = not st.session_state.dark_mode

per_page = st.sidebar.slider("Coins in main table", 10, 250, 150, step=10)

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
        st.error("Rate limit — wait a moment and click Refresh")
        return pd.DataFrame()

df = get_crypto_data(vs_currency)

# Watchlist
if "watchlist" not in st.session_state:
    st.session_state.watchlist = set()

if not df.empty:
    # Filters
    st.sidebar.subheader("Table Filters")
    min_market_cap = st.sidebar.number_input("Min Market Cap ($M)", value=0, step=10)
    change_min = st.sidebar.slider("24h Change Min (%)", -100, 100, -10)
    change_max = st.sidebar.slider("24h Change Max (%)", -100, 100, 50)

    # Filtered data
    filtered_df = df.copy()
    if min_market_cap > 0:
        filtered_df = filtered_df[filtered_df["market_cap"] >= min_market_cap * 1_000_000]
    filtered_df = filtered_df[
        (filtered_df["price_change_percentage_24h"] >= change_min) & 
        (filtered_df["price_change_percentage_24h"] <= change_max)
    ]

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
        disp["Watchlist"] = disp["id"].apply(lambda x: "⭐" if x in st.session_state.watchlist else "☆")
        return disp

    def show_table(data, title):
        st.subheader(title)
        disp = make_display_df(data)
        st.dataframe(
            disp.style.format({
                "Price": f"${{:,.4f}}", "24h %": "{:+.2f}%",
                "Market Cap": "${:,.0f}", "24h Volume": "${:,.0f}"
            }).map(lambda x: "color:green;font-weight:bold" if isinstance(x, float) and x > 0 else ("color:red;font-weight:bold" if isinstance(x, float) else ""), subset=["24h %"]),
            width="stretch", height=550
        )
        # Watchlist controls
        coin_options = data["name"].tolist()
        selected_for_watch = st.multiselect("Toggle coins in Watchlist", coin_options, key=f"watch_{title}")
        if st.button("Update Watchlist", key=f"btn_{title}"):
            st.session_state.watchlist = {row["id"] for _, row in data.iterrows() if row["name"] in selected_for_watch}
            st.success("Watchlist updated!")

    with tab1:
        show_table(filtered_df, f"All Coins ({len(filtered_df)} shown)")

    with tab2:
        gainers = filtered_df.nlargest(30, "price_change_percentage_24h")
        show_table(gainers, "Top Gainers 24h")

    with tab3:
        losers = filtered_df.nsmallest(30, "price_change_percentage_24h")
        show_table(losers, "Top Losers 24h")

    # Watchlist section
    st.subheader("⭐ Your Watchlist")
    if st.session_state.watchlist:
        watch_df = df[df["id"].isin(st.session_state.watchlist)]
        if not watch_df.empty:
            show_table(watch_df, "Your Saved Coins")
    else:
        st.info("Select coins using the multiselect boxes above to build your watchlist")

    # Charts
    st.subheader("📈 Price History Chart")
    selected_name = st.selectbox("Select coin for chart", df["name"].tolist())
    coin_row = df[df["name"] == selected_name].iloc[0]
    coin_id = coin_row["id"]

    timeframe = st.selectbox("Timeframe", ["1", "7", "30", "90", "365", "max"], index=2)

    @st.cache_data(ttl=300)
    def get_history(coin_id, days, currency):
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": currency, "days": days}
        try:
            r = requests.get(url, params=params)
            prices = pd.DataFrame(r.json()["prices"], columns=["timestamp", "price"])
            prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit="ms")
            return prices
        except:
            return pd.DataFrame()

    hist = get_history(coin_id, timeframe, vs_currency)
    if not hist.empty:
        fig = px.line(hist, x="timestamp", y="price", title=f"{selected_name} Price History")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

if st.button("🔄 Refresh All Data"):
    st.rerun()

st.caption("Dashboard updated with your requests")
