import baostock as bs
import akshare as ak
import pandas as pd
from datetime import datetime

def get_hist_data_baostock(code, start_date, end_date):
    """
    从 baostock 获取 A 股历史日线数据（前复权）。
    参数:
        code: str, 股票代码，如 'sz.000001'
        start_date: str, 起始日期 'YYYY-MM-DD'
        end_date: str, 结束日期 'YYYY-MM-DD'
    返回:
        DataFrame，索引为 date，列包含 open, high, low, close, volume；
        如果获取失败返回 None。
    """
    # 登录 baostock（免费且无需注册）
    lg = bs.login()
    if lg.error_code != '0':
        print(f"⚠️ baostock 登录警告: {lg.error_msg}")
    
    # 查询历史日K线
    rs = bs.query_history_k_data_plus(
        code,
        "date,open,high,low,close,volume",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2"      # 2：前复权
    )
    
    # 将返回的迭代器转换为 list
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    bs.logout()
    
    if len(data_list) == 0:
        print(f"⚠️ 未获取到数据，请检查股票代码 {code} 或日期范围。")
        return None
    
    # 转为 DataFrame 并处理数据类型
    df = pd.DataFrame(data_list, columns=rs.fields)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    
    return df


def get_realtime_akshare(code):
    """
    从 akshare 获取实时行情快照。
    参数:
        code: str, baostock 格式代码，如 'sz.000001'
    返回:
        dict: {'price': 最新价, 'change_pct': 涨跌幅, 'volume': 成交量, 'time': 查询时间}
        失败返回 None。
    """
    # baostock 格式 'sz.000001' → akshare 格式 '000001'
    symbol = code.split('.')[1]
    try:
        # 获取沪深A股实时行情数据
        df = ak.stock_zh_a_spot_em()
        stock_info = df[df['代码'] == symbol]
        if not stock_info.empty:
            return {
                'price': float(stock_info['最新价'].values[0]),
                'change_pct': float(stock_info['涨跌幅'].values[0]),
                'volume': float(stock_info['成交量'].values[0]),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        print(f"⚠️ 获取实时行情失败: {e}")
    return None
import akshare as ak

def get_hist_data_akshare(symbol, start_date, end_date, adjust="qfq"):
    """
    从 akshare 获取 A 股历史日线数据（前复权），作为备用数据源。
    symbol: 纯数字代码，如 '000001'
    start_date/end_date: 'YYYY-MM-DD' 格式
    """
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', ''),
            adjust=adjust
        )
        df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        print(f"akshare 获取失败: {e}")
        return None

def get_hist_data(code, start_date, end_date):
    """
    统一数据接口：先尝试 baostock，失败则用 akshare。
    code 格式：'sz.000001' 或 'sh.600519'
    """
    # 先尝试 baostock
    try:
        df = get_hist_data_baostock(code, start_date, end_date)
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        print(f"baostock 获取失败，切换到 akshare: {e}")
    
    # 回退到 akshare
    symbol = code.split('.')[1]  # 从 'sz.000001' 提取 '000001'
    return get_hist_data_akshare(symbol, start_date, end_date)