import yfinance as yf
import pandas as pd
import time
import random
import requests
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from .models import Stock, StockData

def fetch_stock_data_with_backoff(symbol, period='1y', max_retries=None, base_delay=None, session=None):
    """
    Fetch historical stock data using Yahoo Finance API with exponential backoff for rate limiting
    
    Args:
        symbol (str): Stock symbol (e.g., AAPL)
        period (str): Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        max_retries (int): Maximum number of retry attempts
        base_delay (int): Base delay in seconds for backoff
        
    Returns:
        tuple: (DataFrame with historical stock data or None if an error occurs, company_info dict)
    """
    # Use settings if available, otherwise use defaults
    if max_retries is None:
        max_retries = getattr(settings, 'STOCK_API_MAX_RETRIES', 5)
    
    if base_delay is None:
        base_delay = getattr(settings, 'STOCK_API_BACKOFF_FACTOR', 2)
    
    # Check cache first
    cache_key = f"stock_data_{symbol}_{period}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print(f"Using cached data for {symbol}")
        return cached_data
    
    for attempt in range(max_retries):
        try:
            # Fetch data from Yahoo Finance
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)
            
            if data.empty:
                print(f"{symbol}: No price data found, symbol may be delisted (period={period})")
                return None, None
            
            # Get company info
            try:
                info = stock.info
                name = info.get('shortName', info.get('longName', symbol))
            except Exception as info_err:
                print(f"Error fetching info for {symbol}: {info_err}")
                name = symbol
                info = {}
            
            # Cache the data for 1 hour (3600 seconds)
            cache.set(cache_key, (data, info), 3600)
            
            return data, info
            
        except Exception as e:
            # Check if it's a rate limiting error (may need to adjust based on actual error message)
            if "429" in str(e) or "Too Many Requests" in str(e):
                if attempt < max_retries - 1:
                    # Calculate delay with exponential backoff and jitter
                    delay = (2 ** attempt) * base_delay + random.uniform(0, 1)
                    print(f"Rate limited for {symbol}. Retrying in {delay:.2f} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print(f"Maximum retries reached for {symbol}")
                    return None, None
            else:
                print(f"Failed to get ticker '{symbol}' reason: {str(e)}")
                return None, None
    
    return None, None

def fetch_stock_data(symbol, period='1y', session=None):

    """
    Fetch historical stock data using Yahoo Finance API
    
    Args:
        symbol (str): Stock symbol (e.g., AAPL)
        period (str): Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        pandas.DataFrame: DataFrame with historical stock data or None if an error occurs
    """
   
    result = fetch_stock_data_with_backoff(symbol, period)

    
    if result is None or result[0] is None:
        return None
    
    data, info = result
    
    try:
        # Get company name
        name = info.get('shortName', info.get('longName', symbol))
        
        # Save stock to database if it doesn't exist
        stock_obj, created = Stock.objects.get_or_create(
            symbol=symbol,
            defaults={'name': name}
        )
        
        # If not created, update the name in case it changed
        if not created:
            stock_obj.name = name
            stock_obj.save()
        
        # Clean data and reset index to make date a column
        data = data.reset_index()
        
        # Convert date column to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(data['Date']):
            data['Date'] = pd.to_datetime(data['Date'])
        
        # Store historical data in the database - use bulk_create for better performance
        stock_data_objects = []
        for _, row in data.iterrows():
            stock_data = StockData(
                stock=stock_obj,
                date=row['Date'].date(),
                open_price=row['Open'],
                high_price=row['High'],
                low_price=row['Low'],
                close_price=row['Close'],
                volume=row['Volume']
            )
            stock_data_objects.append(stock_data)
        
        # Use bulk update or create for better performance
        # This is a simplified version - for production, you might want to use bulk_create
        # with a more sophisticated conflict resolution strategy
        for obj in stock_data_objects:
            StockData.objects.update_or_create(
                stock=obj.stock,
                date=obj.date,
                defaults={
                    'open_price': obj.open_price,
                    'high_price': obj.high_price,
                    'low_price': obj.low_price,
                    'close_price': obj.close_price,
                    'volume': obj.volume
                }
            )
        
        return data
        
    except Exception as e:
        print(f"Error processing data for {symbol}: {e}")
        return None

def get_stock_info(symbol):
    """Get company information for a stock symbol"""
    # Try to get from cache first
    cache_key = f"stock_info_{symbol}"
    cached_info = cache.get(cache_key)
    
    if cached_info:
        return cached_info
    
    # Fetch with backoff strategy
    result = fetch_stock_data_with_backoff(symbol, period='1d')
    
    if result is None or result[1] is None:
        default_info = {
            'name': symbol,
            'sector': 'N/A',
            'industry': 'N/A',
            'market_cap': 'N/A',
            'pe_ratio': 'N/A',
            'dividend_yield': 'N/A',
            'description': 'Information not available'
        }
        return default_info
    
    _, info = result
    
    # Extract relevant information
    stock_info = {
        'name': info.get('shortName', info.get('longName', symbol)),
        'sector': info.get('sector', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'market_cap': info.get('marketCap', 'N/A'),
        'pe_ratio': info.get('trailingPE', 'N/A'),
        'dividend_yield': info.get('dividendYield', 'N/A'),
        'description': info.get('longBusinessSummary', 'No description available')
    }
    
    # Cache for 6 hours (21600 seconds)
    cache.set(cache_key, stock_info, 21600)
    
    return stock_info

# Add a utility function to limit batch API calls
def fetch_multiple_stocks(symbols, period='1y', delay_between_calls=1):
    """
    Fetch data for multiple stocks with a delay between calls to avoid rate limiting
    
    Args:
        symbols (list): List of stock symbols
        period (str): Data period for each stock
        delay_between_calls (float): Delay in seconds between API calls
        
    Returns:
        dict: Dictionary of stock symbols to their data
    """
    results = {}
    
    for symbol in symbols:
        data = fetch_stock_data(symbol, period)
        results[symbol] = data
        
        # Add delay to avoid hitting rate limits
        if symbol != symbols[-1]:  # Don't delay after the last symbol
            time.sleep(delay_between_calls)
    
    return results