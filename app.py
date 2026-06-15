import streamlit as st
import pandas as pd
import plotly.express as px
import ccxt
import time

st.set_page_config(page_title="Crypto Dashboard - CCXT", layout="wide")

st.title("🚀 CCXT Multi-Exchange Dashboard")
st.markdown("**XT.com + MEXC + BitMEX** | Powered by CCXT")

# Sidebar
with st.sidebar:
    st.header("Controls")
    exchange_name = st.selectbox("Select Exchange", ["xt", "mexc", "bitmex"], index=0)
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

# Initialize exchange
@st.cache_resource
def get_exchange(name):
    if name == "xt":
        return ccxt.xt()
    elif name == "mexc":
        return ccxt.mexc()
    else:
        return ccxt.bitmex()

exchange = get_exchange(exchange_name)

# Fetch tickers
@st.cache_data(ttl=30)
def get_tickers(_exchange):
    try:
        tickers = _exchange.fetch_tickers()
        data = []
        for symbol, info in tickers.items():
            if "USDT" in symbol:  # Focus on USDT pairs
                base = symbol.split("/")[0] if "/" in symbol else symbol.replace("USDT", "")
                data.append({
                    "name": base,
                    "symbol": symbol,
                    "Price": info.get("last"),
                    "24h %": info.get("percentage") or info.get("change", 0)
                })
        df = pd.DataFrame(data)
        return df.dropna(subset=["Price"]).head(200)
    except Exception as e:
        st.error(f"Error fetching data from {exchange_name.upper()}: {e}")
        return pd.DataFrame()

df = get_tickers(exchange)

if df.empty:
    st.error("Could not load data. Try Manual Refresh or another exchange.")
else:
    df = df.sort_values("Price", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))

    tab1, tab2, tab3 = st.tabs(["📋 All Coins", "🔥 Top Gainers", "📉 Top Losers"])

    def show_table(data, title):
        st.subheader(f"{title} on {exchange_name.upper()} ({len(data)} shown)")
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

    # Historical Chart using CCXT
    st.subheader("📈 Historical Candlestick Chart")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox("Select Coin", df["name"].tolist(), index=0)
    with col2:
        timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=4)

    @st.cache_data(ttl=60)
    def get_ohlc(_exchange, symbol, tf, limit=200):
        try:
            ohlcv = _exchange.fetch_ohlcv(f"{symbol}/USDT", tf, limit=limit)
            df_ohlc = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df_ohlc["timestamp"] = pd.to_datetime(df_ohlc["timestamp"], unit="ms")
            return df_ohlc
        except:
            return pd.DataFrame()

    ohlc_df = get_ohlc(exchange, selected, timeframe)

    if not ohlc_df.empty:
        fig = px.line(ohlc_df, x="timestamp", y="close", title=f"{selected}/USDT — {timeframe} Chart")
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No OHLC data available for this pair right now.")

if auto_refresh:
    st.caption("🔄 Auto-refreshing...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
