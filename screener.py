from datetime import datetime
import json
import math
import pandas as pd
import yfinance as yf

# List saham lengkap + daftar permintaan terbaru (tanpa duplikasi)
TICKER_LIST = [
    "^JKSE",     # IHSG
    # Permintaan Awal & Tambahan Baru
    "TPIA.JK", "CUAN.JK", "BREN.JK", "BRPT.JK", "CDIA.JK", "BNBR.JK",
    "JGLE.JK", "BRMS.JK", "CBRE.JK", "DEWA.JK", "MDIA.JK", "KOTA.JK",
    "BYAN.JK", "TLKM.JK", "BBCA.JK", "BMRI.JK", "BBRI.JK", "BBNI.JK",
    "BRIS.JK", "ASII.JK", "UNTR.JK", "PGAS.JK", "PTBA.JK", "ANTM.JK",
    "GOTO.JK", "AMRT.JK", "ICBP.JK", "INDF.JK", "CPIN.JK", "MEDC.JK",
    "ADRO.JK", "KLBF.JK", "INKP.JK", "MDKA.JK", "TINS.JK", "BUMI.JK",
    "ENRG.JK", "WBSA.JK", "WIFI.JK", "INET.JK", "ARTO.JK", "EMAS.JK",
    "DSSA.JK", "AADI.JK", "ADMR.JK", "MTDL.JK", "MYOR.JK", "MBMA.JK",
    "INCO.JK", "BIPI.JK", "PTRO.JK", "INDY.JK", "KOKA.JK", "AGAR.JK",
    "BUVA.JK", "BACH.JK", "DOOH.JK", "BULL.JK", "DATA.JK", "PACK.JK",
    "LUCY.JK", "BAPA.JK", "MAPI.JK"
]

# Pembersihan otomatis jika ada duplikasi ticker
TICKERS = list(dict.fromkeys(TICKER_LIST))

