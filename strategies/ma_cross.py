import pandas as pd
import numpy as np

def calculate_ma_signals(df, short_window=5, long_window=20):
    """
    在传入的 DataFrame 上计算双均线、金叉死叉信号及持仓状态。

    参数:
        df: DataFrame，必须包含 'close' 列，索引为日期。
        short_window: 短期均线窗口，默认 5。
        long_window: 长期均线窗口，默认 20。

    返回:
        DataFrame，新增列：
        - ma_short: 短期均线
        - ma_long: 长期均线
        - signal: 1=买入，-1=卖出，0=无信号
        - position: 1=持仓，0=空仓
    """
    df = df.copy()
    
    # 计算短期和长期移动平均线
    df['ma_short'] = df['close'].rolling(window=short_window).mean()
    df['ma_long'] = df['close'].rolling(window=long_window).mean()
    
    # 初始化信号列
    df['signal'] = 0
    df['position'] = 0
    
    # 金叉条件：今日短均 > 长均，并且昨日短均 <= 长均
    golden_cross = (
        (df['ma_short'] > df['ma_long']) & 
        (df['ma_short'].shift(1) <= df['ma_long'].shift(1))
    )
    # 死叉条件：今日短均 < 长均，并且昨日短均 >= 长均
    dead_cross = (
        (df['ma_short'] < df['ma_long']) & 
        (df['ma_short'].shift(1) >= df['ma_long'].shift(1))
    )
    
    df.loc[golden_cross, 'signal'] = 1
    df.loc[dead_cross, 'signal'] = -1
    
    # 持仓状态：短均在长均之上就持仓，否则空仓
    df.loc[df['ma_short'] > df['ma_long'], 'position'] = 1
    df.loc[df['ma_short'] < df['ma_long'], 'position'] = 0
    # 均线相等时保持前一日持仓（用前向填充）
    df['position'] = df['position'].replace(0, np.nan).ffill().fillna(0).astype(int)
    
    return df


def get_latest_signal(df):
    """
    从带有信号列的 DataFrame 中提取最新信号状态。

    参数:
        df: DataFrame，必须包含 'signal' 和 'position' 列。

    返回:
        tuple: (信号文字, 持仓文字)
    """
    if df is None or len(df) == 0:
        return "⚪ 无信号", "⚪ 空仓"
    
    latest = df.iloc[-1]
    signals = df[df['signal'] != 0]
    
    if len(signals) > 0:
        last_signal = signals.iloc[-1]
        if last_signal['signal'] == 1:
            signal_text = "🟢 买入"
        else:
            signal_text = "🔴 卖出"
    else:
        signal_text = "⚪ 无信号"
    
    if latest['position'] == 1:
        position_text = "🟢 持仓中"
    else:
        position_text = "⚪ 空仓"
    
    return signal_text, position_text