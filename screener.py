import json
from datetime import datetime
import math
import pandas as pd
import yfinance as yf

# Hanya IHSG yang di-fetch secara default
TICKERS = ["^JKSE"]

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def clean_val(val):
    if val is None or math.isnan(val) or math.isinf(val):
        return 0.0
    return round(float(val), 2)

def process_ticker_data(ticker_symbol):
    df = yf.download(ticker_symbol, period="6mo", progress=False)
    if df.empty or len(df) < 35:
        return None

    close_prices = df['Close'].squeeze()
    high_prices = df['High'].squeeze()
    low_prices = df['Low'].squeeze()
    volume_data = df['Volume'].squeeze()

    # Indikator
    ema20_series = close_prices.ewm(span=20, adjust=False).mean()
    rsi_series = calculate_rsi(close_prices)
    vol_ma20_series = volume_data.rolling(window=20).mean()

    # SND Harian (Support & Resistance 20 Hari)
    resistance_20 = high_prices.iloc[-21:-1].max()
    support_20 = low_prices.iloc[-21:-1].min()

    last_close = clean_val(close_prices.iloc[-1])
    last_rsi = clean_val(rsi_series.iloc[-1])
    last_ema20 = clean_val(ema20_series.iloc[-1])
    res_val = clean_val(resistance_20)
    sup_val = clean_val(support_20)

    # Status RSI
    if last_rsi < 35:
        rsi_status = "BUY"
    elif last_rsi > 70:
        rsi_status = "SELL"
    else:
        rsi_status = "NEUTRAL"

    # Status EMA (Tren)
    if last_close > last_ema20:
        ema_status = "BUY"
    elif last_close < last_ema20:
        ema_status = "SELL"
    else:
        ema_status = "NEUTRAL"

    # Volume Ratio (VR)
    last_vol = float(volume_data.iloc[-1])
    last_vol_ma = float(vol_ma20_series.iloc[-1])
    vol_ratio = clean_val(last_vol / last_vol_ma) if last_vol_ma > 0 else 1.0

    # Kalkulasi Entry, SL, & TP
    entry_price = last_close
    # Stop Loss di bawah support / 3% di bawah entry
    stop_loss = clean_val(sup_val * 0.98 if sup_val > 0 else last_close * 0.97)
    # Take Profit di resistance / 5% di atas entry
    take_profit = clean_val(res_val if res_val > last_close else last_close * 1.05)

    # Signal Sederhana
    signal = "NEUTRAL"
    if last_close > res_val and res_val > 0:
        signal = "SBR" if vol_ratio >= 1.5 else "Break R"
    elif last_close < sup_val and sup_val > 0:
        signal = "SBS" if vol_ratio >= 1.5 else "Break S"
    elif rsi_status == "BUY" or ema_status == "BUY":
        signal = "BUY"
    elif rsi_status == "SELL" or ema_status == "SELL":
        signal = "SELL"

    clean_name = ticker_symbol.replace(".JK", "").replace("^JKSE", "IHSG")

    return {
        "ticker": clean_name,
        "price": last_close,
        "rsi": last_rsi,
        "rsi_status": rsi_status,
        "ema20": last_ema20,
        "ema_status": ema_status,
        "support": sup_val,
        "resistance": res_val,
        "vol_ratio": vol_ratio,
        "entry": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "signal": signal
    }

def run_screener():
    results = []
    print("Memproses data IHSG...")

    for ticker in TICKERS:
        try:
            data = process_ticker_data(ticker)
            if data:
                results.append(data)
        except Exception as e:
            print(f"Gagal memproses {ticker}: {e}")

    output_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stocks": results
    }

    with open("data.json", "w") as f:
        json.dump(output_data, f, indent=4)

    print("Data berhasil disimpan di data.json")

if __name__ == "__main__":
    run_screener()