# Pengelompokan Kategori Sektor
SECTOR_MAP = {
    "IHSG": "Indeks Utama",
    # Perbankan & Keuangan
    "BBCA": "Bank", "BMRI": "Bank", "BBRI": "Bank", "BBNI": "Bank", 
    "BRIS": "Bank", "ARTO": "Bank Digital",
    # Tambang & Mineral
    "ANTM": "Tambang Mineral", "MDKA": "Tambang Mineral", "TINS": "Tambang Mineral", 
    "INCO": "Tambang Nickel", "MBMA": "Tambang Nickel", "BRMS": "Tambang Emas", 
    "EMAS": "Tambang Emas", "AADI": "Tambang Mineral", "ADMR": "Tambang Mineral",
    # Energi & Batu Bara
    "ADRO": "Energi", "PTBA": "Energi", "BYAN": "Energi", "BUMI": "Energi", 
    "ENRG": "Energi", "MEDC": "Energi", "PGAS": "Energi", "INDY": "Energi", 
    "BIPI": "Energi", "DSSA": "Energi", "BREN": "Energi Terbarukan", 
    "CUAN": "Energi", "BRPT": "Energi & Kimia", "TPIA": "Petrokimia",
    # Teknologi & Telekomunikasi
    "TLKM": "Telekomunikasi", "GOTO": "Teknologi", "WIFI": "Teknologi", 
    "INET": "Teknologi", "MTDL": "Teknologi", "DOOH": "Teknologi", 
    "DATA": "Teknologi",
    # Konsumer, Ritel & Hotel/Hiburan
    "AMRT": "Ritel", "MAPI": "Ritel", "ICBP": "Konsumer", "INDF": "Konsumer", 
    "MYOR": "Konsumer", "CPIN": "Peternakan", "KLBF": "Farmasi", 
    "LUCY": "Resto & Hiburan", "BUVA": "Hotel & Pariwisata",
    # Otomotif, Infrastruktur & Jasa
    "ASII": "Otomotif & Grup", "UNTR": "Alat Berat", "PTRO": "Kontraktor Tambang", 
    "DEWA": "Kontraktor", "KOKA": "Konstruksi", "CBRE": "Pelayaran", 
    "BULL": "Pelayaran", "BNBR": "Infrastruktur", "INKP": "Kertas", 
    "CDIA": "Perdagangan", "JGLE": "Properti", "KOTA": "Properti", 
    "BAPA": "Properti", "MDIA": "Media", "WBSA": "Industri", 
    "AGAR": "Industri", "BACH": "Jasa", "PACK": "Kemasan"
}

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def calculate_stochastic(high, low, close, k_window=14, d_window=3):
    lowest_low = low.rolling(window=k_window).min()
    highest_high = high.rolling(window=k_window).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_window).mean()
    return k, d

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

    ema20_series = close_prices.ewm(span=20, adjust=False).mean()
    rsi_series = calculate_rsi(close_prices)
    vol_ma20_series = volume_data.rolling(window=20).mean()

    macd_series, macd_signal_series = calculate_macd(close_prices)
    stoch_k_series, stoch_d_series = calculate_stochastic(high_prices, low_prices, close_prices)

    resistance_20 = high_prices.iloc[-21:-1].max()
    support_20 = low_prices.iloc[-21:-1].min()

    last_close = clean_val(close_prices.iloc[-1])
    last_rsi = clean_val(rsi_series.iloc[-1])
    last_ema20 = clean_val(ema20_series.iloc[-1])
    res_val = clean_val(resistance_20)
    sup_val = clean_val(support_20)

    last_macd = clean_val(macd_series.iloc[-1])
    last_macd_signal = clean_val(macd_signal_series.iloc[-1])
    last_stoch_k = clean_val(stoch_k_series.iloc[-1])
    last_stoch_d = clean_val(stoch_d_series.iloc[-1])

    rsi_status = "BUY" if last_rsi < 35 else ("SELL" if last_rsi > 70 else "NEUTRAL")
    ema_status = "BUY" if last_close > last_ema20 else ("SELL" if last_close < last_ema20 else "NEUTRAL")
    macd_status = "BUY" if last_macd > last_macd_signal else "SELL"
    stoch_status = "BUY" if last_stoch_k < 20 else ("SELL" if last_stoch_k > 80 else "NEUTRAL")

    last_vol = float(volume_data.iloc[-1])
    last_vol_ma = float(vol_ma20_series.iloc[-1])
    vol_ratio = clean_val(last_vol / last_vol_ma) if last_vol_ma > 0 else 1.0

    buy_count = [rsi_status, ema_status, macd_status, stoch_status].count("BUY")
    sell_count = [rsi_status, ema_status, macd_status, stoch_status].count("SELL")
    
    buy_percent = round((buy_count / 4) * 100)
    sell_percent = round((sell_count / 4) * 100)

    signal = "NEUTRAL"
    if last_close > res_val and res_val > 0:
        signal = "SBR" if vol_ratio >= 1.5 else "Break R"
    elif last_close < sup_val and sup_val > 0:
        signal = "SBS" if vol_ratio >= 1.5 else "Break S"
    elif buy_percent >= 75:
        signal = "BUY"
    elif sell_percent >= 75:
        signal = "SELL"

    clean_name = ticker_symbol.replace(".JK", "").replace("^JKSE", "IHSG")
    is_ihsg = clean_name == "IHSG"
    sector_label = SECTOR_MAP.get(clean_name, "Lainnya")

    return {
        "ticker": clean_name,
        "sector": sector_label,
        "price": last_close,
        "rsi": last_rsi,
        "rsi_status": rsi_status,
        "ema20": last_ema20,
        "ema_status": ema_status,
        "macd": last_macd,
        "macd_signal": last_macd_signal,
        "stoch_k": last_stoch_k,
        "stoch_d": last_stoch_d,
        "support": sup_val,
        "resistance": res_val,
        "vol_ratio": vol_ratio,
        "entry": 0.0 if is_ihsg else last_close,
        "stop_loss": 0.0 if is_ihsg else clean_val(sup_val * 0.98 if sup_val > 0 else last_close * 0.97),
        "take_profit": 0.0 if is_ihsg else clean_val(res_val if res_val > last_close else last_close * 1.05),
        "buy_percent": buy_percent,
        "sell_percent": sell_percent,
        "signal": signal
    }

def run_screener():
    results = []
    print(f"Memproses {len(TICKERS)} emiten...")

    for ticker in TICKERS:
        try:
            data = process_ticker_data(ticker)
            if data:
                results.append(data)
                print(f"Sukses: {ticker}")
        except Exception as e:
            print(f"Gagal memproses {ticker}: {e}")

    output_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stocks": results
    }

    with open("data.json", "w") as f:
        json.dump(output_data, f, indent=4)

    print("Selesai! Data berhasil diperbarui di data.json")

if __name__ == "__main__":
    run_screener()
    
