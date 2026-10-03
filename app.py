import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="TIS晨報 - 重要市場收盤表現", layout="wide")

# ---------------------------------------------------------
# 1. 精確設定商品代碼 (Ticker Map)
# ---------------------------------------------------------
TICKERS = {
    # 美國 & 歐洲
    "道瓊工業指數": "^DJI",
    "那斯達克指數": "^IXIC",
    "標普500指數": "^GSPC",
    "費城半導體指數": "^SOX",
    "羅素2000指數": "^RUT",
    "英國FTSE 100": "^FTSE",
    "德國DAX指數": "^GDAXI",
    "法國CAC指數": "^FCHI",
    "道瓊歐洲600指數": "^STOXX",
    # 亞洲
    "日經225指數": "^N225",
    "南韓KOSPI指數": "^KS11",
    "恆生指數": "^HSI",
    "上證指數": "000001.SS",
    "新加坡STI指數": "^STI",
    "泰國曼谷SET指數": "^SET.BK",
    "富時馬來西亞指數": "^KLSE",
    "菲律賓綜合指數": "PSEI.XC",
    "印尼雅加達指數": "^JKSE",
    # 台灣 & 國際指數
    "加權指數": "^TWII",
    "不含電子指數": "^IR0001",
    "上櫃指數": "^TWOII",
    "0050": "0050.TW",
    "0051": "0051.TW",
    "MSCI全球指數": "URTH",
    "歐洲Stoxx 50": "^STOXX50E",
    "MSCI新興市場": "EEM",
    "MSCI拉丁美洲": "ILF",
    # 金屬能源
    "Crude Oil 原油": "CL=F",
    "Natural Gas 天然氣": "NG=F",
    "Gold 黃金": "GC=F",
    "Silver 白銀": "SI=F",
    "Copper 銅": "HG=F",
    # 農作物商品
    "CRB 商品指數": "^CRB",
    "Corn 玉米": "ZC=F",
    "Wheat 小麥": "ZW=F",
    "Soybean 黃豆": "ZS=F",
    "Cotton 棉花": "CT=F",
    # 其他商品 / 指標
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
                results[name] = (
                    f"{c:,.2f}",
                    f"{chg:+,.2f}",
                    f"{pct:+,.2f}%",
                    pct,
                )
            else:
                results[name] = ("-", "-", "-", 0)
        except Exception:
            results[name] = ("-", "-", "-", 0)
    return results


data = get_all_data()


# 輔助函式：產生單一儲存格 HTML
def cell(item_name):
    if item_name not in data or data[item_name][0] == "-":
        return f"<td>{item_name}</td><td>-</td><td>-</td><td>-</td>"

    val, chg, pct_str, raw_pct = data[item_name]
    # 上漲紅色，下跌綠色
    if raw_pct > 0:
        color = "#DC2626"
    elif raw_pct < 0:
        color = "#16A34A"
    else:
        color = "#000000"

    return (
        f"<td style='text-align:left;'>{item_name}</td>"
        f"<td style='text-align:right;'>{val}</td>"
        f"<td style='text-align:right; color:{color};'>{chg}</td>"
        f"<td style='text-align:right; color:{color};'>{pct_str}</td>"
    )


# ---------------------------------------------------------
# 2. 組合完整的 HTML 頁面結構 (不使用複雜的內部 f-string 嵌套)
# ---------------------------------------------------------
style_html = """
<style>
    .tis-table {
        width: 100%;
        border-collapse: collapse;
        font-family: "Microsoft JhengHei", "PingFang TC", sans-serif;
        font-size: 13px;
        background-color: white;
    }
    .tis-table th {
        background-color: #002060;
        color: white;
        padding: 6px;
        text-align: center;
        border: 1px solid #002060;
        font-weight: bold;
    }
    .tis-table td {
        padding: 5px 6px;
        border: 1px solid #d0d0d0;
    }
    .side-header {
        background-color: #002060;
        color: white;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        width: 35px;
        line-height: 1.2;
    }
</style>
<h2 style='text-align:left; color:#002060; font-weight:bold; margin-bottom:15px;'>TIS晨報-重要市場收盤表現</h2>
"""

table_body = f"""
<table class='tis-table'>
    <!-- 欄位標頭 -->
    <tr>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
    </tr>

    <!-- 第 1 列 -->
    <tr>
        <td class='side-header' rowspan='5'>美<br>國</td>
        {cell('道瓊工業指數')}
        <td class='side-header' rowspan='9'>亞<br>洲</td>
        {cell('日經225指數')}
        <td class='side-header' rowspan='5'>台<br>灣</td>
        {cell('加權指數')}
    </tr>

    <!-- 第 2 列 -->
    <tr>
        {cell('那斯達克指數')}
        {cell('南韓KOSPI指數')}
        {cell('不含電子指數')}
    </tr>

    <!-- 第 3 列 -->
    <tr>
        {cell('標普500指數')}
        {cell('恆生指數')}
        {cell('上櫃指數')}
    </tr>

    <!-- 第 4 列 -->
    <tr>
        {cell('費城半導體指數')}
        {cell('上證指數')}
        {cell('0050')}
    </tr>

    <!-- 第 5 列 -->
    <tr>
        {cell('羅素2000指數')}
        {cell('新加坡STI指數')}
        {cell('0051')}
    </tr>

    <!-- 第 6 列 -->
    <tr>
        <td class='side-header' rowspan='4'>歐<br>洲</td>
        {cell('英國FTSE 100')}
        {cell('泰國曼谷SET指數')}
        <td class='side-header' rowspan='4'>國<br>際<br>指<br>數</td>
        {cell('MSCI全球指數')}
    </tr>

    <!-- 第 7 列 -->
    <tr>
        {cell('德國DAX指數')}
        {cell('富時馬來西亞指數')}
        {cell('歐洲Stoxx 50')}
    </tr>

    <!-- 第 8 列 -->
    <tr>
        {cell('法國CAC指數')}
        {cell('菲律賓綜合指數')}
        {cell('MSCI新興市場')}
    </tr>

    <!-- 第 9 列 -->
    <tr>
        {cell('道瓊歐洲600指數')}
        {cell('印尼雅加達指數')}
        {cell('MSCI拉丁美洲')}
    </tr>

    <!-- 商品與指標標頭 -->
    <tr style='border-top: 3px solid #002060;'>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
    </tr>

    <!-- 第 10 列 -->
    <tr>
        <td class='side-header' rowspan='5'>金<br>屬<br>能<br>源</td>
        {cell('Crude Oil 原油')}
        <td class='side-header' rowspan='5'>農<br>作<br>商<br>品</td>
        {cell('CRB 商品指數')}
        <td class='side-header' rowspan='5'>其<br>他<br>商<br>品</td>
        {cell('DXY 美元指數')}
    </tr>

    <!-- 第 11 列 -->
    <tr>
        {cell('Natural Gas 天然氣')}
        {cell('Corn 玉米')}
        {cell('BDIY波羅的海指數')}
    </tr>

    <!-- 第 12 列 -->
    <tr>
        {cell('Gold 黃金')}
        {cell('Wheat 小麥')}
        {cell('VIX 指數')}
    </tr>

    <!-- 第 13 列 -->
    <tr>
        {cell('Silver 白銀')}
        {cell('Soybean 黃豆')}
        {cell('VXN 指數')}
    </tr>

    <!-- 第 14 列 -->
    <tr>
        {cell('Copper 銅')}
        {cell('Cotton 棉花')}
        {cell('美國10年公債殖利率')}
    </tr>
</table>
"""

# 渲染完整網頁
st.markdown(style_html + table_body, unsafe_allow_html=True)
