import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta

class StockAnalyzer:
    def __init__(self):
        self.thai_stocks = {
            'ADVANC.BK': 'ADVANC',
            'AOT.BK': 'AOT',
            'BDMS.BK': 'BDMS',
            'BH.BK': 'BH',
            'BTS.BK': 'BTS',
            'CPALL.BK': 'CPALL',
            'CPF.BK': 'CPF',
            'CRC.BK': 'CRC',
            'DTAC.BK': 'DTAC',
            'GULF.BK': 'GULF',
            'INTUCH.BK': 'INTUCH',
            'IVL.BK': 'IVL',
            'KBANK.BK': 'KBANK',
            'KTB.BK': 'KTB',
            'PTT.BK': 'PTT',
            'PTTEP.BK': 'PTTEP',
            'SCB.BK': 'SCB',
            'SCC.BK': 'SCC',
            'TISCO.BK': 'TISCO',
            'TRUE.BK': 'TRUE'
        }
    
    def get_stock_data(self, symbol, period='6mo'):
        """ดึงข้อมูลหุ้นจาก Yahoo Finance"""
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            info = stock.info
            return df, info
        except Exception as e:
            return None, None
    
    def calculate_indicators(self, df):
        """คำนวณตัวชี้วัดทางเทคนิค"""
        if df is None or df.empty:
            return None
        
        try:
            # RSI
            df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
            
            # Moving Averages
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
            df['BB_Upper'] = bb.bollinger_hband()
            df['BB_Middle'] = bb.bollinger_mavg()
            df['BB_Lower'] = bb.bollinger_lband()
            
            # Volume
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            
        return df
    
    def get_trend(self, df):
        """วิเคราะห์แนวโน้ม"""
        if df is None or df.empty:
            return "ไม่สามารถวิเคราะห์ได้"
        
        try:
            latest = df.iloc[-1]
            
            if pd.isna(latest['SMA_20']) or pd.isna(latest['SMA_50']) or pd.isna(latest['SMA_200']):
                return "ข้อมูลไม่เพียงพอ"
            
            if latest['Close'] > latest['SMA_20'] > latest['SMA_50'] > latest['SMA_200']:
                return "ขาขึ้นแข็งแกร่ง"
            elif latest['Close'] > latest['SMA_50'] > latest['SMA_200']:
                return "ขาขึ้น"
            elif latest['Close'] < latest['SMA_20'] < latest['SMA_50'] < latest['SMA_200']:
                return "ขาลงรุนแรง"
            elif latest['Close'] < latest['SMA_50'] < latest['SMA_200']:
                return "ขาลง"
            elif latest['SMA_20'] > latest['SMA_50'] and latest['Close'] < latest['SMA_20']:
                return "ปรับฐานในขาขึ้น"
            elif latest['SMA_20'] < latest['SMA_50'] and latest['Close'] > latest['SMA_20']:
                return "ฟื้นตัวในขาลง"
            else:
                return "Sideways"
        except:
            return "ไม่สามารถวิเคราะห์ได้"
    
    def get_rsi_signal(self, rsi_value):
        """วิเคราะห์สัญญาณ RSI"""
        if pd.isna(rsi_value):
            return "ไม่มีข้อมูล", "⚪"
        
        if rsi_value < 30:
            return "ซื้อ (oversold)", "🟢"
        elif rsi_value > 70:
            return "ขาย (overbought)", "🔴"
        elif 40 <= rsi_value <= 60:
            return " neutral", "⚪"
        elif rsi_value < 40:
            return "ใกล้ซื้อ", "🟡"
        else:
            return "ใกล้ขาย", "🟡"
    
    def get_macd_signal(self, macd, signal, hist):
        """วิเคราะห์สัญญาณ MACD"""
        if pd.isna(macd) or pd.isna(signal):
            return "ไม่มีข้อมูล", "⚪"
        
        if macd > signal and hist > 0:
            return " bullish", "🟢"
        elif macd < signal and hist < 0:
            return " bearish", "🔴"
        elif macd > signal:
            return "เริ่ม bullish", "🟡"
        else:
            return "เริ่ม bearish", "🟡"
    
    def get_bb_signal(self, price, bb_lower, bb_upper):
        """วิเคราะห์สัญญาณ Bollinger Bands"""
        if pd.isna(bb_lower) or pd.isna(bb_upper):
            return "ไม่มีข้อมูล", "⚪"
        
        if price <= bb_lower:
            return "ซื้อ (oversold)", "🟢"
        elif price >= bb_upper:
            return "ขาย (overbought)", "🔴"
        else:
            return "ปกติ", "⚪"
    
    def get_dividend_info(self, info):
        """ดึงข้อมูลปันผลที่ถูกต้อง"""
        try:
            div_yield = info.get('dividendYield', 0)
            
            # ถ้าไม่มีข้อมูล
            if div_yield is None or div_yield == 0:
                return {
                    'dividend_yield': 0,
                    'payout_ratio': 0,
                    'has_dividend': False
                }
            
            # Yahoo Finance ส่งค่ามาเป็นทศนิยม (0.05 = 5%)
            if isinstance(div_yield, (int, float)):
                if div_yield > 1:  # ถ้าเป็นเปอร์เซ็นต์แล้ว
                    div_percent = div_yield
                else:
                    div_percent = div_yield * 100
            else:
                div_percent = 0
            
            # Payout ratio
            payout = info.get('payoutRatio', 0)
            if isinstance(payout, (int, float)):
                if payout > 1:
                    payout_percent = payout
                else:
                    payout_percent = payout * 100
            else:
                payout_percent = 0
            
            return {
                'dividend_yield': round(div_percent, 2),
                'payout_ratio': round(payout_percent, 2),
                'has_dividend': div_percent > 0
            }
        except:
            return {
                'dividend_yield': 0,
                'payout_ratio': 0,
                'has_dividend': False
            }
    
    def get_fundamental_summary(self, info):
        """สรุปปัจจัยพื้นฐาน"""
        summary = []
        
        # P/E
        pe = info.get('trailingPE', None)
        if pe and pe > 0:
            if pe < 10:
                summary.append(("P/E", f"{pe:.1f}", "ต่ำ"))
            elif pe < 15:
                summary.append(("P/E", f"{pe:.1f}", "เหมาะสม"))
            elif pe < 25:
                summary.append(("P/E", f"{pe:.1f}", "สูง"))
            else:
                summary.append(("P/E", f"{pe:.1f}", "สูงมาก"))
        
        # P/B
        pb = info.get('priceToBook', None)
        if pb and pb > 0:
            if pb < 1:
                summary.append(("P/B", f"{pb:.2f}", "ต่ำ"))
            elif pb < 1.5:
                summary.append(("P/B", f"{pb:.2f}", "เหมาะสม"))
            elif pb < 3:
                summary.append(("P/B", f"{pb:.2f}", "สูง"))
            else:
                summary.append(("P/B", f"{pb:.2f}", "สูงมาก"))
        
        return summary
