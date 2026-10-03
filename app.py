import datetime
import math
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

st.set_page_config(page_title="TIS晨報 - 重要市場收盤表現", layout="wide")

# ---------------------------------------------------------
# 1. 介面控制區：日期選擇
# ---------------------------------------------------------
st.title("TIS晨報 - 重要市場收盤表現")

today = datetime.date.today()
selected_date = st.date_input(
    "請選擇查詢日期（預設為最新）：",
    value=today,
    max_value=today,
)

# ---------------------------------------------------------
# 2. 定義指數代碼與備援列表 (Ticker Map with Fallbacks)
# ---------------------------------------------------------
TICKERS_CONFIG = {
    # 美國 & 歐洲
    "道瓊工業指數": ["^DJI"],
    "那斯達克指數": ["^IXIC"],
    "標普500指數": ["^GSPC"],
    "費城半導體指數": ["^SOX"],
    "羅素2000指數": ["^RUT"],
    "英國FTSE 100": ["^FTSE"],
    "德國DAX指數": ["^GDAXI"],
    "法國CAC指數": ["^FCHI"],
    "道瓊歐洲600指數": ["^STOXX"],
    # 亞洲
    "日經225指數": ["^N225"],
    "南韓KOSPI指數": ["^KS11"],
    "恆生指數": ["^HSI"],
    "上證指數": ["000001.SS"],
    "新加坡STI指數": ["^STI"],
    "泰國曼谷SET指數": ["^SET.BK", "^SET", "SET.BK"],
    "富時馬來西亞指數": ["^KLSE"],
    "菲律賓綜合指數": ["^PSI", "^PSEI", "PSEI.XC"],
    "印尼雅加達指數": ["^JKSE"],
    # 台灣 & 國際指數
    "加權指數": ["^TWII"],
    "不含電子指數": ["^TW28", "0052.TW"],
    "上櫃指數": ["^TWO", "^TWOII"],
    "0050": ["0050.TW"],
    "0051": ["0051.TW"],
    "MSCI全球指數": ["URTH"],
    "歐洲Stoxx 50": ["^STOXX50E"],
    "MSCI新興市場": ["EEM"],
    "MSCI拉丁美洲": ["ILF"],
    # 金屬能源
    "Crude Oil 原油": ["CL=F"],
    "Natural Gas 天然氣": ["NG=F"],
    "Gold 黃金": ["GC=F"],
    "Silver 白銀": ["SI=F"],
    "Copper 銅": ["HG=F"],
    # 農作物商品
    "CRB 商品指數": ["DBC", "^CRB"],
    "Corn 玉米": ["ZC=F"],
    "Wheat 小麥": ["ZW=F"],
    "Soybean 黃豆": ["ZS=F"],
    "Cotton 棉花": ["CT=F"],
    # 其他商品 / 指標
    "DXY 美元指數": ["DX-Y.NYB"],
    "BDIY波羅的海指數": ["BDRY", "BDI"],
    "VIX 指數": ["^VIX"],
    "VXN 指數": ["^VXN"],
    "美國10年公債殖利率": ["^TNX"],
}


def fetch_single_ticker_data(ticker_list, start_dt, end_dt):
    """嘗試從備援代碼列表中抓取第一筆有效的歷史收盤數據"""
    for symbol in ticker_list:
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_dt, end=end_dt)
            df = df[df["Close"].notna()]
            if len(df) >= 2:
                c = df["Close"].iloc[-1]
                p = df["Close"].iloc[-2]
                if not math.isnan(c) and not math.isnan(p):
                    chg = c - p
                    pct = (chg / p) * 100
                    return (f"{c:,.2f}", f"{chg:+,.2f}", f"{pct:+,.2f}%", pct)
            elif len(df) == 1:
                c = df["Close"].iloc[0]
                if not math.isnan(c):
                    return (f"{c:,.2f}", "-", "-", 0)
        except Exception:
            continue
    return ("-", "-", "-", 0)


@st.cache_data(ttl=1800)
def get_market_data(target_date):
    results = {}
    start_dt = target_date - datetime.timedelta(days=20)
    end_dt = target_date + datetime.timedelta(days=1)

    for name, ticker_list in TICKERS_CONFIG.items():
        results[name] = fetch_single_ticker_data(ticker_list, start_dt, end_dt)

    return results


data = get_market_data(selected_date)


# 產生單一項目 4 個 <td> 的 HTML 儲存格
def cell(item_name):
    if item_name not in data or data[item_name][0] == "-":
        return f"<td class='item-name'>{item_name}</td><td>-</td><td>-</td><td>-</td>"

    val, chg, pct_str, raw_pct = data[item_name]
    if raw_pct > 0:
        color = "#DC2626"  # 上漲紅
    elif raw_pct < 0:
        color = "#16A34A"  # 下跌綠
    else:
        color = "#000000"

    return (
        f"<td class='item-name'>{item_name}</td>"
        f"<td class='num-val'>{val}</td>"
        f"<td class='num-val' style='color:{color};'>{chg}</td>"
        f"<td class='num-val' style='color:{color};'>{pct_str}</td>"
    )


# ---------------------------------------------------------
# 3. 構建精確對齊的 HTML 表格
# ---------------------------------------------------------
date_str = selected_date.strftime("%Y/%m/%d")

full_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        font-family: "Microsoft JhengHei", "PingFang TC", Arial, sans-serif;
        margin: 0;
        padding: 5px;
        background-color: #ffffff;
    }}
    .sub-title {{
        color: #333;
        font-size: 14px;
        margin-bottom: 10px;
        font-weight: bold;
    }}
    .tis-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        table-layout: fixed;
    }}
    .tis-table th {{
        background-color: #002060;
        color: #ffffff;
        padding: 6px 2px;
        text-align: center;
        border: 1px solid #002060;
        font-weight: bold;
    }}
    .tis-table td {{
        padding: 4px 3px;
        border: 1px solid #d0d0d0;
        white-space: nowrap;
        overflow: hidden;
    }}
    .side-header {{
        background-color: #002060;
        color: #ffffff;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        width: 32px;
        line-height: 1.2;
    }}
    .item-name {{
        text-align: left;
        width: 110px;
    }}
    .num-val {{
        text-align: right;
    }}
</style>
</head>
<body>

<div class='sub-title'>基準日期：{date_str}</div>

<table class='tis-table'>
    <!-- 表頭 (15 欄) -->
    <tr>
        <th colspan='2'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='2'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='2'>指數</th><th>收盤價</th><th>變動</th><th>(%)</th>
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

    <!-- 下半部商品標頭 -->
    <tr style='border-top: 3px solid #002060;'>
        <th colspan='2'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='2'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
        <th colspan='2'>Commodity</th><th>收盤價</th><th>變動</th><th>(%)</th>
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

</body>
</html>
"""

# ---------------------------------------------------------
# 4. 渲染至 Streamlit
# ---------------------------------------------------------
components.html(full_html, height=730, scrolling=True)
