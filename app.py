import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ccxt

st.set_page_config(page_title="Crypto Dashboard - CCXT", layout="wide")

st.title("🚀 CCXT Multi-Exchange Dashboard")
st.markdown("**Price Comparison + Candlestick Charts** | XT + MEXC + BitMEX")

# Sidebar
with st.sidebar:
    st.header("Controls")
    auto_refresh = st.checkbox("Auto Refresh (60s)", value=True)
    focus_coin = st.text_input("Focus Coin", value="BTC").upper()

# Initialize exchanges
@st.cache_resource
def get_exchanges():
    return {
        "XT.com": ccxt.xt(),
        "MEXC": ccxt.mexc(),
        "BitMEX": ccxt.bitmex()
    }

exchanges = get_exchanges()

# Price Comparison
@st.cache_data(ttl=20)
def get_price_comparison(coin):
    data = []
    for ex_name, ex in exchanges.items():
        try:
            ticker = ex.fetch_ticker(f"{coin}/USDT")
            data.append({
                "Exchange": ex_name,
                "Price": ticker.get("last"),
                "24h Change %": ticker.get("percentage") or 0,
                "Volume": ticker.get("quoteVolume")
            })
        except:
            data.append({"Exchange": ex_name, "Price": None, "24h Change %": None, "Volume": None})
    return pd.DataFrame(data)

df_comp = get_price_comparison(focus_coin)

st.subheader(f"💰 Price Comparison — {focus_coin}/USDT")
st.dataframe(
    df_comp.style.format({"Price": "${:,.6f}", "24h Change %": "{:+.2f}%"})
    .map(lambda x: "color:green;font-weight:bold" if isinstance(x, float) and x > 0 else "color:red;font-weight:bold", subset=["24h Change %"]),
    use_container_width=True
)

# Candlestick Chart (MEXC)
st.subheader(f"📊 {focus_coin}/USDT Candlestick")
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=4)

@st.cache_data(ttl=60)
def get_candles(coin, tf):
    try:
        mexc = ccxt.mexc()
        ohlcv = mexc.fetch_ohlcv(f"{coin}/USDT", tf, limit=300)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except:
        return pd.DataFrame()

candles = get_candles(focus_coin, timeframe)

if not candles.empty:
    fig = go.Figure(data=[go.Candlestick(
        x=candles["timestamp"],
        open=candles["open"],
        high=candles["high"],
        low=candles["low"],
        close=candles["close"]
    )])
    fig.update_layout(height=600, title=f"{focus_coin}/USDT {timeframe}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No candlestick data available for this coin/timeframe.")

if auto_refresh:
    st.caption("🔄 Auto-refreshing...")
if st.button("🔄 Manual Refresh"):
    st.rerun()
