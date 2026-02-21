import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta

# ตั้งค่าหน้า
st.set_page_config(
    page_title="Thai Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

# ซ่อน Streamlit branding
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Title
st.title("📊 วิเคราะห์หุ้นไทย")
st.markdown("พัฒนาโดยใช้ Streamlit และ Yahoo Finance")
st.markdown("---")

# ใช้ cache เพื่อลดการโหลดซ้ำ
@st.cache_data(ttl=3600)  # cache 1 ชั่วโมง
def load_stock_data(symbol, period):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        return df, stock.info
    except:
        return None, None

# รายชื่อหุ้น
thai_stocks = {
    'ADVANC.BK': 'ADVANC',
    'AOT.BK': 'AOT',
    'BDMS.BK': 'BDMS',
    'CPALL.BK': 'CPALL',
    'KBANK.BK': 'KBANK',
    'PTT.BK': 'PTT',
    'SCB.BK': 'SCB',
    'SCC.BK': 'SCC',
    'TISCO.BK': 'TISCO'
}

# Sidebar
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    selected_stock = st.selectbox(
        "เลือกหุ้น",
        options=list(thai_stocks.keys()),
        format_func=lambda x: thai_stocks[x]
    )
    
    period = st.selectbox(
        "ระยะเวลา",
        options=['1mo', '3mo', '6mo', '1y'],
        index=2
    )
    
    if st.button("🔄 โหลดข้อมูลใหม่"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### เกี่ยวกับแอป")
    st.markdown("""
    - วิเคราะห์ทางเทคนิคเบื้องต้น
    - ข้อมูลจาก Yahoo Finance
    - อัปเดตทุกชั่วโมง
    """)

# โหลดข้อมูล
with st.spinner('กำลังโหลดข้อมูล...'):
    df, info = load_stock_data(selected_stock, period)

if df is not None and not df.empty:
    # คำนวณ indicators
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    
    # แสดงข้อมูล
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100
        
        st.metric(
            label=f"{thai_stocks[selected_stock]}",
            value=f"฿{current_price:.2f}",
            delta=f"{change:.2f} ({change_pct:.2f}%)"
        )
    
    with col2:
        rsi = df['RSI'].iloc[-1]
        if not pd.isna(rsi):
            rsi_status = "🟢 Oversold" if rsi < 30 else "🔴 Overbought" if rsi > 70 else "⚪ Neutral"
            st.metric("RSI", f"{rsi:.2f}", rsi_status)
    
    with col3:
        if 'dividendYield' in info and info['dividendYield']:
            div_yield = info['dividendYield'] * 100
            st.metric("อัตราปันผล", f"{div_yield:.2f}%")
    
    # กราฟ
    st.subheader("📈 กราฟราคา")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3],
                        vertical_spacing=0.1)
    
    # กราฟราคา
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'],
                                 name='ราคา'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'],
                            name='SMA 20', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'],
                            name='SMA 50', line=dict(color='blue')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                            name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # ตารางข้อมูลล่าสุด
    with st.expander("📊 ดูข้อมูลดิบ"):
        st.dataframe(df.tail(10))
        
else:
    st.error("ไม่สามารถโหลดข้อมูลได้ กรุณาลองใหม่อีกครั้ง")

st.markdown("---")
st.caption("⚠️ ข้อมูลนี้เพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำในการลงทุน")
