import pandas as pd
import numpy as np

def compute_backtest(df, signal_col='pred_dir', price_col='close', 
                     initial_capital=100000, commission_rate=0.001,
                     slippage=0.001):
    """
    基于预先生成的交易信号进行向量化回测。
    
    参数:
        df: DataFrame，必须包含 price_col 和 signal_col。
            signal_col 的值应为 1（买入/持仓）或 0（卖出/空仓）。
        initial_capital: 初始资金。
        commission_rate: 单边手续费率（如 0.001 表示 0.1%）。
        slippage: 滑点比例（如 0.001 表示 0.1%）。
    
    返回:
        dict: {
            'nav': 净值序列 (pandas Series)，
            'total_return': 累计收益率，
            'annual_return': 年化收益率，
            'annual_volatility': 年化波动率，
            'sharpe_ratio': 夏普比率（假设无风险利率为0），
            'max_drawdown': 最大回撤，
            'win_rate': 胜率（按交易日），
            'profit_loss_ratio': 盈亏比
        }
    """
    df = df.copy()
    # 确保索引为日期
    df.index = pd.to_datetime(df.index)
    
    # 计算日收益率
    df['ret'] = df[price_col].pct_change()
    
    # 为避免未来函数，信号必须滞后一天：今天信号决定明天交易
    df['trade_signal'] = df[signal_col].shift(1)
    df['trade_signal'] = df['trade_signal'].fillna(0).astype(int)
    
    # 策略日收益：当信号为1时，持有资产获得当日收益；信号为0时空仓收益为0
    df['strategy_ret'] = df['trade_signal'] * df['ret']
    
    # 考虑交易成本：当信号发生变动时（今天信号与昨天信号不同），扣除成本
    df['signal_change'] = df['trade_signal'].diff().abs()
    # 每次信号转换（0→1 或 1→0）产生一次交易，成本 = 佣金 + 滑点
    cost_rate = commission_rate + slippage
    df['cost'] = df['signal_change'] * cost_rate
    df['strategy_ret_net'] = df['strategy_ret'] - df['cost']
    
    # 计算净值
    df['nav'] = (1 + df['strategy_ret_net']).cumprod() * initial_capital
    
    # 净值序列
    nav = df['nav'].dropna()
    
    # ---- 计算绩效指标 ----
    # 累计收益率
    total_return = (nav.iloc[-1] / initial_capital) - 1
    
    # 年化收益率（假设252个交易日）
    trading_days = len(nav)
    annual_return = (nav.iloc[-1] / initial_capital) ** (252 / trading_days) - 1
    
    # 日收益率序列
    daily_returns = df['strategy_ret_net'].dropna()
    annual_volatility = daily_returns.std() * np.sqrt(252)
    
    # 夏普比率（无风险利率设为0）
    sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() != 0 else 0
    
    # 最大回撤
    cummax = nav.cummax()
    drawdown = nav / cummax - 1
    max_drawdown = drawdown.min()
    
    # 胜率、盈亏比（基于有交易的交易日）
    positive_ret = daily_returns[daily_returns > 0]
    negative_ret = daily_returns[daily_returns < 0]
    win_rate = len(positive_ret) / (len(positive_ret) + len(negative_ret)) if len(daily_returns) > 0 else 0
    avg_win = positive_ret.mean() if len(positive_ret) > 0 else 0
    avg_loss = abs(negative_ret.mean()) if len(negative_ret) > 0 else 0
    profit_loss_ratio = avg_win / avg_loss if avg_loss != 0 else np.nan
    
    return {
        'nav': nav,
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio
    }