import pandas as pd
import numpy as np

# 默认股票池（你可以自行增减）
DEFAULT_POOL = {
    "平安银行": "sz.000001",
    "万科A": "sz.000002",
    "贵州茅台": "sh.600519",
    "宁德时代": "sz.300750",
    "中国平安": "sh.601318"
}

def calculate_momentum_scores(hist_data_dict, mom_window=60):
    """
    计算每只股票的最新动量值（过去 mom_window 日的累计收益率）。
    
    参数:
        hist_data_dict: dict, {股票名: DataFrame}，每个 DataFrame 必须包含 'close' 列，索引为日期。
        mom_window: 动量窗口，默认60。
    
    返回:
        dict: {股票名: 动量值}，未排序。
    """
    scores = {}
    for name, df in hist_data_dict.items():
        if df is None or len(df) < mom_window:
            scores[name] = np.nan
            continue
        df = df.copy()
        df['ret'] = df['close'].pct_change()
        # 过去60日累计收益
        df['momentum'] = df['ret'].rolling(mom_window).apply(
            lambda x: (1 + x).prod() - 1, raw=False
        )
        latest = df['momentum'].iloc[-1]
        scores[name] = latest if not np.isnan(latest) else np.nan
    return scores


def get_top_holdings(scores, top_n=2):
    """
    根据动量分数选出前 top_n 只股票。
    
    返回: list of (股票名, 动量值)，按动量降序排列。
    """
    # 剔除 nan 值
    valid_scores = {k: v for k, v in scores.items() if not np.isnan(v)}
    if len(valid_scores) == 0:
        return []
    sorted_scores = sorted(valid_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores[:top_n]


def get_latest_rotation_signal(all_data_dict, mom_window=60, top_n=2):
    """
    获取动量轮动策略的最新持仓建议。
    
    参数:
        all_data_dict: {股票名: DataFrame}
        mom_window: 动量窗口
        top_n: 持仓数量
    
    返回:
        dict:
        {
            'holdings': ['股票A', '股票B'],
            'holdings_detail': [('股票A', 0.15), ('股票B', 0.12)],
            'signal_text': 持仓信号文字,
            'rankings': 完整排序列表 [(股票名, 动量值), ...]
        }
    """
    scores = calculate_momentum_scores(all_data_dict, mom_window)
    top_holdings = get_top_holdings(scores, top_n)
    
    holdings_names = [name for name, score in top_holdings]
    
    if len(holdings_names) > 0:
        signal_text = f"🟢 持仓: {', '.join(holdings_names)}"
    else:
        signal_text = "⚪ 无足够数据"
    
    return {
        'holdings': holdings_names,
        'holdings_detail': top_holdings,
        'signal_text': signal_text,
        'rankings': sorted(scores.items(), key=lambda x: x[1], reverse=True)
    }