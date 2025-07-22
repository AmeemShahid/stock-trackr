#!/usr/bin/env python3
"""
Standalone Discord Stock Bot - All-in-one file for local execution
Author: Stock Bot Assistant
Date: July 21, 2025

This file contains the complete Discord stock bot in a single file
for easy local deployment when cloud hosting isn't available.
"""

import os
import json
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import yfinance as yf
import requests
import pandas as pd

# Discord imports
import discord
from discord.ext import commands, tasks

# AI imports
try:
    from groq import Groq
except ImportError:
    Groq = None

# Chart imports
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

# Web server imports
try:
    from flask import Flask, jsonify
    flask_available = True
except ImportError:
    Flask = None
    jsonify = None
    flask_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('standalone_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    def __init__(self):
        # Required environment variables
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
        if not self.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Optional settings
        self.ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        self.WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
        self.WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.PRICE_ALERT_THRESHOLD = float(os.getenv("PRICE_ALERT_THRESHOLD", "2.0"))
        self.MONITOR_INTERVAL_MINUTES = int(os.getenv("MONITOR_INTERVAL_MINUTES", "5"))
        
        # Create directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("charts", exist_ok=True)

# Data persistence
class PersistenceManager:
    def __init__(self):
        self.tracked_stocks_file = "data/tracked_stocks.json"
        self.user_preferences_file = "data/user_preferences.json"
    
    def load_tracked_stocks(self) -> List[str]:
        try:
            if not os.path.exists(self.tracked_stocks_file):
                self.save_tracked_stocks([])
                return []
            
            with open(self.tracked_stocks_file, 'r') as f:
                data = json.load(f)
                return data.get('stocks', [])
        except Exception as e:
            logger.error(f"Error loading tracked stocks: {e}")
            return []
    
    def save_tracked_stocks(self, stocks: List[str]) -> bool:
        try:
            data = {
                'stocks': stocks,
                'last_updated': datetime.now().isoformat(),
                'count': len(stocks)
            }
            with open(self.tracked_stocks_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving tracked stocks: {e}")
            return False

# Stock data manager
class StockDataManager:
    def __init__(self, config):
        self.config = config
        self.cache = {}
        self.cache_duration = 60
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        try:
            cache_key = f"{symbol}_current"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]['data']
            
            data = await self._get_yfinance_data(symbol)
            if data:
                self._update_cache(cache_key, data)
                return data
            
            return None
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    async def _get_yfinance_data(self, symbol: str) -> Optional[Dict]:
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
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
    
    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            hist = await loop.run_in_executor(None, lambda: ticker.history(period=period))
            return hist if not hist.empty else None
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache:
            return False
        cache_time = self.cache[key]['timestamp']
        return (datetime.now() - cache_time).seconds < self.cache_duration
    
    def _update_cache(self, key: str, data) -> None:
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }

