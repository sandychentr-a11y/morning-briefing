from datetime import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------
# 1. 頁面佈局與標題
# ---------------------------------------------------------
st.set_page_config(
    page_title="TIS晨報 - 重要市場收盤表現",
    layout="wide",
)

st.title("TIS晨報 - 重要市場收盤表現")

# ---------------------------------------------------------
# 2. 市場類別與對應 Ticker (含多重備援代碼)
# ---------------------------------------------------------
MARKET_INDEXES = {
    "美國 / 歐洲市場": {
        "道瓊工業指數": ["^DJI"],
        "那斯達克指數": ["^IXIC"],
        "標普500指數": ["^GSPC"],
        "費城半導體指數": ["^SOX"],
        "羅素2000指數": ["^RUT"],
        "英國FTSE 100": ["^FTSE"],
        "德國DAX指數": ["^GDAXI"],
        "法國CAC指數": ["^FCHI"],
        "道瓊歐洲600指數": ["^STOXX"],
    },
    "亞洲市場": {
        "日經225指數": ["^N225"],
        "南韓KOSPI指數": ["^KS11"],
        "恆生指數": ["^HSI"],
        "上證指數": ["000001.SS"],
        "滬深300指數": ["000300.SS", "399300.SZ", "ASHR"],
        "新加坡STI指數": ["^STI"],
        "泰國曼谷SET指數": ["^SET.BK", "^SET"],
        "富時馬來西亞指數": ["^KLSE"],
        "印尼雅加達指數": ["^JKSE"],
    },
    "台灣市場": {
        "加權指數": ["^TWII"],
        "不含電子指數": ["^TW28", "0052.TW"],
        "上櫃指數": ["^OTC", "^TWO", "006201.TWO"],
        "0050": ["0050.TW"],
        "0051": ["0051.TW"],
    },
}


# ---------------------------------------------------------
# 3. 資料抓取與 fallback 處理 (回溯 10 天防休市/連假)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_ticker_data_with_fallback(symbol_list):
    for symbol in symbol_list:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="10d")  # 抓取 10 天，確保跨連假仍能取得有效歷史數據
            df = df[df["Close"].notna()]

            if len(df) >= 2:
                price = df["Close"].iloc[-1]
                prev_close = df["Close"].iloc[-2]
                change = price - prev_close
                pct = (change / prev_close) * 100

                sign = "+" if change > 0 else ""
                return {
                    "price": f"{price:,.2f}",
                    "change": f"{sign}{change:,.2f}" if change != 0 else "0.00",
                    "pct": f"{sign}{pct:.2f}%" if pct != 0 else "0.00%",
                }
            elif len(df) == 1:
                price = df["Close"].iloc[0]
                return {
                    "price": f"{price:,.2f}",
                    "change": "0.00",
                    "pct": "0.00%",
                }
        except Exception:
            continue

    return {"price": "-", "change": "-", "pct": "-"}


def generate_market_table(market_dict):
    data_list = []
    for name, symbols in market_dict.items():
        res = fetch_ticker_data_with_fallback(symbols)
        data_list.append(
            {
                "指數": name,
                "收盤價": res["price"],
                "變動": res["change"],
                "(%)": res["pct"],
            }
        )
    return pd.DataFrame(data_list)


# ---------------------------------------------------------
# 4. 三欄式畫面排版呈現
# ---------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🇺🇸 美國 / 歐洲市場")
    df_us = generate_market_table(MARKET_INDEXES["美國 / 歐洲市場"])
    st.dataframe(df_us, hide_index=True, use_container_width=True)

with col2:
    st.subheader("🌏 亞洲市場")
    df_asia = generate_market_table(MARKET_INDEXES["亞洲市場"])
    st.dataframe(df_asia, hide_index=True, use_container_width=True)

with col3:
    st.subheader("🇹🇼 台灣市場")
    df_tw = generate_market_table(MARKET_INDEXES["台灣市場"])
    st.dataframe(df_tw, hide_index=True, use_container_width=True)

st.caption(
    f"基準日期 / 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
