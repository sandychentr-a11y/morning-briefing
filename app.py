import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------
# 1. 頁面佈局與樣式設定
# ---------------------------------------------------------
st.set_page_config(
    page_title="TIS 晨報 - 重要市場收盤表現",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自訂 CSS 讓風格更接近金融專業晨報
st.markdown(
    """
    <style>
    .main-title {
        font-size: 28px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 14px;
        color: #64748B;
        text-align: center;
        margin-bottom: 25px;
    }
    .category-header {
        background-color: #1E3A8A;
        color: white;
        padding: 8px 12px;
        font-weight: bold;
        border-radius: 4px;
        margin-bottom: 10px;
        text-align: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. 市場類別與商品代碼表 (Ticker Map)
# ---------------------------------------------------------
CATEGORIES = {
    "🇺🇸 美國市場": {
        "道瓊工業指數": "^DJI",
        "那斯達克指數": "^IXIC",
        "標普500指數": "^GSPC",
        "費城半導體指數": "^SOX",
        "羅素2000指數": "^RUT",
    },
    "🇹🇼 台灣市場": {
        "加權指數": "^TWII",
        "不含電子指數": "^IR0001",
        "櫃買指數": "^TWOII",
        "元大台灣50": "0050.TW",
    },
    "🌏 亞洲市場": {
        "日經225指數": "^N225",
        "南韓KOSPI指數": "^KS11",
        "恆生指數": "^HSI",
        "上證指數": "000001.SS",
        "新加坡STI指數": "^STI",
    },
    "🌍 歐美/國際指數": {
        "英國FTSE 100": "^FTSE",
        "德國DAX指數": "^GDAXI",
        "法國CAC指數": "^FCHI",
        "MSCI全球指數": "URTH",
    },
    "🛢️ 金屬/能源商品": {
        "Crude Oil 原油": "CL=F",
        "Natural Gas 天然氣": "NG=F",
        "Gold 黃金": "GC=F",
        "Silver 白銀": "SI=F",
        "Copper 銅": "HG=F",
    },
    "📊 其他金融指標": {
        "DXY 美元指數": "DX-Y.NYB",
        "VIX 恐慌指數": "^VIX",
        "美國10年期公債殖利率": "^TNX",
    },
}

# ---------------------------------------------------------
# 3. 自動抓取市場數據 (快取 1 小時以提升網頁載入速度)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_group_data(ticker_dict):
    data_list = []
    for name, ticker in ticker_dict.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                close = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                change = close - prev
                pct_change = (change / prev) * 100

                data_list.append(
                    {
                        "指數/商品": name,
                        "收盤價": f"{close:,.2f}",
                        "變動": f"{change:+.2f}",
                        "漲跌幅 (%)": f"{pct_change:+.2f}%",
                        "_raw_pct": pct_change,  # 用於樣式判斷
                    }
                )
        except Exception:
            data_list.append(
                {
                    "指數/商品": name,
                    "收盤價": "N/A",
                    "變動": "N/A",
                    "漲跌幅 (%)": "N/A",
                    "_raw_pct": 0,
                }
            )

    return pd.DataFrame(data_list)


# 高亮顏色處理：漲紅跌綠
def color_text(val):
    if isinstance(val, str) and ("+" in val or "-" in val):
        if val.startswith("+"):
            return "color: #DC2626; font-weight: bold;"  # 紅色 (漲)
        elif val.startswith("-"):
            return "color: #16A34A; font-weight: bold;"  # 綠色 (跌)
    return ""


# ---------------------------------------------------------
# 4. 網頁頁面佈局渲染
# ---------------------------------------------------------
st.markdown(
    '<div class="main-title">TIS 晨報 - 重要市場收盤表現</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="sub-title">更新時間：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
    unsafe_allow_html=True,
)

# 側邊欄控制
with st.sidebar:
    st.header("⚙️ 晨報設定")
    if st.button("🔄 立即更新數據"):
        st.cache_data.clear()
        st.rerun()
    st.caption("數據來源：Yahoo Finance")

# 採用 3 欄式美觀網頁排版 (卡片樣式)
col1, col2, col3 = st.columns(3)

groups = list(CATEGORIES.items())

# 第一欄：美國市場 & 台灣市場
with col1:
    for cat_name, tickers in [groups[0], groups[1]]:
        st.markdown(
            f'<div class="category-header">{cat_name}</div>',
            unsafe_allow_html=True,
        )
        df = fetch_group_data(tickers)
        display_df = df.drop(columns=["_raw_pct"])
        styled_df = display_df.style.map(color_text, subset=["變動", "漲跌幅 (%)"])
        st.dataframe(
            styled_df, use_container_width=True, hide_index=True, height=210
        )

# 第二欄：亞洲市場 & 國際/歐洲市場
with col2:
    for cat_name, tickers in [groups[2], groups[3]]:
        st.markdown(
            f'<div class="category-header">{cat_name}</div>',
            unsafe_allow_html=True,
        )
        df = fetch_group_data(tickers)
        display_df = df.drop(columns=["_raw_pct"])
        styled_df = display_df.style.map(color_text, subset=["變動", "漲跌幅 (%)"])
        st.dataframe(
            styled_df, use_container_width=True, hide_index=True, height=210
        )

# 第三欄：金屬/能源商品 & 其他金融指標
with col3:
    for cat_name, tickers in [groups[4], groups[5]]:
        st.markdown(
            f'<div class="category-header">{cat_name}</div>',
            unsafe_allow_html=True,
        )
        df = fetch_group_data(tickers)
        display_df = df.drop(columns=["_raw_pct"])
        styled_df = display_df.style.map(color_text, subset=["變動", "漲跌幅 (%)"])
        st.dataframe(
            styled_df, use_container_width=True, hide_index=True, height=210
        )

st.markdown("---")
st.caption("僅供內部教育訓練使用，請勿外傳。")
