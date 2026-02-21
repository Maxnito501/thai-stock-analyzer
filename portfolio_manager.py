import json
import os
from datetime import datetime

class PortfolioManager:
    def __init__(self, filename="portfolio.json"):
        self.filename = filename
        self.portfolio = self.load_portfolio()
    
    def load_portfolio(self):
        """โหลดข้อมูลพอร์ต"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_portfolio(self):
        """บันทึกข้อมูลพอร์ต"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.portfolio, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_stock(self, symbol, name, shares, price, date=None):
        """เพิ่มหุ้น"""
        if symbol not in self.portfolio:
            self.portfolio[symbol] = {
                'name': name,
                'transactions': []
            }
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        self.portfolio[symbol]['transactions'].append({
            'date': date,
            'shares': shares,
            'price': price,
            'type': 'buy'
        })
        
        self.save_portfolio()
        return True
    
    def sell_stock(self, symbol, shares, price, date=None):
        """ขายหุ้น"""
        if symbol not in self.portfolio:
            return False
        
        current = self.get_current_shares(symbol)
        if shares > current:
            return False
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        self.portfolio[symbol]['transactions'].append({
            'date': date,
            'shares': -shares,
            'price': price,
            'type': 'sell'
        })
        
        self.save_portfolio()
        return True
    
    def get_current_shares(self, symbol):
        """จำนวนหุ้นปัจจุบัน"""
        if symbol not in self.portfolio:
            return 0
        
        total = 0
        for t in self.portfolio[symbol]['transactions']:
            total += t['shares']
        return max(0, total)
    
    def get_average_cost(self, symbol):
        """ต้นทุนเฉลี่ย"""
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
    
    def get_all_holdings(self):
        """รายการหุ้นทั้งหมดที่ถืออยู่"""
        holdings = []
        for symbol, data in self.portfolio.items():
            shares = self.get_current_shares(symbol)
            if shares > 0:
                holdings.append({
                    'symbol': symbol,
                    'name': data['name'],
                    'shares': shares,
                    'avg_cost': self.get_average_cost(symbol)
                })
        return holdings
    
    def get_portfolio_summary(self, current_prices):
        """สรุปพอร์ต"""
        summary = []
        total_value = 0
        total_cost_value = 0
        
        for symbol, data in self.portfolio.items():
            shares = self.get_current_shares(symbol)
            if shares > 0:
                avg_cost = self.get_average_cost(symbol)
                current_price = current_prices.get(symbol, 0)
                
                if current_price > 0:
                    current_value = shares * current_price
                    cost_value = shares * avg_cost
                    profit = current_value - cost_value
                    profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0
                    
                    summary.append({
                        'symbol': data['name'],
                        'code': symbol,
                        'shares': shares,
                        'avg_cost': round(avg_cost, 2),
                        'current_price': round(current_price, 2),
                        'current_value': round(current_value, 2),
                        'profit': round(profit, 2),
                        'profit_pct': round(profit_pct, 2)
                    })
                    
                    total_value += current_value
                    total_cost_value += cost_value
        
        return summary, total_value, total_cost_value
    
    def get_investment_advice(self, symbol, current_price, analysis):
        """ให้คำแนะนำการลงทุน"""
        shares = self.get_current_shares(symbol)
        avg_cost = self.get_average_cost(symbol)
        
        # กรณียังไม่มีหุ้น
        if shares == 0:
            if analysis['signal'] == "ซื้อ":
                return "🔵 เริ่มสะสม", f"สัญญาณซื้อ แนะนำเริ่มสะสม {analysis.get('name', symbol)}"
            elif analysis['signal'] == "ขาย":
                return "🟡 รอดู", f"สัญญาณขาย แนะนำรอดูก่อน"
            else:
                return "⚪ รอ", f"ไม่มีสัญญาณชัดเจน แนะนำรอ"
        
        # กรณีมีหุ้น
        if shares > 0:
            profit_pct = ((current_price - avg_cost) / avg_cost) * 100
            
            # ขาดทุน
            if profit_pct < -10:
                if analysis['signal'] == "ซื้อ":
                    return "🟢 ถัวเฉลี่ย", f"ขาดทุน {profit_pct:.1f}% แต่สัญญาณซื้อ แนะนำถัวเฉลี่ย"
                elif analysis['signal'] == "ขาย":
                    return "🔴 ขายตัดขาดทุน", f"ขาดทุน {profit_pct:.1f}% และสัญญาณขาย แนะนำตัดขาดทุน"
                else:
                    return "🟡 ถือรอ", f"ขาดทุน {profit_pct:.1f}% แนะนำถือรอ"
            
            # กำไร
            elif profit_pct > 15:
                if analysis['signal'] == "ขาย":
                    return "🟢 ขายทำ
