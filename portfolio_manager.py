import json
import os
from datetime import datetime

class PortfolioManager:
    def __init__(self, filename="portfolio.json"):
        self.filename = filename
        self.portfolio = self.load_portfolio()
    
    def load_portfolio(self):
        """โหลดข้อมูลพอร์ตการลงทุน"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_portfolio(self):
        """บันทึกข้อมูลพอร์ต"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.portfolio, f, ensure_ascii=False, indent=2)
    
    def add_stock(self, symbol, name, shares, buy_price, buy_date=None):
        """เพิ่มหุ้นในพอร์ต"""
        if symbol not in self.portfolio:
            self.portfolio[symbol] = {
                'name': name,
                'transactions': []
            }
        
        if buy_date is None:
            buy_date = datetime.now().strftime('%Y-%m-%d')
        
        self.portfolio[symbol]['transactions'].append({
            'date': buy_date,
            'shares': shares,
            'price': buy_price,
            'type': 'buy'
        })
        
        self.save_portfolio()
    
    def sell_stock(self, symbol, shares, sell_price, sell_date=None):
        """ขายหุ้น"""
        if symbol not in self.portfolio:
            return False
        
        total_shares = self.get_current_shares(symbol)
        if shares > total_shares:
            return False
        
        if sell_date is None:
            sell_date = datetime.now().strftime('%Y-%m-%d')
        
        self.portfolio[symbol]['transactions'].append({
            'date': sell_date,
            'shares': -shares,
            'price': sell_price,
            'type': 'sell'
        })
        
        self.save_portfolio()
        return True
    
    def get_current_shares(self, symbol):
        """คำนวณจำนวนหุ้นปัจจุบัน"""
        if symbol not in self.portfolio:
            return 0
        
        total = 0
        for t in self.portfolio[symbol]['transactions']:
            total += t['shares']
        return total
    
    def get_average_cost(self, symbol):
        """คำนวณต้นทุนเฉลี่ย"""
        if symbol not in self.portfolio:
            return 0
        
        total_cost = 0
        total_shares = 0
        
        for t in self.portfolio[symbol]['transactions']:
            if t['type'] == 'buy':
                total_cost += t['shares'] * t['price']
                total_shares += t['shares']
        
        if total_shares == 0:
            return 0
        
        return total_cost / total_shares
    
    def get_portfolio_summary(self, current_prices):
        """สรุปพอร์ตการลงทุน"""
        summary = []
        total_value = 0
        total_cost = 0
        
        for symbol, data in self.portfolio.items():
            shares = self.get_current_shares(symbol)
            if shares > 0:
                avg_cost = self.get_average_cost(symbol)
                current_price = current_prices.get(symbol, 0)
                current_value = shares * current_price
                total_cost_value = shares * avg_cost
                
                profit_loss = current_value - total_cost_value
                profit_loss_pct = (profit_loss / total_cost_value * 100) if total_cost_value > 0 else 0
                
                summary.append({
                    'symbol': data['name'],
                    'shares': shares,
                    'avg_cost': avg_cost,
                    'current_price': current_price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct
                })
                
                total_value += current_value
                total_cost += total_cost_value
        
        return summary, total_value, total_cost
    
    def get_investment_advice(self, symbol, current_price, analysis):
        """ให้คำแนะนำการลงทุนตามสถานการณ์"""
        shares = self.get_current_shares(symbol)
        avg_cost = self.get_average_cost(symbol)
        
        # กรณียังไม่มีหุ้น
        if shares == 0:
            if analysis['overall_signal'] == "ซื้อ":
                return "🔵 แนะนำ: เริ่มสะสม", "ควรเข้าซื้อครั้งแรก เนื่องจากสัญญาณทางเทคนิคบวก"
            elif analysis['overall_signal'] == "ขาย":
                return "🟡 แนะนำ: รอดู", "ยังไม่ควรเข้าซื้อ รอสัญญาณซื้อก่อน"
            else:
                return "⚪ แนะนำ: รอ", "รอดูสถานการณ์ ยังไม่มีสัญญาณชัดเจน"
        
        # กรณีมีหุ้นอยู่แล้ว
        if shares > 0:
            profit_loss = ((current_price - avg_cost) / avg_cost) * 100
            
            # ติดลบ (ราคาต่ำกว่าทุน)
            if profit_loss < -10:
                if analysis['trend'] == "ขาลง" or analysis['overall_signal'] == "ขาย":
                    return "🔴 แนะนำ: ขายตัดขาดทุน", f"ขาดทุน {profit_loss:.1f}% แนวโน้มยังขาลง แนะนำตัดขาดทุน"
                elif analysis['overall_signal'] == "ซื้อ":
                    return "🟢 แนะนำ: ถัวเฉลี่ย", f"ขาดทุน {profit_loss:.1f}% แต่สัญญาณซื้อ แนะนำถัวเฉลี่ยลดต้นทุน"
                else:
                    return "🟡 แนะนำ: ถือรอ", f"ขาดทุน {profit_loss:.1f}% ยังไม่มีสัญญาณชัดเจน แนะนำถือรอ"
            
            # กำไร (ราคาสูงกว่าทุน)
            elif profit_loss > 15:
                if analysis['trend'] == "ขาลง" or analysis['overall_signal'] == "ขาย":
                    return "🟢 แนะนำ: ขายทำกำไร", f"กำไร {profit_loss:.1f}% สัญญาณขาย แนะนำขายทำกำไรบางส่วน"
                elif analysis['overall_signal'] == "ซื้อ" and analysis['trend'] == "ขาขึ้น":
                    return "💰 แนะนำ: ถือต่อ", f"กำไร {profit_loss:.1f}% แนวโน้มยังดี แนะนำถือต่อ"
                else:
                    return "🟡 แนะนำ: ขายบางส่วน", f"กำไร {profit_loss:.1f}% แต่สัญญาณเริ่มเปลี่ยน แนะนำขายบางส่วน"
            
            # ใกล้เคียงทุน
            else:
                if analysis['overall_signal'] == "ซื้อ":
                    return "🟢 แนะนำ: ซื้อเพิ่ม", f"ใกล้เคียงทุน ({profit_loss:.1f}%) และสัญญาณซื้อ แนะนำซื้อเพิ่ม"
                elif analysis['overall_signal'] == "ขาย":
                    return "🔴 แนะนำ: ขาย", f"ใกล้เคียงทุน ({profit_loss:.1f}%) แต่สัญญาณขาย แนะนำขายออก"
                elif analysis['dividend_info']['dividend_yield'] > 4:
                    return "💵 แนะนำ: ถือรอปันผล", f"อัตราปันผลสูง {analysis['dividend_info']['dividend_yield']:.1f}% แนะนำถือรอปันผล"
                else:
                    return "⚪ แนะนำ: รอดู", f"ใกล้เคียงทุน ({profit_loss:.1f}%) รอดูสัญญาณถัดไป"
