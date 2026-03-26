import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import time
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stock_analyzer import StockAnalyzer

st.set_page_config(page_title="DCA Plan", page_icon="📊", layout="wide")

st.title("📊 DCA / EDCA Plan")
st.markdown("""
วางแผนการลงทุนแบบ DCA (Dollar Cost Averaging) และ EDCA (Enhanced DCA)  
- **DCA**: ลงทุนเท่ากันทุกเดือน  
- **EDCA**: ลงทุนเพิ่มเมื่อราคาลง (RSI < 30 หรือราคาต่ำกว่า EMA200)
""")

# ============================================
# โหลด StockAnalyzer
# ============================================
@st.cache_resource
def get_analyzer():
    return StockAnalyzer()

analyzer = get_analyzer()

# ============================================
# ดึงรายชื่อหุ้น
# ============================================
stock_list = list(analyzer.thai_stocks.keys())
stock_names = {k: v for k, v in analyzer.thai_stocks.items()}

# ตัวเลือกหุ้น
col1, col2 = st.columns(2)

with col1:
    selected_code = st.selectbox(
        "เลือกหุ้น",
        stock_list,
        format_func=lambda x: f"{stock_names.get(x, x)} ({x})"
    )

with col2:
    strategy = st.selectbox("กลยุทธ์", ["DCA (ลงทุนสม่ำเสมอ)", "EDCA (ซื้อเมื่อย่อ)"])

# ============================================
# ข้อมูลการลงทุน
# ============================================
st.subheader("💸 ข้อมูลการลงทุน")

col1, col2, col3 = st.columns(3)

with col1:
    # ใช้ get_current_price (เพิ่มใน stock_analyzer.py)
    current_price = analyzer.get_current_price(selected_code) if hasattr(analyzer, 'get_current_price') else None
    st.metric("ราคาปัจจุบัน", f"฿{current_price:.2f}" if current_price else "N/A")

with col2:
    initial_investment = st.number_input("เงินลงทุนเริ่มต้น (บาท)", min_value=0, value=10000, step=1000)

with col3:
    monthly_investment = st.number_input("เงินลงทุนต่อเดือน (บาท)", min_value=0, value=5000, step=500)

# ============================================
# ข้อมูลพอร์ตปัจจุบัน
# ============================================
st.subheader("📈 พอร์ตปัจจุบัน")

col1, col2 = st.columns(2)

with col1:
    current_shares = st.number_input("จำนวนหุ้นที่ถืออยู่", min_value=0, value=0, step=100)

with col2:
    avg_cost = st.number_input("ต้นทุนเฉลี่ย (บาท/หุ้น)", min_value=0.0, value=0.0, step=0.5)

# ============================================
# ดึงข้อมูลราคาย้อนหลัง (ใช้ cache)
# ============================================
@st.cache_data(ttl=3600)
def get_historical_data(symbol):
    """ดึงข้อมูลราคาย้อนหลัง (cache 1 ชม.)"""
    try:
        time.sleep(random.uniform(0.5, 1.0))  # หน่วงเวลา ป้องกันบล็อก
        df, info = analyzer.get_stock_data(symbol, period="1y")
        if df is not None and not df.empty:
            # คำนวณ EMA200 และ RSI
            df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            return df
    except Exception as e:
        st.warning(f"ไม่สามารถดึงข้อมูล {symbol} ได้: {e}")
    return None

df = get_historical_data(selected_code)

