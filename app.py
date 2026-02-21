import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import yfinance as yf

from stock_analyzer import StockAnalyzer
from portfolio_manager import PortfolioManager

# ตั้งค่าหน้า
st.set_page_config(
    page_title="Thai Stock Analyzer Pro",
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

# เริ่มต้น
st.title("📊 วิเคราะห์หุ้นไทย แบบละเอียด")
st.markdown("พิมพ์รหัสหุ้นหรือชื่อหุ้นที่ต้องการวิเคราะห์")
st.markdown("---")

# โหลดคลาส
analyzer = StockAnalyzer()
portfolio = PortfolioManager()

# Sidebar
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    
    # ค้นหาหุ้น
    search_query = st.text_input("🔍 ค้นหาหุ้น", placeholder="เช่น ADVANC, PTT, KBANK, หรือ 1234")
    
    # เลือกหุ้นจากรายการหรือจากที่ค้นหา
    stock_options = list(analyzer.thai_stocks.keys())
    stock_names = [f"{analyzer.thai_stocks[s]} ({s})" for s in stock_options]
    
    if search_query:
        # ค้นหาหุ้น
        search_results = analyzer.search_stock(search_query)
        if search_results:
            st.success(f"พบ {len(search_results)} รายการ")
            selected_index = 0
            # สร้างตัวเลือกจากผลการค้นหา
            search_options = [f"{name} ({sym})" for sym, name in search_results]
            selected_display = st.selectbox("เลือกหุ้นที่พบ", search_options)
            # แยกรหัสหุ้น
            selected_stock = selected_display.split('(')[-1].split(')')[0]
        else:
            # ถ้าไม่พบ ให้ลองใช้รหัสที่พิมพ์โดยตรง
            custom_symbol = analyzer.validate_stock_symbol(search_query)
            st.info(f"ลองใช้: {custom_symbol}")
            if st.button(f"✅ วิเคราะห์ {custom_symbol}"):
                selected_stock = custom_symbol
            else:
                selected_stock = st.selectbox("หรือเลือกจากรายการ", stock_options, format_func=lambda x: f"{analyzer.thai_stocks[x]} ({x})")
    else:
        selected_stock = st.selectbox("เลือกหุ้น", stock_options, format_func=lambda x: f"{analyzer.thai_stocks[x]} ({x})")
    
    # ระยะเวลา
    period = st.selectbox(
        "ระยะเวลา",
        options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=2,
        format_func=lambda x: {
            '1mo': '1 เดือน', 
            '3mo': '3 เดือน', 
            '6mo': '6 เดือน', 
            '1y': '1 ปี', 
            '2y': '2 ปี',
            '5y': '5 ปี'
        }[x]
    )
    
    st.markdown("---")
    st.header("📋 พอร์ตของฉัน")
    
    # แสดงหุ้นในพอร์ต
    if 'selected_stock' in locals():
        stock_name = analyzer.thai_stocks.get(selected_stock, selected_stock.split('.')[0])
        current_shares = portfolio.get_current_shares(selected_stock)
        
        if current_shares > 0:
            avg_cost = portfolio.get_average_cost(selected_stock)
            st.info(f"📊 {stock_name}: {current_shares} หุ้น @ ฿{avg_cost:.2f}")
        
        # เพิ่มหุ้น
        with st.expander("➕ เพิ่มหุ้น"):
            shares = st.number_input("จำนวนหุ้น", min_value=1, value=100, step=100)
            buy_price = st.number_input("ราคาซื้อ", min_value=0.01, value=50.0, step=1.0)
            if st.button("บันทึก"):
                portfolio.add_stock(selected_stock, stock_name, shares, buy_price)
                st.success("บันทึกแล้ว")
                st.rerun()
        
        # ขายหุ้น
        if current_shares > 0:
            with st.expander("➖ ขายหุ้น"):
                sell_shares = st.number_input("จำนวนขาย", min_value=1, max_value=current_shares, value=min(100, current_shares))
                sell_price = st.number_input("ราคาขาย", min_value=0.01, value=50.0, step=1.0)
                if st.button("บันทึกการขาย"):
                    if portfolio.sell_stock(selected_stock, sell_shares, sell_price):
                        st.success("บันทึกแล้ว")
                        st.rerun()
                    else:
                        st.error("ไม่สามารถขายได้")
    
    st.markdown("---")
    if st.button("🔄 โหลดข้อมูลใหม่"):
        st.cache_data.clear()
        st.rerun()

# โหลดข้อมูลหุ้น
if 'selected_stock' in locals():
    with st.spinner('กำลังโหลดข้อมูล...'):
        df, info = analyzer.get_stock_data(selected_stock, period)

    if df is not None and not df.empty:
        # คำนวณ indicators
        df = analyzer.calculate_indicators(df)
        
        # ข้อมูลล่าสุด
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        current_price = latest['Close']
        price_change = current_price - prev['Close']
        price_change_pct = (price_change / prev['Close']) * 100 if prev['Close'] > 0 else 0
        
        # ชื่อหุ้น
        stock_display_name = info.get('name', stock_name) if info else stock_name
        
        st.header(f"📈 {stock_display_name}")
        
        # แสดงข้อมูลพื้นฐาน
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="ราคาปัจจุบัน",
                value=f"฿{current_price:.2f}",
                delta=f"{price_change:.2f} ({price_change_pct:.2f}%)"
            )
        
        with col2:
            if info and info.get('pe'):
                st.metric("P/E", f"{info.get('pe'):.2f}")
            else:
                st.metric("P/E", "N/A")
        
        with col3:
            if info and info.get('pb'):
                st.metric("P/B", f"{info.get('pb'):.2f}")
            else:
                st.metric("P/B", "N/A")
        
        with col4:
            div_info = analyzer.get_dividend_info(info or {})
            if div_info['dividend_yield'] > 0:
                st.metric("ปันผล", f"{div_info['dividend_yield']:.2f}%")
            else:
                st.metric("ปันผล", "ไม่มี")
        
        with col5:
            trend, trend_emoji = analyzer.get_trend_analysis(df)
            st.metric("แนวโน้ม", trend)
        
        st.markdown("---")
        
        # สร้างกราฟ 3 แถว
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=('กราฟราคาและปริมาณ', 'RSI (14)', 'MACD')
        )
        
        # กราฟแท่งเทียน
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='ราคา',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # เพิ่ม SMA
        if 'SMA_20' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='orange', width=1)),
                row=1, col=1
            )
        
        if 'SMA_50' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='blue', width=1)),
                row=1, col=1
            )
        
        if 'SMA_200' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(color='red', width=1)),
                row=1, col=1
            )
        
        # เพิ่มปริมาณการซื้อขาย
        colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' for i in range(len(df))]
        fig.add_trace(
            go.Bar(x=df.index, y=df['Volume'], name='ปริมาณ', marker_color=colors, opacity=0.3),
            row=1, col=1
        )
        
        # RSI
        if 'RSI_14' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['RSI_14'], name='RSI 14', line=dict(color='purple', width=2)),
                row=2, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=2, col=1)
        
        # MACD
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue', width=1.5)),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(x=df
