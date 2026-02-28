import os
import time
import requests

print("Bot started.")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not WEBHOOK_URL:
    print("WEBHOOK_URL is NOT set.")
else:
    print("WEBHOOK_URL detected.")
    requests.post(WEBHOOK_URL, json={"content": "🚨 DIRECT WEBHOOK TEST — If you see this, webhook works."})

while True:
    print("Alive...")
    time.sleep(60)
