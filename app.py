import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="TIS晨報 - 重要市場收盤表現", layout="wide"
)

# ---------------------------------------------------------
# 1. 完整對應圖一的所有商品代碼 (Ticker List)
# ---------------------------------------------------------
TICKERS = {
    # 區塊 1: 美國 & 歐洲
    "道瓊工業指數": "^DJI",
    "那斯達克指數": "^IXIC",
    "標普500指數": "^GSPC",
    "費城半導體指數": "^SOX",
    "羅素2000指數": "^RUT",
    "英國FTSE 100": "^FTSE",
    "德國DAX指數": "^GDAXI",
    "法國CAC指數": "^FCHI",
    "道瓊歐洲600指數": "^STOXX",
    # 區塊 2: 亞洲
    "日經225指數": "^N225",
    "南韓KOSPI指數": "^KS11",
    "恆生指數": "^HSI",
    "上證指數": "000001.SS",
    "新加坡STI指數": "^STI",
    "泰國曼谷SET指數": "^SET.BK",
    "富時馬來西亞指數": "^KLSE",
    "菲律賓綜合指數": "PSEI.XC",
    "印尼雅加達指數": "^JKSE",
    # 區塊 3: 台灣 & 國際指數
    "加權指數": "^TWII",
    "不含電子指數": "^IR0001",
    "上櫃指數": "^TWOII",
    "0050": "0050.TW",
    "0051": "0051.TW",
    "MSCI全球指數": "URTH",
    "歐洲Stoxx 50": "^STOXX50E",
    "MSCI新興市場": "EEM",
    "MSCI拉丁美洲": "ILF",
    # 區塊 4: 金屬能源
    "Crude Oil 原油": "CL=F",
    "Natural Gas 天然氣": "NG=F",
    "Gold 黃金": "GC=F",
    "Silver 白銀": "SI=F",
    "Copper 銅": "HG=F",
    # 區塊 5: 農作物商品
    "CRB 商品指數": "^CRB",
    "Corn 玉米": "ZC=F",
    "Wheat 小麥": "ZW=F",
    "Soybean 黃豆": "ZS=F",
    "Cotton 棉花": "CT=F",
    # 區塊 6: 其他商品 / 指標
    "DXY 美元指數": "DX-Y.NYB",
    "BDIY波羅的海指數": "^BDI",
    "VIX 指數": "^VIX",
    "VXN 指數": "^VXN",
    "美國10年公債殖利率": "^TNX",
}


@st.cache_data(ttl=3600)
def get_all_data():
    results = {}
    for name, ticker in TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                c = hist["Close"].iloc[-1]
                p = hist["Close"].iloc[-2]
                chg = c - p
                pct = (chg / p) * 100
                results[name] = (f"{c:,.2f}", f"{chg:+,.2f}", f"{pct:+,.2f}%", pct)
            else:
                results[name] = ("-", "-", "-", 0)
        except:
            results[name] = ("-", "-", "-", 0)
    return results


data = get_all_data()


# 輔助函式：產生表格格子的 HTML (帶漲跌顏色)
def fmt(item_name):
    if item_name not in data or data[item_name][0] == "-":
        return f"<td>{item_name}</td><td>-</td><td>-</td><td>-</td>"

    val, chg, pct_str, raw_pct = data[item_name]
    color = "#DC2626" if raw_pct > 0 else ("#16A34A" if raw_pct < 0 else "#000")
    return f"""
        <td style='text-align:left;'>{item_name}</td>
        <td style='text-align:right;'>{val}</td>
        <td style='text-align:right; color:{color};'>{chg}</td>
        <td style='text-align:right; color:{color};'>{pct_str}</td>
    """


# ---------------------------------------------------------
# 2. 完全還原圖一的 HTML/CSS 表格結構
# ---------------------------------------------------------
html_code = f"""
<style>
    .tis-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: "Microsoft JhengHei", sans-serif;
        font-size: 13px;
    }}
    .tis-table th {{
        background-color: #002060;
        color: white;
        padding: 6px;
        text-align: center;
        border: 1px solid #ccc;
    }}
    .tis-table td {{
        padding: 4px 6px;
        border: 1px solid #e0e0e0;
    }}
    .side-header {{
        background-color: #002060;
        color: white;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        width: 40px;
    }}
</style>

<h2 style='text-align:left; color:#000; font-weight:bold;'>TIS晨報-重要市場收盤表現</h2>

<table class='tis-table'>
    <!-- 第一排：股票市場 -->
    <tr>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
    </tr>
    <tr>
        <td class='side-header' rowspan='5'>美<br>國</td>
        {fmt('道瓊工業指數')}
        <td class='side-header' rowspan='9'>亞<br>洲</td>
        {fmt('日經225指數')}
        <td class='side-header' rowspan='5'>台<br>灣</td>
        {fmt('加權指數')}
    </tr>
    <tr>
        {fmt('那斯達克指數')}
        {fmt('南韓KOSPI指數')}
        {fmt('不含電子指數')}
    </tr>
    <tr>
        {fmt('標普500指數')}
        {fmt('恆生指數')}
        {fmt('上櫃指數')}
    </tr>
    <tr>
        {fmt('費城半導體指數')}
        {fmt('上證指數')}
        {fmt('0050')}
    </tr>
    <tr>
        {fmt('羅素2000指數')}
        {fmt('新加坡STI指數')}
        {fmt('0051')}
    </tr>
    <tr>
        <td class='side-header' rowspan='4'>歐<br>洲</td>
        {fmt('英國FTSE 100')}
        {fmt('泰國曼谷SET指數')}
        <td class='side-header' rowspan='4'>國<br>際<br>指<br>數</td>
        {fmt('MSCI全球指數')}
    </tr>
    <tr>
        {fmt('德國DAX指數')}
        {fmt('富時馬來西亞指數')}
        {fmt('歐洲Stoxx 50')}
    </tr>
    <tr>
        {fmt('法國CAC指數')}
        {fmt('菲律賓綜合指數')}
        {fmt('MSCI新興市場')}
    </tr>
    <tr>
        {fmt('道瓊歐洲600指數')}
        {fmt('印尼雅加達指數')}
        {fmt('MSCI拉丁美洲')}
    </tr>

    <!-- 第二排：商品與指標 -->
    <tr style='border-top: 3px solid #002060;'>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
    </tr>
    <tr>
        <td class='side-header' rowspan='5'>金<br>屬<br>能<br>源</td>
        {fmt('Crude Oil 原油')}
        <td class='side-header' rowspan='5'>農<br>作<br>商<br>品</td>
        {fmt('CRB 商品指數')}
        <td class='side-header' rowspan='5'>其<br>他<br>商<br>品</td>
        {fmt('DXY 美元指數')}
    </tr>
    <tr>
        {fmt('Natural Gas 天然氣')}
        {fmt('Corn 玉米')}
        {fmt('BDIY波羅的海指數')}
    </tr>
    <tr>
        {fmt('Gold 黃金')}
        {fmt('Wheat 小麥')}
        {fmt('VIX 指數')}
    </tr>
    <tr>
        {fmt('Silver 白銀')}
        {fmt('Soybean 黃豆')}
        {fmt('VXN 指數')}
    </tr>
    <tr>
        {fmt('Copper 銅')}
        {fmt('Cotton 棉花')}
        {fmt('美國10年公債殖利率')}
    </tr>
</table>
"""

st.markdown(html_code, unsafe_allow_html=True)
