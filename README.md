# Trend Continuation Options Bot

Automated QQQ options continuation strategy.

## Strategy

- Daily EMA20 bias
- 1H pullback within 0.6%
- 1H breakout confirmation
- Volatility filter
- 2.5R structure
- 7–14 DTE contracts

## Risk Model

- 2% per trade recommended
- +50% target
- -22% stop

## Deployment

Designed for Railway.
Requires WEBHOOK_URL environment variable.