# Chart generator
class ChartGenerator:
    def __init__(self, config):
        self.config = config
        plt.style.use('dark_background')
    
    async def create_candlestick_chart(self, symbol: str, historical_data: pd.DataFrame) -> Optional[str]:
        try:
            if historical_data is None or historical_data.empty:
                return None
            
            loop = asyncio.get_event_loop()
            chart_path = await loop.run_in_executor(None, self._create_chart_sync, symbol, historical_data)
            return chart_path
        except Exception as e:
            logger.error(f"Error creating chart for {symbol}: {e}")
            return None
    
    def _create_chart_sync(self, symbol: str, data: pd.DataFrame) -> str:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
        
        if len(data) > 30:
            data = data.tail(30)
        
        # Candlestick chart
        dates = mdates.date2num(data.index)
        for i, (date, row) in enumerate(zip(dates, data.itertuples())):
            open_price = row[1]
            high_price = row[2]
            low_price = row[3]
            close_price = row[4]
            
            color = '#00ff88' if close_price >= open_price else '#ff4444'
            ax1.plot([date, date], [low_price, high_price], color=color, linewidth=1, alpha=0.8)
            
            height = abs(close_price - open_price)
            bottom = min(open_price, close_price)
            rect = Rectangle((date - 0.3, bottom), 0.6, height, facecolor=color, edgecolor=color, alpha=0.8)
            ax1.add_patch(rect)
        
        # Moving averages
        if len(data) >= 20:
            ma20 = data['Close'].rolling(window=20).mean()
            ax1.plot(dates, ma20, color='#ffa500', linewidth=2, alpha=0.7, label='MA20')
        
        if len(data) >= 10:
            ma10 = data['Close'].rolling(window=10).mean()
            ax1.plot(dates, ma10, color='#00bfff', linewidth=2, alpha=0.7, label='MA10')
        
        current_price = data['Close'].iloc[-1]
        ax1.axhline(y=current_price, color='white', linestyle='--', alpha=0.7, label=f'Current: ${current_price:.2f}')
        
        # Volume chart
        volumes = data['Volume']
        colors = ['#00ff88' if close >= open else '#ff4444' for open, close in zip(data['Open'], data['Close'])]
        ax2.bar(dates, volumes, color=colors, alpha=0.7, width=0.6)
        
        # Formatting
        ax1.set_title(f'{symbol} - 30 Day Candlestick Chart', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(FuncFormatter(self._format_volume))
        
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        plt.tight_layout()
        
        chart_path = f"charts/{symbol}_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='#2f3136', edgecolor='none')
        plt.close()
        
        return chart_path
    
    def _format_volume(self, x, pos):
        if x >= 1e9:
            return f'{x/1e9:.1f}B'
        elif x >= 1e6:
            return f'{x/1e6:.1f}M'
        elif x >= 1e3:
            return f'{x/1e3:.1f}K'
        else:
            return f'{int(x)}'

# AI advisor
class AIAdvisor:
    def __init__(self, config):
        self.config = config
        if Groq is None:
            logger.warning("Groq package not installed. AI advice will be unavailable.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.config.GROQ_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
    
    async def get_stock_advice(self, symbol: str, current_data: Dict, historical_data: Optional[pd.DataFrame] = None) -> Optional[str]:
        if not self.client:
            return "❌ AI advisor is not available. Please check Groq API configuration."
        
        try:
            context = self._prepare_context(symbol, current_data, historical_data)
            prompt = self._create_analysis_prompt(symbol, context)
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._get_groq_response, prompt)
            return response
        except Exception as e:
            logger.error(f"Error getting AI advice for {symbol}: {e}")
            return f"❌ Failed to generate AI advice: {str(e)}"
    
    def _prepare_context(self, symbol: str, current_data: Dict, historical_data: Optional[pd.DataFrame]) -> Dict:
        context = {
            'symbol': symbol,
            'current_price': current_data['current_price'],
            'change': current_data['change'],
            'change_percent': current_data['change_percent'],
            'volume': current_data.get('volume', 'N/A'),
            'timestamp': datetime.now().isoformat()
        }
        
        if historical_data is not None and not historical_data.empty:
            # Calculate technical indicators
            if len(historical_data) >= 20:
                ma20_series = historical_data['Close'].rolling(window=20).mean()
                context['ma20'] = float(ma20_series.iloc[-1])
                context['ma20_trend'] = 'bullish' if historical_data['Close'].iloc[-1] > context['ma20'] else 'bearish'
            
            if len(historical_data) >= 14:
                delta = historical_data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                context['rsi'] = float(rsi.iloc[-1]) if not rsi.empty else 50.0
        
        return context
    
    def _create_analysis_prompt(self, symbol: str, context: Dict) -> str:
        prompt = f"""
You are an expert financial analyst. Provide a comprehensive analysis and trading recommendation for {symbol} stock.

CURRENT DATA:
- Symbol: {symbol}
- Current Price: ${context['current_price']:.2f}
- Daily Change: {context['change']:+.2f} ({context['change_percent']:+.2f}%)
- Volume: {context.get('volume', 'N/A')}

TECHNICAL INDICATORS:
"""
        if 'ma20' in context:
            prompt += f"- 20-day MA: ${context['ma20']:.2f} (Trend: {context['ma20_trend']})\n"
        if 'rsi' in context:
            prompt += f"- RSI: {context['rsi']:.2f}\n"
        
        prompt += """
Provide detailed analysis including:
1. **RECOMMENDATION**: Clear BUY/SELL/HOLD with confidence level (1-10)
2. **TECHNICAL ANALYSIS**: Moving averages, RSI, trend analysis
3. **RISK ASSESSMENT**: Volatility, risk factors, position sizing
4. **PRICE TARGETS**: Resistance/support levels, projections
5. **TRADING STRATEGY**: Entry points, timing recommendations

Focus on actionable signals based on current market conditions.
"""
        return prompt
    
    def _get_groq_response(self, prompt: str) -> str:
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst providing detailed trading advice."},
                    {"role": "user", "content": prompt}
                ],
                model=self.config.GROQ_MODEL,
                max_tokens=8000,
                temperature=0.3
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting Groq response: {e}")
            raise

