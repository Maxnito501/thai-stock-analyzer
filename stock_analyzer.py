import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import requests
import time

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
            'SIRI.BK': 'SIRI',
            'TISCO.BK': 'TISCO',
            'TRUE.BK': 'TRUE',
            'BANPU.BK': 'BANPU',
            'CHG.BK': 'CHG',
            'COM7.BK': 'COM7',
            'EA.BK': 'EA',
            'JAS.BK': 'JAS',
            'LH.BK': 'LH',
            'MINT.BK': 'MINT',
            'PTG.BK': 'PTG',
            'RATCH.BK': 'RATCH',
            'SAWAD.BK': 'SAWAD',
            'TMB.BK': 'TMB',
            'TOP.BK': 'TOP',
            'TU.BK': 'TU',
            'WHA.BK': 'WHA'
        }
        
        # หมวดหมู่หุ้น
        self.sectors = {
            'ธนาคาร': ['KBANK.BK', 'KTB.BK', 'SCB.BK', 'TISCO.BK', 'TMB.BK'],
            'พลังงาน': ['PTT.BK', 'PTTEP.BK', 'GULF.BK', 'BANPU.BK', 'EA.BK', 'TOP.BK', 'RATCH.BK'],
            'สื่อสาร': ['ADVANC.BK', 'DTAC.BK', 'INTUCH.BK', 'TRUE.BK', 'JAS.BK'],
            'ค้าปลีก': ['CPALL.BK', 'CRC.BK', 'COM7.BK'],
            'อาหาร': ['CPF.BK', 'MINT.BK', 'TU.BK'],
            'การแพทย์': ['BDMS.BK', 'BH.BK', 'CHG.BK'],
            'ขนส่ง': ['AOT.BK', 'BTS.BK'],
            'อสังหาฯ': ['SIRI.BK', 'LH.BK', 'WHA.BK'],
            'การเงิน': ['SAWAD.BK']
        }
    
    def validate_stock_symbol(self, symbol):
        """ตรวจสอบรหัสหุ้นและแปลงเป็นรูปแบบที่ถูกต้อง"""
        symbol = symbol.upper().strip()
        
        # ถ้าไม่มี .BK ต่อท้าย ให้เพิ่มให้
        if not symbol.endswith('.BK'):
            # ถ้าเป็นตัวเลข 4 หลัก (หุ้นไทย)
            if symbol.isdigit() and len(symbol) == 4:
                symbol = f"{symbol}.BK"
            # ถ้าเป็นตัวอักษร
            elif symbol.isalpha():
                symbol = f"{symbol}.BK"
        
        return symbol
    
    def search_stock(self, query):
        """ค้นหาหุ้นจากชื่อหรือรหัส"""
        query = query.upper().strip()
        results = []
        
        # ค้นจากรายการที่มี
        for symbol, name in self.thai_stocks.items():
            if query in symbol or query in name:
                results.append((symbol, name))
        
        # ถ้าไม่พบและ query น่าจะเป็นรหัสหุ้น ให้ลองใช้โดยตรง
        if not results and len(query) > 0:
            # ตรวจสอบว่าเป็นรหัสที่ถูกต้องหรือไม่
            test_symbol = self.validate_stock_symbol(query)
            try:
                stock = yf.Ticker(test_symbol)
                info = stock.info
                if info and info.get('regularMarketPrice') is not None:
                    # มีข้อมูล แสดงว่ารหัสถูกต้อง
                    display_name = info.get('shortName', test_symbol)
                    results.append((test_symbol, display_name))
                    # เพิ่มเข้าไปใน thai_stocks อัตโนมัติ
                    self.thai_stocks[test_symbol] = display_name
            except:
                pass
        
        return results
    
    def get_stock_info_from_yahoo(self, symbol):
        """ดึงข้อมูลหุ้นจาก Yahoo Finance พร้อมรายละเอียด"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # ข้อมูลเพิ่มเติม
            enhanced_info = {
                'name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector', 'ไม่ระบุ'),
                'industry': info.get('industry', 'ไม่ระบุ'),
                'website': info.get('website', 'ไม่ระบุ'),
                'market_cap': info.get('marketCap', 0),
                'pe': info.get('trailingPE', None),
                'pb': info.get('priceToBook', None),
                'roe': info.get('returnOnEquity', None),
                'roa': info.get('returnOnAssets', None),
                'dividend_yield': info.get('dividendYield', 0),
                'payout_ratio': info.get('payoutRatio', 0),
                'beta': info.get('beta', None),
                '52w_high': info.get('fiftyTwoWeekHigh', None),
                '52w_low': info.get('fiftyTwoWeekLow', None),
                'avg_volume': info.get('averageVolume', 0),
                'volume': info.get('volume', 0),
                'eps': info.get('trailingEps', None),
                'profit_margin': info.get('profitMargins', None),
                'debt_to_equity': info.get('debtToEquity', None),
                'current_ratio': info.get('currentRatio', None),
                'recommendation': info.get('recommendationKey', 'N/A'),
                'target_price': info.get('targetMeanPrice', None)
            }
            
            return enhanced_info
            
        except Exception as e:
            return None
    
    def get_stock_data(self, symbol, period='6mo'):
        """ดึงข้อมูลหุ้นจาก Yahoo Finance"""
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            info = self.get_stock_info_from_yahoo(symbol)
            return df, info
        except Exception as e:
            return None, None
    
    def calculate_indicators(self, df):
        """คำนวณตัวชี้วัดทางเทคนิคแบบครบถ้วน"""
        if df is None or df.empty:
            return None
        
        try:
            # RSI (3 ค่า)
            df['RSI_7'] = ta.momentum.RSIIndicator(df['Close'], window=7).rsi()
            df['RSI_14'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
            df['RSI_21'] = ta.momentum.RSIIndicator(df['Close'], window=21).rsi()
            
            # Moving Averages
            df['SMA_5'] = ta.trend.sma_indicator(df['Close'], window=5)
            df['SMA_10'] = ta.trend.sma_indicator(df['Close'], window=10)
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['SMA_100'] = ta.trend.sma_indicator(df['Close'], window=100)
            df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
            
            df['EMA_5'] = ta.trend.ema_indicator(df['Close'], window=5)
            df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
            df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
            df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
            
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
            df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
            df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
            
            # Volume
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            df['Volume_5_SMA'] = df['Volume'].rolling(window=5).mean()
            df['Volume_5_Ratio'] = df['Volume'] / df['Volume_5_SMA']
            
            # Support/Resistance
            df['Resistance_20'] = df['High'].rolling(window=20).max()
            df['Support_20'] = df['Low'].rolling(window=20).min()
            df['Resistance_50'] = df['High'].rolling(window=50).max()
            df['Support_50'] = df['Low'].rolling(window=50).min()
            
            # Price change
            df['Price_Change_1d'] = df['Close'].pct_change(1) * 100
            df['Price_Change_5d'] = df['Close'].pct_change(5) * 100
            df['Price_Change_10d'] = df['Close'].pct_change(10) * 100
            df['Price_Change_20d'] = df['Close'].pct_change(20) * 100
            
            # Volume change
            df['Volume_Change'] = df['Volume'].pct_change() * 100
            
            # Volatility
            df['Volatility_5'] = df['Close'].pct_change().rolling(window=5).std() * np.sqrt(252)
            df['Volatility_20'] = df['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
            
            # ADX (trend strength)
            adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'])
            df['ADX'] = adx.adx()
            df['DI_Pos'] = adx.adx_pos()
            df['DI_Neg'] = adx.adx_neg()
            
            # ATR (Average True Range)
            df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()
            df['ATR_Pct'] = (df['ATR'] / df['Close']) * 100
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
            df['Stoch_K'] = stoch.stoch()
            df['Stoch_D'] = stoch.stoch_signal()
            
            # CCI (Commodity Channel Index)
            df['CCI'] = ta.trend.CCIIndicator(df['High'], df['Low'], df['Close']).cci()
            
            # Money Flow Index
            df['MFI'] = ta.volume.MFIIndicator(df['High'], df['Low'], df['Close'], df['Volume']).money_flow_index()
            
            # OBV (On-Balance Volume)
            df['OBV'] = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
            df['OBV_Change'] = df['OBV'].pct_change() * 100
            
            # Momentum Indicators
            df['Momentum_5'] = df['Close'] - df['Close'].shift(5)
            df['Momentum_10'] = df['Close'] - df['Close'].shift(10)
            df['Momentum_5_Pct'] = (df['Momentum_5'] / df['Close'].shift(5)) * 100
            df['Momentum_10_Pct'] = (df['Momentum_10'] / df['Close'].shift(10)) * 100
            
            # Rate of Change
            df['ROC_5'] = ta.momentum.ROCIndicator(df['Close'], window=5).roc()
            df['ROC_10'] = ta.momentum.ROCIndicator(df['Close'], window=10).roc()
            df['ROC_20'] = ta.momentum.ROCIndicator(df['Close'], window=20).roc()
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            
        return df
    
    def scan_momentum_stocks(self, limit=20):
        """สแกนหาหุ้นที่มีโมเมนตัมสำหรับเล่นสั้น"""
        results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (symbol, name) in enumerate(self.thai_stocks.items()):
            status_text.text(f"กำลังสแกน {name} ({i+1}/{len(self.thai_stocks)})...")
            
            try:
                # ดึงข้อมูล 3 เดือนล่าสุด
                df, info = self.get_stock_data(symbol, period='3mo')
                
                if df is not None and not df.empty and len(df) > 20:
                    df = self.calculate_indicators(df)
                    
                    # ข้อมูลล่าสุด
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    current_price = latest['Close']
                    prev_price = prev['Close']
                    
                    # คำนวณโมเมนตัมสัญญาณ
                    momentum_score = 0
                    signals = []
                    
                    # 1. ราคาเหนือ EMA 5 (ระยะสั้น)
                    if not pd.isna(latest['EMA_5']) and current_price > latest['EMA_5']:
                        momentum_score += 1
                        signals.append("EMA_5")
                    
                    # 2. EMA 5 > EMA 10 (กระทิงระยะสั้น)
                    if not pd.isna(latest['EMA_5']) and not pd.isna(latest['EMA_10']) and latest['EMA_5'] > latest['EMA_10']:
                        momentum_score += 1
                        signals.append("EMA_CROSS")
                    
                    # 3. RSI 7 อยู่ในช่วงกระทิง (50-70)
                    if not pd.isna(latest['RSI_7']) and 50 < latest['RSI_7'] < 70:
                        momentum_score += 1
                        signals.append("RSI_7")
                    
                    # 4. MACD กระทิง
                    if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_Signal']) and latest['MACD'] > latest['MACD_Signal']:
                        momentum_score += 1
                        signals.append("MACD")
                    
                    # 5. ปริมาณสูงกว่าค่าเฉลี่ย
                    if not pd.isna(latest['Volume_Ratio']) and latest['Volume_Ratio'] > 1.2:
                        momentum_score += 1
                        signals.append("VOLUME")
                    
                    # 6. ราคาเพิ่มขึ้น 5 วัน
                    if not pd.isna(latest['Price_Change_5d']) and latest['Price_Change_5d'] > 3:
                        momentum_score += 1
                        signals.append("GAIN_5D")
                    
                    # 7. ROC 5 เป็นบวก
                    if not pd.isna(latest['ROC_5']) and latest['ROC_5'] > 1:
                        momentum_score += 1
                        signals.append("ROC")
                    
                    # 8. Stochastic ในโซนกระทิง
                    if not pd.isna(latest['Stoch_K']) and not pd.isna(latest['Stoch_D']) and latest['Stoch_K'] > latest['Stoch_D'] and latest['Stoch_K'] < 80:
                        momentum_score += 1
                        signals.append("STOCH")
                    
                    # 9. ATR สูง (ความผันผวน)
                    if not pd.isna(latest['ATR_Pct']) and latest['ATR_Pct'] > 2:
                        momentum_score += 1
                        signals.append("HIGH_ATR")
                    
                    # 10. ราคาใกล้แนวต้าน ( breakout โอกาส)
                    if not pd.isna(latest['Resistance_20']) and current_price / latest['Resistance_20'] > 0.95:
                        momentum_score += 1
                        signals.append("NEAR_RESISTANCE")
                    
                    # คำนวณเปอร์เซ็นต์โมเมนตัม
                    momentum_pct = (momentum_score / 10) * 100
                    
                    # เฉพาะหุ้นที่มีโมเมนตัมสูง (> 50%)
                    if momentum_pct >= 50:
                        # หาสัญญาณเพิ่มเติม
                        if momentum_pct >= 80:
                            signal_type = "แข็งแกร่ง"
                            signal_emoji = "🟢"
                        elif momentum_pct >= 60:
                            signal_type = "ดี"
                            signal_emoji = "🟡"
                        else:
                            signal_type = "ปานกลาง"
                            signal_emoji = "⚪"
                        
                        # ราคาเป้าหมายระยะสั้น
                        target_price = current_price * 1.05  # +5%
                        stop_loss = current_price * 0.97  # -3%
                        
                        # คำนวณระยะเวลาที่เหมาะถือ
                        if latest['ATR_Pct'] > 3:
                            holding_period = "1-3 วัน"
                        elif latest['ATR_Pct'] > 2:
                            holding_period = "3-7 วัน"
                        else:
                            holding_period = "1-2 สัปดาห์"
                        
                        results.append({
                            'symbol': name,
                            'code': symbol,
                            'price': current_price,
                            'change_1d': latest.get('Price_Change_1d', 0),
                            'change_5d': latest.get('Price_Change_5d', 0),
                            'volume_ratio': latest.get('Volume_Ratio', 1),
                            'rsi': latest.get('RSI_14', 50),
                            'momentum_score': momentum_score,
                            'momentum_pct': momentum_pct,
                            'signal_type': signal_type,
                            'signal_emoji': signal_emoji,
                            'signals': signals,
                            'target': target_price,
                            'stop_loss': stop_loss,
                            'holding_period': holding_period,
                            'atr_pct': latest.get('ATR_Pct', 0)
                        })
            
            except Exception as e:
                pass
            
            # อัปเดต progress bar
            progress_bar.progress((i + 1) / len(self.thai_stocks))
        
        status_text.text(f"สแกนเสร็จสิ้น พบ {len(results)} หุ้น")
        progress_bar.empty()
        
        # เรียงตามโมเมนตัมสูงสุด
        results.sort(key=lambda x: x['momentum_pct'], reverse=True)
        
        return results[:limit]
    
    def scan_breakout_stocks(self, limit=20):
        """สแกนหาหุ้นที่กำลังจะ breakout"""
        results = []
        
        for symbol, name in self.thai_stocks.items():
            try:
                df, info = self.get_stock_data(symbol, period='3mo')
                
                if df is not None and not df.empty and len(df) > 50:
                    df = self.calculate_indicators(df)
                    
                    latest = df.iloc[-1]
                    current_price = latest['Close']
                    
                    # หาแนวต้านสำคัญ
                    resistance_50 = latest['Resistance_50'] if not pd.isna(latest['Resistance_50']) else 0
                    resistance_20 = latest['Resistance_20'] if not pd.isna(latest['Resistance_20']) else 0
                    
                    if resistance_20 > 0 and resistance_50 > 0:
                        # ใกล้แนวต้าน 50 วัน
                        dist_to_resistance_50 = ((resistance_50 - current_price) / current_price) * 100
                        
                        # ใกล้แนวต้าน 20 วัน
                        dist_to_resistance_20 = ((resistance_20 - current_price) / current_price) * 100
                        
                        # ปริมาณเพิ่มขึ้น
                        volume_surge = not pd.isna(latest['Volume_Ratio']) and latest['Volume_Ratio'] > 1.3
                        
                        # RSI ไม่ overbought
                        rsi_ok = not pd.isna(latest['RSI_14']) and latest['RSI_14'] < 65
                        
                        # เงื่อนไข breakout
                        if 0 < dist_to_resistance_20 < 3 and volume_surge and rsi_ok:
                            breakout_type = "แนวต้านระยะสั้น"
                            probability = "สูง" if latest['Volume_Ratio'] > 1.5 else "ปานกลาง"
                            
                            results.append({
                                'symbol': name,
                                'code': symbol,
                                'price': current_price,
                                'resistance_20': resistance_20,
                                'dist_to_resistance': dist_to_resistance_20,
                                'volume_ratio': latest['Volume_Ratio'],
                                'rsi': latest['RSI_14'],
                                'breakout_type': breakout_type,
                                'probability': probability,
                                'target_1': resistance_20 * 1.03,
                                'target_2': resistance_20 * 1.05,
                                'stop_loss': current_price * 0.97
                            })
                        
                        elif 0 < dist_to_resistance_50 < 5 and volume_surge:
                            breakout_type = "แนวต้านหลัก"
                            probability = "ปานกลาง"
                            
                            results.append({
                                'symbol': name,
                                'code': symbol,
                                'price': current_price,
                                'resistance_50': resistance_50,
                                'dist_to_resistance': dist_to_resistance_50,
                                'volume_ratio': latest['Volume_Ratio'],
                                'rsi': latest['RSI_14'],
                                'breakout_type': breakout_type,
                                'probability': probability,
                                'target_1': resistance_50 * 1.05,
                                'target_2': resistance_50 * 1.08,
                                'stop_loss': current_price * 0.95
                            })
            
            except Exception as e:
                pass
        
        # เรียงตามระยะห่างจากแนวต้าน
        results.sort(key=lambda x: x['dist_to_resistance'])
        
        return results[:limit]
    
    def scan_oversold_rebound(self, limit=20):
        """สแกนหาหุ้นที่ oversold และมีโอกาสรีบาวด์"""
        results = []
        
        for symbol, name in self.thai_stocks.items():
            try:
                df, info = self.get_stock_data(symbol, period='3mo')
                
                if df is not None and not df.empty and len(df) > 20:
                    df = self.calculate_indicators(df)
                    
                    latest = df.iloc[-1]
                    current_price = latest['Close']
                    
                    # เงื่อนไข oversold
                    rsi_oversold = not pd.isna(latest['RSI_14']) and latest['RSI_14'] < 35
                    rsi_7_oversold = not pd.isna(latest['RSI_7']) and latest['RSI_7'] < 30
                    
                    # ราคาใกล้แนวรับ
                    support_20 = latest['Support_20'] if not pd.isna(latest['Support_20']) else 0
                    near_support = False
                    if support_20 > 0:
                        dist_to_support = ((current_price - support_20) / support_20) * 100
                        near_support = 0 < dist_to_support < 3
                    
                    # MACD เริ่มมีสัญญาณซื้อ
                    macd_bullish = False
                    if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_Signal']):
                        prev = df.iloc[-2]
                        macd_bullish = latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']
                    
                    if (rsi_oversold or rsi_7_oversold) and (near_support or macd_bullish):
                        rebound_score = 0
                        if rsi_7_oversold:
                            rebound_score += 2
                        if near_support:
                            rebound_score += 2
                        if macd_bullish:
                            rebound_score += 1
                        if not pd.isna(latest['Volume_Ratio']) and latest['Volume_Ratio'] > 1:
                            rebound_score += 1
                        
                        probability = "สูง" if rebound_score >= 4 else "ปานกลาง" if rebound_score >= 3 else "ต่ำ"
                        
                        results.append({
                            'symbol': name,
                            'code': symbol,
                            'price': current_price,
                            'rsi_14': latest['RSI_14'],
                            'rsi_7': latest['RSI_7'],
                            'support': support_20,
                            'dist_to_support': dist_to_support if support_20 > 0 else 999,
                            'macd_signal': "bullish" if macd_bullish else "neutral",
                            'rebound_score': rebound_score,
                            'probability': probability,
                            'target_1': current_price * 1.03,
                            'target_2': current_price * 1.05,
                            'stop_loss': current_price * 0.95
                        })
            
            except Exception as e:
                pass
        
        # เรียงตามคะแนนรีบาวด์
        results.sort(key=lambda x: x['rebound_score'], reverse=True)
        
        return results[:limit]
    
    def get_trend_analysis(self, df):
        """วิเคราะห์แนวโน้มแบบละเอียด"""
        if df is None or df.empty:
            return "ไม่สามารถวิเคราะห์ได้", "⚪"
        
        try:
            latest = df.iloc[-1]
            
            # ตรวจสอบ Moving Averages
            ma_score = 0
            if not pd.isna(latest['SMA_20']) and latest['Close'] > latest['SMA_20']:
                ma_score += 1
            if not pd.isna(latest['SMA_50']) and latest['Close'] > latest['SMA_50']:
                ma_score += 1
            if not pd.isna(latest['SMA_200']) and latest['Close'] > latest['SMA_200']:
                ma_score += 1
            if not pd.isna(latest['SMA_20']) and not pd.isna(latest['SMA_50']) and latest['SMA_20'] > latest['SMA_50']:
                ma_score += 1
            if not pd.isna(latest['SMA_50']) and not pd.isna(latest['SMA_200']) and latest['SMA_50'] > latest['SMA_200']:
                ma_score += 1
            
            # ตรวจสอบ ADX (trend strength)
            adx_strength = ""
            if not pd.isna(latest['ADX']):
                if latest['ADX'] > 40:
                    adx_strength = "แข็งแกร่ง"
                elif latest['ADX'] > 25:
                    adx_strength = "ปานกลาง"
                else:
                    adx_strength = "อ่อน"
            
            # สรุปแนวโน้ม
            if ma_score >= 4 and not pd.isna(latest['ADX']) and latest['ADX'] > 25:
                trend = f"ขาขึ้น {adx_strength}"
                emoji = "🟢"
            elif ma_score <= 1 and not pd.isna(latest['ADX']) and latest['ADX'] > 25:
                trend = f"ขาลง {adx_strength}"
                emoji = "🔴"
            elif ma_score >= 3:
                trend = "ขาขึ้นอ่อน"
                emoji = "🟡"
            elif ma_score <= 2:
                trend = "ขาลงอ่อน"
                emoji = "🟡"
            else:
                trend = "Sideways"
                emoji = "⚪"
            
            return trend, emoji
            
        except:
            return "ไม่สามารถวิเคราะห์ได้", "⚪"
    
    def get_rsi_analysis(self, df):
        """วิเคราะห์ RSI แบบละเอียด"""
        if df is None or df.empty:
            return {}
        
        latest = df.iloc[-1]
        analysis = {}
        
        for period in [7, 14, 21]:
            col = f'RSI_{period}'
            if col in df and not pd.isna(latest[col]):
                rsi = latest[col]
                
                if rsi < 30:
                    signal = "ซื้อ"
                    emoji = "🟢"
                    desc = "oversold รุนแรง"
                elif rsi < 40:
                    signal = "เริ่มซื้อ"
                    emoji = "🟡"
                    desc = "oversold เล็กน้อย"
                elif rsi > 70:
                    signal = "ขาย"
                    emoji = "🔴"
                    desc = "overbought รุนแรง"
                elif rsi > 60:
                    signal = "เริ่มขาย"
                    emoji = "🟡"
                    desc = "overbought เล็กน้อย"
                else:
                    signal = "neutral"
                    emoji = "⚪"
                    desc = "ปกติ"
                
                analysis[f'RSI_{period}'] = {
                    'value': rsi,
                    'signal': signal,
                    'emoji': emoji,
                    'desc': desc
                }
        
        return analysis
    
    def get_macd_analysis(self, df):
        """วิเคราะห์ MACD แบบละเอียด"""
        if df is None or df.empty:
            return {}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        analysis = {}
        
        if all(col in df for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
            macd = latest['MACD']
            signal = latest['MACD_Signal']
            hist = latest['MACD_Histogram']
            prev_hist = prev['MACD_Histogram'] if 'MACD_Histogram' in prev else 0
            
            # ตรวจสอบสัญญาณ
            if not pd.isna(macd) and not pd.isna(signal):
                if macd > signal and hist > 0 and hist > prev_hist:
                    signal_text = " bullish แรง"
                    emoji = "🟢"
                elif macd > signal and hist > 0:
                    signal_text = " bullish"
                    emoji = "🟡"
                elif macd < signal and hist < 0 and hist < prev_hist:
                    signal_text = " bearish แรง"
                    emoji = "🔴"
                elif macd < signal and hist < 0:
                    signal_text = " bearish"
                    emoji = "🟡"
                elif macd > signal:
                    signal_text = "เริ่ม bullish"
                    emoji = "🟡"
                else:
                    signal_text = "เริ่ม bearish"
                    emoji = "🟡"
                
                analysis['MACD'] = {
                    'value': f"{macd:.2f}",
                    'signal': signal_text,
                    'emoji': emoji
                }
        
        return analysis
    
    def get_volume_analysis(self, df):
        """วิเคราะห์ปริมาณการซื้อขาย"""
        if df is None or df.empty:
            return {}
        
        latest = df.iloc[-1]
        analysis = {}
        
        if 'Volume_Ratio' in df and not pd.isna(latest['Volume_Ratio']):
            ratio = latest['Volume_Ratio']
            
            if ratio > 2:
                signal = "สูงมาก"
                emoji = "🔴"
                desc = "มีการซื้อขายหนาแน่น"
            elif ratio > 1.5:
                signal = "สูง"
                emoji = "🟡"
                desc = "มีการซื้อขายสูงกว่าปกติ"
            elif ratio > 1.2:
                signal = "สูงปานกลาง"
                emoji = "🟡"
                desc = "มีความสนใจเพิ่มขึ้น"
            elif ratio < 0.5:
                signal = "ต่ำมาก"
                emoji = "🔴"
                desc = "เงียบเหงา"
            elif ratio < 0.8:
                signal = "ต่ำ"
                emoji = "🟡"
                desc = "น้อยกว่าปกติ"
            else:
                signal = "ปกติ"
                emoji = "⚪"
                desc = "ปริมาณปกติ"
            
            analysis['Volume'] = {
                'value': f"{ratio:.2f}x",
                'signal': signal,
                'emoji': emoji,
                'desc': desc
            }
        
        return analysis
    
    def get_support_resistance(self, df):
        """วิเคราะห์แนวรับแนวต้าน"""
        if df is None or df.empty:
            return {}
        
        latest = df.iloc[-1]
        price = latest['Close']
        
        analysis = {}
        
        if 'Support_20' in df and 'Resistance_20' in df:
            support = latest['Support_20']
            resistance = latest['Resistance_20']
            
            if not pd.isna(support) and not pd.isna(resistance) and support > 0 and price > 0:
                # ระยะห่างจากแนวรับ/ต้าน
                dist_to_support = ((price - support) / support) * 100
                dist_to_resistance = ((resistance - price) / price) * 100
                
                analysis['Support_20'] = {
                    'value': f"฿{support:.2f}",
                    'distance': f"{dist_to_support:.1f}%",
                    'signal': "ใกล้แนวรับ" if dist_to_support < 3 else "ไกลแนวรับ"
                }
                
                analysis['Resistance_20'] = {
                    'value': f"฿{resistance:.2f}",
                    'distance': f"{dist_to_resistance:.1f}%",
                    'signal': "ใกล้แนวต้าน" if dist_to_resistance < 3 else "ไกลแนวต้าน"
                }
        
        return analysis
    
    def get_dividend_info(self, info):
        """ดึงข้อมูลปันผลที่ถูกต้อง"""
        try:
            # ถ้า info เป็น None หรือไม่มีข้อมูล
            if info is None or not isinstance(info, dict):
                return {
                    'dividend_yield': 0,
                    'payout_ratio': 0,
                    'has_dividend': False
                }
            
            div_yield = info.get('
