import datetime
import json
import urllib.request
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="滬深300 & 泰國SET指數 API直連測試", layout="wide")

st.title("📊 滬深300 & 泰國SET指數 專用看板 (API 直連版)")

today = datetime.date.today()
selected_date = st.date_input("選擇查詢日期：", value=today, max_value=today)

# ---------------------------------------------------------
# 1. 東方財富網 (EastMoney) 官方 API - 滬深300
# ---------------------------------------------------------
def fetch_csi300_eastmoney(target_date):
    """
    直連東方財富官方 K 線 API 抓取滬深300 (000300)
    """
    try:
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000300&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55&klt=101&fqt=1&end=20500101&lmt=120"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            if res_json and "data" in res_json and res_json["data"] and "klines" in res_json["data"]:
                klines = res_json["data"]["klines"]
                records = []
                for k in klines:
                    parts = k.split(",")
                    # 格式: 日期, 開盤, 收盤, 最高, 最低...
                    dt = datetime.datetime.strptime(parts[0], "%Y-%m-%d").date()
                    close_p = float(parts[2])
                    records.append({"Date": dt, "Close": close_p})

                df = pd.DataFrame(records)
                df_filtered = df[df["Date"] <= target_date]

                if not df_filtered.empty:
                    latest_date = df_filtered["Date"].iloc[-1]
                    latest_close = df_filtered["Close"].iloc[-1]

                    # 判斷是否休市 (週末或選取的日期沒有資料)
                    is_closed = (target_date.weekday() >= 5 or target_date not in df_filtered["Date"].values)

                    if is_closed:
                        return (f"{latest_close:,.2f}", "休市", "休市", 0, True)

                    if len(df_filtered) >= 2:
                        c = df_filtered["Close"].iloc[-1]
                        p = df_filtered["Close"].iloc[-2]
                        chg = c - p
                        pct = (chg / p) * 100 if p != 0 else 0
                        return (f"{c:,.2f}", f"{chg:+,.2f}", f"{pct:+,.2f}%", pct, False)
                    elif len(df_filtered) == 1:
                        return (f"{latest_close:,.2f}", "0.00", "0.00%", 0, False)
    except Exception:
        pass

    return ("-", "-", "-", 0, False)

# ---------------------------------------------------------
# 2. Yahoo Web API 直連 - 泰國曼谷SET指數
# ---------------------------------------------------------
def fetch_thai_set_api(target_date):
    """
    直連 Yahoo Finance Web API 抓取泰國曼谷 SET 指數
    """
    for symbol in ["^SET.BK", "SET.BK"]:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                result = res_json["chart"]["result"][0]
                timestamps = result["timestamp"]
                closes = result["indicators"]["quote"][0]["close"]

                dates = [datetime.datetime.fromtimestamp(ts).date() for ts in timestamps]
                df = pd.DataFrame({"Date": dates, "Close": closes}).dropna()
                df = df[df["Close"] > 0]

                df_filtered = df[df["Date"] <= target_date]

                if not df_filtered.empty:
                    latest_date = df_filtered["Date"].iloc[-1]
                    latest_close = df_filtered["Close"].iloc[-1]

                    is_closed = (target_date.weekday() >= 5 or target_date not in df_filtered["Date"].values)

                    if is_closed:
                        return (f"{latest_close:,.2f}", "休市", "休市", 0, True)

                    if len(df_filtered) >= 2:
                        c = df_filtered["Close"].iloc[-1]
                        p = df_filtered["Close"].iloc[-2]
                        chg = c - p
                        pct = (chg / p) * 100 if p != 0 else 0
                        return (f"{c:,.2f}", f"{chg:+,.2f}", f"{pct:+,.2f}%", pct, False)
                    elif len(df_filtered) == 1:
                        return (f"{latest_close:,.2f}", "0.00", "0.00%", 0, False)
        except Exception:
            continue

    return ("-", "-", "-", 0, False)

# ---------------------------------------------------------
# 3. 執行抓取與渲染
# ---------------------------------------------------------
csi300_data = fetch_csi300_eastmoney(selected_date)
thai_data = fetch_thai_set_api(selected_date)

def format_cell_html(data):
    val, chg, pct_str, raw_pct, is_closed = data
    if val == "-":
        return "<td>-</td><td>-</td><td>-</td>"

    if is_closed:
        return f"<td><b>{val}</b></td><td style='color:#6B7280;'>休市</td><td style='color:#6B7280;'>休市</td>"

    if raw_pct > 0:
        color = "#DC2626"  # 上漲紅
    elif raw_pct < 0:
        color = "#16A34A"  # 下跌綠
    else:
        color = "#000000"

    return f"<td><b>{val}</b></td><td style='color:{color}; font-weight:bold;'>{chg}</td><td style='color:{color}; font-weight:bold;'>{pct_str}</td>"

date_str = selected_date.strftime("%Y/%m/%d")

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
            <th style="width: 25%;">來源 API</th>
            <th style="width: 20%;">收盤價</th>
            <th style="width: 15%;">變動</th>
            <th style="width: 15%;">漲跌幅 (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="name-col">滬深300指數 (CSI 300)</td>
            <td style="text-align:center; color:#666;">東方財富 API (000300)</td>
            {format_cell_html(csi300_data)}
        </tr>
        <tr>
            <td class="name-col">泰國曼谷SET指數 (SET Index)</td>
            <td style="text-align:center; color:#666;">Yahoo Chart API (^SET.BK)</td>
            {format_cell_html(thai_data)}
        </tr>
    </tbody>
</table>

</body>
</html>
"""

components.html(single_table_html, height=220, scrolling=False)
