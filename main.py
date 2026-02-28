print("Bot started.")

import time
import yfinance as yf

print("Libraries imported.")

while True:
    print("Downloading data...")
    data = yf.download("QQQ", period="5d", interval="1d", progress=False)
    print("Rows:", len(data))
    time.sleep(60)
