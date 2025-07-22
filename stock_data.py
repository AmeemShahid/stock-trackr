"""
Stock data management using yfinance and Alpha Vantage APIs
"""

import yfinance as yf
import requests
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pandas as pd

from config import Config

logger = logging.getLogger(__name__)

class StockDataManager:
    """Manages stock data fetching from multiple sources"""
    
    def __init__(self):
        self.config = Config()
        self.cache = {}
        self.cache_duration = 60  # Cache duration in seconds
        
    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get current stock data for a symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_current"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            # Try yfinance first (free and reliable)
            data = await self._get_yfinance_data(symbol)
            
            if data:
                self._update_cache(cache_key, data)
                return data
            
            # Fallback to Alpha Vantage if yfinance fails
            data = await self._get_alpha_vantage_data(symbol)
            if data:
                self._update_cache(cache_key, data)
                return data
                
            logger.warning(f"Could not fetch data for {symbol} from any source")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    async def _get_yfinance_data(self, symbol: str) -> Optional[Dict]:
        """Get stock data using yfinance"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            
            # Get current data
            info = await loop.run_in_executor(None, lambda: ticker.info)
            hist = await loop.run_in_executor(None, lambda: ticker.history(period="2d"))
            
            if hist.empty:
                return None
            
            current_data = hist.iloc[-1]
            previous_data = hist.iloc[-2] if len(hist) > 1 else current_data
            
            current_price = float(current_data['Close'])
            previous_close = float(previous_data['Close'])
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'open': float(current_data['Open']),
                'high': float(current_data['High']),
                'low': float(current_data['Low']),
                'volume': int(current_data['Volume']),
                'previous_close': previous_close,
                'timestamp': datetime.now().isoformat(),
                'source': 'yfinance'
            }
            
        except Exception as e:
            logger.error(f"Error fetching yfinance data for {symbol}: {e}")
            return None
    
    async def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Get stock data using Alpha Vantage API"""
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.config.ALPHA_VANTAGE_API_KEY
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.get(url, params=params, timeout=10)
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'Global Quote' not in data:
                return None
            
            quote = data['Global Quote']
            
            current_price = float(quote['05. price'])
            previous_close = float(quote['08. previous close'])
            change = float(quote['09. change'])
            change_percent = float(quote['10. change percent'].replace('%', ''))
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'open': float(quote['02. open']),
                'high': float(quote['03. high']),
                'low': float(quote['04. low']),
                'volume': int(quote['06. volume']),
                'previous_close': previous_close,
                'timestamp': datetime.now().isoformat(),
                'source': 'alpha_vantage'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Get historical stock data"""
        try:
            cache_key = f"{symbol}_hist_{period}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            hist = await loop.run_in_executor(None, lambda: ticker.history(period=period))
            
            if not hist.empty:
                self._update_cache(cache_key, hist)
                return hist
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key]['timestamp']
        return (datetime.now() - cache_time).seconds < self.cache_duration
    
    def _update_cache(self, key: str, data) -> None:
        """Update cache with new data"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
