import datetime
import json
import math
import urllib.request
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
# 2. 定義指數代碼配置 (優化滬深300與泰國指數的 Ticker 順序)
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
    "滬深300指數": ["000300.SS", "399300.SZ", "ASHR"],  # 增加多重備援
    "新加坡STI指數": ["^STI"],
    "泰國曼谷SET指數": ["^SET.BK", "^SET", "SET.BK"],  # 多重格式切換
    "富時馬來西亞指數": ["^KLSE"],
    "印尼雅加達指數": ["^JKSE"],
    # 台灣 & 國際指數
    "加權指數": ["^TWII"],
    "不含電子指數": ["^TW28", "0052.TW"],
    "上櫃指數": ["TPEX_DIRECT", "^TWOII", "^TWO", "^OTC", "006201.TWO"],
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


def fetch_otc_from_tpex(target_date):
    """專屬 API：直接抓取台灣櫃買中心 (TPEx) 官方數據"""
    try:
        url = "https://www.tpex.org.tw/web/stock/aftertrading/index_summary/summary_response.php"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "aaData" in res_data and len(res_data["aaData"]) > 0:
                latest = res_data["aaData"][0]
                close_val = float(str(latest[1]).replace(",", ""))
                chg_val = float(str(latest[2]).replace(",", ""))
                prev_val = close_val - chg_val
                pct = (chg_val / prev_val) * 100 if prev_val != 0 else 0

                if target_date.weekday() >= 5:
                    return (f"{close_val:,.2f}", "休市", "休市", 0, True)

                return (
                    f"{close_val:,.2f}",
                    f"{chg_val:+,.2f}",
                    f"{pct:+,.2f}%",
                    pct,
                    False,
                )
    except Exception:
        pass
    return None


def fetch_single_ticker_data(item_name, ticker_list, target_date):
    """
    強健資料抓取邏輯：
    1. 逐一嘗試 ticker_list，直到抓取到有漲跌幅的歷史 Candle 資料[cite: 11]。
    2. 精確區分交易日與休市[cite: 11]。
    """
    if item_name == "上櫃指數" and target_date == datetime.date.today():
        tpex_res = fetch_otc_from_tpex(target_date)
        if tpex_res:
            return tpex_res

    start_dt = target_date - datetime.timedelta(days=35)
    end_dt = target_date + datetime.timedelta(days=2)

    for symbol in ticker_list:
        if symbol == "TPEX_DIRECT":
            tpex_res = fetch_otc_from_tpex(target_date)
            if tpex_res:
                return tpex_res
            continue

        try:
            stock = yf.Ticker(symbol)
            # 優先使用 period 抓取歷史 Candle，避免 start/end 在某些時區失效
            df = stock.history(period="1mo")
            if df.empty:
                df = stock.history(start=start_dt, end=end_dt)

            df = df[df["Close"].notna()]
            if len(df) == 0:
                continue

            # 正規化時區與日期格式
            try:
                df.index = df.index.tz_convert("Asia/Taipei").date
            except Exception:
                df.index = pd.to_datetime(df.index).date

            # 抓取 target_date 當天或前一個交易日
            df_filtered = df[df.index <= target_date]
            if len(df_filtered) == 0:
                df_filtered = df

            latest_traded_date = df_filtered.index[-1]
            latest_price = df_filtered["Close"].iloc[-1]

            # 判斷是否休市
            is_closed = False
            if target_date.weekday() >= 5:
                is_closed = True
            elif target_date not in df_filtered.index:
                # 若為國定連假（如十一長假）
                days_diff = (target_date - latest_traded_date).days
                if days_diff >= 1 and item_name in ["上證指數", "滬深300指數"]:
                    is_closed = True

            if is_closed:
                return (
                    f"{latest_price:,.2f}",
                    "休市",
                    "休市",
                    0,
                    True,
                )

            # 計算漲跌數值與變動
            if len(df_filtered) >= 2:
                c = df_filtered["Close"].iloc[-1]
                p = df_filtered["Close"].iloc[-2]
                if not math.isnan(c) and not math.isnan(p) and p != 0:
                    chg = c - p
                    pct = (chg / p) * 100
                    # 如果計算出來的變動不為 0，代表成功找到真正有更新的代碼
                    return (
                        f"{c:,.2f}",
                        f"{chg:+,.2f}",
                        f"{pct:+,.2f}%",
                        pct,
                        False,
                    )
            elif len(df_filtered) == 1:
                return (f"{latest_price:,.2f}", "0.00", "0.00%", 0, False)

        except Exception:
            continue

    # 上櫃指數專屬備援
    if item_name == "上櫃指數":
        tpex_res = fetch_otc_from_tpex(target_date)
        if tpex_res:
            return tpex_res

    return ("-", "-", "-", 0, False)


