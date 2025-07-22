#!/usr/bin/env python3
"""
Create Download Package for Discord Stock Bot
Creates a ZIP file with all necessary files for local deployment
"""

import os
import zipfile
import shutil
from datetime import datetime

def create_download_package():
    """Create a downloadable package with all bot files"""
    
    print("Creating Discord Stock Bot download package...")
    
    # Files to include in the package
    files_to_include = [
        # Core bot files
        'main.py',
        'config.py', 
        'stock_data.py',
        'chart_generator.py',
        'ai_advisor.py',
        'persistence.py',
        'web_server.py',
        
        # Alternative versions
        'standalone_bot.py',
        'keepalive.py',
        
        # Setup and run scripts
        'setup_local.py',
        'local_requirements.txt',
        'run_bot.bat',
        'run_bot.sh',
        
        # Documentation
        'README.md',
        'DOWNLOAD_GUIDE.md',
        'replit.md'
    ]
    
    # Create package directory
    package_name = f"discord-stock-bot-{datetime.now().strftime('%Y%m%d')}"
    package_dir = f"packages/{package_name}"
    
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir, exist_ok=True)
    
    # Copy files to package directory
    copied_files = []
    for file in files_to_include:
        if os.path.exists(file):
            shutil.copy2(file, package_dir)
            copied_files.append(file)
            print(f"✅ Added: {file}")
        else:
            print(f"⚠️  Skipped: {file} (not found)")
    
    # Create data and charts directories
    os.makedirs(f"{package_dir}/data", exist_ok=True)
    os.makedirs(f"{package_dir}/charts", exist_ok=True)
    
    # Create .gitkeep files
    with open(f"{package_dir}/data/.gitkeep", "w") as f:
        f.write("# Data files will be stored here\n")
    with open(f"{package_dir}/charts/.gitkeep", "w") as f:
        f.write("# Chart images will be saved here\n")
    
    # Create example .env file
    env_example = """# Discord Stock Bot - Environment Variables
# Rename this file to .env and fill in your actual API keys

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
    
    with open(f"{package_dir}/.env.example", "w") as f:
        f.write(env_example)
    
    # Create ZIP file
    zip_filename = f"{package_name}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, "packages")
                zipf.write(file_path, arc_name)
    
    # Clean up temporary directory
    shutil.rmtree("packages")
    
    print(f"\n🎉 Package created: {zip_filename}")
    print(f"📁 Contains {len(copied_files)} files + directories")
    print(f"📊 Package size: {os.path.getsize(zip_filename) / 1024:.1f} KB")
    print("\n📋 To use:")
    print("1. Extract the ZIP file")
    print("2. Run: python setup_local.py")
    print("3. Edit .env file with your API keys")
    print("4. Run the bot with run_bot.bat or run_bot.sh")
    
    return zip_filename

if __name__ == "__main__":
    create_download_package()