if df is not None and not df.empty:
    # ============================================
    # จำลอง DCA / EDCA
    # ============================================
    st.subheader("📊 ผลการจำลองการลงทุน")
    
    # กำหนดช่วงเวลา 12 เดือน
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    simulation_results = []
    total_shares = current_shares
    total_invested = current_shares * avg_cost if avg_cost > 0 else 0
    
    for i, date in enumerate(monthly_dates):
        # หาราคา ณ วันที่ใกล้เคียง
        closest_idx = df.index.get_indexer([date], method='nearest')[0]
        price = df['Close'].iloc[closest_idx]
        
        if i == 0:
            invest = initial_investment
        else:
            invest = monthly_investment
        
        # EDCA: ซื้อเพิ่มเมื่อราคาลง
        note = ""
        if strategy == "EDCA (ซื้อเมื่อย่อ)":
            rsi = df['RSI'].iloc[closest_idx]
            price_below_ema = price < df['EMA200'].iloc[closest_idx]
            
            if not pd.isna(rsi) and (rsi < 30 or price_below_ema):
                invest = invest * 1.5
                note = "✨ EDCA (ซื้อเพิ่ม)"
            else:
                note = "DCA ปกติ"
        else:
            note = "DCA ปกติ"
        
        shares_bought = invest / price if price > 0 else 0
        total_shares += shares_bought
        total_invested += invest
        
        rsi_val = df['RSI'].iloc[closest_idx] if not pd.isna(df['RSI'].iloc[closest_idx]) else 0
        
        simulation_results.append({
            "วันที่": date.strftime("%d/%m/%Y"),
            "ราคา": round(price, 2),
            "RSI": round(rsi_val, 1),
            "ต่ำกว่า EMA200?": "✅" if price < df['EMA200'].iloc[closest_idx] else "❌",
            "เงินลงทุน": f"฿{invest:,.0f}",
            "ซื้อได้": f"{shares_bought:.0f} หุ้น",
            "รวมหุ้น": f"{total_shares:.0f} หุ้น",
            "รวมเงินลงทุน": f"฿{total_invested:,.0f}",
            "หมายเหตุ": note
        })
    
    # แสดงตารางผลลัพธ์
    df_results = pd.DataFrame(simulation_results)
    st.dataframe(df_results, use_container_width=True, hide_index=True)
    
    # ============================================
    # สรุปผล
    # ============================================
    st.subheader("📈 สรุปผล")
    
    avg_cost_new = total_invested / total_shares if total_shares > 0 else 0
    current_value = total_shares * current_price if current_price else 0
    profit = current_value - total_invested
    profit_pct = (profit / total_invested) * 100 if total_invested > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("จำนวนหุ้นรวม", f"{total_shares:.0f} หุ้น")
    with col2:
        st.metric("ต้นทุนเฉลี่ยใหม่", f"฿{avg_cost_new:.2f}")
    with col3:
        st.metric("มูลค่าปัจจุบัน", f"฿{current_value:,.0f}")
    with col4:
        st.metric("กำไร/ขาดทุน", f"฿{profit:,.0f}", f"{profit_pct:.1f}%")
    
    # ============================================
    # กราฟ
    # ============================================
    st.subheader("📉 กราฟราคาและจุดซื้อ")
    
    fig = go.Figure()
    
    # เส้นราคา
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='ราคา',
        line=dict(color='blue', width=1)
    ))
    
    # เส้น EMA200
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA200'],
        mode='lines',
        name='EMA200',
        line=dict(color='red', width=1.5, dash='dash')
    ))
    
    # จุดซื้อ
    buy_dates = [datetime.strptime(r["วันที่"], "%d/%m/%Y") for r in simulation_results]
    buy_prices = []
    for r in simulation_results:
        invest_str = r["เงินลงทุน"].replace("฿", "").replace(",", "")
        shares_str = r["ซื้อได้"].replace(" หุ้น", "")
        if shares_str != "0":
            buy_prices.append(float(invest_str) / float(shares_str))
        else:
            buy_prices.append(0)
    
    fig.add_trace(go.Scatter(
        x=buy_dates,
        y=buy_prices,
        mode='markers',
        name='จุดซื้อ',
        marker=dict(color='green', size=8, symbol='circle')
    ))
    
    fig.update_layout(
        title=f"ราคา {selected_code} และจุดซื้อ",
        xaxis_title="วันที่",
        yaxis_title="ราคา",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.warning("ไม่สามารถดึงข้อมูลราคาย้อนหลังได้")

st.markdown("---")
st.caption("พัฒนาโดย Suchat50 — วางแผน DCA/EDCA เพื่อการลงทุนระยะยาว")
