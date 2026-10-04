import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import os


# CONFIGURATION
load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

BASE_URL = "https://www.alphavantage.co/query"

# PAGE CONFIG
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

# FUNCTION: GET STOCK DATA
@st.cache_data(ttl=60)
def get_stock_data(symbol):

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": API_KEY
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        st.error(f"API connection error: {e}")
        return None

    # Check API response
    if "Time Series (Daily)" not in data:

        if "Note" in data:
            st.warning(data["Note"])

        elif "Error Message" in data:
            st.error(data["Error Message"])

        else:
            st.error("Unable to fetch stock data.")

        return None

    # Convert API data into DataFrame
    df = pd.DataFrame.from_dict(
        data["Time Series (Daily)"],
        orient="index"
    )

    # Convert index to datetime
    df.index = pd.to_datetime(df.index)

    # Rename columns
    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume"
    })

    # Convert values to float
    df = df.astype(float)

    # Sort by date
    df = df.sort_index()

    return df

# FUNCTION: CALCULATE INDICATORS
def calculate_indicators(df):

    # SMA 20
    df["SMA20"] = df["Close"].rolling(20).mean()

    # SMA 50
    df["SMA50"] = df["Close"].rolling(50).mean()

    # EMA 20
    df["EMA20"] = df["Close"].ewm(
        span=20,
        adjust=False
    ).mean()

    # RSI
    delta = df["Close"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df["Close"].ewm(
        span=26,
        adjust=False
    ).mean()

    df["MACD"] = ema12 - ema26

    df["Signal"] = df["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    return df

# TITLE
st.title("📈 Real-Time Stock Market Dashboard")

st.write(
    "Track stock prices, moving averages, RSI, MACD and trading volume."
)

# SIDEBAR
st.sidebar.header("⚙️ Stock Settings")


symbol = st.sidebar.selectbox(
    "Select Stock",
    [
        "IBM",
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "TSLA",
        "NVDA",
        "META"
    ]
)

# Number of days
period = st.sidebar.slider(
    "Number of Days",
    min_value=30,
    max_value=100,
    value=100
)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):

    st.cache_data.clear()

    st.rerun()

# API KEY CHECK
if not API_KEY:

    st.error(
        "API key not found. Please add "
        "ALPHA_VANTAGE_API_KEY to your .env file."
    )

    st.stop()

# GET DATA
df = get_stock_data(symbol)


if df is None:

    st.stop()

# CALCULATE INDICATORS
df = calculate_indicators(df)

# SELECT DATA
display_df = df.tail(period)

# CURRENT STOCK INFORMATION
latest = df.iloc[-1]

current_price = latest["Close"]

open_price = latest["Open"]

high_price = latest["High"]

low_price = latest["Low"]

volume = latest["Volume"]

# Previous close
previous_close = df.iloc[-2]["Close"]

# Price change
change = current_price - previous_close

# Percentage change
change_percent = (
    change / previous_close
) * 100

# METRICS
st.subheader(f"{symbol} Market Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Current Price",
    f"${current_price:.2f}",
    f"{change_percent:.2f}%"
)

col2.metric(
    "Open",
    f"${open_price:.2f}"
)

col3.metric(
    "High",
    f"${high_price:.2f}"
)

col4.metric(
    "Low",
    f"${low_price:.2f}"
)

col5.metric(
    "Volume",
    f"{volume:,.0f}"
)

# CANDLESTICK CHART
st.subheader("📊 Candlestick Chart")

fig_candle = go.Figure()

fig_candle.add_trace(
    go.Candlestick(
        x=display_df.index,

        open=display_df["Open"],

        high=display_df["High"],

        low=display_df["Low"],

        close=display_df["Close"],

        name=symbol
    )
)

fig_candle.update_layout(

    title=f"{symbol} Stock Price",

    xaxis_title="Date",

    yaxis_title="Price",

    template="plotly_dark",

    height=550,

    xaxis_rangeslider_visible=False
)

st.plotly_chart(
    fig_candle,
    use_container_width=True
)

# MOVING AVERAGE CHART
st.subheader("📈 Moving Averages")

fig_ma = go.Figure()

# Close Price
fig_ma.add_trace(
    go.Scatter(
        x=display_df.index,

        y=display_df["Close"],

        mode="lines",

        name="Close Price"
    )
)

# SMA 20
fig_ma.add_trace(
    go.Scatter(
        x=display_df.index,

        y=display_df["SMA20"],

        mode="lines",

        name="SMA 20"
    )
)

# SMA 50
fig_ma.add_trace(
    go.Scatter(
        x=display_df.index,

        y=display_df["SMA50"],

        mode="lines",

        name="SMA 50"
    )
)

# EMA 20
fig_ma.add_trace(
    go.Scatter(
        x=display_df.index,

        y=display_df["EMA20"],

        mode="lines",

        name="EMA 20"
    )
)

fig_ma.update_layout(

    title=f"{symbol} Price + Moving Averages",

    xaxis_title="Date",

    yaxis_title="Price",

    template="plotly_dark",

    height=500
)

st.plotly_chart(
    fig_ma,
    use_container_width=True
)

# VOLUME CHART
st.subheader("📦 Trading Volume")

fig_volume = go.Figure()

fig_volume.add_trace(
    go.Bar(
        x=display_df.index,

        y=display_df["Volume"],

        name="Volume"
    )
)

fig_volume.update_layout(

    title="Trading Volume",

    xaxis_title="Date",

    yaxis_title="Volume",

    template="plotly_dark",

    height=400
)

st.plotly_chart(
    fig_volume,
    use_container_width=True
)


# RSI
st.subheader("📉 RSI - Relative Strength Index")

fig_rsi = go.Figure()

fig_rsi.add_trace(
    go.Scatter(
        x=display_df.index,

        y=display_df["RSI"],

        mode="lines",

        name="RSI"
    )
)

# Overbought level
fig_rsi.add_hline(
    y=70,

    line_dash="dash",

    annotation_text="Overbought (70)"
)

# Oversold level
fig_rsi.add_hline(
    y=30,

    line_dash="dash",

    annotation_text="Oversold (30)"
)


fig_rsi.update_layout(

    title="RSI",

    xaxis_title="Date",

    yaxis_title="RSI",

    template="plotly_dark",

    height=400,

    yaxis=dict(
        range=[0, 100]
    )
)


st.plotly_chart(
    fig_rsi,
    use_container_width=True
)

# MACD
st.subheader("📊 MACD")

fig_macd = go.Figure()

fig_macd.add_trace(
    go.Scatter(
        x=display_df.index,

        y=display_df["MACD"],

        mode="lines",

        name="MACD"
    )
)

fig_macd.add_trace(
    go.Scatter(
        x=display_df.index,

        y=display_df["Signal"],

        mode="lines",

        name="Signal"
    )
)

fig_macd.update_layout(

    title="MACD & Signal Line",

    xaxis_title="Date",

    yaxis_title="MACD",

    template="plotly_dark",

    height=400
)

st.plotly_chart(
    fig_macd,
    use_container_width=True
)

# RAW DATA
with st.expander("📋 View Raw Stock Data"):

    st.dataframe(
        display_df.sort_index(
            ascending=False
        ),
        use_container_width=True
    )

# FOOTER
st.markdown("---")

st.caption(
    "Stock Market Dashboard | "
    "Python • Pandas • Plotly • Requests • Streamlit"
)