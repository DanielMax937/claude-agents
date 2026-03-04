#!/usr/bin/env python3
"""
Market Data Fetcher for A-Shares and Chinese Futures
获取A股和中国期货市场的日交易数据

Usage:
    python market_data_fetcher.py <symbol> [start_date] [end_date]

Examples:
    python market_data_fetcher.py 000001              # 平安银行 (A股)
    python market_data_fetcher.py 600519              # 贵州茅台 (A股)
    python market_data_fetcher.py RB2501              # 螺纹钢期货
    python market_data_fetcher.py M2501               # 豆粕期货
    python market_data_fetcher.py 000001 2024-01-01 2024-12-31  # 指定日期范围
"""

import sys
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

import akshare as ak
import pandas as pd


def detect_symbol_type(symbol: str) -> str:
    """
    检测证券类型

    Args:
        symbol: 证券代码

    Returns:
        "stock" 或 "futures"
    """
    # A股代码: 6位纯数字
    # 期货代码: 字母+数字组合 (如 RB2501, M2501, IF2501)
    if re.match(r'^\d{6}$', symbol):
        return "stock"
    elif re.match(r'^[A-Za-z]+\d+$', symbol):
        return "futures"
    else:
        raise ValueError(f"无法识别的证券代码格式: {symbol}")


def get_stock_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"  # qfq=前复权, hfq=后复权, ""=不复权
) -> pd.DataFrame:
    """
    获取A股日线数据

    Args:
        symbol: 股票代码 (如 000001, 600519)
        start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
        end_date: 结束日期 (YYYYMMDD 或 YYYY-MM-DD)
        adjust: 复权类型

    Returns:
        包含 OHLCV 的 DataFrame
    """
    # 标准化日期格式
    if start_date:
        start_date = start_date.replace("-", "")
    if end_date:
        end_date = end_date.replace("-", "")

    # 默认日期范围
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    print(f"获取A股数据: {symbol}")
    print(f"日期范围: {start_date} 至 {end_date}")
    print(f"复权方式: {adjust or '不复权'}")
    print("-" * 50)

    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )

    # 标准化列名
    column_mapping = {
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount',
        '振幅': 'amplitude',
        '涨跌幅': 'pct_change',
        '涨跌额': 'change',
        '换手率': 'turnover'
    }
    df = df.rename(columns=column_mapping)

    return df


def get_futures_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    获取期货日线数据

    Args:
        symbol: 期货合约代码 (如 RB2501, M2501)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    Returns:
        包含 OHLCV 的 DataFrame
    """
    # 标准化合约代码为小写
    symbol_lower = symbol.lower()

    print(f"获取期货数据: {symbol.upper()}")
    print("-" * 50)

    # 尝试从新浪获取数据
    try:
        df = ak.futures_zh_daily_sina(symbol=symbol_lower)
    except Exception as e:
        # 尝试大写
        try:
            df = ak.futures_zh_daily_sina(symbol=symbol.upper())
        except Exception:
            raise ValueError(f"获取期货数据失败: {symbol}. 错误: {e}")

    # 标准化列名
    column_mapping = {
        'date': 'date',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'hold': 'open_interest'
    }
    df = df.rename(columns=column_mapping)

    # 过滤日期范围
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df['date'] >= start_dt]

        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df['date'] <= end_dt]

    return df


def fetch_market_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """
    获取市场数据 (自动识别股票或期货)

    Args:
        symbol: 证券代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        (DataFrame, 证券类型)
    """
    symbol_type = detect_symbol_type(symbol)

    if symbol_type == "stock":
        df = get_stock_data(symbol, start_date, end_date)
    else:
        df = get_futures_data(symbol, start_date, end_date)

    return df, symbol_type


def format_output(df: pd.DataFrame, symbol_type: str) -> str:
    """格式化输出"""
    if df.empty:
        return "无数据"

    # 选择核心列
    core_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    available_columns = [c for c in core_columns if c in df.columns]

    display_df = df[available_columns].copy()

    # 格式化日期
    if 'date' in display_df.columns:
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')

    return display_df.to_string(index=False)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    symbol = sys.argv[1]
    start_date = sys.argv[2] if len(sys.argv) > 2 else None
    end_date = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        df, symbol_type = fetch_market_data(symbol, start_date, end_date)

        print(f"\n证券类型: {'A股' if symbol_type == 'stock' else '期货'}")
        print(f"数据条数: {len(df)}")
        print("\n" + "=" * 70)
        print(format_output(df, symbol_type))
        print("=" * 70)

        # 显示统计摘要
        if not df.empty and 'close' in df.columns:
            print(f"\n统计摘要:")
            print(f"  最高收盘价: {df['close'].max():.2f}")
            print(f"  最低收盘价: {df['close'].min():.2f}")
            print(f"  平均收盘价: {df['close'].mean():.2f}")
            if 'volume' in df.columns:
                print(f"  平均成交量: {df['volume'].mean():,.0f}")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
