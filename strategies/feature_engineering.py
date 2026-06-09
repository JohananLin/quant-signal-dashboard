import pandas as pd
import numpy as np

def create_features(df):
    """
    从原始OHLCV数据中构造技术因子，并创建预测标签。

    参数:
        df: DataFrame，索引为日期，必须包含 'close', 'volume'
    返回:
        DataFrame，包含所有因子和标签，已删除含NaN的行
    """
    df = df.copy()
    
    # ---- 收益率相关 ----
    df['ret1'] = df['close'].pct_change()               # 日收益率
    
    # ---- 动量因子 ----
    df['mom5'] = df['close'].pct_change(5)               # 5日动量
    df['mom10'] = df['close'].pct_change(10)             # 10日动量
    df['mom20'] = df['close'].pct_change(20)             # 20日动量
    
    # ---- 波动率因子 ----
    df['vol5'] = df['ret1'].rolling(5).std()             # 5日波动率
    df['vol20'] = df['ret1'].rolling(20).std()           # 20日波动率
    
    # ---- 均价偏离因子 ----
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['dist_ma5'] = (df['close'] - df['ma5']) / df['ma5']   # 收盘价相对于MA5的偏离
    df['dist_ma20'] = (df['close'] - df['ma20']) / df['ma20']
    
    # ---- 成交量因子 ----
    df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()  # 量比
    
    # ---- 标签：未来1日涨跌 ----
    df['target_ret'] = df['close'].pct_change().shift(-1)   # 下一日收益率
    df['target_dir'] = (df['target_ret'] > 0).astype(int)   # 1表示涨，0表示跌
    
    # 删除包含NaN的行（因子窗口期产生的空值）
    df.dropna(inplace=True)
    
    return df


# 为了方便，可以直接定义特征列名列表
FEATURE_COLS = [
    'mom5', 'mom10', 'mom20',
    'vol5', 'vol20',
    'dist_ma5', 'dist_ma20',
    'volume_ratio'
]