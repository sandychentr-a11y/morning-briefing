import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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


# 產生單一儲存格 HTML 函式
def cell(item_name):
    if item_name not in data or data[item_name][0] == "-":
        return f"<td>{item_name}</td><td>-</td><td>-</td><td>-</td>"

    val, chg, pct_str, raw_pct = data[item_name]
    if raw_pct > 0:
        color = "#DC2626"  # 紅漲
    elif raw_pct < 0:
        color = "#16A34A"  # 綠跌
    else:
        color = "#000000"

    return (
        f"<td style='text-align:left;'>{item_name}</td>"
        f"<td style='text-align:right;'>{val}</td>"
        f"<td style='text-align:right; color:{color};'>{chg}</td>"
        f"<td style='text-align:right; color:{color};'>{pct_str}</td>"
    )


# ---------------------------------------------------------
# 2. 構建 HTML 表格
# ---------------------------------------------------------
full_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        font-family: "Microsoft JhengHei", "PingFang TC", sans-serif;
        margin: 0;
        padding: 10px;
        background-color: #ffffff;
    }}
    h2 {{
        color: #000000;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 12px;
    }}
    .tis-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }}
    .tis-table th {{
        background-color: #002060;
        color: #ffffff;
        padding: 6px;
        text-align: center;
        border: 1px solid #002060;
        font-weight: bold;
    }}
    .tis-table td {{
        padding: 5px 6px;
        border: 1px solid #d0d0d0;
    }}
    .side-header {{
        background-color: #002060;
        color: #ffffff;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        width: 35px;
        line-height: 1.3;
    }}
</style>
</head>
<body>

<h2>TIS晨報-重要市場收盤表現</h2>

<table class='tis-table'>
    <tr>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
    </tr>

    <tr>
        <td class='side-header' rowspan='5'>美<br>國</td>
        {cell('道瓊工業指數')}
        <td class='side-header' rowspan='9'>亞<br>洲</td>
        {cell('日經225指數')}
        <td class='side-header' rowspan='5'>台<br>灣</td>
        {cell('加權指數')}
    </tr>

    <tr>
        {cell('那斯達克指數')}
        {cell('南韓KOSPI指數')}
        {cell('不含電子指數')}
    </tr>

    <tr>
        {cell('標普500指數')}
        {cell('恆生指數')}
        {cell('上櫃指數')}
    </tr>

    <tr>
        {cell('費城半導體指數')}
        {cell('上證指數')}
        {cell('0050')}
    </tr>

    <tr>
        {cell('羅素2000指數')}
        {cell('新加坡STI指數')}
        {cell('0051')}
    </tr>

    <tr>
        <td class='side-header' rowspan='4'>歐<br>洲</td>
        {cell('英國FTSE 100')}
        {cell('泰國曼谷SET指數')}
        <td class='side-header' rowspan='4'>國<br>際<br>指<br>數</td>
        {cell('MSCI全球指數')}
    </tr>

    <tr>
        {cell('德國DAX指數')}
        {cell('富時馬來西亞指數')}
        {cell('歐洲Stoxx 50')}
    </tr>

    <tr>
        {cell('法國CAC指數')}
        {cell('菲律賓綜合指數')}
        {cell('MSCI新興市場')}
    </tr>

    <tr>
        {cell('道瓊歐洲600指數')}
        {cell('印尼雅加達指數')}
        {cell('MSCI拉丁美洲')}
    </tr>

    <tr style='border-top: 3px solid #002060;'>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='4'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
    </tr>

    <tr>
        <td class='side-header' rowspan='5'>金<br>屬<br>能<br>源</td>
        {cell('Crude Oil 原油')}
        <td class='side-header' rowspan='5'>農<br>作<br>商<br>品</td>
        {cell('CRB 商品指數')}
        <td class='side-header' rowspan='5'>其<br>他<br>商<br>品</td>
        {cell('DXY 美元指數')}
    </tr>

    <tr>
        {cell('Natural Gas 天然氣')}
        {cell('Corn 玉米')}
        {cell('BDIY波羅的海指數')}
    </tr>

    <tr>
        {cell('Gold 黃金')}
        {cell('Wheat 小麥')}
        {cell('VIX 指數')}
    </tr>

    <tr>
        {cell('Silver 白銀')}
        {cell('Soybean 黃豆')}
        {cell('VXN 指數')}
    </tr>

    <tr>
        {cell('Copper 銅')}
        {cell('Cotton 棉花')}
        {cell('美國10年公債殖利率')}
    </tr>
</table>

</body>
</html>
"""

# ---------------------------------------------------------
# 3. 使用 Streamlit 原生 HTML 元件安全渲染
# ---------------------------------------------------------
components.html(full_html, height=750, scrolling=True)
