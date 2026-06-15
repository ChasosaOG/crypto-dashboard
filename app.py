%%writefile app.py
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Your Crypto Dashboard", layout="wide")
st.title("🚀 Your Personal Crypto Info Dashboard")
st.markdown("**Real-time prices + supplies for traders & investors** | CoinGecko Data | Refresh anytime")

# Sidebar
vs_currency = st.sidebar.selectbox(
    "Select Currency (changes everything instantly)", 
    ["usd", "eur", "gbp", "jpy", "inr", "brl", "aud", "cad", "chf", "cny", "try", "rub"],
    index=0
)
per_page = st.sidebar.slider("Coins to show", 10, 250, 150, step=10)

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
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error("Rate limit – wait 60 seconds and refresh")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Connection error: {e}")
        return pd.DataFrame()

df = get_crypto_data(vs_currency)

if not df.empty:
    # Columns for display
    cols = ["name", "symbol", "current_price", "price_change_percentage_24h",
            "market_cap", "total_volume", "circulating_supply",
            "total_supply", "max_supply", "ath", "ath_change_percentage", "image"]
    
    df_display = df[cols].copy()
    df_display = df_display.rename(columns={
        "current_price": "Price",
        "price_change_percentage_24h": "24h %",
        "market_cap": "Market Cap",
        "total_volume": "24h Volume",
        "circulating_supply": "Circulating Supply",
        "total_supply": "Total Supply",
        "max_supply": "Max Supply",
        "ath": "All-Time High",
        "ath_change_percentage": "% from ATH"
    })

    # Always show the full table first
    st.subheader(f"📋 Top Cryptos in {vs_currency.upper()}")
    
    search = st.text_input("🔍 Search coin (name or symbol)", key="search_input")
    if search:
        mask = (df_display["name"].str.contains(search, case=False, na=False) | 
                df_display["symbol"].str.contains(search, case=False, na=False))
        df_filtered = df_display[mask]
    else:
        df_filtered = df_display

    # Color 24h change
    def color_24h(val):
        if pd.isna(val):
            return ""
        return f"color: {'green' if val > 0 else 'red'}; font-weight: bold"

    st.dataframe(
        df_filtered.style.format({
            "Price": f"${{:,.4f}}",
            "24h %": "{:+.2f}%",
            "Market Cap": "${:,.0f}",
            "24h Volume": "${:,.0f}",
            "% from ATH": "{:+.2f}%"
        }).map(color_24h, subset=["24h %"]),
        width="stretch",
        height=700,
        use_container_width=True  # fallback for older versions
    )

    # Detailed single coin view
    st.subheader("📊 Full Details for One Coin")
    selected_coin = st.selectbox("Pick a coin", df["name"].tolist(), index=0)
    row = df[df["name"] == selected_coin].iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(row["image"], width=120)
        st.metric("Price", f"${row['current_price']:,.4f}", f"{row['price_change_percentage_24h']:+.2f}% 24h")
    with col2:
        st.write(f"**Circulating**: {row.get('circulating_supply', 'N/A'):,}")
        st.write(f"**Total Supply**: {row.get('total_supply', 'N/A'):,}")
        st.write(f"**Max Supply**: {row.get('max_supply', 'N/A'):,}")
    with col3:
        st.write(f"**Market Cap**: ${row.get('market_cap', 'N/A'):,}")
        st.write(f"**24h Volume**: ${row.get('total_volume', 'N/A'):,}")
        st.write(f"**ATH**: ${row.get('ath', 'N/A'):,} ({row.get('ath_change_percentage', 'N/A'):+.2f}%)")

    st.caption("💡 Pro tip: Add your **XT3020** referral banner or trading notes here later!")

# Manual refresh
if st.button("🔄 Refresh All Data"):
    st.rerun()

st.success("✅ Dashboard updated! Currency switches instantly. Search works on the full list.")
