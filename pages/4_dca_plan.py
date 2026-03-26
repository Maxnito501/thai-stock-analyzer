import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stock_analyzer import StockAnalyzer

st.set_page_config(page_title="DCA Plan", page_icon="📊", layout="wide")

st.title("📊 DCA / EDCA Plan")
st.markdown("วางแผนการลงทุนแบบ DCA (ลงทุนสม่ำเสมอ) และ EDCA (ซื้อเมื่อย่อ)")

# โหลด StockAnalyzer
@st.cache_resource
def get_analyzer():
    return StockAnalyzer()

analyzer = get_analyzer()

# ดึงรายชื่อหุ้น
stock_list = list(analyzer.thai_stocks.keys())
stock_names = {k: v for k, v in analyzer.thai_stocks.items()}

# เลือกหุ้น
selected_code = st.selectbox(
    "เลือกหุ้น",
    stock_list,
    format_func=lambda x: f"{stock_names.get(x, x)} ({x})"
)

# กลยุทธ์
strategy = st.selectbox("กลยุทธ์", ["DCA (ลงทุนสม่ำเสมอ)", "EDCA (ซื้อเมื่อย่อ)"])

# ข้อมูลการลงทุน
col1, col2 = st.columns(2)
with col1:
    initial_investment = st.number_input("เงินลงทุนเริ่มต้น (บาท)", min_value=0, value=10000, step=1000)
with col2:
    monthly_investment = st.number_input("เงินลงทุนต่อเดือน (บาท)", min_value=0, value=5000, step=500)

# ดึงข้อมูลราคา
@st.cache_data(ttl=3600)
def get_data(symbol):
    df, info = analyzer.get_stock_data(symbol, period="1y")
    if df is not None and not df.empty:
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        return df
    return None

df = get_data(selected_code)

if df is not None:
    st.success(f"ดึงข้อมูล {selected_code} สำเร็จ")
    
    # จำลอง DCA
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    total_shares = 0
    total_invested = 0
    results = []
    
    for i, date in enumerate(monthly_dates):
        closest_idx = df.index.get_indexer([date], method='nearest')[0]
        price = df['Close'].iloc[closest_idx]
        invest = initial_investment if i == 0 else monthly_investment
        shares = invest / price
        total_shares += shares
        total_invested += invest
        
        results.append({
            "วันที่": date.strftime("%d/%m/%Y"),
            "ราคา": round(price, 2),
            "เงินลงทุน": f"฿{invest:,.0f}",
            "ซื้อได้": f"{shares:.0f} หุ้น",
            "รวมหุ้น": f"{total_shares:.0f}",
            "รวมเงิน": f"฿{total_invested:,.0f}"
        })
    
    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    
    # สรุป
    current_price = df['Close'].iloc[-1]
    avg_cost = total_invested / total_shares if total_shares > 0 else 0
    current_value = total_shares * current_price
    profit = current_value - total_invested
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("รวมหุ้น", f"{total_shares:.0f}")
    with col2:
        st.metric("ต้นทุนเฉลี่ย", f"฿{avg_cost:.2f}")
    with col3:
        st.metric("มูลค่าปัจจุบัน", f"฿{current_value:,.0f}")
    with col4:
        st.metric("กำไร/ขาดทุน", f"฿{profit:,.0f}", f"{(profit/total_invested*100):.1f}%")
    
    # กราฟ
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคา'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], mode='lines', name='EMA200'))
    fig.update_layout(title=f"ราคา {selected_code}", height=400)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("ไม่สามารถดึงข้อมูลได้")

st.caption("พัฒนาโดย Suchat50")
