"""
Chart generation for stock data using matplotlib
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for threading
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
import pandas as pd
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
import os

from config import Config
from stock_data import StockDataManager

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generates candlestick charts for stock data"""
    
    def __init__(self):
        self.config = Config()
        self.stock_manager = StockDataManager()
        
        # Set matplotlib style
        plt.style.use('dark_background')
        
    async def create_candlestick_chart(self, symbol: str, days: int = 30) -> Optional[str]:
        """Create a candlestick chart for the given symbol"""
        try:
            # Get historical data
            historical_data = await self.stock_manager.get_historical_data(symbol, period="1mo")
            
            if historical_data is None or historical_data.empty:
                logger.warning(f"No historical data available for {symbol}")
                return None
            
            # Create the chart
            chart_path = await self._generate_candlestick_chart(symbol, historical_data)
            return chart_path
            
        except Exception as e:
            logger.error(f"Error creating chart for {symbol}: {e}")
            return None
    
    async def _generate_candlestick_chart(self, symbol: str, data: pd.DataFrame) -> str:
        """Generate the actual candlestick chart"""
        try:
            # Run chart generation in thread pool
            loop = asyncio.get_event_loop()
            chart_path = await loop.run_in_executor(
                None, self._create_chart_sync, symbol, data
            )
            return chart_path
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            raise
    
    def _create_chart_sync(self, symbol: str, data: pd.DataFrame) -> str:
        """Synchronous chart creation"""
        # Create figure and axis
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # Get the last 30 days of data
        if len(data) > 30:
            data = data.tail(30)
        
        # Create candlestick chart
        self._plot_candlesticks(ax1, data)
        
        # Add volume chart
        self._plot_volume(ax2, data)
        
        # Configure main chart
        ax1.set_title(f'{symbol} - 30 Day Candlestick Chart', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Configure volume chart
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        
        # Rotate date labels
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save chart
        chart_path = self.config.get_chart_path(symbol)
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', 
                   facecolor='#2f3136', edgecolor='none')
        plt.close()
        
        return chart_path
    
    def _plot_candlesticks(self, ax, data: pd.DataFrame):
        """Plot candlestick chart"""
        # Convert index to matplotlib date format
        dates = mdates.date2num(data.index)
        
        for i, (date, row) in enumerate(zip(dates, data.itertuples())):
            open_price = row[1]  # Open
            high_price = row[2]  # High
            low_price = row[3]   # Low
            close_price = row[4] # Close
            
            # Determine color
            color = '#00ff88' if close_price >= open_price else '#ff4444'
            
            # Draw the high-low line
            ax.plot([date, date], [low_price, high_price], 
                   color=color, linewidth=1, alpha=0.8)
            
            # Draw the open-close rectangle
            height = abs(close_price - open_price)
            bottom = min(open_price, close_price)
            
            rect = Rectangle((date - 0.3, bottom), 0.6, height,
                           facecolor=color, edgecolor=color, alpha=0.8)
            ax.add_patch(rect)
        
        # Add moving averages
        if len(data) >= 20:
            ma20 = data['Close'].rolling(window=20).mean()
            ax.plot(dates, ma20, color='#ffa500', linewidth=2, 
                   alpha=0.7, label='MA20')
        
        if len(data) >= 10:
            ma10 = data['Close'].rolling(window=10).mean()
            ax.plot(dates, ma10, color='#00bfff', linewidth=2, 
                   alpha=0.7, label='MA10')
        
        # Set x-axis to show dates properly
        ax.set_xlim(dates[0] - 0.5, dates[-1] + 0.5)
        
        # Add current price line
        current_price = data['Close'].iloc[-1]
        ax.axhline(y=current_price, color='white', linestyle='--', 
                  alpha=0.7, label=f'Current: ${current_price:.2f}')
    
    def _plot_volume(self, ax, data: pd.DataFrame):
        """Plot volume chart"""
        dates = mdates.date2num(data.index)
        volumes = data['Volume']
        
        # Color bars based on price movement
        colors = ['#00ff88' if close >= open else '#ff4444' 
                 for open, close in zip(data['Open'], data['Close'])]
        
        ax.bar(dates, volumes, color=colors, alpha=0.7, width=0.6)
        
        # Format volume numbers
        ax.yaxis.set_major_formatter(FuncFormatter(self._format_volume))
        
        # Set x-axis limits
        ax.set_xlim(dates[0] - 0.5, dates[-1] + 0.5)
    
    def _format_volume(self, x, pos):
        """Format volume numbers for display"""
        if x >= 1e9:
            return f'{x/1e9:.1f}B'
        elif x >= 1e6:
            return f'{x/1e6:.1f}M'
        elif x >= 1e3:
            return f'{x/1e3:.1f}K'
        else:
            return f'{int(x)}'
