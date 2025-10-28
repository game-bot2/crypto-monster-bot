import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime
import ta

class LiveCryptoMonster:
    def __init__(self, balance=100):
        self.balance = balance
        self.positions = {}
        
        self.coins = ['BTC', 'ETH', 'SOL', 'ADA', 'MATIC', 'DOGE', 'XRP']
        
        self.leverage = 5
        self.max_risk_per_trade = 0.05
        self.max_coins = 3
        self.take_profit = 0.35
        self.stop_loss = 0.15

    def get_cryptocompare_price(self, symbol):
        try:
            url = f"https://min-api.cryptocompare.com/data/price"
            params = {
                'fsym': symbol,
                'tsyms': 'USD'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'USD' in data:
                price = data['USD']
                return price
            else:
                return 0
                
        except Exception as e:
            print(f"Price error for {symbol}: {e}")
            return 0

    def get_cryptocompare_histo(self, symbol, period='day', limit=90):
        try:
            url = f"https://min-api.cryptocompare.com/data/v2/histoday"
            params = {
                'fsym': symbol,
                'tsym': 'USD',
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['Response'] == 'Success':
                df = pd.DataFrame(data['Data']['Data'])
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df = df.rename(columns={
                    'time': 'timestamp',
                    'open': 'open',
                    'high': 'high', 
                    'low': 'low',
                    'close': 'close',
                    'volumefrom': 'volume'
                })
                return df
            else:
                return None
                
        except Exception as e:
            print(f"Histo error for {symbol}: {e}")
            return None

    def calculate_technical_indicators(self, df):
        if df is None or len(df) < 20:
            return None
            
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        try:
            df['RSI_14'] = ta.momentum.RSIIndicator(close, window=14).rsi()
            
            macd = ta.trend.MACD(close)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            
            bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=2)
            df['BB_Upper'] = bollinger.bollinger_hband()
            df['BB_Lower'] = bollinger.bollinger_lband()
            df['BB_Middle'] = bollinger.bollinger_mavg()
            
            df['Volume_SMA'] = volume.rolling(20).mean()
            df['Volume_Ratio'] = volume / df['Volume_SMA']
            
            return df.dropna()
        except Exception as e:
            print(f"Indicator error: {e}")
            return None

    def monster_trading_strategy(self, df, symbol):
        if df is None or len(df) < 50:
            return 'HOLD', 0, 0
            
        current = df.iloc[-1]
        buy_score = 0
        sell_score = 0
        confidence = 0
        
        try:
            # RSI
            if not np.isnan(current['RSI_14']):
                if current['RSI_14'] < 30:
                    buy_score += 15
                    confidence += 2
                elif current['RSI_14'] > 70:
                    sell_score += 15
                    confidence += 2
            
            # MACD
            if not np.isnan(current['MACD']) and not np.isnan(current['MACD_Signal']):
                if current['MACD'] > current['MACD_Signal']:
                    buy_score += 10
                    confidence += 1
                else:
                    sell_score += 10
                    confidence += 1
            
            # Bollinger Bands
            if not np.isnan(current['BB_Lower']) and not np.isnan(current['BB_Upper']):
                if current['close'] < current['BB_Lower']:
                    buy_score += 8
                    confidence += 1
                elif current['close'] > current['BB_Upper']:
                    sell_score += 8
                    confidence += 1
            
            # Volume
            if not np.isnan(current['Volume_Ratio']):
                if current['Volume_Ratio'] > 1.5:
                    buy_score += 5
                    confidence += 1
            
            # Final decision
            if buy_score >= 25 and confidence >= 4:
                return 'BUY', buy_score, confidence
            elif sell_score >= 20 and confidence >= 3:
                return 'SELL', sell_score, confidence
            
            return 'HOLD', max(buy_score, sell_score), confidence
            
        except Exception as e:
            print(f"Strategy error for {symbol}: {e}")
            return 'HOLD', 0, 0

    def run_live_trading(self):
        print("CRYPTO MONSTER BOT STARTED!")
        print(f"Balance: ${self.balance}")
        print(f"Leverage: {self.leverage}x")
        print("Scanning for signals...")
        
        while True:
            print(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)
            
            signals_found = False
            
            for coin in self.coins:
                try:
                    current_price = self.get_cryptocompare_price(coin)
                    if current_price == 0:
                        print(f"❌ {coin}: No price data")
                        continue
                    
                    df = self.get_cryptocompare_histo(coin, 'day', 90)
                    
                    if df is not None and len(df) >= 50:
                        df = self.calculate_technical_indicators(df)
                        
                        if df is not None:
                            signal, score, confidence = self.monster_trading_strategy(df, coin)
                            
                            if signal == 'BUY':
                                print(f"🚀 BUY {coin}: ${current_price:,.2f} | Score: {score} | Confidence: {confidence}")
                                signals_found = True
                            elif signal == 'SELL':
                                print(f"🔴 SELL {coin}: ${current_price:,.2f} | Score: {score} | Confidence: {confidence}")
                                signals_found = True
                            else:
                                print(f"⚪ HOLD {coin}: ${current_price:,.2f} | Score: {score}")
                                signals_found = True
                        else:
                            print(f"⚪ HOLD {coin}: ${current_price:,.2f} | Calculating...")
                            signals_found = True
                    else:
                        print(f"⚪ HOLD {coin}: ${current_price:,.2f} | Getting data...")
                        signals_found = True
                        
                except Exception as e:
                    print(f"❌ Error {coin}: {e}")
            
            if not signals_found:
                print("No signals available - retrying...")
            
            print("=" * 70)
            print("Waiting 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    monster = LiveCryptoMonster(100)
    monster.run_live_trading()
