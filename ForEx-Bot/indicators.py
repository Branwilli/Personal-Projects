import numpy as np
import pandas as pd

df = pd.read_csv('EURUSD1.csv', sep='\t', header=None)

def standardize_df(df):
    df.columns = ["datetime","open","high","low","close","volume"]
    
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    
    df = df.loc[df.index >= df.index.max() - pd.Timedelta(days=365)]
    df = df.resample('15min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def add_features(df):

    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected DataFrame, got {type(df)}")

    if 'close' not in df.columns:
        raise ValueError("Missing 'close' column")

    #Returns 
    df['ret_1'] = df['close'].pct_change(1)
    df['ret_5'] = df['close'].pct_change(5)

    #Volatility
    df['volatility'] = df['ret_1'].ewm(span=20, adjust=False).std()
    df['volatility_spike'] = df['volatility'] / df['volatility'].ewm(span=50, adjust=False).mean()

    #Volume
    df['volume_spike'] = df['volume'] / df['volume'].ewm(span=20, adjust=False).mean()

    #Range
    df['range'] = df['high'] - df['low']
    df['range_expansion'] = df['range'] / df['range'].ewm(span=20, adjust=False).mean()

    #Breakouts
    df['rolling_high'] = df['high'].cummax()
    df['rolling_low'] = df['low'].cummin()

    df['high_break'] = (df['close'] > df['rolling_high'].shift(1)).astype(int)
    df['low_break'] = (df['close'] < df['rolling_low'].shift(1)).astype(int)

    #Moving Averages
    df['ma_10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['ma_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['trend_strength'] = df['ma_10'] - df['ma_20']

    #Momentum 
    df['momentum_5'] = df['close'].pct_change(5)

    #RSI
    df['RSI'] = compute_rsi(df['close'])

    #Multi-timeframe 
    df_1h = df.resample('1h').last()
    df['hourly_trend'] = df_1h['close'].ewm(span=20, adjust=False).mean().reindex(df.index, method='ffill')
    
    df_daily = df.resample('1D').last()
    df['daily_trend'] = df_daily['close'].ewm(span=50).mean().reindex(df.index, method='ffill')

    df['htf_bias'] = (df['close'] > df['daily_trend']).astype(int)
    df['htf_bias_hourly'] = (df['close'] > df['hourly_trend']).astype(int)
    
    #Opportunity Interactions 
    df['vol_trend'] = df['volatility'] * df['trend_strength']
    df['vol_spike_strength'] = df['volatility_spike'] * df['range_expansion']
    df['volume_vol'] = df['volume_spike'] * df['volatility']
    df['expansion_strength'] = df['range_expansion'] * df['trend_strength']

    #Direction Interactions 
    df['rsi_mom'] = df['RSI'] * df['momentum_5']
    df['trend_bias'] = df['trend_strength'] * df['htf_bias']
    df['multi_tf_trend'] = df['hourly_trend'] * df['daily_trend']
    df['break_direction'] = df['high_break'] - df['low_break']

    # Bullish/Bearish Interactions
    df['bullish_signal'] = ((df['trend_strength'] > 0).astype(int) * (df['momentum_5'] > 0).astype(int) * (df['RSI'] > 50).astype(int))

    df['bearish_signal'] = ((df['trend_strength'] < 0).astype(int) * (df['momentum_5'] < 0).astype(int) * (df['RSI'] < 50).astype(int))

    df['bullish_rebound'] = ((df['hourly_trend'] > 0) & (df['RSI'] < 30) & (df['momentum_5'] > 0)).astype(int)
    df['bearish_rebound'] = ((df['hourly_trend'] < 0) & (df['RSI'] > 70) & (df['momentum_5'] < 0)).astype(int)

    df['bullish_continuation'] = ((df['hourly_trend'] > 0) & (df['momentum_5'] > 0) & (df['high_break'] == 1)).astype(int)
    df['bearish_continuation'] = ((df['hourly_trend'] < 0) & (df['momentum_5'] < 0) & (df['low_break'] == 1)).astype(int)

    #Hybrid Features 
    df['trend_vol_mom'] = df['trend_strength'] * df['volatility'] * df['momentum_5']
    df['rsi_trend'] = df['RSI'] * df['trend_strength']
    
    df['trend_norm'] = df['trend_strength'] / (df['volatility'] + 1e-9)
    df['rsi_centered'] = df['RSI'] - 50
    df['momentum_sign'] = np.sign(df['momentum_5'])

    df['trend_rsi'] = df['trend_norm'] * df['rsi_centered']
    df['trend_mom'] = df['trend_norm'] * df['momentum_5']
    df['direction_strength'] = df['trend_strength'] * df['momentum_5']

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.ffill().bfill()

    return df

def filter_data(df):
    trend_std = df['trend_strength'].rolling(50).std()

    mask = abs(df['trend_strength']) > trend_std

    return df[mask]

def add_targets(df):
    df = df.copy()

    future_return = df['close'].shift(-1) /df['close'] - 1

    threshold = abs(future_return).quantile(0.70)
    
    #Stage 1: Opportunity
    cond = (
        (df['trend_strength'] > df['trend_strength'].rolling(50).mean()).astype(int) +
        (df['volatility'] > df['volatility'].rolling(50).mean()).astype(int) +
        (df['vol_trend'] > df['vol_trend'].rolling(50).mean()).astype(int) +
        (df['momentum_5'].abs() > df['momentum_5'].rolling(50).mean()).astype(int) 
    )

    df['target_opportunity'] = (
        (abs(future_return) > threshold) &
        (cond >= 2)
    ).astype(int)

    #Stage 2: Direction
    direction_cond = (
        (df['volatility_spike'] > df['volatility_spike'].rolling(50).mean()).astype(int) +
        (df['volume_spike'] > df['volume_vol'].rolling(50).mean()).astype(int) +
        (df['trend_strength'].abs() > df['trend_strength'].rolling(50).mean()).astype(int)
    )
    
    df['target_direction'] = np.where(
        (future_return > df['volatility']) & (direction_cond >= 1) & (df['bullish_signal'] == 1), 1,
        np.where((future_return < -df['volatility']) & (direction_cond >= 1) & (df['bearish_signal'] == 1), 0, np.nan)
    )
    return df

