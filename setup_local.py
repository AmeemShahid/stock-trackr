#!/usr/bin/env python3
"""
Local Setup Script for Discord Stock Bot
Automatically installs dependencies and creates necessary files for local deployment
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("    Discord Stock Bot - Local Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    packages = [
        "discord.py>=2.3.0",
        "yfinance>=0.2.0", 
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "groq>=0.4.0",
        "flask>=3.0.0",
        "python-dotenv>=1.0.0"
    ]
    
    try:
        for package in packages:
            print(f"   Installing {package.split('>=')[0]}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ All dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("   Try running: pip install -r local_requirements.txt")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["data", "charts"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   Created: {directory}/")
    print("✅ Directories created")

def create_env_file():
    """Create .env template file"""
    print("\n🔐 Creating .env template...")
    
    env_template = """# Discord Stock Bot - Environment Variables
# Copy this file and fill in your actual API keys

# Required: Discord Bot Token from https://discord.com/developers/applications
DISCORD_TOKEN=your_discord_bot_token_here

# Required: Groq API Key from https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# Optional: Alpha Vantage API Key (fallback data source)
ALPHA_VANTAGE_API_KEY=demo

# Optional: Configuration (defaults shown)
GROQ_MODEL=llama-3.3-70b-versatile
PRICE_ALERT_THRESHOLD=2.0
MONITOR_INTERVAL_MINUTES=5
WEB_PORT=5000
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("   ⚠️  IMPORTANT: Edit .env file with your actual API keys!")
    else:
        print("✅ .env file already exists")

def create_data_files():
    """Create initial data files"""
    print("\n📊 Creating data files...")
    
    # Create tracked stocks file
    tracked_stocks = {
        "stocks": [],
        "last_updated": None
    }
    
    with open("data/tracked_stocks.json", "w") as f:
        json.dump(tracked_stocks, f, indent=2)
    
    # Create user preferences file  
    user_preferences = {
        "price_alert_threshold": 2.0,
        "monitor_interval_minutes": 5,
        "channels_created": [],
        "last_updated": None
    }
    
    with open("data/user_preferences.json", "w") as f:
        json.dump(user_preferences, f, indent=2)
    
    # Create .gitkeep for charts directory
    with open("charts/.gitkeep", "w") as f:
        f.write("# Charts will be saved here\n")
    
    print("✅ Data files initialized")

def create_run_script():
    """Create easy run scripts for different platforms"""
    print("\n🚀 Creating run scripts...")
    
    # Windows batch file
    windows_script = """@echo off
echo Starting Discord Stock Bot...
echo.
python main.py
pause
"""
    
    with open("run_bot.bat", "w") as f:
        f.write(windows_script)
    
    # Unix/Linux shell script
    unix_script = """#!/bin/bash
echo "Starting Discord Stock Bot..."
echo
python3 main.py
"""
    
    with open("run_bot.sh", "w") as f:
        f.write(unix_script)
    
    # Make shell script executable on Unix systems
    try:
        os.chmod("run_bot.sh", 0o755)
    except:
        pass  # Windows doesn't support chmod
    
    print("✅ Run scripts created:")
    print("   - run_bot.bat (Windows)")
    print("   - run_bot.sh (Linux/Mac)")

def print_instructions():
    """Print final setup instructions"""
    print("\n" + "=" * 60)
    print("    Setup Complete! Next Steps:")
    print("=" * 60)
    print()
    print("1. 📝 Edit the .env file with your API keys:")
    print("   - Get Discord token: https://discord.com/developers/applications") 
    print("   - Get Groq API key: https://console.groq.com")
    print()
    print("2. 🤖 Set up Discord bot permissions:")
    print("   - View Channels, Send Messages, Use Slash Commands")
    print("   - Manage Channels, Embed Links, Attach Files")
    print()
    print("3. 🚀 Run the bot:")
    print("   Windows: double-click run_bot.bat")
    print("   Linux/Mac: ./run_bot.sh")
    print("   Manual: python main.py")
    print()
    print("4. 📊 Available commands in Discord:")
    print("   /price, /track, /untrack, /liststocks")
    print("   /stockadvice, /managechannels, /help")
    print()
    print("5. 🌐 Web monitoring available at: http://localhost:5000")
    print()
    print("📖 For detailed setup guide, see README.md")
    print("=" * 60)

def main():
    """Main setup function"""
    print_banner()
    check_python_version()
    install_dependencies()
    create_directories()
    create_env_file()
    create_data_files()
    create_run_script()
    print_instructions()

if __name__ == "__main__":
    main()