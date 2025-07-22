# Discord Stock Bot

A powerful Discord bot for real-time stock tracking with AI-powered advice, candlestick charts, and flexible deployment options.

## Features

- **Real-time Stock Tracking**: Monitor stock prices with automatic alerts
- **AI-Powered Advice**: Get detailed trading signals using Groq AI
- **Candlestick Charts**: Generate OHLC charts with technical indicators
- **Slash Commands**: Easy-to-use Discord slash commands
- **Persistent Storage**: JSON-based data persistence
- **Uptime Monitoring**: Built-in web server for UptimeRobot
- **Local & Cloud Ready**: Works both locally and on Replit

## Commands

- `/price <symbol>` - Get current stock price with candlestick chart
- `/liststocks` - List all tracked stocks  
- `/track <symbol>` - Add a stock to tracking list and create dedicated channel
- `/untrack <symbol> [delete_channel]` - Remove a stock from tracking list (optionally delete channel)
- `/stockadvice <symbol>` - Get AI-powered stock advice with detailed signals
- `/managechannels` - Create channels for all tracked stocks at once
- `/help` - Show bot commands and usage

## Channel Management Features

- **Automatic Channel Creation**: When you track a stock, the bot creates a dedicated channel in the "Stock Tracking" category
- **Organized Categories**: All stock channels are organized under "Stock Tracking" category
- **Individual Stock Channels**: Each tracked stock gets its own channel (e.g., `#stock-tsla`, `#stock-aapl`)
- **Targeted Alerts**: Price alerts are sent to the specific stock channel when available
- **Channel Cleanup**: Option to delete channels when untracking stocks

## Setup

### Environment Variables

Set these environment variables in Replit Secrets or create a `.env` file:

```env
DISCORD_TOKEN=your_discord_bot_token           # Required: From Discord Developer Portal
GROQ_API_KEY=your_groq_api_key                # Required: From console.groq.com
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key  # Optional fallback
GROQ_MODEL=llama-3.3-70b-versatile            # Optional, default model
PRICE_ALERT_THRESHOLD=2.0                     # Optional, default 2%
MONITOR_INTERVAL_MINUTES=5                    # Optional, default 5 minutes
WEB_PORT=5000                                 # Optional, default 5000
```

### Discord Bot Setup

1. Go to https://discord.com/developers/applications
2. Create a new application and bot
3. Copy the bot token and set as `DISCORD_TOKEN`
4. Generate an invite link with "applications.commands" scope
5. Add the bot to your Discord server

### Groq API Setup

1. Sign up at https://console.groq.com
2. Create an API key in your dashboard
3. Set the key as `GROQ_API_KEY`
4. The free tier provides substantial usage for testing

## Bot Permissions Required

When inviting the bot to your Discord server, make sure it has these permissions:
- **View Channels** - To see server channels
- **Send Messages** - To send responses and alerts  
- **Use Slash Commands** - For command functionality
- **Manage Channels** - To create stock tracking channels
- **Manage Roles** - To organize channel permissions
- **Embed Links** - To send rich embed messages
- **Attach Files** - To send chart images

## Deployment Options

### Option 1: Download for Local PC (Easiest)
1. **Download all files** from this project
2. **Run setup**: `python setup_local.py` (auto-installs everything)
3. **Configure**: Edit `.env` file with your API keys
4. **Launch**: Double-click `run_bot.bat` (Windows) or `./run_bot.sh` (Linux/Mac)

See `DOWNLOAD_GUIDE.md` for detailed local setup instructions.

### Option 2: Replit (Cloud)
- Zero configuration required
- Automatic dependency management
- Built-in environment variable management
- Free tier available

### Option 3: Single File Version
For minimal deployment, use just the standalone version:
```bash
python standalone_bot.py
```

### Option 4: UptimeRobot Monitoring Only
Use the keepalive server for monitoring without Discord bot:
```bash
python keepalive.py
```
Then configure UptimeRobot to ping: `http://your-server:5000/ping`

## File Structure

```
├── main.py              # Main modular bot
├── config.py            # Configuration management  
├── stock_data.py        # Stock data fetching
├── chart_generator.py   # Chart generation
├── ai_advisor.py        # AI trading advice
├── persistence.py       # Data storage
├── web_server.py        # Web monitoring
├── standalone_bot.py    # Single-file version
├── keepalive.py         # UptimeRobot server
├── data/               # JSON storage
└── charts/             # Generated charts
```
