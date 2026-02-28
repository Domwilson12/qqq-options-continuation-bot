import os
import yfinance as yf
import pandas as pd
import requests
import pytz
from datetime import datetime

SYMBOL = "QQQ"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

print("Bot started for after-hours test.")

def send_discord(message):
    if not WEBHOOK_URL:
        print("WEBHOOK_URL not set.")
        return
    requests.post(WEBHOOK_URL, json={"content": message})

def get_option_contract(direction):
    try:
        ticker = yf.Ticker(SYMBOL)

        # Use last daily close instead of 1-minute data
        daily = yf.download(SYMBOL, period="5d", interval="1d", progress=False)
        if isinstance(daily.columns, pd.MultiIndex):
            daily.columns = daily.columns.get_level_values(0)

        current_price = daily["Close"].iloc[-1]

        expirations = ticker.options

        est = pytz.timezone("US/Eastern")
        today = datetime.now(est).date()

        chosen_exp = None
        for exp in expirations:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if 0 <= dte <= 30:  # widened for guaranteed test
                chosen_exp = exp
                break

        if not chosen_exp:
            print("No expiration found.")
            return None

        chain = ticker.option_chain(chosen_exp)
        options = chain.calls if direction == "CALL" else chain.puts

        options["distance"] = abs(options["strike"] - current_price)
        best = options.sort_values("distance").iloc[0]

        strike = int(best["strike"])

        bid = best["bid"]
        ask = best["ask"]

        # If after-hours bid/ask are zero, estimate simple premium
        if bid == 0 and ask == 0:
            mid_price = round(abs(current_price - strike) * 0.02 + 1, 2)
        else:
            mid_price = round((bid + ask) / 2, 2)

        exp_date = datetime.strptime(chosen_exp, "%Y-%m-%d")
        formatted_date = f"{exp_date.month}/{exp_date.day}"

        contract_type = "C" if direction == "CALL" else "P"

        return f"${SYMBOL} {formatted_date} {strike} {contract_type} @ {mid_price}"

    except Exception as e:
        print("Option selection error:", e)
        return None

# 🚨 FORCE TEST SIGNAL
contract = get_option_contract("CALL")

if contract:
    message = (
        f"🚨 QQQ CALL SIGNAL 🚨\n"
        f"{contract}\n"
        f"Target: +50%\n"
        f"Stop: -22%"
    )
    send_discord(message)
    print("After-hours test signal sent:", contract)
else:
    print("Failed to build contract.")
