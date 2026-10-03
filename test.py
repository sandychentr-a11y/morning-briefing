import datetime
import json
import urllib.request
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="滬深300 & 泰國指數 專用看板", layout="wide")

st.title("📊 滬深300 & 泰國SET指數 獨立報價看板")

# 1. 日期選擇器
today = datetime.date.today()
selected_date = st.date_input("選擇查詢日期：", value=today, max_value=today)


# 2. 直連 API 抓取函數
def fetch_yahoo_direct_index(symbol, target_date):
    """直接呼叫 Yahoo Finance v8 API 取得歷史 K 線與漲跌幅"""
    try:
        # 設定搜尋時間區間 (前後 30 天)
        end_ts = int(
            datetime.datetime.combine(
                target_date + datetime.timedelta(days=2), datetime.time.max
            ).timestamp()
        )
        start_ts = int(
            datetime.datetime.combine(
                target_date - datetime.timedelta(days=30), datetime.time.min
            ).timestamp()
        )

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start_ts}&period2={end_ts}&interval=1d"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            closes = result["indicators"]["quote"][0]["close"]

            # 清理與建立 DataFrame
            dates = [
                datetime.datetime.fromtimestamp(ts).date() for ts in timestamps
            ]
            df = pd.DataFrame({"Date": dates, "Close": closes}).dropna()
            df = df[df["Close"] > 0]

            # 根據選擇的日期截斷
            df_filtered = df[df["Date"] <= target_date]
            if len(df_filtered) == 0:
                df_filtered = df

            latest_traded_date = df_filtered["Date"].iloc[-1]
            latest_price = df_filtered["Close"].iloc[-1]

            # 判斷當天是否休市 (週末或連假)
            is_closed = False
            if target_date.weekday() >= 5:
                is_closed = True
            elif target_date not in df_filtered["Date"].values:
                days_diff = (target_date - latest_traded_date).days
                if days_diff >= 1:
                    is_closed = True

            if is_closed:
                return (f"{latest_price:,.2f}", "休市", "休市", 0, True)

            # 正常交易日計算漲跌額與幅度
            if len(df_filtered) >= 2:
                c = df_filtered["Close"].iloc[-1]
                p = df_filtered["Close"].iloc[-2]
                chg = c - p
                pct = (chg / p) * 100 if p != 0 else 0
                return (f"{c:,.2f}", f"{chg:+,.2f}", f"{pct:+,.2f}%", pct, False)
            elif len(df_filtered) == 1:
                return (f"{latest_price:,.2f}", "0.00", "0.00%", 0, False)

    except Exception as e:
        pass

    return ("-", "-", "-", 0, False)


# 3. 取得兩大指數資料
csi300_data = fetch_yahoo_direct_index("000300.SS", selected_date)
thai_data = fetch_yahoo_direct_index("^SET.BK", selected_date)


# 4. 格式化為 HTML 儲存格
def format_cell_html(data):
    val, chg, pct_str, raw_pct, is_closed = data
    if val == "-":
        return "<td>-</td><td>-</td><td>-</td>"

    if is_closed:
        return f"<td><b>{val}</b></td><td style='color:#6B7280;'>休市</td><td style='color:#6B7280;'>休市</td>"

    if raw_pct > 0:
        color = "#DC2626"  # 紅色
    elif raw_pct < 0:
        color = "#16A34A"  # 綠色
    else:
        color = "#000000"

    return f"<td><b>{val}</b></td><td style='color:{color}; font-weight:bold;'>{chg}</td><td style='color:{color}; font-weight:bold;'>{pct_str}</td>"


date_str = selected_date.strftime("%Y/%m/%d")

# 5. 獨立顯示表格 HTML
single_table_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        font-family: "Microsoft JhengHei", Arial, sans-serif;
        background-color: #ffffff;
        padding: 10px;
    }}
    .index-table {{
        width: 100%;
        max-width: 800px;
        border-collapse: collapse;
        font-size: 14px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    .index-table th {{
        background-color: #002060;
        color: #ffffff;
        padding: 10px;
        border: 1px solid #002060;
        text-align: center;
    }}
    .index-table td {{
        padding: 10px;
        border: 1px solid #d0d0d0;
        text-align: right;
    }}
    .index-table .name-col {{
        text-align: left;
        font-weight: bold;
        background-color: #f8fafc;
    }}
</style>
</head>
<body>

<h4 style="margin-bottom: 8px; color: #333;">基準日期：{date_str}</h4>

<table class="index-table">
    <thead>
        <tr>
            <th style="width: 25%;">指數名稱</th>
            <th style="width: 25%;">代碼</th>
            <th style="width: 20%;">收盤價</th>
            <th style="width: 15%;">變動</th>
            <th style="width: 15%;">漲跌幅 (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="name-col">滬深300指數 (CSI 300)</td>
            <td style="text-align:center; color:#666;">000300.SS</td>
            {format_cell_html(csi300_data)}
        </tr>
        <tr>
            <td class="name-col">泰國曼谷SET指數 (SET Index)</td>
            <td style="text-align:center; color:#666;">^SET.BK</td>
            {format_cell_html(thai_data)}
        </tr>
    </tbody>
</table>

</body>
</html>
"""

# 6. 在 Streamlit 網頁單獨呈現
components.html(single_table_html, height=220, scrolling=False)