@st.cache_data(ttl=1800)
def get_market_data(target_date):
    results = {}
    for name, ticker_list in TICKERS_CONFIG.items():
        results[name] = fetch_single_ticker_data(name, ticker_list, target_date)
    return results


data = get_market_data(selected_date)


# 產生單一項目 4 個 <td> 的 HTML 儲存格
def cell(item_name):
    if item_name not in data or data[item_name][0] == "-":
        return f"<td class='item-name'>{item_name}</td><td class='num-val'>-</td><td class='num-val'>-</td><td class='num-val'>-</td>"

    val, chg, pct_str, raw_pct, is_closed = data[item_name]

    if is_closed:
        return (
            f"<td class='item-name'>{item_name}</td>"
            f"<td class='num-val'>{val}</td>"
            f"<td class='num-val' style='color:#6B7280; font-size: 11px;'>休市</td>"
            f"<td class='num-val' style='color:#6B7280; font-size: 11px;'>休市</td>"
        )

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
# 3. 構建深藍色 HTML 表格 (含下半部 Commodity 區域)
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
        border: 1px solid #002060;
        font-weight: bold;
    }}
    .th-center {{ text-align: center; }}
    .th-right {{ text-align: right; padding-right: 5px; }}
    
    .tis-table td {{
        padding: 4px 3px;
        border: 1px solid #d0d0d0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .side-header {{
        background-color: #002060;
        color: #ffffff;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        line-height: 1.2;
    }}
    .item-name {{
        text-align: left;
        padding-left: 4px;
    }}
    .num-val {{
        text-align: right;
        padding-right: 5px;
    }}
</style>
</head>
<body>

<div class='sub-title'>基準日期：{date_str}</div>

<table class='tis-table'>
    <colgroup>
        <col style="width: 2.5%;">
        <col style="width: 11.5%;">
        <col style="width: 7.0%;">
        <col style="width: 6.2%;">
        <col style="width: 6.2%;">
        
        <col style="width: 2.5%;">
        <col style="width: 11.5%;">
        <col style="width: 7.0%;">
        <col style="width: 6.2%;">
        <col style="width: 6.2%;">
        
        <col style="width: 2.5%;">
        <col style="width: 11.5%;">
        <col style="width: 7.0%;">
        <col style="width: 6.2%;">
        <col style="width: 6.2%;">
    </colgroup>

    <!-- 上半部表頭 -->
    <tr>
        <th colspan='2' class='th-center'>指數</th><th class='th-right'>收盤價</th><th class='th-right'>變動</th><th class='th-right'>(%)</th>
        <th colspan='2' class='th-center'>指數</th><th class='th-right'>收盤價</th><th class='th-right'>變動</th><th class='th-right'>(%)</th>
        <th colspan='2' class='th-center'>指數</th><th class='th-right'>收盤價</th><th class='th-right'>變動</th><th class='th-right'>(%)</th>
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

    <!-- 第 5 列 (滬深300指數) -->
    <tr>
        {cell('羅素2000指數')}
        {cell('滬深300指數')}
        {cell('0051')}
    </tr>

    <!-- 第 6 列 -->
    <tr>
        <td class='side-header' rowspan='4'>歐<br>洲</td>
        {cell('英國FTSE 100')}
        {cell('新加坡STI指數')}
        <td class='side-header' rowspan='4'>國<br>際<br>指<br>數</td>
        {cell('MSCI全球指數')}
    </tr>

    <!-- 第 7 列 -->
    <tr>
        {cell('德國DAX指數')}
        {cell('泰國曼谷SET指數')}
        {cell('歐洲Stoxx 50')}
    </tr>

    <!-- 第 8 列 -->
    <tr>
        {cell('法國CAC指數')}
        {cell('富時馬來西亞指數')}
        {cell('MSCI新興市場')}
    </tr>

    <!-- 第 9 列 -->
    <tr>
        {cell('道瓊歐洲600指數')}
        {cell('印尼雅加達指數')}
        {cell('MSCI拉丁美洲')}
    </tr>

    <!-- 下半部商品標頭 (Commodity) -->
    <tr style='border-top: 3px solid #002060;'>
        <th colspan='2' class='th-center'>Commodity</th><th class='th-right'>收盤價</th><th class='th-right'>變動</th><th class='th-right'>(%)</th>
        <th colspan='2' class='th-center'>Commodity</th><th class='th-right'>收盤價</th><th class='th-right'>變動</th><th class='th-right'>(%)</th>
        <th colspan='2' class='th-center'>Commodity</th><th class='th-right'>收盤價</th><th class='th-right'>變動</th><th class='th-right'>(%)</th>
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
