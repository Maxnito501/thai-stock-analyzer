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

# Initialize
analyzer = StockAnalyzer()
portfolio = PortfolioManager()

# Title
st.title("📊 ระบบวิเคราะห์หุ้นไทยพร้อมคำแนะนำ")
st.markdown("---")

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
        index=2
    )
    
    st.markdown("---")
    st.header("📋 พอร์ตการลงทุน")
    
    # แสดงหุ้นในพอร์ต
    stock_symbol = selected_stock.split('.')[0]
    current_shares = portfolio.get_current_shares(selected_stock)
    
    if current_shares > 0:
        avg_cost = portfolio.get_average_cost(selected_stock)
        st.info(f"📊 {analyzer.thai_stocks[selected_stock]}: {current_shares} หุ้น @ ฿{avg_cost:.2f}")
    
    # เพิ่มหุ้นในพอร์ต
    with st.expander("➕ เพิ่มหุ้นในพอร์ต"):
        shares = st.number_input("จำนวนหุ้น", min_value=1, value=100, step=100)
        buy_price = st.number_input("ราคาซื้อ", min_value=0.01, value=50.0, step=1.0)
        buy_date = st.date_input("วันที่ซื้อ", datetime.now())
        
        if st.button("บันทึกการซื้อ"):
            portfolio.add_stock(
                selected_stock,
                analyzer.thai_stocks[selected_stock],
                shares,
                buy_price,
                buy_date.strftime('%Y-%m-%d')
            )
            st.success("บันทึกเรียบร้อย")
            st.rerun()
    
    # ขายหุ้น
    if current_shares > 0:
        with st.expander("➖ ขายหุ้น"):
            sell_shares = st.number_input("จำนวนที่ขาย", min_value=1, max_value=current_shares, value=min(100, current_shares))
            sell_price = st.number_input("ราคาขาย", min_value=0.01, value=50.0, step=1.0)
            sell_date = st.date_input("วันที่ขาย", datetime.now())
            
            if st.button("บันทึกการขาย"):
                if portfolio.sell_stock(selected_stock, sell_shares, sell_price, sell_date.strftime('%Y-%m-%d')):
                    st.success("บันทึกเรียบร้อย")
                    st.rerun()
                else:
                    st.error("ไม่สามารถขายได้")
    
    st.markdown("---")
    if st.button("🔄 โหลดข้อมูลใหม่"):
        st.cache_data.clear()
        st.rerun()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # โหลดข้อมูล
    with st.spinner('กำลังโหลดข้อมูล...'):
        df, info = analyzer.get_stock_data(selected_stock, period)
    
    if df is not None and not df.empty:
        df = analyzer.calculate_indicators(df)
        
        # ข้อมูลปัจจุบัน
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100
        
        # แสดงราคา
        st.subheader(f"📈 {analyzer.thai_stocks[selected_stock]}")
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("ราคาปัจจุบัน", f"฿{current_price:.2f}", f"{change:.2f} ({change_pct:.2f}%)")
        with metric_col2:
            st.metric("สูงสุด", f"฿{df['High'].iloc[-1]:.2f}")
        with metric_col3:
            st.metric("ต่ำสุด", f"฿{df['Low'].iloc[-1]:.2f}")
        with metric_col4:
            st.metric("ปริมาณ", f"{df['Volume'].iloc[-1]:,.0f}")
        
        # กราฟ
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=('ราคาและ Moving Average', 'RSI', 'MACD')
        )
        
        # กราฟราคา
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='ราคา'
            ),
            row=1, col=1
        )
        
        # Moving Averages
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='orange')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='blue')),
            row=1, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # MACD
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='red')),
            row=3, col=1
        )
        
        fig.update_layout(height=700, showlegend=False, xaxis_rangeslider_visible=False)
        fig.update_xaxes(title_text="วันที่", row=3, col=1)
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🔍 วิเคราะห์ทางเทคนิค")
    
    if df is not None and not df.empty:
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # RSI
        rsi_signal, rsi_emoji = analyzer.get_rsi_signal(latest['RSI'])
        st.markdown(f"**RSI ({latest['RSI']:.2f})** {rsi_emoji} {rsi_signal}")
        
        # MACD
        macd_signal, macd_emoji = analyzer.get_macd_signal(
            latest['MACD'], latest['MACD_Signal'],
            prev['MACD'], prev['MACD_Signal']
        )
        st.markdown(f"**MACD** {macd_emoji} {macd_signal}")
        
        # Volume
        volume_signal, volume_emoji = analyzer.get_volume_signal(
            latest['Volume'], latest['Volume_SMA']
        )
        st.markdown(f"**ปริมาณซื้อขาย** {volume_emoji} {volume_signal}")
        
        # Bollinger Bands
        bb_signal, bb_emoji = analyzer.get_bollinger_signal(
            latest['Close'], latest['BB_Lower'], latest['BB_Upper']
        )
        st.markdown(f"**Bollinger Bands** {bb_emoji} {bb_signal}")
        
        # แนวโน้ม
        trend = analyzer.get_trend_analysis(df)
        st.markdown(f"**แนวโน้ม:** {trend}")
        
        st.markdown("---")
        st.subheader("📊 ปัจจัยพื้นฐาน")
        
        # P/E
        pe = info.get('trailingPE', 'N/A')
        if pe != 'N/A' and pe:
            st.markdown(f"**P/E Ratio:** {pe:.2f}")
        else:
            st.markdown(f"**P/E Ratio:** ไม่มีข้อมูล")
        
        # P/B
        pb = info.get('priceToBook', 'N/A')
        if pb != 'N/A' and pb:
            st.markdown(f"**P/B Ratio:** {pb:.2f}")
        
        # Dividend
        div_info = analyzer.get_dividend_info(info)
        if div_info['dividend_yield'] > 0:
            st.markdown(f"**อัตราปันผล:** {div_info['dividend_yield']:.2f}%")
        else:
            st.markdown(f"**อัตราปันผล:** ไม่มีข้อมูล")
        
        # Fundamental rating
        rating, rating_emoji, details = analyzer.get_fundamental_rating(info)
        st.markdown(f"**พื้นฐาน:** {rating_emoji} {rating}")
        for d in details[:3]:
            st.markdown(f"- {d}")
        
        st.markdown("---")
        st.subheader("🎯 สรุปสัญญาณ")
        
        # นับสัญญาณ
        buy_signals = sum([
            1 if rsi_signal.startswith("ซื้อ") else 0,
            1 if macd_signal.startswith("ซื้อ") else 0,
            1 if bb_signal.startswith("ซื้อ") else 0
        ])
        
        sell_signals = sum([
            1 if rsi_signal.startswith("ขาย") else 0,
            1 if macd_signal.startswith("ขาย") else 0,
            1 if bb_signal.startswith("ขาย") else 0
        ])
        
        if buy_signals >= 2:
            overall = "ซื้อ"
            overall_emoji = "🟢"
        elif sell_signals >= 2:
            overall = "ขาย"
            overall_emoji = "🔴"
        else:
            overall = "รอ"
            overall_emoji = "🟡"
        
        st.markdown(f"## {overall_emoji} {overall}")
        
        # ความน่าจะเป็น
        total_signals = buy_signals + sell_signals
        if total_signals > 0:
            buy_prob = (buy_signals / 3) * 100
            sell_prob = (sell_signals / 3) * 100
            st.progress(buy_prob/100, text=f"โอกาสซื้อ {buy_prob:.0f}%")
            st.progress(sell_prob/100, text=f"โอกาสขาย {sell_prob:.0f}%")

