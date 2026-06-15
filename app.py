import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Your Crypto Dashboard", layout="wide")

st.title("🚀 Your Personal Crypto Info Dashboard")
st.markdown("**Real-time Prices • Supplies • Charts • Trader Tools** | CoinGecko Data")

# Sidebar
st.sidebar.header("🔧 Filters & Controls")
vs_currency = st.sidebar.selectbox("Currency", ["usd", "eur", "gbp", "jpy", "inr", "brl", "aud", "cad", "chf", "cny", "try", "rub"], index=0)
per_page = st.sidebar.slider("Max coins to load", 10, 250, 200, step=10)

auto_refresh = st.sidebar.checkbox("Auto Refresh Every 60s", value=True)

st.sidebar.subheader("Advanced Filters")
search = st.sidebar.text_input("Search Name/Symbol", "")
price_min = st.sidebar.number_input("Min Price", value=0.0, format="%.6f")
price_max = st.sidebar.number_input("Max Price", value=100000.0, format="%.2f")
vol_min = st.sidebar.number_input("Min 24h Volume ($M)", value=0, step=1)
mcap_min = st.sidebar.number_input("Min Market Cap ($M)", value=0, step=10)

sort_by = st.sidebar.selectbox("Sort By", ["market_cap", "price_change_percentage_24h", "current_price", "total_volume"], index=0)
sort_order = st.sidebar.radio("Sort Order", ["Descending", "Ascending"])

@st.cache_data(ttl=60)
def get_crypto_data(currency, per_page):
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
        st.error("Rate limit — click Refresh")
        return pd.DataFrame()

df = get_crypto_data(vs_currency, per_page)

if not df.empty:
    # Apply filters
    filtered = df.copy()
    if search:
        filtered = filtered[filtered["name"].str.contains(search, case=False) | 
                           filtered["symbol"].str.contains(search, case=False)]
    if price_min > 0:
        filtered = filtered[filtered["current_price"] >= price_min]
    if price_max < 100000:
        filtered = filtered[filtered["current_price"] <= price_max]
    if vol_min > 0:
        filtered = filtered[filtered["total_volume"] >= vol_min * 1_000_000]
    if mcap_min > 0:
        filtered = filtered[filtered["market_cap"] >= mcap_min * 1_000_000]

    # Sort
    ascending = sort_order == "Ascending"
    filtered = filtered.sort_values(by=sort_by, ascending=ascending).reset_index(drop=True)
    filtered = filtered.reset_index()
    filtered = filtered.rename(columns={"index": "Rank"})
    filtered["Rank"] = filtered["Rank"] + 1

    tab1, tab2, tab3 = st.tabs(["📋 All Coins", "🔥 Top Gainers", "📉 Top Losers"])

    def make_display_df(data):
        disp = data[["Rank", "name", "symbol", "current_price", "price_change_percentage_24h",
                     "market_cap", "total_volume", "circulating_supply", "total_supply", "max_supply", "ath"]].copy()
        disp = disp.rename(columns={
            "current_price": "Price", 
            "price_change_percentage_24h": "24h %",
            "market_cap": "Market Cap", 
            "total_volume": "24h Volume",
            "circulating_supply": "Circulating", 
            "total_supply": "Total",
            "max_supply": "Max Supply", 
            "ath": "ATH"
        })
        return disp

    def show_table(data, title):
        st.subheader(f"{title} ({len(data)} coins)")
        disp = make_display_df(data)
        st.dataframe(
            disp.style.format({
                "Price": f"${{:,.6f}}", 
                "24h %": "{:+.2f}%",
                "Market Cap": "${:,.0f}", 
                "24h Volume": "${:,.0f}"
            }).map(lambda x: "color:green;font-weight:bold" if isinstance(x, float) and x > 0 else "color:red;font-weight:bold", subset=["24h %"]),
            width="stretch", 
            height=550
        )

    with tab1:
        show_table(filtered, "All Coins")

    with tab2:
        gainers = filtered.nlargest(30, "price_change_percentage_24h")
        show_table(gainers, "Top Gainers")

    with tab3:
        losers = filtered.nsmallest(30, "price_change_percentage_24h")
        show_table(losers, "Top Losers")

    # Dynamic Chart - updates with your selection
    st.subheader("📈 Price History Chart")
    default_index = 0  # Rank #1
    selected_name = st.selectbox("Select coin for chart", 
                                filtered["name"].tolist(), 
                                index=default_index)
    
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

# Refresh
if auto_refresh:
    st.caption("🔄 Auto-refreshing every 60 seconds...")
if st.button("🔄 Manual Refresh"):
    st.rerun()

st.caption("✅ Rank starts from #1 | Chart updates on coin selection")
