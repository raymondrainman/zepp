import os
import pandas as pd
import ccxt
import asyncio
from telegram import Bot
from flask import Flask
from threading import Thread

# Config uit omgevingsvariabelen
TELEGRAM_TOKEN = os.environ '7733338006:AAG-nblQ5QGrO_U9scNYGPkVyQSEUhrZWuI'
CHAT_ID = int(os.environ '6437002032')
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'
MA_PERIOD = 9
CHECK_INTERVAL = 60  # seconden

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return '✅ MA9 Telegram Bot draait!'

def get_heikin_ashi_ohlcv():
    exchange = ccxt.bybit()
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=MA_PERIOD + 1)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    ha_df = pd.DataFrame()
    ha_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    ha_df['open'] = 0.0
    ha_df.loc[0, 'open'] = df.loc[0, 'open']

    for i in range(1, len(df)):
        ha_df.loc[i, 'open'] = (ha_df.loc[i-1, 'open'] + ha_df.loc[i-1, 'close']) / 2

    ha_df['high'] = df[['high', 'open', 'close']].max(axis=1)
    ha_df['low'] = df[['low', 'open', 'close']].min(axis=1)

    return ha_df

async def analyze_and_alert():
    print("Bot draait. Wachten op signalen...")
    last_signal = None

    while True:
        try:
            ha = get_heikin_ashi_ohlcv()
            ha['ma'] = ha['close'].rolling(window=MA_PERIOD).mean()
            last_candle = ha.iloc[-1]

            if last_candle['close'] > last_candle['ma'] and last_signal != 'bullish':
                await bot.send_message(chat_id=CHAT_ID, text='📈 Bullish signaal: HA sluit boven MA9.')
                print("Bullish signaal verzonden.")
                last_signal = 'bullish'

            elif last_candle['close'] < last_candle['ma'] and last_signal != 'bearish':
                await bot.send_message(chat_id=CHAT_ID, text='📉 Bearish signaal: HA sluit onder MA9.')
                print("Bearish signaal verzonden.")
                last_signal = 'bearish'

        except Exception as e:
            print(f"Fout bij analyse: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(analyze_and_alert())

if __name__ == '__main__':
    Thread(target=start_bot).start()
    app.run(host='0.0.0.0', port=8080)
