import yfinance as yf
import pandas as pd
import requests
import os
import time
import pytz
from datetime import datetime, time as dt_time

# ==========================
# SETTINGS
# ==========================

SYMBOL = "QQQ"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

PULLBACK_THRESHOLD = 0.006  # 0.6%
LAST_SIGNAL = None

# ==========================
# DISCORD
# ==========================

def send_discord(message):
    if not WEBHOOK_URL:
        print("WEBHOOK_URL not set.")
        return
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print("Discord error:", e)

# ==========================
# OPTION SELECTION
# ==========================

def get_option_contract(direction, current_price):
    try:
        ticker = yf.Ticker(SYMBOL)
        expirations = ticker.options

        est = pytz.timezone("US/Eastern")
        today = datetime.now(est).date()

        chosen_exp = None
        for exp in expirations:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if 7 <= dte <= 14:
                chosen_exp = exp
                break

        if not chosen_exp:
            return None

        chain = ticker.option_chain(chosen_exp)
        options = chain.calls if direction == "CALL" else chain.puts

        options["distance"] = abs(options["strike"] - current_price)
        best = options.sort_values("distance").iloc[0]

        strike = int(best["strike"])
        mid_price = round((best["bid"] + best["ask"]) / 2, 2)

        exp_date = datetime.strptime(chosen_exp, "%Y-%m-%d")
        formatted_date = f"{exp_date.month}/{exp_date.day}"

        contract_type = "C" if direction == "CALL" else "P"

        return f"${SYMBOL} {formatted_date} {strike} {contract_type} @ {mid_price}"

    except Exception as e:
        print("Option selection error:", e)
        return None

# ==========================
# SIGNAL LOGIC
# ==========================

def check_signal():
    global LAST_SIGNAL

    est = pytz.timezone("US/Eastern")
    now = datetime.now(est)

    if not (dt_time(9,30) <= now.time() <= dt_time(16,0)):
        print("Market closed.")
        return

    print("Checking signal at", now.strftime("%Y-%m-%d %H:%M"))

    try:
        # DAILY DATA
        daily = yf.download(SYMBOL, period="60d", interval="1d", progress=False)

        if daily.empty:
            print("Daily data empty.")
            return

        if isinstance(daily.columns, pd.MultiIndex):
            daily.columns = daily.columns.get_level_values(0)

        daily["ema20"] = daily["Close"].ewm(span=20).mean()

        bullish_daily = daily["Close"].iloc[-1] > daily["ema20"].iloc[-1]
        bearish_daily = daily["Close"].iloc[-1] < daily["ema20"].iloc[-1]

        # 1H DATA
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
            print("Not enough 1H candles yet.")
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

        contract = get_option_contract(current_signal, close)

        if contract:
            message = (
                f"🚨 QQQ {current_signal} SIGNAL 🚨\n"
                f"{contract}\n"
                f"Target: +50%\n"
                f"Stop: -22%"
            )
            send_discord(message)
            print("Signal sent:", contract)

    except Exception as e:
        print("Signal logic error:", e)

# ==========================
# MAIN LOOP
# ==========================

if __name__ == "__main__":
    print("Bot started.")

    while True:
        try:
            check_signal()
        except Exception as e:
            print("Main loop error:", e)

        time.sleep(3600)
