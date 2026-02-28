import yfinance as yf
import pandas as pd
import numpy as np

SYMBOL = "QQQ"
RSI_PERIOD = 14

# Load 6 months of 5m data
df = yf.download(SYMBOL, period="6mo", interval="5m", progress=False)

df["ema20"] = df["Close"].ewm(span=20).mean()
df["ema50"] = df["Close"].ewm(span=50).mean()

# RSI
delta = df["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(RSI_PERIOD).mean()
avg_loss = loss.rolling(RSI_PERIOD).mean()
rs = avg_gain / avg_loss
df["rsi"] = 100 - (100 / (1 + rs))

df.dropna(inplace=True)

trades = []

for i in range(50, len(df)-20):

    bullish_trend = (
        df["Close"].iloc[i] > df["ema20"].iloc[i] > df["ema50"].iloc[i]
    )

    bearish_trend = (
        df["Close"].iloc[i] < df["ema20"].iloc[i] < df["ema50"].iloc[i]
    )

    long_signal = (
        bullish_trend and
        df["Close"].iloc[i] > df["ema20"].iloc[i] and
        df["Close"].iloc[i-1] < df["ema20"].iloc[i-1] and
        40 <= df["rsi"].iloc[i] <= 55
    )

    short_signal = (
        bearish_trend and
        df["Close"].iloc[i] < df["ema20"].iloc[i] and
        df["Close"].iloc[i-1] > df["ema20"].iloc[i-1] and
        45 <= df["rsi"].iloc[i] <= 60
    )

    if long_signal or short_signal:

        entry_price = df["Close"].iloc[i]
        direction = 1 if long_signal else -1

        for j in range(i+1, i+20):  # 20 bars forward (~100 mins)

            move = (df["Close"].iloc[j] - entry_price) / entry_price
            option_return = move * 6 * direction  # 6x leverage simulation

            if option_return >= 0.40:
                trades.append(0.40)
                break
            elif option_return <= -0.25:
                trades.append(-0.25)
                break

# Results
wins = [t for t in trades if t > 0]
losses = [t for t in trades if t < 0]

print("Total Trades:", len(trades))
print("Win Rate:", round(len(wins)/len(trades)*100,2), "%")
print("Average Return:", round(np.mean(trades)*100,2), "%")
print("Expectancy per trade:", round(np.mean(trades)*100,2), "%")