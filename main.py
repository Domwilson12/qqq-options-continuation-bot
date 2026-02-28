import time
import os
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, time as dt_time

SYMBOL = "QQQ"
PULLBACK_THRESHOLD = 0.006

print("Bot started successfully.")

def check_signal():
    try:
        est = pytz.timezone("US/Eastern")
        now = datetime.now(est)

        print("Heartbeat:", now.strftime("%Y-%m-%d %H:%M:%S"))

        if not (dt_time(9,30) <= now.time() <= dt_time(16,0)):
            print("Market closed.")
            return

        # DAILY
        daily = yf.download(SYMBOL, period="60d", interval="1d", progress=False)
        if daily.empty:
            print("Daily data empty.")
            return

        if isinstance(daily.columns, pd.MultiIndex):
            daily.columns = daily.columns.get_level_values(0)

        daily["ema20"] = daily["Close"].ewm(span=20).mean()

        # 1H
        df = yf.download(SYMBOL, period="30d", interval="60m", progress=False)
        if df.empty:
            print("1H data empty.")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["ema20"] = df["Close"].ewm(span=20).mean()
        df["range"] = df["High"] - df["Low"]
        df["avg_range20"] = df["range"].rolling(20).mean()

        if len(df) < 25:
            print("Not enough candles.")
            return

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        close = latest["Close"]
        ema20 = latest["ema20"]

        pullback = abs(close - ema20) / ema20 < PULLBACK_THRESHOLD
        long_break = close > prev["High"]
        strong_candle = latest["range"] > latest["avg_range20"]

        if pullback and long_break and strong_candle:
            print("CALL setup detected at", round(close, 2))
        else:
            print("No setup.")

    except Exception as e:
        print("Signal error:", e)

while True:
    check_signal()
    time.sleep(300)
