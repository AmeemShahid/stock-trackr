"""
AI-powered stock advice using Groq API
"""

import asyncio
import logging
from typing import Optional, Dict
import json
from datetime import datetime
import pandas as pd

try:
    from groq import Groq
except ImportError:
    Groq = None

from config import Config

logger = logging.getLogger(__name__)

class AIAdvisor:
    """Provides AI-powered stock advice using Groq"""
    
    def __init__(self):
        self.config = Config()
        if Groq is None:
            logger.warning("Groq package not installed. AI advice will be unavailable.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.config.GROQ_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
    
    async def get_stock_advice(self, symbol: str, current_data: Dict, 
                              historical_data: Optional[pd.DataFrame] = None) -> Optional[str]:
        """Get comprehensive AI-powered stock advice"""
        if not self.client:
            return "❌ AI advisor is not available. Please check Groq API configuration."
        
        try:
            # Prepare context for AI
            context = self._prepare_context(symbol, current_data, historical_data)
            
            # Create detailed prompt
            prompt = self._create_analysis_prompt(symbol, context)
            
            # Get AI response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self._get_groq_response, prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting AI advice for {symbol}: {e}")
            return f"❌ Failed to generate AI advice: {str(e)}"
    
    def _prepare_context(self, symbol: str, current_data: Dict, 
                        historical_data: Optional[pd.DataFrame]) -> Dict:
        """Prepare context data for AI analysis"""
        context = {
            'symbol': symbol,
            'current_price': current_data['current_price'],
            'change': current_data['change'],
            'change_percent': current_data['change_percent'],
            'volume': current_data.get('volume', 'N/A'),
            'open': current_data.get('open'),
            'high': current_data.get('high'),
            'low': current_data.get('low'),
            'timestamp': datetime.now().isoformat()
        }
        
        if historical_data is not None and not historical_data.empty:
            # Calculate technical indicators
            context.update(self._calculate_technical_indicators(historical_data))
        
        return context
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators from historical data"""
        try:
            indicators = {}
            
            # Moving averages
            if len(data) >= 20:
                ma20_series = data['Close'].rolling(window=20).mean()
                indicators['ma20'] = float(ma20_series.iloc[-1])
                indicators['ma20_trend'] = 'bullish' if data['Close'].iloc[-1] > indicators['ma20'] else 'bearish'
            
            if len(data) >= 10:
                ma10_series = data['Close'].rolling(window=10).mean()
                indicators['ma10'] = float(ma10_series.iloc[-1])
                indicators['ma10_trend'] = 'bullish' if data['Close'].iloc[-1] > indicators['ma10'] else 'bearish'
            
            if len(data) >= 5:
                ma5_series = data['Close'].rolling(window=5).mean()
                indicators['ma5'] = float(ma5_series.iloc[-1])
                indicators['ma5_trend'] = 'bullish' if data['Close'].iloc[-1] > indicators['ma5'] else 'bearish'
            
            # RSI calculation
            if len(data) >= 14:
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = float(rsi.iloc[-1]) if not rsi.empty else 50.0
                
                if indicators['rsi'] > 70:
                    indicators['rsi_signal'] = 'overbought'
                elif indicators['rsi'] < 30:
                    indicators['rsi_signal'] = 'oversold'
                else:
                    indicators['rsi_signal'] = 'neutral'
            
            # Volume analysis
            avg_volume_series = data['Volume'].rolling(window=10).mean()
            avg_volume = avg_volume_series.iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            indicators['volume_ratio'] = float(current_volume / avg_volume)
            indicators['volume_signal'] = 'high' if indicators['volume_ratio'] > 1.5 else 'normal'
            
            # Price momentum
            if len(data) >= 5:
                price_5d_ago = data['Close'].iloc[-5]
                current_price = data['Close'].iloc[-1]
                indicators['momentum_5d'] = float((current_price - price_5d_ago) / price_5d_ago * 100)
            
            # Volatility
            indicators['volatility'] = float(data['Close'].pct_change().rolling(window=10).std().iloc[-1] * 100)
            
            # Support and resistance levels
            high_20d = data['High'].rolling(window=20).max().iloc[-1]
            low_20d = data['Low'].rolling(window=20).min().iloc[-1]
            indicators['resistance_level'] = float(high_20d)
            indicators['support_level'] = float(low_20d)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def _create_analysis_prompt(self, symbol: str, context: Dict) -> str:
        """Create detailed prompt for AI analysis"""
        prompt = f"""
You are an expert financial analyst and trading advisor. Provide a comprehensive analysis and trading recommendation for {symbol} stock.

CURRENT MARKET DATA:
- Symbol: {symbol}
- Current Price: ${context['current_price']:.2f}
- Daily Change: {context['change']:+.2f} ({context['change_percent']:+.2f}%)
- Volume: {context.get('volume', 'N/A')}
- Open: ${context.get('open', 'N/A')}
- High: ${context.get('high', 'N/A')}
- Low: ${context.get('low', 'N/A')}

TECHNICAL INDICATORS:
"""
        
        # Add technical indicators if available
        if 'ma20' in context:
            prompt += f"- 20-day MA: ${context['ma20']:.2f} (Trend: {context['ma20_trend']})\n"
        if 'ma10' in context:
            prompt += f"- 10-day MA: ${context['ma10']:.2f} (Trend: {context['ma10_trend']})\n"
        if 'ma5' in context:
            prompt += f"- 5-day MA: ${context['ma5']:.2f} (Trend: {context['ma5_trend']})\n"
        if 'rsi' in context:
            prompt += f"- RSI: {context['rsi']:.2f} (Signal: {context['rsi_signal']})\n"
        if 'volume_ratio' in context:
            prompt += f"- Volume Ratio: {context['volume_ratio']:.2f}x (Signal: {context['volume_signal']})\n"
        if 'momentum_5d' in context:
            prompt += f"- 5-day Momentum: {context['momentum_5d']:+.2f}%\n"
        if 'volatility' in context:
            prompt += f"- Volatility: {context['volatility']:.2f}%\n"
        if 'support_level' in context and 'resistance_level' in context:
            prompt += f"- Support Level: ${context['support_level']:.2f}\n"
            prompt += f"- Resistance Level: ${context['resistance_level']:.2f}\n"
        
        prompt += f"""
ANALYSIS REQUIREMENTS:
Please provide a detailed analysis including:

1. **IMMEDIATE RECOMMENDATION**: Clear BUY/SELL/HOLD recommendation with confidence level (1-10)

2. **TECHNICAL ANALYSIS**:
   - Moving average analysis and trend direction
   - RSI interpretation and momentum signals
   - Volume analysis and institutional activity
   - Support and resistance levels
   - Chart patterns if identifiable

3. **RISK ASSESSMENT**:
   - Current volatility analysis
   - Risk factors to consider
   - Position sizing recommendations
   - Stop-loss and take-profit levels

4. **MARKET CONTEXT**:
   - Overall market sentiment impact
   - Sector performance comparison
   - Recent news or events affecting the stock

5. **TRADING STRATEGY**:
   - Entry points and timing
   - Short-term vs long-term outlook
   - Alternative scenarios (bullish/bearish cases)

6. **SPECIFIC PRICE TARGETS**:
   - Next resistance/support levels
   - 1-week, 1-month price projections
   - Risk-reward ratio

Provide actionable, specific advice based on current market conditions and technical analysis. Be detailed in your reasoning and include specific price levels, percentages, and timeframes. Focus on practical trading signals that can be acted upon immediately.

Current timestamp: {context['timestamp']}
"""
        
        return prompt
    
    def _get_groq_response(self, prompt: str) -> str:
        """Get response from Groq API"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert financial analyst and trading advisor with deep knowledge of technical analysis, market trends, and risk management. Provide detailed, actionable trading advice based on real-time market data and technical indicators."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.config.GROQ_MODEL,
                max_tokens=self.config.MAX_RESPONSE_TOKENS,
                temperature=0.3,  # Lower temperature for more consistent financial advice
                top_p=0.9
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting Groq response: {e}")
            raise
