import yfinance as yf
import pandas as pd
import requests
import os
import time
import pytz
from datetime import datetime, time as dt_time

SYMBOL = "QQQ"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PULLBACK_THRESHOLD = 0.006

LAST_SIGNAL = None

def send_discord(message):
    if not WEBHOOK_URL:
        print("WEBHOOK_URL not set.")
        return
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print("Discord error:", e)

def check_signal():
    global LAST_SIGNAL

    est = pytz.timezone("US/Eastern")
    now = datetime.now(est)

    print("Heartbeat:", now.strftime("%Y-%m-%d %H:%M:%S"))

    if not (dt_time(9,30) <= now.time() <= dt_time(16,0)):
        print("Market closed.")
        return

    try:
        daily = yf.download(SYMBOL, period="60d", interval="1d", progress=False)
        if daily.empty:
            print("Daily data empty.")
            return

        if isinstance(daily.columns, pd.MultiIndex):
            daily.columns = daily.columns.get_level_values(0)

        daily["ema20"] = daily["Close"].ewm(span=20).mean()

        bullish_daily = daily["Close"].iloc[-1] > daily["ema20"].iloc[-1]
        bearish_daily = daily["Close"].iloc[-1] < daily["ema20"].iloc[-1]

        df = yf.download(SYMBOL, period="30d", interval="60m", progress=False)
        if df.empty:
            print("Hourly data empty.")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["ema20"] = df["Close"].ewm(span=20).mean()
        df["range"] = df["High"] - df["Low"]
        df["avg_range20"] = df["range"].rolling(20).mean()

        if len(df) < 25:
            print("Not enough hourly candles.")
            return

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        close = latest["Close"]
        ema20 = latest["ema20"]

        pullback = abs(close - ema20) / ema20 < PULLBACK_THRESHOLD
        long_break = close > prev["High"]
        short_break = close < prev["Low"]
        strong_candle = latest["range"] > latest["avg_range20"]

        current_signal = None

        if bullish_daily and pullback and long_break and strong_candle:
            current_signal = "CALL"
        elif bearish_daily and pullback and short_break and strong_candle:
            current_signal = "PUT"

        if not current_signal:
            print("No valid setup.")
            return

        if current_signal == LAST_SIGNAL:
            print("Duplicate signal ignored.")
            return

        LAST_SIGNAL = current_signal

        message = f"QQQ {current_signal} SIGNAL at {round(close,2)}"
        send_discord(message)
        print("Signal sent.")

    except Exception as e:
        print("Signal error:", e)

print("Bot started successfully.")

while True:
    try:
        check_signal()
    except Exception as e:
        print("Main loop error:", e)

    time.sleep(300)  # 5-minute heartbeat so Railway sees activity
