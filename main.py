#!/usr/bin/env python3
"""
Discord Stock Bot - Real-time stock tracking with AI-powered advice
Author: Stock Bot Assistant
Date: July 21, 2025
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
import threading
import os
from datetime import datetime

from config import Config
from stock_data import StockDataManager
from chart_generator import ChartGenerator
from ai_advisor import AIAdvisor
from persistence import PersistenceManager
from web_server import WebServer

from dotenv import load_dotenv
import os

load_dotenv()  # 👈 Must be before os.getenv

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StockBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False  # Not needed for slash commands
        super().__init__(command_prefix='!', intents=intents)
        
        self.config = Config()
        self.stock_manager = StockDataManager()
        self.chart_generator = ChartGenerator()
        self.ai_advisor = AIAdvisor()
        self.persistence = PersistenceManager()
        
        # Load tracked stocks and user preferences
        self.tracked_stocks = self.persistence.load_tracked_stocks()
        self.user_preferences = self.persistence.load_user_preferences()
        self.last_prices = {}
        
    async def setup_hook(self):
        """Setup hook called when bot starts"""
        await self.sync_commands()
        self.price_monitor.start()
        logger.info("Bot setup completed")
        
    async def sync_commands(self):
        """Sync slash commands with Discord"""
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        logger.error(f"Command error: {error}")
        if isinstance(error, commands.CommandNotFound):
            return
        await ctx.send(f"An error occurred: {str(error)}")
    
    @tasks.loop(minutes=5)
    async def price_monitor(self):
        """Monitor price changes for tracked stocks"""
        if not self.tracked_stocks:
            return
            
        try:
            for symbol in self.tracked_stocks:
                current_data = await self.stock_manager.get_stock_data(symbol)
                if not current_data:
                    continue
                    
                current_price = current_data['current_price']
                last_price = self.last_prices.get(symbol, current_price)
                
                # Calculate percentage change
                if last_price != 0:
                    change_percent = ((current_price - last_price) / last_price) * 100
                    
                    # Alert if significant change (>= 2%)
                    if abs(change_percent) >= 2.0:
                        await self.send_price_alert(symbol, current_data, change_percent)
                
                self.last_prices[symbol] = current_price
                
        except Exception as e:
            logger.error(f"Error in price monitor: {e}")
    
    async def send_price_alert(self, symbol, stock_data, change_percent):
        """Send price alert to specific stock channel or general channels"""
        embed = discord.Embed(
            title=f"🚨 Price Alert: {symbol}",
            color=discord.Color.red() if change_percent < 0 else discord.Color.green()
        )
        
        embed.add_field(name="Current Price", value=f"${stock_data['current_price']:.2f}", inline=True)
        embed.add_field(name="Change", value=f"{change_percent:+.2f}%", inline=True)
        embed.add_field(name="Volume", value=f"{stock_data.get('volume', 'N/A'):,}", inline=True)
        
        embed.timestamp = datetime.utcnow()
        
        for guild in self.guilds:
            # Try to find specific stock channel first
            stock_channel_name = f"stock-{symbol.lower()}"
            stock_channel = discord.utils.get(guild.text_channels, name=stock_channel_name)
            
            if stock_channel:
                try:
                    await stock_channel.send(embed=embed)
                    continue
                except discord.Forbidden:
                    pass
            
            # Fallback to general channels
            for channel in guild.text_channels:
                if channel.name in ['general', 'stock-alerts', 'trading']:
                    try:
                        await channel.send(embed=embed)
                        break
                    except discord.Forbidden:
                        continue
    
    async def create_stock_category_and_channel(self, guild, symbol):
        """Create or find stocks tracking category and create channel for specific stock"""
        try:
            # Find or create "Stock Tracking" category
            category = discord.utils.get(guild.categories, name="Stock Tracking")
            if not category:
                category = await guild.create_category("Stock Tracking")
                logger.info(f"Created 'Stock Tracking' category in {guild.name}")
            
            # Create channel for specific stock
            channel_name = f"stock-{symbol.lower()}"
            existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
            
            if not existing_channel:
                channel = await guild.create_text_channel(
                    channel_name,
                    category=category,
                    topic=f"Real-time tracking and alerts for {symbol} stock"
                )
                
                # Send welcome message to new channel
                embed = discord.Embed(
                    title=f"📊 Welcome to {symbol} Tracking",
                    description=f"This channel is dedicated to tracking {symbol} stock. You'll receive price alerts and can use stock commands here.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Available Commands",
                    value=f"`/price {symbol}` - Get current price and chart\n`/stockadvice {symbol}` - Get AI trading advice",
                    inline=False
                )
                await channel.send(embed=embed)
                
                logger.info(f"Created channel '{channel_name}' in {guild.name}")
                return channel
            else:
                logger.info(f"Channel '{channel_name}' already exists in {guild.name}")
                return existing_channel
                
        except discord.Forbidden:
            logger.warning(f"No permission to create channels in {guild.name}")
            return None
        except Exception as e:
            logger.error(f"Error creating stock channel in {guild.name}: {e}")
            return None

# Initialize bot instance
bot = StockBot()

# Slash Commands
@bot.tree.command(name="price", description="Get current stock price with candlestick chart")
async def price_command(interaction: discord.Interaction, symbol: str):
    """Get stock price with OHLC chart"""
    await interaction.response.defer()
    
    try:
        symbol = symbol.upper()
        stock_data = await bot.stock_manager.get_stock_data(symbol)
        
        if not stock_data:
            await interaction.followup.send(f"❌ Could not fetch data for {symbol}")
            return
        
        # Generate chart
        chart_path = await bot.chart_generator.create_candlestick_chart(symbol)
        
        # Create embed
        embed = discord.Embed(
            title=f"📈 {symbol} Stock Price",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Current Price", value=f"${stock_data['current_price']:.2f}", inline=True)
        embed.add_field(name="Change", value=f"{stock_data['change']:+.2f} ({stock_data['change_percent']:+.2f}%)", inline=True)
        embed.add_field(name="Volume", value=f"{stock_data.get('volume', 'N/A'):,}", inline=True)
        
        if 'open' in stock_data:
            embed.add_field(name="Open", value=f"${stock_data['open']:.2f}", inline=True)
            embed.add_field(name="High", value=f"${stock_data['high']:.2f}", inline=True)
            embed.add_field(name="Low", value=f"${stock_data['low']:.2f}", inline=True)
        
        embed.timestamp = datetime.utcnow()
        
        # Send with chart if available
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
    """List all tracked stocks"""
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
    """Add stock to tracking list and create dedicated channel"""
    await interaction.response.defer()
    
    symbol = symbol.upper()
    
    # Verify stock exists
    stock_data = await bot.stock_manager.get_stock_data(symbol)
    if not stock_data:
        await interaction.followup.send(f"❌ Could not find stock data for {symbol}")
        return
    
    if symbol in bot.tracked_stocks:
        await interaction.followup.send(f"📊 {symbol} is already being tracked")
        return
    
    # Add to tracking list
    bot.tracked_stocks.append(symbol)
    bot.persistence.save_tracked_stocks(bot.tracked_stocks)
    
    # Create dedicated channel for this stock
    channel = await bot.create_stock_category_and_channel(interaction.guild, symbol)
    
    # Create response embed
    embed = discord.Embed(
        title=f"✅ Added {symbol} to Tracking",
        description=f"Now tracking {symbol} with real-time alerts",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Current Price", value=f"${stock_data['current_price']:.2f}", inline=True)
    embed.add_field(name="Change", value=f"{stock_data['change']:+.2f} ({stock_data['change_percent']:+.2f}%)", inline=True)
    embed.add_field(name="Volume", value=f"{stock_data.get('volume', 'N/A'):,}", inline=True)
    
    if channel:
        embed.add_field(
            name="Dedicated Channel", 
            value=f"Created {channel.mention} for {symbol} tracking", 
            inline=False
        )
    
    embed.timestamp = datetime.utcnow()
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="untrack", description="Remove a stock from tracking list")
async def untrack_command(interaction: discord.Interaction, symbol: str, delete_channel: bool = False):
    """Remove stock from tracking list and optionally delete channel"""
    await interaction.response.defer()
    
    symbol = symbol.upper()
    
    if symbol not in bot.tracked_stocks:
        await interaction.followup.send(f"❌ {symbol} is not being tracked")
        return
    
    # Remove from tracking list
    bot.tracked_stocks.remove(symbol)
    bot.persistence.save_tracked_stocks(bot.tracked_stocks)
    
    # Handle channel deletion if requested
    channel_deleted = False
    if delete_channel:
        channel_name = f"stock-{symbol.lower()}"
        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        
        if channel:
            try:
                await channel.delete(reason=f"Stock {symbol} untracked by {interaction.user}")
                channel_deleted = True
                logger.info(f"Deleted channel '{channel_name}' in {interaction.guild.name}")
            except discord.Forbidden:
                logger.warning(f"No permission to delete channel '{channel_name}' in {interaction.guild.name}")
            except Exception as e:
                logger.error(f"Error deleting channel '{channel_name}': {e}")
    
    # Create response embed
    embed = discord.Embed(
        title=f"✅ Removed {symbol} from Tracking",
        description=f"Stopped tracking {symbol}",
        color=discord.Color.orange()
    )
    
    if delete_channel and channel_deleted:
        embed.add_field(name="Channel Deleted", value=f"Removed #stock-{symbol.lower()} channel", inline=False)
    elif delete_channel and not channel_deleted:
        embed.add_field(name="Channel", value=f"Could not delete #stock-{symbol.lower()} channel (check permissions)", inline=False)
    
    embed.timestamp = datetime.utcnow()
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="stockadvice", description="Get AI-powered stock advice with detailed signals")
async def stockadvice_command(interaction: discord.Interaction, symbol: str):
    """Get AI-powered stock advice"""
    await interaction.response.defer()
    
    try:
        symbol = symbol.upper()
        
        # Get current stock data
        stock_data = await bot.stock_manager.get_stock_data(symbol)
        if not stock_data:
            await interaction.followup.send(f"❌ Could not fetch data for {symbol}")
            return
        
        # Get historical data for better analysis
        historical_data = await bot.stock_manager.get_historical_data(symbol, period="1mo")
        
        # Get AI advice
        advice = await bot.ai_advisor.get_stock_advice(symbol, stock_data, historical_data)
        
        if not advice:
            await interaction.followup.send(f"❌ Could not generate advice for {symbol}")
            return
        
        # Create embed with advice
        embed = discord.Embed(
            title=f"🤖 AI Stock Advice: {symbol}",
            description=advice[:4000],  # Discord embed description limit
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Current Price", value=f"${stock_data['current_price']:.2f}", inline=True)
        embed.add_field(name="Change", value=f"{stock_data['change_percent']:+.2f}%", inline=True)
        embed.timestamp = datetime.utcnow()
        
        await interaction.followup.send(embed=embed)
        
        # If advice is longer, send additional messages
        if len(advice) > 4000:
            remaining_advice = advice[4000:]
            while remaining_advice:
                chunk = remaining_advice[:2000]  # Message content limit
                remaining_advice = remaining_advice[2000:]
                await interaction.followup.send(f"```{chunk}```")
        
    except Exception as e:
        logger.error(f"Error in stockadvice command: {e}")
        await interaction.followup.send(f"❌ An error occurred: {str(e)}")

@bot.tree.command(name="help", description="Show bot commands and usage")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="📚 Stock Bot Help",
        description="Real-time stock tracking with AI-powered advice",
        color=discord.Color.blue()
    )
    
    commands_info = [
        ("/price <symbol>", "Get current stock price with candlestick chart"),
        ("/liststocks", "List all tracked stocks"),
        ("/track <symbol>", "Add a stock to tracking list"),
        ("/untrack <symbol> [delete_channel]", "Remove a stock from tracking list (optionally delete channel)"),
        ("/stockadvice <symbol>", "Get AI-powered stock advice with detailed signals"),
        ("/help", "Show this help message")
    ]
    
    for cmd, desc in commands_info:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.add_field(
        name="📊 Features",
        value="• Real-time price monitoring\n• Automatic price alerts\n• OHLC candlestick charts\n• AI-powered trading signals\n• Persistent stock tracking",
        inline=False
    )
    
    embed.timestamp = datetime.utcnow()
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="managechannels", description="Create channels for all tracked stocks")
async def managechannels_command(interaction: discord.Interaction):
    """Create channels for all currently tracked stocks"""
    await interaction.response.defer()
    
    if not bot.tracked_stocks:
        await interaction.followup.send("📋 No stocks are currently being tracked.")
        return
    
    created_channels = []
    existing_channels = []
    failed_channels = []
    
    for symbol in bot.tracked_stocks:
        channel = await bot.create_stock_category_and_channel(interaction.guild, symbol)
        if channel:
            channel_name = f"stock-{symbol.lower()}"
            existing_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
            if existing_channel and existing_channel == channel:
                created_channels.append(symbol)
            else:
                existing_channels.append(symbol)
        else:
            failed_channels.append(symbol)
    
    # Create response embed
    embed = discord.Embed(
        title="📊 Stock Channels Management",
        description="Channel creation results for tracked stocks",
        color=discord.Color.blue()
    )
    
    if created_channels:
        embed.add_field(
            name="✅ Channels Created",
            value=", ".join(created_channels),
            inline=False
        )
    
    if existing_channels:
        embed.add_field(
            name="📁 Already Existed",
            value=", ".join(existing_channels),
            inline=False
        )
    
    if failed_channels:
        embed.add_field(
            name="❌ Failed to Create",
            value=", ".join(failed_channels),
            inline=False
        )
    
    embed.add_field(
        name="Summary",
        value=f"Total: {len(bot.tracked_stocks)} | Created: {len(created_channels)} | Existing: {len(existing_channels)} | Failed: {len(failed_channels)}",
        inline=False
    )
    
    embed.timestamp = datetime.utcnow()
    await interaction.followup.send(embed=embed)

def start_web_server():
    """Start the web server in a separate thread"""
    web_server = WebServer()
    web_server.run()

def main():
    """Main function to run the bot"""
    logger.info("Starting Stock Bot...")
    
    # Start web server for ping endpoint
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Start Discord bot
    try:
        bot.run(bot.config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()
