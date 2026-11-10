"""Historical Yahoo Finance prices. Explicitly store raw and adjusted prices."""
from __future__ import annotations
from datetime import datetime
import pandas as pd

def normalize_prices(ticker: str, frame: pd.DataFrame) -> list[dict]:
    if frame is None or frame.empty:
        raise ValueError(f"No market price observations returned for {ticker}")
    rows = []
    for date, rec in frame.iterrows():
        day = pd.Timestamp(date).date().isoformat()
        close = rec.get("Close")
        if pd.isna(close) or float(close) <= 0:
            continue
        adjusted = rec.get("Adj Close")
        rows.append({"ticker": ticker, "price_date": day, "close_price": float(close),
                     "adjusted_close_price": None if adjusted is None or pd.isna(adjusted) else float(adjusted),
                     "currency": "USD", "source_url": f"https://finance.yahoo.com/quote/{ticker}/history/"})
    if not rows:
        raise ValueError(f"No valid prices returned for {ticker}")
    return rows

def download_prices(ticker: str, start: str, end: str) -> list[dict]:
    import yfinance as yf
    frame = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False, threads=False)
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    return normalize_prices(ticker, frame)
