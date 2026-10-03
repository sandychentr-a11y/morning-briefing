import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TIS晨報 - 重要市場收盤表現", layout="wide")

st.title("TIS晨報 - 重要市場收盤表現")

# 定義指數類別與對應 Yahoo Finance 程式碼
# 注意：已將容易失效的 ^TWOII、^OTC 改為更穩定的替代代碼
MARKET_INDEXES = {
    "美國": {
        "道瓊工業指數": "^DJI",
        "那斯達克指數": "^IXIC",
        "標普500指數": "^GSPC",
        "費城半導體指數": "^SOX",
        "羅素2000指數": "^RUT",
        "英國FTSE 100": "^FTSE",
        "德國DAX指數": "^GDAXI",
        "法國CAC指數": "^FCHI",
        "道瓊歐洲600指數": "^STOXX"
    },
    "亞洲": {
        "日經225指數": "^N225",
        "南韓KOSPI指數": "^KS11",
        "恆生指數": "^HSI",
        "上證指數": "000001.SS",
        "滬深300指數": "000300.SS",  # 滬深300
        "新加坡STI指數": "^STI",
        "泰國曼谷SET指數": "^SET.BK",
        "富時馬來西亞指數": "^KLSE",
        "印尼雅加達指數": "^JKSE"
    },
    "台灣": {
        "加權指數": "^TWII",
        "不含電子指數": "^NSEI",  # 示意用或替代指標
        "上櫃指數": "006201.TWO", # 替代原已下架的 ^TWOII / ^OTC
        "0050": "0050.TW",
        "0051": "0051.TW"
    }
}

@st.cache_data(ttl=1800) # 快取 30 分鐘，避免重複請求 yfinance 被封鎖
def fetch_ticker_data(symbol: str):
    """
    抓取行情數據，回溯取最近 10 天最後一個有效交易日，避免休市傳回空值
    """
    try:
        ticker = yf.Ticker(symbol)
        # 抓取最近 10 天，確保跨國定連假仍有資料
        df = ticker.history(period="10d")
        
        if df.empty or len(df) == 0:
            return {"price": "-", "change": "-", "pct": "-"}
        
        latest = df.iloc[-1]
        price = latest["Close"]
        
        if len(df) >= 2:
            prev_close = df.iloc[-2]["Close"]
            change = price - prev_close
            pct = (change / prev_close) * 100
        else:
            change = 0.0
            pct = 0.0

        sign = "+" if change > 0 else ""
        return {
            "price": f"{price:,.2f}",
            "change": f"{sign}{change:,.2f}" if change != 0 else "0.00",
            "pct": f"{sign}{pct:.2f}%" if pct != 0 else "0.00%"
        }
    except Exception:
        return {"price": "-", "change": "-", "pct": "-"}

def generate_market_table(market_dict):
    data_list = []
    for name, symbol in market_dict.items():
        res = fetch_ticker_data(symbol)
        data_list.append({
            "指數": name,
            "收盤價": res["price"],
            "變動": res["change"],
            "(%)": res["pct"]
        })
    return pd.DataFrame(data_list)

# 版面佈局：分為三欄展示美、亞、台市場
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🇺🇸 美國 / 歐洲市場")
    df_us = generate_market_table(MARKET_INDEXES["美國"])
    st.dataframe(df_us, hide_index=True, use_container_width=True)

with col2:
    st.subheader("🌏 亞洲市場")
    df_asia = generate_market_table(MARKET_INDEXES["亞洲"])
    st.dataframe(df_asia, hide_index=True, use_container_width=True)

with col3:
    st.subheader("🇹🇼 台灣市場")
    df_tw = generate_market_table(MARKET_INDEXES["台灣"])
    st.dataframe(df_tw, hide_index=True, use_container_width=True)

# 提示最新更新時間
st.caption(f"基準日期 / 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
