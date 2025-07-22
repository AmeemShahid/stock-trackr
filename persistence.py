"""
Data persistence management using JSON files
"""

import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class PersistenceManager:
    """Manages data persistence using JSON files"""
    
    def __init__(self):
        self.config = Config()
    
    def load_tracked_stocks(self) -> List[str]:
        """Load tracked stocks from JSON file"""
        try:
            file_path = self.config.get_tracked_stocks_file()
            
            if not os.path.exists(file_path):
                # Create default file
                self.save_tracked_stocks([])
                return []
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data.get('stocks', [])
                
        except Exception as e:
            logger.error(f"Error loading tracked stocks: {e}")
            return []
    
    def save_tracked_stocks(self, stocks: List[str]) -> bool:
        """Save tracked stocks to JSON file"""
        try:
            file_path = self.config.get_tracked_stocks_file()
            
            data = {
                'stocks': stocks,
                'last_updated': datetime.now().isoformat(),
                'count': len(stocks)
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(stocks)} tracked stocks")
            return True
            
        except Exception as e:
            logger.error(f"Error saving tracked stocks: {e}")
            return False
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences from JSON file"""
        try:
            file_path = self.config.get_user_preferences_file()
            
            if not os.path.exists(file_path):
                # Create default preferences
                default_prefs = {
                    'alert_threshold': 2.0,
                    'chart_style': 'dark',
                    'preferred_timeframe': '1mo',
                    'notifications_enabled': True
                }
                self.save_user_preferences(default_prefs)
                return default_prefs
            
            with open(file_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading user preferences: {e}")
            return {}
    
    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Save user preferences to JSON file"""
        try:
            file_path = self.config.get_user_preferences_file()
            
            preferences['last_updated'] = datetime.now().isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(preferences, f, indent=2)
            
            logger.info("Saved user preferences")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
            return False
    
    def add_tracked_stock(self, symbol: str) -> bool:
        """Add a stock to the tracked list"""
        try:
            stocks = self.load_tracked_stocks()
            
            if symbol not in stocks:
                stocks.append(symbol.upper())
                return self.save_tracked_stocks(stocks)
            
            return True  # Already exists
            
        except Exception as e:
            logger.error(f"Error adding tracked stock {symbol}: {e}")
            return False
    
    def remove_tracked_stock(self, symbol: str) -> bool:
        """Remove a stock from the tracked list"""
        try:
            stocks = self.load_tracked_stocks()
            
            if symbol.upper() in stocks:
                stocks.remove(symbol.upper())
                return self.save_tracked_stocks(stocks)
            
            return True  # Doesn't exist
            
        except Exception as e:
            logger.error(f"Error removing tracked stock {symbol}: {e}")
            return False
    
    def get_tracked_stocks_info(self) -> Dict[str, Any]:
        """Get detailed information about tracked stocks"""
        try:
            file_path = self.config.get_tracked_stocks_file()
            
            if not os.path.exists(file_path):
                return {
                    'stocks': [],
                    'count': 0,
                    'last_updated': None
                }
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data
                
        except Exception as e:
            logger.error(f"Error getting tracked stocks info: {e}")
            return {
                'stocks': [],
                'count': 0,
                'last_updated': None,
                'error': str(e)
            }
    
    def backup_data(self, backup_dir: str = "backups") -> bool:
        """Create backup of all data files"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup tracked stocks
            stocks_file = self.config.get_tracked_stocks_file()
            if os.path.exists(stocks_file):
                backup_path = os.path.join(backup_dir, f"tracked_stocks_{timestamp}.json")
                with open(stocks_file, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
            
            # Backup user preferences
            prefs_file = self.config.get_user_preferences_file()
            if os.path.exists(prefs_file):
                backup_path = os.path.join(backup_dir, f"user_preferences_{timestamp}.json")
                with open(prefs_file, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
            
            logger.info(f"Data backup created with timestamp {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
