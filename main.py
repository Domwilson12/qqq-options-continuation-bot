def check_signal():
    global LAST_SIGNAL

    try:
        est = pytz.timezone("US/Eastern")
        now = datetime.now(est)

        print("Heartbeat:", now.strftime("%Y-%m-%d %H:%M:%S"))

        # 🚨 FORCE TEST SIGNAL (ignores market hours & setup logic)
        print("Running forced test signal...")

        ticker = yf.Ticker(SYMBOL)
        price_data = yf.download(SYMBOL, period="1d", interval="1m", progress=False)

        if price_data.empty:
            print("Price data empty.")
            return

        if isinstance(price_data.columns, pd.MultiIndex):
            price_data.columns = price_data.columns.get_level_values(0)

        current_price = price_data["Close"].iloc[-1]

        contract = get_option_contract("CALL", current_price)

        if contract:
            message = (
                f"🚨 QQQ CALL SIGNAL 🚨\n"
                f"{contract}\n"
                f"Target: +50%\n"
                f"Stop: -22%"
            )
            send_discord(message)
            print("Test signal sent:", contract)

        # Stop after one forced test
        time.sleep(5)
        exit()

    except Exception as e:
        print("Test signal error:", e)
