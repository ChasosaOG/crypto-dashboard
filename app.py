import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import ccxt

st.set_page_config(page_title="Your Perfect Crypto Dashboard", layout="wide")

st.title("🚀 Your Perfect Crypto Dashboard")
st.markdown("**CoinGecko Data + CCXT Real-Time Comparison** | XT + MEXC + BitMEX")

# Sidebar Info
with st.sidebar:
    st.header("ℹ️ Supported Features")
    st.write("**Exchanges:** XT.com, MEXC, BitMEX + 100+ more via CCXT")
    st.write("**Currencies:** USD, EUR, GBP, JPY, INR, etc.")
    st.write("**Cryptos:** 150+ major coins from CoinGecko")
    
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)

# === CoinGecko Main Data ===
@st.cache_data(ttl=60)
def get_coingecko_data():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 150, "page": 1, "price_change_percentage": "24h"}
        r = requests.get(url, params=params, timeout=15)
        return pd.DataFrame(r.json())
    except:
        return pd.DataFrame()

df = get_coingecko_data()

if not df.empty:
    df = df.sort_values("market_cap", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))

    tab1, tab2, tab3, tab4 = st.tabs(["📋 All Coins", "🔥 Gainers", "📉 Losers", "📊 Supported Lists"])

    def show_table(data, title):
        st.subheader(title)
        disp = data[["Rank", "name", "symbol", "current_price", "price_change_percentage_24h",
                     "market_cap", "total_volume", "circulating_supply", "max_supply"]].copy()
        disp = disp.rename(columns={
            "current_price": "Price", "price_change_percentage_24h": "24h %",
            "market_cap": "Market Cap", "total_volume": "24h Volume"
        })
        st.dataframe(
            disp.style.format({"Price": "${:,.6f}", "24h %": "{:+.2f}%", "Market Cap": "${:,.0f}", "24h Volume": "${:,.0f}"})
            .map(lambda x: "color:#00cc00;font-weight:bold" if isinstance(x, float) and x > 0 else "color:#ff4444;font-weight:bold", subset=["24h %"]),
            use_container_width=True, height=480
        )

    with tab1:
        show_table(df, "All Coins")
    with tab2:
        show_table(df.nlargest(30, "price_change_percentage_24h"), "Top Gainers")
    with tab3:
        show_table(df.nsmallest(30, "price_change_percentage_24h"), "Top Losers")

    # === New Tab: Supported Lists ===
    with tab4:
        st.subheader("Supported Exchanges (via CCXT)")
        ex_list = ["xt", "mexc", "bitmex", "binance", "bybit", "gate", "kucoin", "bitget"] + list(ccxt.exchanges)[:30]
        st.write(", ".join([e.upper() for e in ex_list]))

        st.subheader("Supported Currencies")
        st.write("USD, EUR, GBP, JPY, INR, BRL, AUD, CAD, CHF, CNY, TRY, RUB, KRW, HKD + more")

        st.subheader("Popular Cryptos")
        st.write(df["name"].head(50).tolist())

    # === CCXT Price Comparison + Candlestick ===
    st.subheader(f"💰 Live Price Comparison — {focus_coin := st.text_input('Focus Coin', 'BTC', key='focus').upper()}")
    @st.cache_data(ttl=20)
    def get_comparison(coin):
        exs = {"XT.com": ccxt.xt(), "MEXC": ccxt.mexc(), "BitMEX": ccxt.bitmex()}
        data = []
        for name, ex in exs.items():
            try:
                ticker = ex.fetch_ticker(f"{coin}/USDT")
                data.append({"Exchange": name, "Price": ticker.get("last"), "24h %": ticker.get("percentage") or 0})
            except:
                data.append({"Exchange": name, "Price": None, "24h %": None})
        return pd.DataFrame(data)

    comp = get_comparison(focus_coin)
    st.dataframe(comp.style.format({"Price": "${:,.6f}", "24h %": "{:+.2f}%"}).map(
        lambda x: "color:green;font-weight:bold" if isinstance(x, float) and x > 0 else "color:red;font-weight:bold", subset=["24h %"]),
        use_container_width=True)

    # Candlestick
    st.subheader(f"📊 {focus_coin}/USDT Candlestick")
    tf = st.selectbox("Timeframe", ["1m","5m","15m","1h","4h","1d"], index=4)
    @st.cache_data(ttl=60)
    def get_candles(coin, timeframe):
        try:
            mexc = ccxt.mexc()
            ohlcv = mexc.fetch_ohlcv(f"{coin}/USDT", timeframe, limit=300)
            dfc = pd.DataFrame(ohlcv, columns=["ts", "o", "h", "l", "c", "v"])
            dfc["ts"] = pd.to_datetime(dfc["ts"], unit="ms")
            return dfc
        except:
            return pd.DataFrame()
    candles = get_candles(focus_coin, tf)
    if not candles.empty:
        fig = go.Figure(data=[go.Candlestick(x=candles["ts"], open=candles["o"], high=candles["h"], low=candles["l"], close=candles["c"])])
        fig.update_layout(height=600, title=f"{focus_coin}/USDT {tf}")
        st.plotly_chart(fig, use_container_width=True)

if auto_refresh:
    st.caption("🔄 Auto-refreshing...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
