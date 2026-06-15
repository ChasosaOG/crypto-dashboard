import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Crypto Dashboard", layout="wide", initial_sidebar_state="expanded")

# Currency symbols mapping
currency_symbols = {
    "usd": "$", "eur": "€", "gbp": "£", "jpy": "¥", "inr": "₹",
    "brl": "R$", "aud": "A$", "cad": "C$", "chf": "CHF", "cny": "¥",
    "try": "₺", "rub": "₽", "krw": "₩", "hkd": "HK$", "sgd": "S$",
    "mxn": "MX$", "zar": "R", "sek": "kr", "nok": "kr", "dkk": "kr"
}

st.title("🚀 Crypto Market Dashboard")
st.markdown("**Real-time Prices • Supplies • Charts • Trader Tools** | CoinGecko")

# Sidebar
with st.sidebar:
    st.header("🔧 Controls")
    vs_currency = st.selectbox("Currency", 
        ["usd", "eur", "gbp", "jpy", "inr", "brl", "aud", "cad", "chf", "cny", 
         "try", "rub", "krw", "hkd", "sgd", "mxn", "zar", "sek", "nok", "dkk"], 
        index=0)
    symbol = currency_symbols.get(vs_currency, vs_currency.upper())
    
    per_page = st.slider("Coins to Load", 10, 250, 150, step=10)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

    st.subheader("Advanced Filters")
    with st.expander("Open Filters", expanded=False):
        search = st.text_input("Search Coin", "")
        col1, col2 = st.columns(2)
        with col1:
            price_min = st.number_input("Min Price", value=0.0, format="%.6f")
            vol_min = st.number_input("Min Volume ($M)", value=0, step=1)
        with col2:
            price_max = st.number_input("Max Price", value=100000.0, format="%.2f")
            mcap_min = st.number_input("Min Market Cap ($M)", value=0, step=10)

        sort_by = st.selectbox("Sort By", ["market_cap", "price_change_percentage_24h", "current_price", "total_volume"], index=0)
        sort_order = st.radio("Order", ["Descending", "Ascending"])

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
        st.error("Rate limit — click refresh")
        return pd.DataFrame()

df = get_crypto_data(vs_currency, per_page)

if not df.empty:
    filtered = df.copy()
    if search:
        filtered = filtered[filtered["name"].str.contains(search, case=False) | filtered["symbol"].str.contains(search, case=False)]
    if price_min > 0: filtered = filtered[filtered["current_price"] >= price_min]
    if price_max < 100000: filtered = filtered[filtered["current_price"] <= price_max]
    if vol_min > 0: filtered = filtered[filtered["total_volume"] >= vol_min * 1_000_000]
    if mcap_min > 0: filtered = filtered[filtered["market_cap"] >= mcap_min * 1_000_000]

    ascending = sort_order == "Ascending"
    filtered = filtered.sort_values(by=sort_by, ascending=ascending).reset_index(drop=True)
    filtered.insert(0, "Rank", range(1, len(filtered) + 1))

    tab1, tab2, tab3 = st.tabs(["📋 Market Overview", "🔥 Gainers", "📉 Losers"])

    def show_table(data, title):
        st.subheader(title)
        disp = data[["Rank", "name", "symbol", "current_price", "price_change_percentage_24h",
                     "market_cap", "total_volume", "circulating_supply", "max_supply"]].copy()
        disp = disp.rename(columns={
            "current_price": "Price", "price_change_percentage_24h": "24h %",
            "market_cap": "Market Cap", "total_volume": "24h Volume",
            "circulating_supply": "Circulating", "max_supply": "Max Supply"
        })
        st.dataframe(
            disp.style.format({
                "Price": f"{symbol}{{:,.6f}}", 
                "24h %": "{:+.2f}%",
                "Market Cap": f"{symbol}{{:,.0f}}", 
                "24h Volume": f"{symbol}{{:,.0f}}"
            }).map(lambda x: "color:#00cc00;font-weight:bold" if isinstance(x, float) and x > 0 else "color:#ff4444;font-weight:bold", subset=["24h %"]),
            use_container_width=True, height=480
        )

    with tab1:
        show_table(filtered, "All Coins")
    with tab2:
        show_table(filtered.nlargest(30, "price_change_percentage_24h"), "Top Gainers")
    with tab3:
        show_table(filtered.nsmallest(30, "price_change_percentage_24h"), "Top Losers")

    # Chart
    st.subheader("📈 Price History")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_name = st.selectbox("Select Coin", filtered["name"].tolist(), index=0)
    with col2:
        timeframe_options = {"1": "1 Day", "7": "7 Days", "30": "30 Days", "90": "90 Days", "365": "1 Year", "max": "All Time"}
        timeframe_label = st.selectbox("Timeframe", options=list(timeframe_options.values()), index=2)
        timeframe = [k for k, v in timeframe_options.items() if v == timeframe_label][0]

    coin_id = df[df["name"] == selected_name]["id"].iloc[0]

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
        fig = px.line(hist, x="timestamp", y="price", title=f"{selected_name} — {timeframe_label} ({symbol})")
        fig.update_layout(height=520)
        st.plotly_chart(fig, use_container_width=True)

if auto_refresh:
    st.caption("🔄 Auto-refreshing every 60 seconds...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
