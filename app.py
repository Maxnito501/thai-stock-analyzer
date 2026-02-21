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

# เริ่มต้น
st.title("📊 วิเคราะห์หุ้นไทย")
st.markdown("พร้อมคำแนะนำการลงทุน")
st.markdown("---")

# โหลดคลาส
analyzer = StockAnalyzer()
portfolio = PortfolioManager()

# Sidebar
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    
    # เลือกหุ้น
    selected_stock = st.selectbox(
        "เลือกหุ้น",
        options=list(analyzer.thai_stocks.keys()),
        format_func=lambda x: f"{analyzer.thai_stocks[x]} ({x})"
    )
    
    # ระยะเวลา
    period = st.selectbox(
        "ระยะเวลา",
        options=['1mo', '3mo', '6mo', '1y', '2y'],
        index=2,
        format_func=lambda x: {'1mo': '1 เดือน', '3mo': '3 เดือน', '6mo': '6 เดือน', '1y': '1 ปี', '2y': '2 ปี'}[x]
    )
    
    st.markdown("---")
    st.header("📋 พอร์ตของฉัน")
    
    # แสดงหุ้นในพอร์ต
    stock_name = analyzer.thai_stocks[selected_stock]
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
    
    # แสดงราคา
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"{stock_name}",
            value=f"฿{current_price:.2f}",
            delta=f"{price_change:.2f} ({price_change_pct:.2f}%)"
        )
    
    with col2:
        rsi_value = latest['RSI'] if 'RSI' in latest and not pd.isna(latest['RSI']) else 50
        rsi_signal, rsi_emoji = analyzer.get_rsi_signal(rsi_value)
        st.metric("RSI", f"{rsi_value:.2f}", rsi_signal)
    
    with col3:
        div_info = analyzer.get_dividend_info(info)
        if div_info['dividend_yield'] > 0:
            st.metric("อัตราปันผล", f"{div_info['dividend_yield']:.2f}%")
        else:
            st.metric("อัตราปันผล", "ไม่มีข้อมูล")
    
    with col4:
        trend = analyzer.get_trend(df)
        st.metric("แนวโน้ม", trend)
    
    st.markdown("---")
    
    # สร้างกราฟ 2 แถว
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=('กราฟราคา', 'RSI')
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
            go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='orange')),
            row=1, col=1
        )
    
    if 'SMA_50' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='blue')),
            row=1, col=1
        )
    
    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.update_layout(height=600, xaxis_rangeslider_visible=False)
    fig.update_xaxes(title_text="วันที่", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # วิเคราะห์สัญญาณ
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🔍 สัญญาณทางเทคนิค")
        
        # RSI
        st.markdown(f"**RSI:** {rsi_emoji} {rsi_signal}")
        
        # MACD
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd_signal, macd_emoji = analyzer.get_macd_signal(
                latest['MACD'], 
                latest['MACD_Signal'],
                latest['MACD_Histogram'] if 'MACD_Histogram' in df.columns else 0
            )
            st.markdown(f"**MACD:** {macd_emoji} {macd_signal}")
        
        # Bollinger Bands
        if 'BB_Lower' in df.columns and 'BB_Upper' in df.columns:
            bb_signal, bb_emoji = analyzer.get_bb_signal(
                current_price, latest['BB_Lower'], latest['BB_Upper']
            )
            st.markdown(f"**Bollinger:** {bb_emoji} {bb_signal}")
        
        # นับสัญญาณ
        buy_count = 0
        sell_count = 0
        
        if "ซื้อ" in rsi_signal:
            buy_count += 1
        if "ขาย" in rsi_signal:
            sell_count += 1
        
        if 'MACD' in df.columns:
            if "bullish" in macd_signal:
                buy_count += 1
            if "bearish" in macd_signal:
                sell_count += 1
        
        if 'BB_Lower' in df.columns:
            if "ซื้อ" in bb_signal:
                buy_count += 1
            if "ขาย" in bb_signal:
                sell_count += 1
        
        # สรุปสัญญาณ
        st.markdown("---")
        if buy_count > sell_count:
            signal = "ซื้อ"
            signal_emoji = "🟢"
            signal_color = "green"
        elif sell_count > buy_count:
            signal = "ขาย"
            signal_emoji = "🔴"
            signal_color = "red"
        else:
            signal = "รอ"
            signal_emoji = "🟡"
            signal_color = "orange"
        
        st.markdown(f"## {signal_emoji} สรุป: {signal}")
        
        # ความน่าจะเป็น
        total = buy_count + sell_count
        if total > 0:
            buy_prob = (buy_count / 3) * 100
            sell_prob = (sell_count / 3) * 100
            st.progress(buy_prob/100, text=f"โอกาสซื้อ {buy_prob:.0f}%")
            st.progress(sell_prob/100, text=f"โอกาสขาย {sell_prob:.0f}%")
    
    with col_right:
        st.subheader("📊 ปัจจัยพื้นฐาน")
        
        # P/E
        pe = info.get('trailingPE', None)
        if pe and pe > 0:
            st.markdown(f"**P/E Ratio:** {pe:.2f}")
        
        # P/B
        pb = info.get('priceToBook', None)
        if pb and pb > 0:
            st.markdown(f"**P/B Ratio:** {pb:.2f}")
        
        # Market Cap
        market_cap = info.get('marketCap', None)
        if market_cap and market_cap > 0:
            if market_cap > 1e9:
                st.markdown(f"**Market Cap:** {market_cap/1e9:.2f} พันล้าน")
        
        # Dividend
        if div_info['dividend_yield'] > 0:
            st.markdown(f"**ปันผล:** {div_info['dividend_yield']:.2f}%")
            if div_info['payout_ratio'] > 0:
                st.markdown(f"**Payout:** {div_info['payout_ratio']:.2f}%")
        
        # Fundamental summary
        st.markdown("---")
        st.markdown("**สรุปปัจจัยพื้นฐาน:**")
        fundamental = analyzer.get_fundamental_summary(info)
        for item in fundamental:
            st.markdown(f"- {item[0]}: {item[1]} ({item[2]})")
    
    st.markdown("---")
    
    # คำแนะนำการลงทุน
    st.subheader("💡 คำแนะนำสำหรับคุณ")
    
    analysis_data = {
        'signal': signal,
        'trend': trend,
        'dividend': div_info['dividend_yield']
    }
    
    advice_title, advice_detail = portfolio.get_investment_advice(
        selected_stock, current_price, analysis_data
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"### {advice_title}")
    with col2:
        st.info(advice_detail)
    
    # แสดงสถานะพอร์ตปัจจุบัน
    if current_shares > 0:
        avg_cost = portfolio.get_average_cost(selected_stock)
        profit_loss = ((current_price - avg_cost) / avg_cost) * 100
        profit_amount = (current_price - avg_cost) * current_shares
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("จำนวนหุ้น", f"{current_shares} หุ้น")
        with col2:
            st.metric("ต้นทุนเฉลี่ย", f"฿{avg_cost:.2f}")
        with col3:
            st.metric("กำไร/ขาดทุน", f"{profit_loss:.1f}%", f"฿{profit_amount:,.0f}")
    
    st.markdown("---")
    
    # แสดงพอร์ตทั้งหมด
    with st.expander("📊 ดูพอร์ตทั้งหมด"):
        # หาราคาปัจจุบันของหุ้นในพอร์ต
        current_prices = {}
        for sym in portfolio.portfolio.keys():
            try:
                stock = yf.Ticker(sym)
                hist = stock.history(period="1d")
                if not hist.empty:
                    current_prices[sym] = hist['Close'].iloc[-1]
                else:
                    current_prices[sym] = 0
            except:
                current_prices[sym] = 0
        
        summary, total_value, total_cost = portfolio.get_portfolio_summary(current_prices)
        
        if summary:
            df_portfolio = pd.DataFrame(summary)
            st.dataframe(
                df_portfolio,
                column_config={
                    'symbol': 'หุ้น',
                    'shares': 'จำนวน',
                    'avg_cost': st.column_config.NumberColumn('ต้นทุน', format="฿%.2f"),
                    'current_price': st.column_config.NumberColumn('ราคา', format="฿%.2f"),
                    'current_value': st.column_config.NumberColumn('มูลค่า', format="฿%.2f"),
                    'profit': st.column_config.NumberColumn('กำไร', format="฿%.2f"),
                    'profit_pct': st.column_config.NumberColumn('%', format="%.2f%%")
                },
                use_container_width=True,
                hide_index=True
            )
            
            total_profit = total_value - total_cost
            total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("มูลค่ารวม", f"฿{total_value:,.2f}")
            with col2:
                st.metric("ต้นทุนรวม", f"฿{total_cost:,.2f}")
            with col3:
                st.metric("กำไรขาดทุน", f"฿{total_profit:,.2f}", f"{total_profit_pct:.2f}%")
        else:
            st.info("ยังไม่มีหุ้นในพอร์ต")
    
    # คำอธิบาย
    with st.expander("ℹ️ คำอธิบายสัญญาณ"):
        st.markdown("""
        ### 🟢 สัญญาณซื้อ
        - **RSI < 30**: ราคาถูกเกินไป (Oversold)
        - **MACD > Signal**: สัญญาณ bullish
        - **ราคา < Bollinger Lower**: ราคาต่ำกว่าแถบล่าง
        
        ### 🔴 สัญญาณขาย
        - **RSI > 70**: ราคาแพงเกินไป (Overbought)
        - **MACD < Signal**: สัญญาณ bearish
        - **ราคา > Bollinger Upper**: ราคาสูงกว่าแถบบน
        
        ### คำแนะนำ
        - **เริ่มสะสม**: ยังไม่มีหุ้น แต่สัญญาณดี
        - **ซื้อเพิ่ม**: มีหุ้นแล้วและสัญญาณดี
        - **ถัวเฉลี่ย**: ขาดทุนแต่สัญญาณเริ่มดี
        - **ขายทำกำไร**: กำไรและสัญญาณขาย
        - **ถือรอปันผล**: ปันผลดี แม้สัญญาณไม่ชัด
        """)

else:
    st.error("ไม่สามารถโหลดข้อมูลได้ กรุณาลองใหม่อีกครั้ง")

st.markdown("---")
st.caption("⚠️ ข้อมูลเพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำในการลงทุน")
