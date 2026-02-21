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

# ตรวจสอบว่ามีการเลือกหุ้นหรือไม่
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = 'ADVANC.BK'

# Sidebar
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    
    # ค้นหาหุ้น
    search_query = st.text_input("🔍 ค้นหาหุ้น", placeholder="เช่น ADVANC, PTT, KBANK, CPALL")
    
    # เลือกหุ้นจากรายการหรือจากที่ค้นหา
    stock_options = list(analyzer.thai_stocks.keys())
    
    if search_query:
        # ค้นหาหุ้น
        search_results = analyzer.search_stock(search_query)
        if search_results:
            st.success(f"พบ {len(search_results)} รายการ")
            # สร้างตัวเลือกจากผลการค้นหา
            search_options = [f"{name} ({sym})" for sym, name in search_results]
            selected_display = st.selectbox("เลือกหุ้นที่พบ", search_options)
            # แยกรหัสหุ้น
            st.session_state.selected_stock = selected_display.split('(')[-1].split(')')[0]
        else:
            # ถ้าไม่พบ ให้ลองใช้รหัสที่พิมพ์โดยตรง
            custom_symbol = analyzer.validate_stock_symbol(search_query)
            st.info(f"ลองใช้รหัส: {custom_symbol}")
            if st.button(f"✅ วิเคราะห์ {custom_symbol}"):
                st.session_state.selected_stock = custom_symbol
            else:
                st.session_state.selected_stock = st.selectbox(
                    "หรือเลือกจากรายการ", 
                    stock_options, 
                    format_func=lambda x: f"{analyzer.thai_stocks[x]} ({x})",
                    index=stock_options.index(st.session_state.selected_stock) if st.session_state.selected_stock in stock_options else 0
                )
    else:
        st.session_state.selected_stock = st.selectbox(
            "เลือกหุ้น", 
            stock_options, 
            format_func=lambda x: f"{analyzer.thai_stocks[x]} ({x})",
            index=stock_options.index(st.session_state.selected_stock) if st.session_state.selected_stock in stock_options else 0
        )
    
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
    stock_name = analyzer.thai_stocks.get(st.session_state.selected_stock, st.session_state.selected_stock.split('.')[0])
    current_shares = portfolio.get_current_shares(st.session_state.selected_stock)
    
    if current_shares > 0:
        avg_cost = portfolio.get_average_cost(st.session_state.selected_stock)
        st.info(f"📊 {stock_name}: {current_shares} หุ้น @ ฿{avg_cost:.2f}")
    
    # เพิ่มหุ้น
    with st.expander("➕ เพิ่มหุ้น"):
        shares = st.number_input("จำนวนหุ้น", min_value=1, value=100, step=100)
        buy_price = st.number_input("ราคาซื้อ", min_value=0.01, value=50.0, step=1.0)
        if st.button("บันทึกการซื้อ"):
            portfolio.add_stock(st.session_state.selected_stock, stock_name, shares, buy_price)
            st.success("บันทึกเรียบร้อย")
            st.rerun()
    
    # ขายหุ้น
    if current_shares > 0:
        with st.expander("➖ ขายหุ้น"):
            sell_shares = st.number_input("จำนวนขาย", min_value=1, max_value=current_shares, value=min(100, current_shares))
            sell_price = st.number_input("ราคาขาย", min_value=0.01, value=50.0, step=1.0)
            if st.button("บันทึกการขาย"):
                if portfolio.sell_stock(st.session_state.selected_stock, sell_shares, sell_price):
                    st.success("บันทึกเรียบร้อย")
                    st.rerun()
                else:
                    st.error("ไม่สามารถขายได้ จำนวนหุ้นไม่พอ")
    
    st.markdown("---")
    if st.button("🔄 โหลดข้อมูลใหม่"):
        st.cache_data.clear()
        st.rerun()

