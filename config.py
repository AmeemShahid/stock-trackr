"""
Configuration management for the Stock Bot
"""

import os
from typing import Optional

class Config:
    """Configuration class for managing environment variables and settings"""
    
    def __init__(self):
        # Discord Bot Token
        self.DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
        if not self.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        # Groq AI API Key
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Alpha Vantage API Key (fallback for stock data)
        self.ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        
        # Web server settings
        self.WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
        self.WEB_PORT: int = int(os.getenv("WEB_PORT", "5000"))
        
        # Data directories
        self.DATA_DIR: str = "data"
        self.CHARTS_DIR: str = "charts"
        
        # Stock data settings
        self.PRICE_ALERT_THRESHOLD: float = float(os.getenv("PRICE_ALERT_THRESHOLD", "2.0"))
        self.MONITOR_INTERVAL_MINUTES: int = int(os.getenv("MONITOR_INTERVAL_MINUTES", "5"))
        
        # AI settings
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.MAX_RESPONSE_TOKENS: int = int(os.getenv("MAX_RESPONSE_TOKENS", "8000"))
        
        # Ensure data directories exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.CHARTS_DIR, exist_ok=True)
    
    def get_tracked_stocks_file(self) -> str:
        """Get path to tracked stocks JSON file"""
        return os.path.join(self.DATA_DIR, "tracked_stocks.json")
    
    def get_user_preferences_file(self) -> str:
        """Get path to user preferences JSON file"""
        return os.path.join(self.DATA_DIR, "user_preferences.json")
    
    def get_chart_path(self, symbol: str) -> str:
        """Get path for chart file"""
        return os.path.join(self.CHARTS_DIR, f"{symbol}_chart.png")
