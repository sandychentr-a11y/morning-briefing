import datetime
import json
import re
import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="StockQ 指數資料抓取測試", layout="wide")

st.title("📊 滬深300 & 泰國SET指數 專用看板 (StockQ 直連版)")

today = datetime.date.today()
selected_date = st.date_input("選擇查詢日期：", value=today, max_value=today)


# ---------------------------------------------------------
# 1. 直接爬取 StockQ 網頁數據 (滬深300 & 泰國SET)
# ---------------------------------------------------------
def fetch_from_stockq(index_code, target_date):
    """
    爬取 StockQ 網頁 (https://www.stockq.org/index/INDEX_CODE.php)
    index_code:
      - 滬深300: 000300
      - 泰國SET: SET
    """
    url = f"https://www.stockq.org/index/{index_code}.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")

            # 搜尋 StockQ 頁面中的歷史價格數據表格
            # StockQ 的歷史表格 class 為 'boardList' 或一般的表格結構
            tables = soup.find_all("table", {"class": "boardList"})
            if not tables:
                tables = soup.find_all("table")

            records = []
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cols = row.find_all(["td", "th"])
                    cols_text = [
                        c.get_text(strip=True).replace(",", "") for c in cols
                    ]

                    # 尋找包含日期的資料列 (格式如: 2026/09/30 或 2026-09-30)
                    if len(cols_text) >= 4:
                        date_str = cols_text[0]
                        # 正規表示式比對日期 YYYY/MM/DD 或 YYYY-MM-DD
                        if re.match(
                            r"^\d{4}[\/\-]\d{2}[\/\-]\d{2}$", date_str
                        ):
                            try:
                                dt = datetime.datetime.strptime(
                                    date_str.replace("-", "/"), "%Y/%m/%d"
                                ).date()
                                close_p = float(cols_text[1])
                                chg_p = float(cols_text[2])
                                pct_p = float(cols_text[3].replace("%", ""))
                                records.append(
                                    {
                                        "Date": dt,
                                        "Close": close_p,
                                        "Chg": chg_p,
                                        "Pct": pct_p,
                                    }
                                )
                            except ValueError:
                                continue

            if records:
                df = pd.DataFrame(records).sort_values("Date")
                df_filtered = df[df["Date"] <= target_date]

                if not df_filtered.empty:
                    latest_traded_date = df_filtered["Date"].iloc[-1]
                    latest_close = df_filtered["Close"].iloc[-1]
                    latest_chg = df_filtered["Chg"].iloc[-1]
                    latest_pct = df_filtered["Pct"].iloc[-1]

                    # 判斷是否休市 (選擇的日期沒有歷史資料，或者為週末)
                    is_closed = (
                        target_date.weekday() >= 5
                        or target_date not in df_filtered["Date"].values
                    )

                    if is_closed:
                        return (
                            f"{latest_close:,.2f}",
                            "休市",
                            "休市",
                            0,
                            True,
                        )

                    return (
                        f"{latest_close:,.2f}",
                        f"{latest_chg:+,.2f}",
                        f"{latest_pct:+,.2f}%",
                        latest_pct,
                        False,
                    )

    except Exception as e:
        pass

    return ("-", "-", "-", 0, False)


# ---------------------------------------------------------
# 2. 執行抓取 (StockQ 代碼：滬深300為 000300，泰國SET為 SET)
# ---------------------------------------------------------
csi300_data = fetch_from_stockq("000300", selected_date)
thai_data = fetch_from_stockq("SET", selected_date)


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
            <th style="width: 25%;">StockQ 代碼</th>
            <th style="width: 20%;">收盤價</th>
            <th style="width: 15%;">變動</th>
            <th style="width: 15%;">漲跌幅 (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="name-col">滬深300指數 (CSI 300)</td>
            <td style="text-align:center; color:#666;">stockq.org/index/000300.php</td>
            {format_cell_html(csi300_data)}
        </tr>
        <tr>
            <td class="name-col">泰國曼谷SET指數 (SET Index)</td>
            <td style="text-align:center; color:#666;">stockq.org/index/SET.php</td>
            {format_cell_html(thai_data)}
        </tr>
    </tbody>
</table>

</body>
</html>
"""

components.html(single_table_html, height=220, scrolling=False)
