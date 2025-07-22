# Discord Stock Bot - Local Download & Setup Guide

## Quick Start (3 Steps)

### 1. Download All Files
Download these files to a folder on your PC:
- `main.py` - Main bot file
- `config.py` - Configuration management
- `stock_data.py` - Stock data fetching
- `chart_generator.py` - Chart generation
- `ai_advisor.py` - AI trading advice
- `persistence.py` - Data storage
- `web_server.py` - Web monitoring
- `standalone_bot.py` - Single-file alternative
- `keepalive.py` - Standalone web server
- `setup_local.py` - Automatic setup script
- `local_requirements.txt` - Dependencies list
- `run_bot.bat` - Windows launcher
- `run_bot.sh` - Linux/Mac launcher

### 2. Run Setup Script
Open command prompt/terminal in the bot folder and run:
```bash
python setup_local.py
```
This automatically installs dependencies and creates necessary files.

### 3. Configure & Run
- Edit the `.env` file with your Discord and Groq API keys
- Double-click `run_bot.bat` (Windows) or run `./run_bot.sh` (Linux/Mac)

## Manual Setup (Alternative)

If the setup script doesn't work, follow these steps:

### Install Dependencies
```bash
pip install discord.py yfinance requests pandas matplotlib groq flask python-dotenv
```

### Create .env File
Create a file named `.env` with your API keys:
```env
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```

### Create Folders
Create these folders in the bot directory:
- `data/` - For storing tracked stocks
- `charts/` - For saving chart images

### Run the Bot
```bash
python main.py
```

## Getting API Keys

### Discord Bot Token
1. Go to https://discord.com/developers/applications
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the token and paste it in your `.env` file
5. Invite the bot to your server with these permissions:
   - View Channels
   - Send Messages  
   - Use Slash Commands
   - Manage Channels
   - Embed Links
   - Attach Files

### Groq API Key
1. Sign up at https://console.groq.com
2. Go to API Keys section
3. Create a new API key
4. Copy it and paste it in your `.env` file

## File Structure After Setup

```
discord-stock-bot/
├── main.py                  # Main bot application
├── config.py               # Configuration management
├── stock_data.py           # Stock data fetching
├── chart_generator.py      # Chart generation
├── ai_advisor.py           # AI trading advice
├── persistence.py          # Data storage
├── web_server.py           # Web monitoring
├── standalone_bot.py       # Single-file version
├── keepalive.py           # Standalone web server
├── .env                   # Your API keys (create this)
├── run_bot.bat           # Windows launcher
├── run_bot.sh            # Linux/Mac launcher
├── data/                 # Data storage (auto-created)
│   ├── tracked_stocks.json
│   └── user_preferences.json
└── charts/               # Chart images (auto-created)
    └── .gitkeep
```

## Running Options

### Option 1: Easy Launchers (Recommended)
- **Windows**: Double-click `run_bot.bat`
- **Linux/Mac**: Run `./run_bot.sh` in terminal

### Option 2: Manual Command
```bash
python main.py
```

### Option 3: Standalone Version
If you only want one file:
```bash
python standalone_bot.py
```

### Option 4: Web Server Only
For monitoring without Discord bot:
```bash
python keepalive.py
```

## Available Commands in Discord

After the bot is running, use these slash commands in your Discord server:

- `/price <symbol>` - Get stock price with chart
- `/track <symbol>` - Track a stock and create channel
- `/untrack <symbol>` - Remove stock from tracking
- `/liststocks` - Show all tracked stocks
- `/stockadvice <symbol>` - Get AI trading advice
- `/managechannels` - Create channels for all tracked stocks
- `/help` - Show command help

## Web Interface

When running, you can monitor the bot at:
- Main status: http://localhost:5000/
- Health check: http://localhost:5000/health
- Simple ping: http://localhost:5000/ping
- Statistics: http://localhost:5000/stats

## Troubleshooting

### "Python not found"
Install Python 3.8+ from https://python.org and make sure it's in your system PATH.

### "discord.py not found"
Run the setup script again or manually install: `pip install discord.py`

### "Bot not responding"
1. Check your Discord token in `.env` file
2. Make sure the bot is invited to your server
3. Verify bot has required permissions

### "AI advice not working"
Check your Groq API key in `.env` file and make sure you have credits.

### "No charts generated"
Make sure the `charts/` folder exists and Python can write to it.

## Support

If you need help:
1. Check the logs in console when running the bot
2. Verify all API keys are correct in `.env` file
3. Make sure all required files are downloaded
4. Try running the setup script again

The bot saves all data locally in JSON files and works completely offline except for API calls to Discord, stock data, and AI services.