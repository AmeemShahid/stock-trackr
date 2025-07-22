# Discord Stock Bot - Development Guide

## Overview

This is a comprehensive Discord bot for real-time stock tracking with AI-powered trading advice, candlestick chart generation, and persistent data storage. The bot provides users with current stock prices, technical analysis, and intelligent trading recommendations through Discord slash commands.

## User Preferences

Preferred communication style: Simple, everyday language.
Features requested: Free Groq AI API, detailed signals with real-time information, no word limits, local file support for backup deployment.

## System Architecture

### Core Architecture Pattern
The application follows a modular, service-oriented architecture with clear separation of concerns:

- **Bot Layer**: Discord.py-based command interface handling user interactions
- **Service Layer**: Specialized managers for stock data, AI advice, chart generation, and persistence
- **Data Layer**: JSON-based file storage for tracked stocks and user preferences
- **Integration Layer**: External API connections to stock data providers and AI services

### Technology Stack
- **Framework**: Discord.py for bot functionality
- **AI Integration**: Groq API for trading advice
- **Data Sources**: yfinance (primary) and Alpha Vantage (fallback) for stock data
- **Charting**: matplotlib for candlestick chart generation
- **Web Server**: Flask for uptime monitoring
- **Data Storage**: JSON files for persistence
- **Configuration**: Environment variables with fallback defaults

## Key Components

### 1. Bot Core (`main.py`)
- **Purpose**: Main Discord bot implementation with slash commands
- **Key Features**: Command handling, scheduled monitoring, event management
- **Commands Supported**: `/price`, `/track`, `/untrack`, `/liststocks`, `/stockadvice`, `/help`

### 2. Stock Data Manager (`stock_data.py`)
- **Purpose**: Unified interface for stock data from multiple sources
- **Primary Source**: yfinance (free, reliable)
- **Fallback Source**: Alpha Vantage API
- **Features**: Data caching, error handling, historical data fetching

### 3. AI Advisor (`ai_advisor.py`)
- **Purpose**: Generate intelligent trading recommendations
- **Provider**: Groq API with Llama 3.3 70B model
- **Features**: Context-aware analysis, technical indicator integration
- **Fallback**: Graceful degradation when AI service unavailable

### 4. Chart Generator (`chart_generator.py`)
- **Purpose**: Create candlestick charts with technical indicators
- **Library**: matplotlib with dark theme
- **Features**: OHLC visualization, customizable timeframes
- **Output**: PNG files saved to charts directory

### 5. Persistence Manager (`persistence.py`)
- **Purpose**: Handle data storage and retrieval
- **Storage**: JSON files in data directory
- **Data Types**: Tracked stocks, user preferences, timestamps
- **Features**: Automatic file creation, error recovery

### 6. Web Server (`web_server.py`)
- **Purpose**: Keep bot alive on cloud platforms
- **Framework**: Flask (optional dependency)
- **Endpoints**: `/` (status), `/ping` (uptime monitoring)
- **Features**: Health checks, service information

### 7. Configuration (`config.py`)
- **Purpose**: Centralized configuration management
- **Sources**: Environment variables with defaults
- **Features**: Input validation, directory creation, path management

## Data Flow

### Stock Price Request Flow
1. User executes `/price <symbol>` command
2. Bot validates symbol and checks cache
3. StockDataManager fetches current data (yfinance → Alpha Vantage fallback)
4. ChartGenerator creates candlestick chart
5. Bot responds with price data and chart attachment

### AI Advice Flow
1. User executes `/stockadvice <symbol>` command
2. StockDataManager gathers current and historical data
3. AIAdvisor prepares context and sends to Groq API
4. AI response is formatted and returned to user
5. Error handling provides fallback messages

### Stock Tracking Flow
1. User adds/removes stocks with `/track`/`untrack` commands
2. PersistenceManager updates tracked_stocks.json
3. Background task monitors tracked stocks at configured intervals
4. Price alerts sent when threshold exceeded
5. Data persisted across bot restarts

## External Dependencies

### Required APIs
- **Discord Bot Token**: For Discord integration (required)
- **Groq API Key**: For AI-powered trading advice (required)
- **Alpha Vantage API Key**: Fallback stock data source (optional, defaults to demo)

### Python Packages
- **discord.py**: Discord bot framework
- **yfinance**: Primary stock data source
- **groq**: AI service integration
- **matplotlib**: Chart generation
- **pandas**: Data manipulation
- **flask**: Web server (optional)
- **requests**: HTTP client

### Data Storage
- **File System**: JSON files in `data/` directory
- **Charts**: PNG files in `charts/` directory
- **Logs**: Application logs in `bot.log`

## Deployment Strategy

### Environment Configuration
The bot requires these environment variables:
- `DISCORD_TOKEN`: Discord bot authentication
- `GROQ_API_KEY`: AI service authentication
- `ALPHA_VANTAGE_API_KEY`: Fallback data source (optional)
- `WEB_PORT`: Web server port (default: 5000)
- `PRICE_ALERT_THRESHOLD`: Alert sensitivity (default: 2.0%)
- `MONITOR_INTERVAL_MINUTES`: Monitoring frequency (default: 5 minutes)

### Local Development
- Install dependencies from requirements
- Configure environment variables in `.env` file
- Run `python main.py`
- Bot auto-creates necessary directories and files

### Cloud Deployment (Replit)
- Environment variables set in Replit secrets
- Web server enables UptimeRobot monitoring
- JSON persistence survives restarts
- Logs available in Replit console

### Scalability Considerations
- JSON storage suitable for single-instance deployment
- Cache system reduces API calls
- Modular design allows easy database migration
- Web server supports health monitoring

### Error Handling Strategy
- Graceful API fallbacks (yfinance → Alpha Vantage)
- Service degradation (AI advice unavailable)
- Automatic retry logic for transient failures
- Comprehensive logging for debugging
- User-friendly error messages