import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 定義要抓取的市場指數與對應的 Yahoo Finance Ticker 代碼
INDEX_TICKERS = {
    # 亞洲市場
    "日經225指數": "^N225",
    "南韓KOSPI指數": "^KS11",
    "恆生指數": "^HSI",
    "上證指數": "000001.SS",
    "滬深300指數": "000300.SS",  # 亦可選用 399300.SZ
    "新加坡STI指數": "^STI",
    "泰國曼谷SET指數": "^SET.BK",
    "富時馬來西亞指數": "^KLSE",
    "印尼雅加達指數": "^JKSE",
    
    # 美國市場
    "道瓊工業指數": "^DJI",
    "那斯達克指數": "^IXIC",
    "標普500指數": "^GSPC",
    "費城半導體指數": "^SOX",
    "羅素2000指數": "^RUT",
    
    # 台灣市場
    "加權指數": "^TWII",
    "櫃買指數": "^TWOII"
}

def fetch_index_data(symbol: str) -> dict:
    """
    抓取指定代碼的最新有效交易日數據（包含收盤價、變動金額、漲跌幅）
    若逢假期休市，自動回溯取得最新可用的交易日數據。
    """
    try:
        ticker = yf.Ticker(symbol)
        # 抓取最近 10 天歷史資料，確保遇到國定連假（如十一黃金週）仍可取得最後一個交易日
        df = ticker.history(period="10d")
        
        if df.empty or len(df) < 1:
            return {"price": "-", "change": "-", "pct_change": "-"}
        
        # 取得最新一筆交易日數據
        latest_price = df['Close'].iloc[-1]
        
        # 計算變動金額與漲跌幅
        if len(df) >= 2:
            prev_price = df['Close'].iloc[-2]
            change = latest_price - prev_price
            pct_change = (change / prev_price) * 100
        else:
            change = 0.0
            pct_change = 0.0

        # 格式化輸出
        change_sign = "+" if change > 0 else ""
        return {
            "price": f"{latest_price:,.2f}",
            "change": f"{change_sign}{change:,.2f}" if change != 0 else "0.00",
            "pct_change": f"{change_sign}{pct_change:.2f}%" if pct_change != 0 else "0.00%"
        }
        
    except Exception as e:
        print(f"抓取 {symbol} 失敗: {e}")
        return {"price": "-", "change": "-", "pct_change": "-"}

def get_market_summary() -> pd.DataFrame:
    """
    生成所有市場指數的收盤表現彙整表
    """
    results = []
    
    for name, symbol in INDEX_TICKERS.items():
        data = fetch_index_data(symbol)
        results.append({
            "指數": name,
            "收盤價": data["price"],
            "變動": data["change"],
            "(%)": data["pct_change"]
        })
        
    return pd.DataFrame(results)

if __name__ == "__main__":
    print(f"=== TIS 晨報 - 重要市場收盤表現（查詢日期：{datetime.now().strftime('%Y/%m/%d')}）===")
    df_summary = get_market_summary()
    print(df_summary.to_string(index=False))