# ส่วนแนะนำการลงทุน (อยู่ท้ายไฟล์)
st.markdown("---")
st.subheader("💡 คำแนะนำการลงทุน")

if df is not None and not df.empty:
    # เตรียมข้อมูลสำหรับวิเคราะห์
    analysis_data = {
        'overall_signal': overall,
        'trend': trend,
        'rsi': latest['RSI'] if not pd.isna(latest['RSI']) else 50,
        'dividend_info': div_info
    }
    
    # ตรวจสอบว่ามีฟังก์ชันนี้หรือไม่
    if hasattr(portfolio, 'get_investment_advice'):
        advice_title, advice_detail = portfolio.get_investment_advice(
            selected_stock, current_price, analysis_data
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"### {advice_title}")
        with col2:
            st.info(advice_detail)
    else:
        # ถ้าไม่มีฟังก์ชัน ให้ใช้ logic ตรงนี้
        st.warning("กำลังวิเคราะห์สัญญาณ...")
        
        # Logic การแนะนำเบื้องต้น
        shares = portfolio.get_current_shares(selected_stock)
        avg_cost = portfolio.get_average_cost(selected_stock)
        
        if shares == 0:  # ยังไม่มีหุ้น
            if overall == "ซื้อ":
                st.success("🔵 แนะนำ: เริ่มสะสม - สัญญาณทางเทคนิคบวก")
            elif overall == "ขาย":
                st.warning("🟡 แนะนำ: รอดู - ยังไม่ควรเข้าซื้อ")
            else:
                st.info("⚪ แนะนำ: รอ - ยังไม่มีสัญญาณชัดเจน")
        else:  # มีหุ้นแล้ว
            profit_loss = ((current_price - avg_cost) / avg_cost) * 100
            
            if profit_loss < -10:  # ขาดทุนเกิน 10%
                if overall == "ซื้อ":
                    st.success(f"🟢 แนะนำ: ถัวเฉลี่ย - ขาดทุน {profit_loss:.1f}% แต่สัญญาณซื้อ")
                elif overall == "ขาย":
                    st.error(f"🔴 แนะนำ: ขายตัดขาดทุน - ขาดทุน {profit_loss:.1f}% แนวโน้มยังขาลง")
                else:
                    st.warning(f"🟡 แนะนำ: ถือรอ - ขาดทุน {profit_loss:.1f}% ยังไม่มีสัญญาณชัดเจน")
            
            elif profit_loss > 15:  # กำไรเกิน 15%
                if overall == "ขาย":
                    st.success(f"🟢 แนะนำ: ขายทำกำไร - กำไร {profit_loss:.1f}% มีสัญญาณขาย")
                elif overall == "ซื้อ" and trend == "ขาขึ้น":
                    st.info(f"💰 แนะนำ: ถือต่อ - กำไร {profit_loss:.1f}% แนวโน้มยังดี")
                else:
                    st.warning(f"🟡 แนะนำ: ขายบางส่วน - กำไร {profit_loss:.1f}% แต่สัญญาณเริ่มเปลี่ยน")
            
            else:  # ใกล้เคียงทุน
                if overall == "ซื้อ":
                    st.success(f"🟢 แนะนำ: ซื้อเพิ่ม - ใกล้เคียงทุนและสัญญาณซื้อ")
                elif overall == "ขาย":
                    st.error(f"🔴 แนะนำ: ขาย - ใกล้เคียงทุนแต่สัญญาณขาย")
                elif div_info['dividend_yield'] > 4:
                    st.info(f"💵 แนะนำ: ถือรอปันผล - อัตราปันผล {div_info['dividend_yield']:.1f}%")
                else:
                    st.warning(f"⚪ แนะนำ: รอดู - ใกล้เคียงทุน รอดูสัญญาณถัดไป")
    
    # แสดงสถานะพอร์ต
    current_shares = portfolio.get_current_shares(selected_stock)
    if current_shares > 0:
        avg_cost = portfolio.get_average_cost(selected_stock)
        profit_loss = ((current_price - avg_cost) / avg_cost) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("จำนวนหุ้น", f"{current_shares} หุ้น")
        with col2:
            st.metric("ต้นทุนเฉลี่ย", f"฿{avg_cost:.2f}")
        with col3:
            st.metric("กำไร/ขาดทุน", f"{profit_loss:.1f}%", f"฿{(current_price - avg_cost) * current_shares:,.0f}")
