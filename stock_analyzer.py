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
            'CPALL.BK': 'CPALL',
            'CPF.BK': 'CPF',
            'DTAC.BK': 'DTAC',
            'INTUCH.BK': 'INTUCH',
            'KBANK.BK': 'KBANK',
            'KTB.BK': 'KTB',
            'PTT.BK': 'PTT',
            'PTTEP.BK': 'PTTEP',
            'SCB.BK': 'SCB',
            'SCC.BK': 'SCC',
            'TISCO.BK': 'TISCO',
            'TRUE.BK': 'TRUE',
            'BH.BK': 'BH',
            'BTS.BK': 'BTS',
            'CRC.BK': 'CRC',
            'GULF.BK': 'GULF',
            'IVL.BK': 'IVL'
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
        
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # Moving Averages
        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
        df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Middle'] = bb.bollinger_mavg()
        df['BB_Lower'] = bb.bollinger_lband()
        
        # Volume
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        
        # Support/Resistance
        df['Resistance'] = df['High'].rolling(window=20).max()
        df['Support'] = df['Low'].rolling(window=20).min()
        
        # Price change
        df['Price_Change'] = df['Close'].pct_change() * 100
        df['Volume_Change'] = df['Volume'].pct_change() * 100
        
        return df
    
    def get_trend_analysis(self, df):
        """วิเคราะห์แนวโน้ม"""
        if df is None or df.empty:
            return "ไม่สามารถวิเคราะห์ได้"
        
        latest = df.iloc[-1]
        
        # ตรวจสอบแนวโน้มจาก Moving Averages
        if latest['Close'] > latest['SMA_50'] > latest['SMA_200']:
            trend = "ขาขึ้นระยะยาว"
            strength = "แข็งแกร่ง" if latest['Close'] > latest['SMA_20'] else "ชะลอตัว"
        elif latest['Close'] < latest['SMA_50'] < latest['SMA_200']:
            trend = "ขาลงระยะยาว"
            strength = "รุนแรง" if latest['Close'] < latest['SMA_20'] else "ชะลอตัว"
        elif latest['Close'] > latest['SMA_50'] and latest['Close'] < latest['SMA_200']:
            trend = "ฟื้นตัว"
            strength = "กลาง"
        elif latest['Close'] < latest['SMA_50'] and latest['Close'] > latest['SMA_200']:
            trend = "ปรับฐาน"
            strength = "กลาง"
        else:
            trend = "Sideways"
            strength = "กลาง"
        
        return f"{trend} ({strength})"
    
    def get_rsi_signal(self, rsi_value):
        """วิเคราะห์สัญญาณจาก RSI"""
        if pd.isna(rsi_value):
            return "ไม่มีข้อมูล", "⚪"
        
        if rsi_value < 30:
            return "ซื้อ (oversold)", "🟢"
        elif rsi_value > 70:
            return "ขาย (overbought)", "🔴"
        elif 40 <= rsi_value <= 60:
            return "รอ (neutral)", "⚪"
        elif rsi_value < 40:
            return "เริ่มซื้อ", "🟡"
        else:
            return "เริ่มขาย", "🟡"
    
    def get_macd_signal(self, macd, signal, prev_macd, prev_signal):
        """วิเคราะห์สัญญาณจาก MACD"""
        if pd.isna(macd) or pd.isna(signal):
            return "ไม่มีข้อมูล", "⚪"
        
        if macd > signal and prev_macd <= prev_signal:
            return "ซื้อ (golden cross)", "🟢"
        elif macd < signal and prev_macd >= prev_signal:
            return "ขาย (death cross)", "🔴"
        elif macd > signal:
            return "ถือ (bullish)", "🟡"
        else:
            return "รอดู (bearish)", "🟡"
    
    def get_volume_signal(self, volume, volume_sma):
        """วิเคราะห์สัญญาณจาก Volume"""
        if pd.isna(volume) or pd.isna(volume_sma) or volume_sma == 0:
            return "ปกติ", "⚪"
        
        volume_ratio = volume / volume_sma
        
        if volume_ratio > 1.5:
            return "สูงมาก", "🟡"
        elif volume_ratio > 1.2:
            return "สูง", "🟢"
        elif volume_ratio < 0.5:
            return "ต่ำมาก", "🔴"
        elif volume_ratio < 0.8:
            return "ต่ำ", "🟡"
        else:
            return "ปกติ", "⚪"
    
    def get_bollinger_signal(self, price, bb_lower, bb_upper):
        """วิเคราะห์สัญญาณจาก Bollinger Bands"""
        if pd.isna(bb_lower) or pd.isna(bb_upper):
            return "ไม่มีข้อมูล", "⚪"
        
        if price <= bb_lower:
            return "ซื้อ (oversold)", "🟢"
        elif price >= bb_upper:
            return "ขาย (overbought)", "🔴"
        else:
            return "ปกติ", "⚪"
    
    def get_fundamental_rating(self, info):
        """วิเคราะห์ปัจจัยพื้นฐาน"""
        rating = 0
        details = []
        
        # P/E Ratio
        pe = info.get('trailingPE', None)
        if pe and pe > 0:
            if pe < 10:
                rating += 2
                details.append("P/E ต่ำมาก")
            elif pe < 15:
                rating += 1
                details.append("P/E เหมาะสม")
            elif pe > 25:
                rating -= 1
                details.append("P/E สูง")
        
        # P/B Ratio
        pb = info.get('priceToBook', None)
        if pb and pb > 0:
            if pb < 1:
                rating += 2
                details.append("P/B ต่ำกว่า 1")
            elif pb < 1.5:
                rating += 1
                details.append("P/B เหมาะสม")
            elif pb > 3:
                rating -= 1
                details.append("P/B สูง")
        
        # Dividend Yield
        div = info.get('dividendYield', 0)
        if div and div > 0:
            div_pct = div * 100
            if div_pct > 5:
                rating += 2
                details.append(f"ปันผลสูง {div_pct:.1f}%")
            elif div_pct > 3:
                rating += 1
                details.append(f"ปันผลดี {div_pct:.1f}%")
            elif div_pct > 0:
                details.append(f"ปันผล {div_pct:.1f}%")
        
        # ROE
        roe = info.get('returnOnEquity', None)
        if roe and roe > 0:
            roe_pct = roe * 100
            if roe_pct > 20:
                rating += 2
                details.append(f"ROE สูง {roe_pct:.1f}%")
            elif roe_pct > 15:
                rating += 1
                details.append(f"ROE ดี {roe_pct:.1f}%")
        
        if rating >= 4:
            return "ดีมาก", "🟢", details
        elif rating >= 2:
            return "ดี", "🟡", details
        elif rating >= 0:
            return "ปานกลาง", "⚪", details
        else:
            return "อ่อน", "🔴", details

    def get_dividend_info(self, info):
        """ดึงข้อมูลปันผลที่ถูกต้อง"""
        div_yield = info.get('dividendYield', 0)
        if div_yield and isinstance(div_yield, (int, float)):
            if div_yield > 1:  # ถ้าเป็นเปอร์เซ็นต์แล้ว (เช่น 5 = 5%)
                div_yield = div_yield / 100
            # ถ้าน้อยกว่า 1 ถือว่าเป็นทศนิยม (เช่น 0.05 = 5%)
        
        payout = info.get('payoutRatio', 0)
        if payout and isinstance(payout, (int, float)):
            if payout > 1:
                payout = payout / 100
        
        return {
            'dividend_yield': div_yield * 100 if div_yield else 0,
            'payout_ratio': payout * 100 if payout else 0,
            'ex_date': info.get('exDividendDate', None),
            'five_year_avg': info.get('fiveYearAvgDividendYield', 0)
        }
