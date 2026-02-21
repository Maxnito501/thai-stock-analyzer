import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import requests

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
            'TRUE.BK': 'TRUE'
        }
        
        # หมวดหมู่หุ้น
        self.sectors = {
            'ธนาคาร': ['KBANK.BK', 'KTB.BK', 'SCB.BK', 'TISCO.BK'],
            'พลังงาน': ['PTT.BK', 'PTTEP.BK', 'GULF.BK'],
            'สื่อสาร': ['ADVANC.BK', 'DTAC.BK', 'INTUCH.BK', 'TRUE.BK'],
            'ค้าปลีก': ['CPALL.BK', 'CRC.BK'],
            'อาหาร': ['CPF.BK'],
            'การแพทย์': ['BDMS.BK', 'BH.BK'],
            'ขนส่ง': ['AOT.BK', 'BTS.BK'],
            'ปิโตรเคมี': ['IVL.BK'],
            'ก่อสร้าง': ['SCC.BK'],
            'อสังหาฯ': ['SIRI.BK']
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
            df['SMA_10'] = ta.trend.sma_indicator(df['Close'], window=10)
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['SMA_100'] = ta.trend.sma_indicator(df['Close'], window=100)
            df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
            
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
            
            # Volume
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Support/Resistance
            df['Resistance'] = df['High'].rolling(window=20).max()
            df['Support'] = df['Low'].rolling(window=20).min()
            
            # Price change
            df['Price_Change'] = df['Close'].pct_change() * 100
            df['Volume_Change'] = df['Volume'].pct_change() * 100
            
            # Volatility
            df['Volatility'] = df['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
            
            # ADX (trend strength)
            adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'])
            df['ADX'] = adx.adx()
            df['DI_Pos'] = adx.adx_pos()
            df['DI_Neg'] = adx.adx_neg()
            
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
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            
        return df
    
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
        
        if 'Support' in df and 'Resistance' in df:
            support = latest['Support']
            resistance = latest['Resistance']
            
            if not pd.isna(support) and not pd.isna(resistance) and support > 0 and price > 0:
                # ระยะห่างจากแนวรับ/ต้าน
                dist_to_support = ((price - support) / support) * 100
                dist_to_resistance = ((resistance - price) / price) * 100
                
                analysis['Support'] = {
                    'value': f"฿{support:.2f}",
                    'distance': f"{dist_to_support:.1f}%",
                    'signal': "ใกล้แนวรับ" if dist_to_support < 3 else "ไกลแนวรับ"
                }
                
                analysis['Resistance'] = {
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
            
            div_yield = info.get('dividend_yield', 0)
            
            # ถ้าไม่มีข้อมูล dividend_yield ลองดูจาก key อื่น
            if div_yield == 0:
                div_yield = info.get('dividendYield', 0)
            
            # ถ้าไม่มีข้อมูล
            if div_yield is None or div_yield == 0:
                # ลองดูจากห้าปีย้อนหลัง
                div_5y = info.get('fiveYearAvgDividendYield', 0)
                if div_5y and div_5y > 0:
                    if div_5y > 1:
                        div_percent = div_5y
                    else:
                        div_percent = div_5y * 100
                    return {
                        'dividend_yield': round(div_percent, 2),
                        'payout_ratio': 0,
                        'has_dividend': True
                    }
                
                return {
                    'dividend_yield': 0,
                    'payout_ratio': 0,
                    'has_dividend': False
                }
            
            # Yahoo Finance ส่งค่ามาเป็นทศนิยม (0.05 = 5%)
            if isinstance(div_yield, (int, float)):
                if div_yield > 1:  # ถ้าเป็นเปอร์เซ็นต์แล้ว (ผิดปกติ)
                    # ตรวจสอบว่ามันเป็นเปอร์เซ็นต์ที่มากเกินไปหรือไม่
                    if div_yield > 100:  # เช่น 674% 
                        # ลองหาร 100 เผื่อว่ามันคูณมาแล้ว
                        div_percent = div_yield / 100
                        if div_percent > 100:  # ยังเกินอยู่
                            div_percent = 0
                    else:
                        div_percent = div_yield
                else:
                    div_percent = div_yield * 100
            else:
                div_percent = 0
            
            # ตรวจสอบค่าที่เป็นไปไม่ได้ (เกิน 30% ปกติหุ้นไม่ปันผลสูงขนาดนั้น)
            if div_percent > 30:
                # ถ้าเกิน 30% แสดงว่ามาจากการคำนวณผิด ให้ลองคำนวณใหม่
                if isinstance(div_yield, (int, float)) and div_yield < 1:
                    div_percent = div_yield * 100
                else:
                    div_percent = 0
            
            # Payout ratio
            payout = info.get('payout_ratio', 0)
            if payout == 0:
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
        except Exception as e:
            print(f"Error in get_dividend_info: {e}")
            return {
                'dividend_yield': 0,
                'payout_ratio': 0,
                'has_dividend': False
            }
    
    def get_fundamental_rating(self, info):
        """ให้คะแนนปัจจัยพื้นฐานแบบละเอียด"""
        if not info:
            return 0, "ไม่มีข้อมูล", "⚪", []
        
        score = 0
        max_score = 10
        details = []
        
        # P/E Ratio (0-2 คะแนน)
        pe = info.get('pe')
        if pe and pe > 0:
            if pe < 10:
                score += 2
                details.append("✅ P/E ต่ำมาก (ถูก)")
            elif pe < 15:
                score += 1.5
                details.append("✅ P/E เหมาะสม")
            elif pe < 20:
                score += 1
                details.append("⚪ P/E ปานกลาง")
            elif pe < 30:
                score += 0.5
                details.append("⚠️ P/E ค่อนข้างสูง")
            else:
                details.append("❌ P/E สูงมาก (แพง)")
        else:
            details.append("❌ ไม่มีข้อมูล P/E")
        
        # P/B Ratio (0-2 คะแนน)
        pb = info.get('pb')
        if pb and pb > 0:
            if pb < 1:
                score += 2
                details.append("✅ P/B ต่ำกว่า 1 (ถูกมาก)")
            elif pb < 1.5:
                score += 1.5
                details.append("✅ P/B เหมาะสม")
            elif pb < 2:
                score += 1
                details.append("⚪ P/B ปานกลาง")
            elif pb < 3:
                score += 0.5
                details.append("⚠️ P/B ค่อนข้างสูง")
            else:
                details.append("❌ P/B สูงมาก")
        else:
            details.append("❌ ไม่มีข้อมูล P/B")
        
        # Dividend Yield (0-2 คะแนน)
        div_info = self.get_dividend_info(info)
        div = div_info['dividend_yield']
        if div and div > 0:
            if div > 5:
                score += 2
                details.append(f"✅ ปันผลสูง {div:.1f}%")
            elif div > 3:
                score += 1.5
                details.append(f"✅ ปันผลดี {div:.1f}%")
            elif div > 1:
                score += 1
                details.append(f"⚪ ปันผล {div:.1f}%")
            else:
                score += 0.5
                details.append(f"⚠️ ปันผลต่ำ {div:.1f}%")
        else:
            details.append("❌ ไม่ปันผล")
        
        # ROE (0-1.5 คะแนน)
        roe = info.get('roe')
        if roe and roe > 0:
            roe_pct = roe * 100
            if roe_pct > 20:
                score += 1.5
                details.append(f"✅ ROE สูง {roe_pct:.1f}%")
            elif roe_pct > 15:
                score += 1
                details.append(f"✅ ROE ดี {roe_pct:.1f}%")
            elif roe_pct > 10:
                score += 0.5
                details.append(f"⚪ ROE ปานกลาง {roe_pct:.1f}%")
            else:
                details.append(f"⚠️ ROE ต่ำ {roe_pct:.1f}%")
        
        # Profit Margin (0-1.5 คะแนน)
        margin = info.get('profit_margin')
        if margin and margin > 0:
            margin_pct = margin * 100
            if margin_pct > 20:
                score += 1.5
                details.append(f"✅ อัตรากำไรสูง {margin_pct:.1f}%")
            elif margin_pct > 15:
                score += 1
                details.append(f"✅ อัตรากำไรดี {margin_pct:.1f}%")
            elif margin_pct > 10:
                score += 0.5
                details.append(f"⚪ อัตรากำไรปานกลาง {margin_pct:.1f}%")
            else:
                details.append(f"⚠️ อัตรากำไรต่ำ {margin_pct:.1f}%")
        
        # Debt to Equity (0-1 คะแนน)
        debt = info.get('debt_to_equity')
        if debt and debt > 0:
            if debt < 0.5:
                score += 1
                details.append(f"✅ หนี้ต่ำ {debt:.2f}")
            elif debt < 1:
                score += 0.5
                details.append(f"⚪ หนี้ปานกลาง {debt:.2f}")
            else:
                details.append(f"⚠️ หนี้สูง {debt:.2f}")
        
        # คำนวณคะแนน
        final_score = (score / max_score) * 100
        
        if final_score >= 80:
            rating = "ดีมาก"
            emoji = "🟢"
        elif final_score >= 60:
            rating = "ดี"
            emoji = "🟡"
        elif final_score >= 40:
            rating = "ปานกลาง"
            emoji = "⚪"
        else:
            rating = "อ่อน"
            emoji = "🔴"
        
        return final_score, rating, emoji, details
    
    def compare_with_sector(self, symbol, info):
        """เปรียบเทียบกับหุ้นในหมวดเดียวกัน"""
        if not info:
            return {}
        
        sector = info.get('sector', '')
        if not sector:
            return {}
        
        comparison = {
            'pe_vs_sector': 'N/A',
            'pb_vs_sector': 'N/A',
            'div_vs_sector': 'N/A'
        }
        
        # หาค่าเฉลี่ยของหมวด
        sector_pe = []
        sector_pb = []
        sector_div = []
        
        # ถ้ามีการกำหนดหมวดใน self.sectors
        for sector_name, symbols in self.sectors.items():
            if sector_name in sector or sector in sector_name:
                for sym in symbols:
                    try:
                        stock = yf.Ticker(sym)
                        s_info = stock.info
                        if s_info.get('trailingPE'):
                            sector_pe.append(s_info.get('trailingPE'))
                        if s_info.get('priceToBook'):
                            sector_pb.append(s_info.get('priceToBook'))
                        if s_info.get('dividendYield'):
                            div = s_info.get('dividendYield')
                            if div and div < 1:
                                sector_div.append(div * 100)
                            else:
                                sector_div.append(div)
                    except:
                        pass
                break
        
        if sector_pe and info.get('pe'):
            avg_pe = sum(sector_pe) / len(sector_pe)
            pe_ratio = info.get('pe') / avg_pe
            if pe_ratio < 0.8:
                comparison['pe_vs_sector'] = "ต่ำกว่าหมวด (ถูก)"
            elif pe_ratio > 1.2:
                comparison['pe_vs_sector'] = "สูงกว่าหมวด (แพง)"
            else:
                comparison['pe_vs_sector'] = "ใกล้เคียงหมวด"
        
        return comparison
