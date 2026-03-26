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

# สร้างแท็บ
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 วิเคราะห์รายตัว", "🚀 สแกนหุ้นโมเมนตัม", "💥 สแกนหุ้น breakout", "📉 สแกนหุ้นรีบาวด์", "📊 DCA Plan"])
with tab1:
    # Sidebar
    with st.sidebar:
        st.header("⚙️ ตั้งค่า")
        
        # ค้นหาหุ้น
        search_query = st.text_input("🔍 ค้นหาหุ้น", placeholder="เช่น ADVANC, PTT, SIRI, CPALL")
        
        # เลือกหุ้นจากรายการหรือจากที่ค้นหา
        stock_options = list(analyzer.thai_stocks.keys())
        
        if search_query:
            # ค้นหาหุ้น
            search_results = analyzer.search_stock(search_query)
            if search_results:
                st.success(f"พบ {len(search_results)} รายการ")
                # สร้างตัวเลือกจากผลการค้นหา
                search_options = [f"{name} ({sym})" for sym, name in search_results]
                selected_display = st.selectbox("เลือกหุ้นที่พบ", search_options, key="search_select")
                # แยกรหัสหุ้น
                if selected_display:
                    st.session_state.selected_stock = selected_display.split('(')[-1].split(')')[0]
            else:
                # ถ้าไม่พบ ให้ลองใช้รหัสที่พิมพ์โดยตรง
                custom_symbol = analyzer.validate_stock_symbol(search_query)
                st.info(f"ลองใช้รหัส: {custom_symbol}")
                if st.button(f"✅ วิเคราะห์ {custom_symbol}"):
                    st.session_state.selected_stock = custom_symbol
        else:
            # ถ้าไม่ได้ค้นหา ให้ใช้ selectbox ปกติ
            current_index = 0
            if st.session_state.selected_stock in stock_options:
                current_index = stock_options.index(st.session_state.selected_stock)
            
            selected = st.selectbox(
                "เลือกหุ้น", 
                stock_options, 
                format_func=lambda x: f"{analyzer.thai_stocks[x]} ({x})",
                index=current_index
            )
            st.session_state.selected_stock = selected
        
        # แสดงหุ้นที่กำลังวิเคราะห์
        st.info(f"📌 กำลังวิเคราะห์: {st.session_state.selected_stock}")
        
        # ระยะเวลา
        period = st.selectbox(
            "ระยะเวลา",
            options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
            index=4,
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
        
        # แสดงหุ้นในพอร์ต - ใช้คีย์ที่ถูกต้อง
        current_stock = st.session_state.selected_stock
        stock_name = analyzer.thai_stocks.get(current_stock, current_stock.split('.')[0])
        current_shares = portfolio.get_current_shares(current_stock)
        
        if current_shares > 0:
            avg_cost = portfolio.get_average_cost(current_stock)
            st.info(f"📊 {stock_name}: {current_shares} หุ้น @ ฿{avg_cost:.2f}")
        else:
            st.info(f"📊 {stock_name}: ยังไม่มีในพอร์ต")
        
        # เพิ่มหุ้น - ใช้ current_stock ที่ถูกต้อง
        with st.expander("➕ เพิ่มหุ้น"):
            st.caption(f"เพิ่ม {stock_name} ({current_stock})")
            shares = st.number_input("จำนวนหุ้น", min_value=1, value=100, step=100, key="buy_shares")
            buy_price = st.number_input("ราคาซื้อ", min_value=0.01, value=50.0, step=0.1, key="buy_price")
            if st.button("บันทึกการซื้อ", key="buy_btn"):
                portfolio.add_stock(current_stock, stock_name, shares, buy_price)
                st.success(f"✅ บันทึก {stock_name} จำนวน {shares} หุ้น ราคา {buy_price} บาท เรียบร้อย")
                st.rerun()
        
        # ขายหุ้น
        if current_shares > 0:
            with st.expander("➖ ขายหุ้น"):
                st.caption(f"ขาย {stock_name} ({current_stock})")
                sell_shares = st.number_input("จำนวนขาย", min_value=1, max_value=current_shares, value=min(100, current_shares), key="sell_shares")
                sell_price = st.number_input("ราคาขาย", min_value=0.01, value=50.0, step=0.1, key="sell_price")
                if st.button("บันทึกการขาย", key="sell_btn"):
                    if portfolio.sell_stock(current_stock, sell_shares, sell_price):
                        st.success(f"✅ ขาย {stock_name} จำนวน {sell_shares} หุ้น ราคา {sell_price} บาท เรียบร้อย")
                        st.rerun()
                    else:
                        st.error("❌ ไม่สามารถขายได้ จำนวนหุ้นไม่พอ")
        
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
                st.markdown(f"- แนวรับ 20 วัน: {sr_analysis['Support_20']['value']} (ห่าง {sr_analysis['Support_20']['distance']})")
                st.markdown(f"- แนวต้าน 20 วัน: {sr_analysis['Resistance_20']['value']} (ห่าง {sr_analysis['Resistance_20']['distance']})")
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
                        # ตรวจสอบให้แน่ใจว่าค่าอยู่ระหว่าง 0-1
                    progress_value = max(0.0, min(1.0, position / 100))
                    st.progress(progress_value, text="")
                
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
            'dividend': div_info['dividend_yield'],
            'name': stock_name
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
                        'code': 'รหัส',
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

    else:
        st.error(f"ไม่สามารถโหลดข้อมูล {st.session_state.selected_stock} ได้ กรุณาตรวจสอบรหัสหุ้นหรือลองใหม่อีกครั้ง")
        st.info("ตัวอย่างรหัสหุ้นที่ถูกต้อง: ADVANC.BK, PTT.BK, KBANK.BK, CPALL.BK, AOT.BK, SIRI.BK")

with tab2:
    st.header("🚀 สแกนหุ้นโมเมนตัม (เล่นสั้น)")
    st.markdown("ค้นหาหุ้นที่มีโมเมนตัมแข็งแกร่ง เหมาะสำหรับเล่นสั้นทำกำไร")
    
    # ส่วนควบคุมการสแกน - จัดกึ่งกลาง
    col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
    with col2:
        st.markdown("### ⚙️ ตั้งค่าการสแกน")
    with col3:
        limit = st.number_input("จำนวนหุ้น", min_value=5, max_value=50, value=20, step=5)
    with col4:
        scan_btn = st.button("🔍 เริ่มสแกน", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # ตัวแปรเก็บผลลัพธ์การสแกน
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = None
    if 'selected_scan_stock' not in st.session_state:
        st.session_state.selected_scan_stock = None
    
    # เมื่อกดปุ่มสแกน
    if scan_btn:
        with st.spinner("กำลังสแกนหุ้นทั้งหมด กรุณารอสักครู่..."):
            # แสดง progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # เรียกใช้ฟังก์ชันสแกน
            momentum_stocks = analyzer.scan_momentum_stocks(limit=limit)
            
            progress_bar.empty()
            status_text.empty()
            
            # เก็บผลลัพธ์ไว้ใน session state
            st.session_state.scan_results = momentum_stocks
            
            if momentum_stocks:
                st.success(f"✅ พบ {len(momentum_stocks)} หุ้นที่มีโมเมนตัม")
            else:
                st.warning("⚠️ ไม่พบหุ้นที่มีโมเมนตัมในขณะนี้")
    
    # แสดงผลการสแกน (ถ้ามี)
    if st.session_state.scan_results:
        momentum_stocks = st.session_state.scan_results
        
        # สร้าง DataFrame
        df_momentum = pd.DataFrame(momentum_stocks)
        
        # ตารางแสดงผลกว้างเต็ม
        st.subheader("📋 รายชื่อหุ้นที่มีโมเมนตัม")
        st.dataframe(
            df_momentum,
            column_config={
                'symbol': 'หุ้น',
                'code': 'รหัส',
                'price': st.column_config.NumberColumn('ราคา', format="฿%.2f"),
                'change_1d': st.column_config.NumberColumn('เปลี่ยน 1วัน', format="%.2f%%"),
                'change_5d': st.column_config.NumberColumn('เปลี่ยน 5วัน', format="%.2f%%"),
                'volume_ratio': st.column_config.NumberColumn('ปริมาณ', format="%.2f"),
                'rsi': st.column_config.NumberColumn('RSI', format="%.2f"),
                'momentum_score': 'คะแนน',
                'momentum_pct': st.column_config.NumberColumn('โมเมนตัม', format="%.0f%%"),
                'signal_type': 'สัญญาณ',
                'holding_period': 'ระยะถือ',
                'target': st.column_config.NumberColumn('เป้าหมาย', format="฿%.2f"),
                'stop_loss': st.column_config.NumberColumn('Cut loss', format="฿%.2f")
            },
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # เลือกหุ้นเพื่อดูกราฟ
        st.subheader("📊 ดูกราฟเทคนิคประกอบ")
        
        # สร้างรายชื่อหุ้นสำหรับ dropdown
        stock_options = [f"{row['symbol']} ({row['code']})" for _, row in df_momentum.iterrows()]
        
        selected_from_scan = st.selectbox(
            "เลือกหุ้นที่ต้องการดูกราฟ",
            options=stock_options,
            index=0 if stock_options else None,
            key="scan_stock_selector"
        )
        
        if selected_from_scan and selected_from_scan != st.session_state.selected_scan_stock:
            st.session_state.selected_scan_stock = selected_from_scan
            # รีเฟรชเพื่อแสดงกราฟ
            st.rerun()
        
        # แสดงกราฟของหุ้นที่เลือก
        if st.session_state.selected_scan_stock:
            # ดึงรหัสหุ้น
            stock_code = st.session_state.selected_scan_stock.split('(')[-1].split(')')[0]
            stock_name = st.session_state.selected_scan_stock.split('(')[0].strip()
            
            st.markdown(f"### 📈 {stock_name} ({stock_code})")
            
            # โหลดข้อมูลหุ้น
            with st.spinner("กำลังโหลดข้อมูลกราฟ..."):
                df_selected, info_selected = analyzer.get_stock_data(stock_code, period='3mo')
                
                if df_selected is not None and not df_selected.empty:
                    # คำนวณ indicators
                    df_selected = analyzer.calculate_indicators(df_selected)
                    
                    # สร้างกราฟ 3 แถว (เหมือนใน Tab1)
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
                            x=df_selected.index,
                            open=df_selected['Open'],
                            high=df_selected['High'],
                            low=df_selected['Low'],
                            close=df_selected['Close'],
                            name='ราคา',
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    
                    # เพิ่ม SMA
                    if 'SMA_20' in df_selected.columns:
                        fig.add_trace(
                            go.Scatter(x=df_selected.index, y=df_selected['SMA_20'], name='SMA 20', line=dict(color='orange', width=1)),
                            row=1, col=1
                        )
                    
                    if 'SMA_50' in df_selected.columns:
                        fig.add_trace(
                            go.Scatter(x=df_selected.index, y=df_selected['SMA_50'], name='SMA 50', line=dict(color='blue', width=1)),
                            row=1, col=1
                        )
                    
                    # เพิ่มปริมาณ
                    colors = ['green' if df_selected['Close'].iloc[i] >= df_selected['Open'].iloc[i] else 'red' for i in range(len(df_selected))]
                    fig.add_trace(
                        go.Bar(x=df_selected.index, y=df_selected['Volume'], name='ปริมาณ', marker_color=colors, opacity=0.3),
                        row=1, col=1
                    )
                    
                    # RSI
                    if 'RSI_14' in df_selected.columns:
                        fig.add_trace(
                            go.Scatter(x=df_selected.index, y=df_selected['RSI_14'], name='RSI 14', line=dict(color='purple', width=2)),
                            row=2, col=1
                        )
                        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
                    
                    # MACD
                    if 'MACD' in df_selected.columns and 'MACD_Signal' in df_selected.columns:
                        fig.add_trace(
                            go.Scatter(x=df_selected.index, y=df_selected['MACD'], name='MACD', line=dict(color='blue', width=1.5)),
                            row=3, col=1
                        )
                        fig.add_trace(
                            go.Scatter(x=df_selected.index, y=df_selected['MACD_Signal'], name='Signal', line=dict(color='red', width=1.5)),
                            row=3, col=1
                        )
                        
                        if 'MACD_Histogram' in df_selected.columns:
                            colors_macd = ['green' if val >= 0 else 'red' for val in df_selected['MACD_Histogram']]
                            fig.add_trace(
                                go.Bar(x=df_selected.index, y=df_selected['MACD_Histogram'], name='Histogram', marker_color=colors_macd, opacity=0.5),
                                row=3, col=1
                            )
                    
                    fig.update_layout(
                        height=600,
                        xaxis_rangeslider_visible=False,
                        showlegend=False
                    )
                    fig.update_xaxes(title_text="วันที่", row=3, col=1)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # สรุปสัญญาณสั้นๆ
                    st.subheader("📊 สรุปสัญญาณ")
                    latest = df_selected.iloc[-1]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        rsi_val = latest['RSI_14'] if 'RSI_14' in latest else 50
                        st.metric("RSI", f"{rsi_val:.2f}")
                    
                    with col2:
                        vol_ratio = latest['Volume_Ratio'] if 'Volume_Ratio' in latest else 1
                        vol_status = "สูง" if vol_ratio > 1.5 else "ปกติ" if vol_ratio > 0.8 else "ต่ำ"
                        st.metric("Volume Ratio", f"{vol_ratio:.2f}", vol_status)
                    
                    with col3:
                        if 'MACD' in latest and 'MACD_Signal' in latest:
                            macd_status = "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish"
                            st.metric("MACD", macd_status)
                        else:
                            st.metric("MACD", "N/A")
                    
                    with col4:
                        trend, _ = analyzer.get_trend_analysis(df_selected)
                        st.metric("แนวโน้ม", trend)
                    
                    # แนวรับ/แนวต้าน
                    sr = analyzer.get_support_resistance(df_selected)
                    if sr:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"🟢 แนวรับ: {sr['Support_20']['value']} (ห่าง {sr['Support_20']['distance']})")
                        with col2:
                            st.warning(f"🔴 แนวต้าน: {sr['Resistance_20']['value']} (ห่าง {sr['Resistance_20']['distance']})")
                else:
                    st.error("ไม่สามารถโหลดข้อมูลกราฟได้")

with tab3:
    st.header("💥 สแกนหุ้น breakout")
    st.markdown("หาหุ้นที่กำลังจะทะลุแนวต้าน มีโอกาสปรับตัวขึ้นแรง")
    
    if st.button("🔍 สแกนหุ้น breakout", key="scan_breakout"):
        with st.spinner("กำลังสแกนหุ้น..."):
            breakout_stocks = analyzer.scan_breakout_stocks(limit=20)
            
            if breakout_stocks:
                st.success(f"พบ {len(breakout_stocks)} หุ้นที่กำลังจะ breakout")
                
                df_breakout = pd.DataFrame(breakout_stocks)
                st.dataframe(
                    df_breakout,
                    column_config={
                        'symbol': 'หุ้น',
                        'code': 'รหัส',
                        'price': st.column_config.NumberColumn('ราคา', format="฿%.2f"),
                        'resistance_20': st.column_config.NumberColumn('แนวต้าน', format="฿%.2f"),
                        'dist_to_resistance': st.column_config.NumberColumn('ระยะห่าง', format="%.2f%%"),
                        'volume_ratio': st.column_config.NumberColumn('ปริมาณ', format="%.2f"),
                        'probability': 'โอกาส',
                        'breakout_type': 'ประเภท',
                        'target_1': st.column_config.NumberColumn('เป้า 1', format="฿%.2f"),
                        'target_2': st.column_config.NumberColumn('เป้า 2', format="฿%.2f"),
                        'stop_loss': st.column_config.NumberColumn('Cut loss', format="฿%.2f")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("ไม่พบหุ้นที่กำลังจะ breakout ในขณะนี้")

with tab4:
    st.header("📉 สแกนหุ้น oversold รอรีบาวด์")
    st.markdown("หาหุ้นที่ถูกขายมากเกินไป มีโอกาสรีบาวด์ทางเทคนิค")
    
    if st.button("🔍 สแกนหุ้นรีบาวด์", key="scan_rebound"):
        with st.spinner("กำลังสแกนหุ้น..."):
            rebound_stocks = analyzer.scan_oversold_rebound(limit=20)
            
            if rebound_stocks:
                st.success(f"พบ {len(rebound_stocks)} หุ้นที่ oversold และมีโอกาสรีบาวด์")
                
                df_rebound = pd.DataFrame(rebound_stocks)
                st.dataframe(
                    df_rebound,
                    column_config={
                        'symbol': 'หุ้น',
                        'code': 'รหัส',
                        'price': st.column_config.NumberColumn('ราคา', format="฿%.2f"),
                        'rsi_14': st.column_config.NumberColumn('RSI 14', format="%.2f"),
                        'rsi_7': st.column_config.NumberColumn('RSI 7', format="%.2f"),
                        'support': st.column_config.NumberColumn('แนวรับ', format="฿%.2f"),
                        'dist_to_support': st.column_config.NumberColumn('ระยะห่าง', format="%.2f%%"),
                        'probability': 'โอกาส',
                        'rebound_score': 'คะแนน',
                        'target_1': st.column_config.NumberColumn('เป้า 1', format="฿%.2f"),
                        'target_2': st.column_config.NumberColumn('เป้า 2', format="฿%.2f"),
                        'stop_loss': st.column_config.NumberColumn('Cut loss', format="฿%.2f")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("ไม่พบหุ้นที่ oversold ในขณะนี้")
with tab5:
    st.header("📊 DCA / EDCA Plan")
    st.markdown("วางแผนการลงทุนแบบ DCA (ลงทุนสม่ำเสมอ) และ EDCA (ซื้อเมื่อย่อ)")
    
    # โหลดคลาส
    analyzer = StockAnalyzer()
    portfolio = PortfolioManager()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💸 ข้อมูลการลงทุน")
        initial_investment = st.number_input("เงินลงทุนเริ่มต้น (บาท)", min_value=0, value=10000, step=1000)
        monthly_investment = st.number_input("เงินลงทุนต่อเดือน (บาท)", min_value=0, value=5000, step=500)
    
    with col2:
        st.subheader("📈 พอร์ตปัจจุบัน")
        current_shares = st.number_input("จำนวนหุ้นที่ถืออยู่", min_value=0, value=0, step=100)
        avg_cost = st.number_input("ต้นทุนเฉลี่ย (บาท/หุ้น)", min_value=0.0, value=0.0, step=0.5)
    
    # เลือกหุ้น
    stock_options = list(analyzer.thai_stocks.keys())
    selected_code = st.selectbox(
        "เลือกหุ้น",
        stock_options,
        format_func=lambda x: f"{analyzer.thai_stocks[x]} ({x})"
    )
    
    # กลยุทธ์
    strategy = st.selectbox("กลยุทธ์", ["DCA (ลงทุนสม่ำเสมอ)", "EDCA (ซื้อเมื่อย่อ)"])
    
    # ดึงข้อมูลราคา
    @st.cache_data(ttl=3600)
    def get_data(symbol):
        df, info = analyzer.get_stock_data(symbol, period="1y")
        if df is not None and not df.empty:
            df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
            return df
        return None
    
    with st.spinner("กำลังโหลดข้อมูล..."):
        df = get_data(selected_code)
    
    if df is not None:
        current_price = df['Close'].iloc[-1]
        st.metric("ราคาปัจจุบัน", f"฿{current_price:.2f}")
        
        st.markdown("---")
        
        # จำลอง DCA
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')
        
        total_shares = current_shares
        total_invested = current_shares * avg_cost if avg_cost > 0 else 0
        results = []
        
        for i, date in enumerate(monthly_dates):
            closest_idx = df.index.get_indexer([date], method='nearest')[0]
            price = df['Close'].iloc[closest_idx]
            
            invest = initial_investment if i == 0 else monthly_investment
            
            if strategy == "EDCA (ซื้อเมื่อย่อ)":
                if price < df['EMA200'].iloc[closest_idx]:
                    invest = invest * 1.5
                    note = "✨ EDCA (ซื้อเพิ่ม)"
                else:
                    note = "DCA ปกติ"
            else:
                note = "DCA ปกติ"
            
            shares_bought = invest / price if price > 0 else 0
            total_shares += shares_bought
            total_invested += invest
            
            results.append({
                "วันที่": date.strftime("%d/%m/%Y"),
                "ราคา": round(price, 2),
                "ต่ำกว่า EMA200?": "✅" if price < df['EMA200'].iloc[closest_idx] else "❌",
                "เงินลงทุน": f"฿{invest:,.0f}",
                "ซื้อได้": f"{shares_bought:.0f} หุ้น",
                "รวมหุ้น": f"{total_shares:.0f}",
                "รวมเงินลงทุน": f"฿{total_invested:,.0f}",
                "หมายเหตุ": note
            })
        
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        # สรุป
        avg_cost_new = total_invested / total_shares if total_shares > 0 else 0
        current_value = total_shares * current_price
        profit = current_value - total_invested
        profit_pct = (profit / total_invested) * 100 if total_invested > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("รวมหุ้น", f"{total_shares:.0f}")
        with col2:
            st.metric("ต้นทุนเฉลี่ย", f"฿{avg_cost_new:.2f}")
        with col3:
            st.metric("มูลค่าปัจจุบัน", f"฿{current_value:,.0f}")
        with col4:
            st.metric("กำไร/ขาดทุน", f"฿{profit:,.0f}", f"{profit_pct:.1f}%")
        
        # กราฟ
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคา'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], mode='lines', name='EMA200'))
        
        buy_dates = [datetime.strptime(r["วันที่"], "%d/%m/%Y") for r in results]
        buy_prices = [float(r["เงินลงทุน"].replace("฿", "").replace(",", "")) / float(r["ซื้อได้"].replace(" หุ้น", "")) for r in results]
        fig.add_trace(go.Scatter(x=buy_dates, y=buy_prices, mode='markers', name='จุดซื้อ', marker=dict(color='green', size=8)))
        
        fig.update_layout(title=f"ราคา {analyzer.thai_stocks[selected_code]}", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("ไม่สามารถดึงข้อมูลได้")

st.markdown("---")
st.caption("⚠️ ข้อมูลเพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำในการลงทุน ควรศึกษาข้อมูลเพิ่มเติมก่อนตัดสินใจลงทุน")