# Web server for ping endpoint
class WebServer:
    def __init__(self, config):
        self.config = config
        if not flask_available:
            logger.warning("Flask not installed. Web server will not be available.")
            self.app = None
            return
        
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        if not self.app:
            return
        
        @self.app.route('/')
        def home():
            return jsonify({
                'status': 'online',
                'service': 'Discord Stock Bot',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/ping')
        def ping():
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'uptime': True
            })
    
    def run(self):
        if not self.app:
            return
        try:
            self.app.run(host=self.config.WEB_HOST, port=self.config.WEB_PORT, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Error running web server: {e}")

# Discord bot
class StockBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = Config()
        self.stock_manager = StockDataManager(self.config)
        self.chart_generator = ChartGenerator(self.config)
        self.ai_advisor = AIAdvisor(self.config)
        self.persistence = PersistenceManager()
        
        self.tracked_stocks = self.persistence.load_tracked_stocks()
        self.last_prices = {}
    
    async def setup_hook(self):
        await self.sync_commands()
        self.price_monitor.start()
        logger.info("Bot setup completed")
    
    async def sync_commands(self):
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
    
    @tasks.loop(minutes=5)
    async def price_monitor(self):
        if not self.tracked_stocks:
            return
        
        try:
            for symbol in self.tracked_stocks:
                current_data = await self.stock_manager.get_stock_data(symbol)
                if not current_data:
                    continue
                
                current_price = current_data['current_price']
                last_price = self.last_prices.get(symbol, current_price)
                
                if last_price != 0:
                    change_percent = ((current_price - last_price) / last_price) * 100
                    if abs(change_percent) >= self.config.PRICE_ALERT_THRESHOLD:
                        await self.send_price_alert(symbol, current_data, change_percent)
                
                self.last_prices[symbol] = current_price
        except Exception as e:
            logger.error(f"Error in price monitor: {e}")
    
    async def send_price_alert(self, symbol, stock_data, change_percent):
        embed = discord.Embed(
            title=f"🚨 Price Alert: {symbol}",
            color=discord.Color.red() if change_percent < 0 else discord.Color.green()
        )
        embed.add_field(name="Current Price", value=f"${stock_data['current_price']:.2f}", inline=True)
        embed.add_field(name="Change", value=f"{change_percent:+.2f}%", inline=True)
        embed.timestamp = datetime.utcnow()
        
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name in ['general', 'stock-alerts', 'trading']:
                    try:
                        await channel.send(embed=embed)
                        break
                    except discord.Forbidden:
                        continue

# Initialize bot
bot = StockBot()

# Slash Commands
@bot.tree.command(name="price", description="Get current stock price with candlestick chart")
async def price_command(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()
    
    try:
        symbol = symbol.upper()
        stock_data = await bot.stock_manager.get_stock_data(symbol)
        
        if not stock_data:
            await interaction.followup.send(f"❌ Could not fetch data for {symbol}")
            return
        
        # Get historical data and create chart
        historical_data = await bot.stock_manager.get_historical_data(symbol, period="1mo")
        chart_path = None
        if historical_data is not None:
            chart_path = await bot.chart_generator.create_candlestick_chart(symbol, historical_data)
        
        # Create embed
        embed = discord.Embed(title=f"📈 {symbol} Stock Price", color=discord.Color.blue())
        embed.add_field(name="Current Price", value=f"${stock_data['current_price']:.2f}", inline=True)
        embed.add_field(name="Change", value=f"{stock_data['change']:+.2f} ({stock_data['change_percent']:+.2f}%)", inline=True)
        embed.add_field(name="Volume", value=f"{stock_data.get('volume', 'N/A'):,}", inline=True)
        embed.timestamp = datetime.utcnow()
        
        if chart_path and os.path.exists(chart_path):
            file = discord.File(chart_path, filename="chart.png")
            embed.set_image(url="attachment://chart.png")
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Error in price command: {e}")
        await interaction.followup.send(f"❌ An error occurred: {str(e)}")

@bot.tree.command(name="liststocks", description="List all tracked stocks")
async def liststocks_command(interaction: discord.Interaction):
    if not bot.tracked_stocks:
        await interaction.response.send_message("📋 No stocks are currently being tracked.")
        return
    
    embed = discord.Embed(
        title="📋 Tracked Stocks",
        description=f"Currently tracking {len(bot.tracked_stocks)} stocks:",
        color=discord.Color.blue()
    )
    stock_list = ", ".join(bot.tracked_stocks)
    embed.add_field(name="Symbols", value=stock_list, inline=False)
    embed.timestamp = datetime.utcnow()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="track", description="Add a stock to tracking list")
async def track_command(interaction: discord.Interaction, symbol: str):
    symbol = symbol.upper()
    
    stock_data = await bot.stock_manager.get_stock_data(symbol)
    if not stock_data:
        await interaction.response.send_message(f"❌ Could not find stock data for {symbol}")
        return
    
    if symbol in bot.tracked_stocks:
        await interaction.response.send_message(f"📊 {symbol} is already being tracked")
        return
    
    bot.tracked_stocks.append(symbol)
    bot.persistence.save_tracked_stocks(bot.tracked_stocks)
    
    await interaction.response.send_message(f"✅ Added {symbol} to tracking list")

@bot.tree.command(name="untrack", description="Remove a stock from tracking list")
async def untrack_command(interaction: discord.Interaction, symbol: str):
    symbol = symbol.upper()
    
    if symbol not in bot.tracked_stocks:
        await interaction.response.send_message(f"❌ {symbol} is not being tracked")
        return
    
    bot.tracked_stocks.remove(symbol)
    bot.persistence.save_tracked_stocks(bot.tracked_stocks)
    
    await interaction.response.send_message(f"✅ Removed {symbol} from tracking list")

@bot.tree.command(name="stockadvice", description="Get AI-powered stock advice with detailed signals")
async def stockadvice_command(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()
    
    try:
        symbol = symbol.upper()
        
        stock_data = await bot.stock_manager.get_stock_data(symbol)
        if not stock_data:
            await interaction.followup.send(f"❌ Could not fetch data for {symbol}")
            return
        
        historical_data = await bot.stock_manager.get_historical_data(symbol, period="1mo")
        advice = await bot.ai_advisor.get_stock_advice(symbol, stock_data, historical_data)
        
        if not advice:
            await interaction.followup.send(f"❌ Could not generate advice for {symbol}")
            return
        
        embed = discord.Embed(
            title=f"🤖 AI Stock Advice: {symbol}",
            description=advice[:4000],
            color=discord.Color.gold()
        )
        embed.add_field(name="Current Price", value=f"${stock_data['current_price']:.2f}", inline=True)
        embed.add_field(name="Change", value=f"{stock_data['change_percent']:+.2f}%", inline=True)
        embed.timestamp = datetime.utcnow()
        
        await interaction.followup.send(embed=embed)
        
        if len(advice) > 4000:
            remaining_advice = advice[4000:]
            while remaining_advice:
                chunk = remaining_advice[:2000]
                remaining_advice = remaining_advice[2000:]
                await interaction.followup.send(f"```{chunk}```")
    except Exception as e:
        logger.error(f"Error in stockadvice command: {e}")
        await interaction.followup.send(f"❌ An error occurred: {str(e)}")

@bot.tree.command(name="help", description="Show bot commands and usage")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Stock Bot Help",
        description="Real-time stock tracking with AI-powered advice",
        color=discord.Color.blue()
    )
    
    commands_info = [
        ("/price <symbol>", "Get current stock price with candlestick chart"),
        ("/liststocks", "List all tracked stocks"),
        ("/track <symbol>", "Add a stock to tracking list"),
        ("/untrack <symbol>", "Remove a stock from tracking list"),
        ("/stockadvice <symbol>", "Get AI-powered stock advice with detailed signals"),
        ("/help", "Show this help message")
    ]
    
    for cmd, desc in commands_info:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.timestamp = datetime.utcnow()
    await interaction.response.send_message(embed=embed)

def start_web_server(config):
    """Start the web server in a separate thread"""
    web_server = WebServer(config)
    web_server.run()

def main():
    """Main function to run the bot"""
    logger.info("Starting Standalone Discord Stock Bot...")
    
    try:
        config = Config()
        
        # Start web server for ping endpoint
        if flask_available:
            web_thread = threading.Thread(target=start_web_server, args=(config,), daemon=True)
            web_thread.start()
            logger.info(f"Web server started on {config.WEB_HOST}:{config.WEB_PORT}")
        
        # Start Discord bot
        bot.run(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()