# ดูพอร์ตทั้งหมด
with st.expander("📊 ดูพอร์ตการลงทุนทั้งหมด"):
    current_prices = {}
    for symbol in portfolio.portfolio.keys():
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            if not hist.empty:
                current_prices[symbol] = hist['Close'].iloc[-1]
        except:
            current_prices[symbol] = 0
    
    summary, total_value, total_cost = portfolio.get_portfolio_summary(current_prices)
    
    if summary:
        df_portfolio = pd.DataFrame(summary)
        df_portfolio['profit_loss_pct'] = df_portfolio['profit_loss_pct'].round(2)
        df_portfolio['profit_loss'] = df_portfolio['profit_loss'].round(2)
        
        st.dataframe(
            df_portfolio,
            column_config={
                'symbol': 'หุ้น',
                'shares': 'จำนวนหุ้น',
                'avg_cost': st.column_config.NumberColumn('ต้นทุนเฉลี่ย', format="฿%.2f"),
                'current_price': st.column_config.NumberColumn('ราคาปัจจุบัน', format="฿%.2f"),
                'current_value': st.column_config.NumberColumn('มูลค่า', format="฿%.2f"),
                'profit_loss': st.column_config.NumberColumn('กำไร/ขาดทุน', format="฿%.2f"),
                'profit_loss_pct': st.column_config.NumberColumn('%', format="%.2f%%")
            },
            use_container_width=True
        )
        
        total_profit = total_value - total_cost
        total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("มูลค่ารวม", f"฿{total_value:,.2f}")
        with col2:
            st.metric("ต้นทุนรวม", f"฿{total_cost:,.2f}")
        with col3:
            st.metric("กำไร/ขาดทุนรวม", f"฿{total_profit:,.2f}", f"{total_profit_pct:.2f}%")
    else:
        st.info("ยังไม่มีหุ้นในพอร์ต")

# คำอธิบายสัญญาณ
with st.expander("ℹ️ คำอธิบายสัญญาณ"):
    st.markdown("""
    ### 🟢 สัญญาณซื้อ
    - **RSI < 30**:  Oversold - เหมาะซื้อ
    - **MACD Golden Cross**: เส้น MACD ตัดขึ้นเหนือ Signal
    - **Bollinger Bands**: ราคาต่ำกว่า Lower Band
    
    ### 🔴 สัญญาณขาย
    - **RSI > 70**: Overbought - เหมาะขาย
    - **MACD Death Cross**: เส้น MACD ตัดลงใต้ Signal
    - **Bollinger Bands**: ราคาสูงกว่า Upper Band
    
    ### 🟡 กลาง/รอ
    - ยัง
