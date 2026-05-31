import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils.data import get_hist_data_baostock
from strategies.ma_cross import calculate_ma_signals, get_latest_signal
from strategies.momentum import get_latest_rotation_signal

# ---------- 页面设置 ----------
st.set_page_config(page_title="量化信号看板", page_icon="📈", layout="wide")

# 移动端优化CSS
st.markdown("""
<style>
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem; }
        h1 { font-size: 1.5rem !important; }
        .stButton button { min-height: 44px; font-size: 16px; }
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 我的量化策略看板")
st.markdown("---")

# ---------- 侧边栏 ----------
st.sidebar.header("⚙️ 控制面板")
strategy_choice = st.sidebar.selectbox(
    "选择策略",
    ["双均线策略 (MA Cross)", "动量轮动策略 (Momentum Rotation)"]
)

if strategy_choice.startswith("双均线"):
    stock_code = st.sidebar.text_input("股票代码 (baostock格式)", value="sz.000001")
else:
    stock_code = None
    st.sidebar.info("默认股票池：平安银行、万科A、贵州茅台、宁德时代、中国平安")

st.sidebar.markdown("---")
st.sidebar.info("数据来源：baostock | 建议每5分钟手动刷新")
refresh_btn = st.sidebar.button("🔄 刷新数据")

if refresh_btn:
    st.session_state['data_loaded'] = True
if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False

# ---------- Tab 页面结构 ----------
tab1, tab2, tab3 = st.tabs(["📊 当前信号", "📈 策略对比", "ℹ️ 关于"])

with tab1:
    col1, col2, col3 = st.columns(3)
    metric_position = col1.empty()
    metric_signal = col2.empty()
    metric_price = col3.empty()
    chart_placeholder = st.empty()
    detail_placeholder = st.empty()
    
    if st.session_state['data_loaded']:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # ===== 双均线 =====
        if strategy_choice.startswith("双均线"):
            with st.spinner("获取数据..."):
                df = get_hist_data_baostock(stock_code, start_date, end_date)
            if df is not None and len(df) > 30:
                df_signal = calculate_ma_signals(df, 5, 20)
                signal_text, position_text = get_latest_signal(df_signal)
                metric_position.metric("持仓状态", position_text)
                metric_signal.metric("最新信号", signal_text)
                price = df_signal['close'].iloc[-1]
                date_str = df_signal.index[-1].strftime('%Y-%m-%d')
                metric_price.metric(f"收盘价 ({date_str})", f"¥{price:.2f}")
                
                plot_df = df_signal.iloc[-100:]
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['open'],
                    high=plot_df['high'], low=plot_df['low'], close=plot_df['close'],
                    name='K线', increasing_line_color='red', decreasing_line_color='green'))
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['ma_short'],
                    line=dict(color='blue', width=1.5), name='MA5'))
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['ma_long'],
                    line=dict(color='orange', width=1.5), name='MA20'))
                buy = plot_df[plot_df['signal']==1]
                sell = plot_df[plot_df['signal']==-1]
                fig.add_trace(go.Scatter(x=buy.index, y=buy['low']*0.98,
                    mode='markers', marker=dict(symbol='triangle-up', size=12, color='red'), name='买入'))
                fig.add_trace(go.Scatter(x=sell.index, y=sell['high']*1.02,
                    mode='markers', marker=dict(symbol='triangle-down', size=12, color='green'), name='卖出'))
                fig.update_layout(title=f"{stock_code} - 双均线", height=500,
                    template='plotly_white', hovermode='x unified')
                fig.update_xaxes(rangeslider_visible=False)
                chart_placeholder.plotly_chart(fig, use_container_width=True)
                
                recent = df_signal[df_signal['signal']!=0].tail(10)
                if not recent.empty:
                    detail_placeholder.markdown("#### 📋 近期信号")
                    disp = recent[['close','signal']].copy()
                    disp['信号'] = disp['signal'].map({1:'🟢买入', -1:'🔴卖出'})
                    disp['日期'] = disp.index.strftime('%Y-%m-%d')
                    detail_placeholder.dataframe(disp[['日期','close','信号']],
                        use_container_width=True, hide_index=True)
            else:
                st.error(f"❌ 无法获取 {stock_code} 的数据")
        
        # ===== 动量轮动 =====
        else:
            stocks = {"平安银行":"sz.000001","万科A":"sz.000002","贵州茅台":"sh.600519",
                      "宁德时代":"sz.300750","中国平安":"sh.601318"}
            with st.spinner("获取多只股票数据..."):
                all_data = {}
                for name, code in stocks.items():
                    df = get_hist_data_baostock(code, start_date, end_date)
                    if df is not None:
                        all_data[name] = df
            if len(all_data) < 3:
                st.error("❌ 数据不足")
            else:
                result = get_latest_rotation_signal(all_data, 60, 2)
                metric_position.metric("持仓", ", ".join(result['holdings']))
                metric_signal.metric("信号", result['signal_text'])
                if result['holdings']:
                    top = result['holdings'][0]
                    price = all_data[top]['close'].iloc[-1]
                    metric_price.metric(f"{top}收盘价", f"¥{price:.2f}")
                else:
                    metric_price.metric("参考价", "-")
                
                names = [x[0] for x in result['rankings']]
                values = [x[1] for x in result['rankings']]
                colors = ['red' if name in result['holdings'] else 'lightgray' for name in names]
                fig = go.Figure(go.Bar(x=names, y=values, marker_color=colors,
                    text=[f"{v:.2%}" for v in values], textposition='auto'))
                fig.update_layout(title="动量排名（60日）", height=400, template='plotly_white')
                chart_placeholder.plotly_chart(fig, use_container_width=True)
                
                detail_placeholder.markdown("#### 📊 动量排名表")
                rank_df = pd.DataFrame(result['rankings'], columns=['股票','动量值'])
                rank_df['动量值'] = rank_df['动量值'].apply(lambda x: f"{x:.2%}")
                rank_df['持仓'] = rank_df['股票'].apply(lambda x: '✅' if x in result['holdings'] else '')
                detail_placeholder.dataframe(rank_df, use_container_width=True, hide_index=True)
    else:
        chart_placeholder.info("👈 请点击侧边栏「刷新数据」按钮加载图表")

with tab2:
    st.subheader("策略表现对比（示例数据）")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("双均线夏普比率", "0.85")
    with col_b:
        st.metric("动量轮动夏普比率", "1.12")
    with col_c:
        st.metric("基准买入持有", "0.60")
    st.markdown("> 以上数据为示意，真实绩效需结合回测引擎（可在后续扩展中接入Day 4的回测代码）")

with tab3:
    st.markdown("""
    ### 📖 使用说明
    - **双均线策略**：当 MA5 上穿 MA20 时产生买入信号，下穿时卖出。
    - **动量轮动策略**：每月末选取过去60日涨幅最高的2只股票持有。
    - **数据源**：baostock（免费A股历史数据）。
    - **刷新频率**：建议每天收盘后手动刷新查看最新信号。
    
    ### ⚠️ 风险提示
    本工具仅供学习参考，不构成任何投资建议。策略回测基于历史数据，未来表现可能与回测结果存在重大差异。
    """)