# Main content
with st.spinner('กำลังโหลดข้อมูล...'):
    df, info = analyzer.get_stock_data(st.session_state.selected_stock, period)

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
    
    # ดึงข้อมูลปันผลอย่างปลอดภัย
    try:
        if info is not None:
            div_info = analyzer.get_dividend_info(info)
        else:
            div_info = {'dividend_yield': 0, 'payout_ratio': 0, 'has_dividend': False}
    except Exception as e:
        st.warning("ไม่สามารถโหลดข้อมูลปันผลได้")
        div_info = {'dividend_yield': 0, 'payout_ratio': 0, 'has_dividend': False}
    
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
        if div_info['dividend_yield'] > 0:
            st.metric("ปันผล", f"{div_info['dividend_yield']:.2f}%")
        else:
            st.metric("ปันผล", "ไม่มี")
    
    with col5:
        trend, trend_emoji = analyzer.get_trend_analysis(df)
        st.metric("แนวโน้ม", f"{trend_emoji} {trend}")
    
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
            go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='red', width=1.5)),
            row=3, col=1
        )
        
        # เพิ่ม histogram
        if 'MACD_Histogram' in df.columns:
            colors_macd = ['green' if val >= 0 else 'red' for val in df['MACD_Histogram']]
            fig.add_trace(
                go.Bar(x=df.index, y=df['MACD_Histogram'], name='Histogram', marker_color=colors_macd, opacity=0.5),
                row=3, col=1
            )
    
    fig.update_layout(
        height=800, 
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(title_text="วันที่", row=3, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # วิเคราะห์ทางเทคนิค
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🔍 วิเคราะห์ทางเทคนิค")
        
        # RSI Analysis
        st.markdown("**📊 RSI Analysis:**")
        rsi_analysis = analyzer.get_rsi_analysis(df)
        if rsi_analysis:
            for period, data in rsi_analysis.items():
                st.markdown(f"- {period}: {data['emoji']} {data['value']:.2f} - {data['signal']} ({data['desc']})")
        else:
            st.markdown("- ไม่มีข้อมูล RSI")
        
        # MACD Analysis
        st.markdown("**📈 MACD Analysis:**")
        macd_analysis = analyzer.get_macd_analysis(df)
        if macd_analysis:
            for indicator, data in macd_analysis.items():
                st.markdown(f"- {indicator}: {data['emoji']} {data['signal']}")
        else:
            st.markdown("- ไม่มีข้อมูล MACD")
        
        # Volume Analysis
        st.markdown("**📊 Volume Analysis:**")
        volume_analysis = analyzer.get_volume_analysis(df)
        if volume_analysis:
            for indicator, data in volume_analysis.items():
                st.markdown(f"- {indicator}: {data['emoji']} {data['signal']} ({data['desc']}) - {data['value']}")
        else:
            st.markdown("- ไม่มีข้อมูล Volume")
        
        # Support/Resistance
        st.markdown("**📏 แนวรับ/แนวต้าน:**")
        sr_analysis = analyzer.get_support_resistance(df)
        if sr_analysis:
            st.markdown(f"- แนวรับ: {sr_analysis['Support']['value']} (ห่าง {sr_analysis['Support']['distance']})")
            st.markdown(f"- แนวต้าน: {sr_analysis['Resistance']['value']} (ห่าง {sr_analysis['Resistance']['distance']})")
        else:
            st.markdown("- ไม่มีข้อมูลแนวรับแนวต้าน")
        
        # นับสัญญาณ
        buy_signals = 0
        sell_signals = 0
        
        # นับจาก RSI
        for period, data in rsi_analysis.items():
            if "ซื้อ" in data['signal']:
                buy_signals += 1
            elif "ขาย" in data['signal']:
                sell_signals += 1
        
        # นับจาก MACD
        for indicator, data in macd_analysis.items():
            if "bullish" in data['signal'].lower():
                buy_signals += 1
            elif "bearish" in data['signal'].lower():
                sell_signals += 1
        
        # นับจาก Volume
        for indicator, data in volume_analysis.items():
            if "สูง" in data['signal'] and price_change > 0:
                buy_signals += 1
            elif "สูง" in data['signal'] and price_change < 0:
                sell_signals += 1
        
        st.markdown("---")
        st.subheader("🎯 สรุปสัญญาณ")
        
        col_buy, col_sell = st.columns(2)
        with col_buy:
            st.markdown(f"### 🟢 ซื้อ: {buy_signals}")
        with col_sell:
            st.markdown(f"### 🔴 ขาย: {sell_signals}")
        
        if buy_signals > sell_signals:
            overall = "ซื้อ"
            overall_emoji = "🟢"
        elif sell_signals > buy_signals:
            overall = "ขาย"
            overall_emoji = "🔴"
        else:
            overall = "รอ"
            overall_emoji = "🟡"
        
        st.markdown(f"## {overall_emoji} สรุป: {overall}")
        
        # ความน่าจะเป็น
        total_signals = buy_signals + sell_signals
        if total_signals > 0:
            buy_prob = (buy_signals / (buy_signals + sell_signals)) * 100 if (buy_signals + sell_signals) > 0 else 0
            sell_prob = (sell_signals / (buy_signals + sell_signals)) * 100 if (buy_signals + sell_signals) > 0 else 0
            st.progress(buy_prob/100, text=f"โอกาสซื้อ {buy_prob:.0f}%")
            st.progress(sell_prob/100, text=f"โอกาสขาย {sell_prob:.0f}%")
    
    with col_right:
        st.subheader("📊 ปัจจัยพื้นฐาน")
        
        if info:
            # Fundamental rating
            score, rating, rating_emoji, details = analyzer.get_fundamental_rating(info)
            st.markdown(f"**คะแนนพื้นฐาน:** {score:.1f}% - {rating_emoji} {rating}")
            
            with st.expander("ดูรายละเอียด"):
                for detail in details:
                    st.markdown(f"- {detail}")
            
            # ข้อมูลบริษัท
            st.markdown("**🏢 ข้อมูลบริษัท:**")
            if info.get('sector'):
                st.markdown(f"- หมวด: {info.get('sector')}")
            if info.get('industry'):
                st.markdown(f"- อุตสาหกรรม: {info.get('industry')}")
            if info.get('website') and info.get('website') != 'ไม่ระบุ':
                st.markdown(f"- เว็บไซต์: {info.get('website')}")
            
            # ข้อมูลทางการเงิน
            st.markdown("**💰 ข้อมูลทางการเงิน:**")
            if info.get('market_cap'):
                market_cap_b = info.get('market_cap') / 1e9
                st.markdown(f"- มูลค่าตลาด: {market_cap_b:.2f} พันล้าน")
            if info.get('eps'):
                st.markdown(f"- EPS: ฿{info.get('eps'):.2f}")
            if info.get('beta'):
                beta_val = info.get('beta')
                beta_desc = "สูง" if beta_val > 1.5 else "ปานกลาง" if beta_val > 1 else "ต่ำ"
                st.markdown(f"- Beta: {beta_val:.2f} ({beta_desc})")
            
            # 52-week range
            if info.get('52w_high') and info.get('52w_low'):
                high = info.get('52w_high')
                low = info.get('52w_low')
                if high and low and high > low:
                    position = ((current_price - low) / (high - low)) * 100
                    st.markdown(f"- 52 สัปดาห์: ฿{low:.2f} - ฿{high:.2f}")
                    st.markdown(f"- ตำแหน่ง: {position:.1f}% ของช่วง")
                    st.progress(position/100, text="")
            
            # Target price
            if info.get('target_price'):
                target = info.get('target_price')
                upside = ((target - current_price) / current_price) * 100
                st.markdown(f"- ราคาเป้าหมาย: ฿{target:.2f} (upside {upside:.1f}%)")
            
            # Recommendation
            if info.get('recommendation'):
                rec = info.get('recommendation')
                rec_emoji = "🟢" if rec in ['buy', 'strong_buy'] else "🔴" if rec in ['sell', 'strong_sell'] else "🟡"
                st.markdown(f"- คำแนะนำ: {rec_emoji} {rec}")
        
        else:
            st.info("ไม่มีข้อมูลปัจจัยพื้นฐาน")
    
    st.markdown("---")
    
    # คำแนะนำการลงทุน
    st.subheader("💡 คำแนะนำสำหรับคุณ")
    
    analysis_data = {
        'signal': overall,
        'trend': trend,
        'dividend': div_info['dividend_yield']
    }
    
    advice_title, advice_detail = portfolio.get_investment_advice(
        st.session_state.selected_stock, current_price, analysis_data
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"### {advice_title}")
    with col2:
        st.info(advice_detail)
    
    # แสดงสถานะพอร์ตปัจจุบัน
    if current_shares > 0:
        avg_cost = portfolio.get_average_cost(st.session_state.selected_stock)
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
    
    # แสดงข้อมูลดิบ
    with st.expander("📋 ดูข้อมูลดิบ"):
        st.dataframe(df.tail(20))
    
    # คำอธิบาย
    with st.expander("ℹ️ คำอธิบายสัญญาณ"):
        st.markdown("""
        ### 🟢 สัญญาณซื้อ
        - **RSI < 30**: ราคาถูกเกินไป (Oversold) มีโอกาสรีบาวด์
        - **MACD > Signal**: สัญญาณ bullish ราคามีแนวโน้มขึ้น
        - **Volume สูง + ราคาขึ้น**: มีแรงซื้อหนาแน่น
        
        ### 🔴 สัญญาณขาย
        - **RSI > 70**: ราคาแพงเกินไป (Overbought) มีโอกาสพักฐาน
        - **MACD < Signal**: สัญญาณ bearish ราคามีแนวโน้มลง
        - **Volume สูง + ราคาลง**: มีแรงขายหนาแน่น
        
        ### คำแนะนำสำหรับพอร์ต
        - **เริ่มสะสม**: ยังไม่มีหุ้น แต่สัญญาณดี
        - **ซื้อเพิ่ม**: มีหุ้นแล้วและสัญญาณดี
        - **ถัวเฉลี่ย**: ขาดทุนแต่สัญญาณเริ่มดี
        - **ขายทำกำไร**: กำไรและสัญญาณขาย
        - **ถือรอปันผล**: ปันผลดี แม้สัญญาณไม่ชัด
        
        ### ปัจจัยพื้นฐาน
        - **P/E ต่ำ**: หุ้นถูกเมื่อเทียบกับกำไร
        - **P/B ต่ำ**: หุ้นถูกเมื่อเทียบกับสินทรัพย์
        - **ปันผลสูง**: จ่ายปันผลสม่ำเสมอ
        - **ROE สูง**: ทำกำไรได้ดีจากส่วนของผู้ถือหุ้น
        """)

else:
    st.error(f"ไม่สามารถโหลดข้อมูล {st.session_state.selected_stock} ได้ กรุณาตรวจสอบรหัสหุ้นหรือลองใหม่อีกครั้ง")
    st.info("ตัวอย่างรหัสหุ้นที่ถูกต้อง: ADVANC.BK, PTT.BK, KBANK.BK, CPALL.BK, AOT.BK")

st.markdown("---")
st.caption("⚠️ ข้อมูลเพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำในการลงทุน ควรศึกษาข้อมูลเพิ่มเติมก่อนตัดสินใจลงทุน")
