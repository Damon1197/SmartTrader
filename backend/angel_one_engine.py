"""
Angel One Smart API Engine for Stock Market Intelligence Platform
Supports live market data, historical data, and market feeds using Angel One Smart API
"""

import os
import asyncio
import aiohttp
import pyotp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import logging
from dotenv import load_dotenv
import json
import requests
import pandas as pd

load_dotenv()

@dataclass
class StockData:
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    high: float
    low: float
    open: float
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    exchange: str = "NSE"
    last_updated: datetime = None

@dataclass
class SectorData:
    sector: str
    performance: float
    top_performers: List[str]
    market_cap: float
    volume: int

class AngelOneEngine:
    """Angel One Smart API data engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Angel One API Configuration
        self.trading_api_key = os.getenv('ANGEL_TRADING_API_KEY')
        self.trading_secret = os.getenv('ANGEL_TRADING_SECRET')
        self.trading_url = os.getenv('ANGEL_TRADING_URL')
        
        self.publisher_api_key = os.getenv('ANGEL_PUBLISHER_API_KEY')
        self.publisher_secret = os.getenv('ANGEL_PUBLISHER_SECRET')
        self.publisher_url = os.getenv('ANGEL_PUBLISHER_URL')
        
        self.marketfeed_api_key = os.getenv('ANGEL_MARKETFEED_API_KEY')
        self.marketfeed_secret = os.getenv('ANGEL_MARKETFEED_SECRET')
        self.marketfeed_url = os.getenv('ANGEL_MARKETFEED_URL')
        
        self.historical_api_key = os.getenv('ANGEL_HISTORICAL_API_KEY')
        self.historical_secret = os.getenv('ANGEL_HISTORICAL_SECRET')
        self.historical_url = os.getenv('ANGEL_HISTORICAL_URL')
        
        self.client_code = os.getenv('ANGEL_CLIENT_CODE')
        self.password = os.getenv('ANGEL_PASSWORD')
        self.totp_secret = os.getenv('ANGEL_TOTP_SECRET')
        
        # Authentication tokens
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None
        self.session_expiry = None
        
        # NSE Top 50 stocks with their tokens (mapping needed for Angel One)
        self.nse_stock_tokens = {
            'RELIANCE': '2885',
            'TCS': '11536',
            'HDFCBANK': '1333',
            'BHARTIARTL': '10604',
            'ICICIBANK': '4963',
            'INFOSYS': '1594',
            'SBIN': '3045',
            'LICI': '19061',
            'ITC': '1660',
            'HINDUNILVR': '1394',
            'LT': '11483',
            'KOTAKBANK': '1922',
            'AXISBANK': '5900',
            'ASIANPAINT': '236',
            'MARUTI': '10999',
            'SUNPHARMA': '3351',
            'TITAN': '3506',
            'ULTRACEMCO': '11532',
            'WIPRO': '3787',
            'ONGC': '2475',
            'NTPC': '11630',
            'JSWSTEEL': '11723',
            'POWERGRID': '14977',
            'M&M': '519',
            'TECHM': '13538',
            'TATAMOTORS': '3456',
            'HCLTECH': '7229',
            'INDUSINDBK': '5258',
            'ADANIENT': '25',
            'COALINDIA': '20374'
        }
        
        # Sector mapping
        self.sector_mapping = {
            'Banking': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'INDUSINDBK'],
            'IT': ['TCS', 'INFOSYS', 'WIPRO', 'HCLTECH', 'TECHM'],
            'Oil & Gas': ['RELIANCE', 'ONGC'],
            'Telecom': ['BHARTIARTL'],
            'FMCG': ['HINDUNILVR', 'ITC'],
            'Pharma': ['SUNPHARMA'],
            'Auto': ['MARUTI', 'TATAMOTORS', 'M&M'],
            'Metals': ['JSWSTEEL'],
            'Cement': ['ULTRACEMCO'],
            'Paints': ['ASIANPAINT'],
            'Jewelry': ['TITAN'],
            'Infrastructure': ['LT', 'POWERGRID', 'NTPC', 'COALINDIA']
        }

    async def authenticate(self) -> bool:
        """Authenticate with Angel One Smart API"""
        try:
            # For now, we'll create a mock authentication since the actual Smart API requires
            # proper installation and may not work with the provided test URLs
            # In production, this would use the SmartConnect library
            
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret)
            current_totp = totp.now()
            
            self.logger.info(f"Generated TOTP: {current_totp}")
            
            # Mock authentication success for development
            self.auth_token = "mock_auth_token_" + str(datetime.now().timestamp())
            self.refresh_token = "mock_refresh_token_" + str(datetime.now().timestamp())
            self.feed_token = "mock_feed_token_" + str(datetime.now().timestamp())
            self.session_expiry = datetime.now() + timedelta(hours=6)
            
            self.logger.info("Angel One authentication successful (mock)")
            return True
            
        except Exception as e:
            self.logger.error(f"Angel One authentication failed: {str(e)}")
            return False

    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        if not self.auth_token or not self.session_expiry:
            return False
        return datetime.now() < self.session_expiry

    async def ensure_authenticated(self):
        """Ensure we have a valid session"""
        if not self.is_session_valid():
            await self.authenticate()

    async def get_live_stock_data(self, symbol: str, source: str = "angel_one") -> Optional[StockData]:
        """Get real-time stock data from Angel One"""
        try:
            await self.ensure_authenticated()
            
            # Get token for symbol
            token = self.nse_stock_tokens.get(symbol.upper())
            if not token:
                self.logger.warning(f"Token not found for symbol: {symbol}")
                return None
            
            # Mock data for development (replace with actual API call)
            # In production, this would call Angel One marketfeed API
            mock_data = await self._get_mock_stock_data(symbol, token)
            
            return mock_data
            
        except Exception as e:
            self.logger.error(f"Error fetching Angel One data for {symbol}: {str(e)}")
            return None

    async def _get_mock_stock_data(self, symbol: str, token: str) -> StockData:
        """Generate mock stock data for development"""
        import random
        
        # Mock price based on symbol
        base_prices = {
            'RELIANCE': 2456.75,
            'TCS': 3442.30,
            'HDFCBANK': 1678.90,
            'BHARTIARTL': 912.45,
            'ICICIBANK': 1089.55,
            'INFOSYS': 1587.45,
            'SBIN': 756.30,
            'ITC': 465.20,
            'HINDUNILVR': 2543.80,
            'MARUTI': 10847.65
        }
        
        base_price = base_prices.get(symbol, 1000.0)
        
        # Add some random variation
        price_variation = random.uniform(-0.05, 0.05)
        current_price = base_price * (1 + price_variation)
        
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        return StockData(
            symbol=symbol,
            price=round(current_price, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=random.randint(100000, 10000000),
            high=round(current_price * 1.02, 2),
            low=round(current_price * 0.98, 2),
            open=round(base_price, 2),
            market_cap=None,
            sector=self._get_sector_for_symbol(symbol),
            exchange="NSE",
            last_updated=datetime.now()
        )

    def _get_sector_for_symbol(self, symbol: str) -> str:
        """Get sector for a given symbol"""
        for sector, symbols in self.sector_mapping.items():
            if symbol in symbols:
                return sector
        return "Others"

    async def get_historical_data(self, symbol: str, interval: str = "1day", 
                                days: int = 30) -> List[Dict]:
        """Get historical candlestick data from Angel One"""
        try:
            await self.ensure_authenticated()
            
            token = self.nse_stock_tokens.get(symbol.upper())
            if not token:
                return []
            
            # Mock historical data for development
            # In production, this would call Angel One historical data API
            historical_data = []
            
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                base_price = 1000 + (i * 10)  # Simple price progression
                
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(base_price, 2),
                    'high': round(base_price * 1.03, 2),
                    'low': round(base_price * 0.97, 2),
                    'close': round(base_price * 1.01, 2),
                    'volume': 1000000 + (i * 50000)
                })
            
            return list(reversed(historical_data))  # Return chronological order
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return []

    async def get_sector_performance(self) -> List[SectorData]:
        """Get sector-wise performance data"""
        sector_data = []
        
        for sector, symbols in self.sector_mapping.items():
            try:
                total_change = 0
                valid_stocks = 0
                top_performers = []
                total_volume = 0
                
                # Get data for all stocks in sector
                for symbol in symbols:
                    stock_data = await self.get_live_stock_data(symbol)
                    if stock_data:
                        total_change += stock_data.change_percent
                        valid_stocks += 1
                        total_volume += stock_data.volume
                        
                        # Track top performers
                        if stock_data.change_percent > 0:
                            top_performers.append({
                                'symbol': stock_data.symbol,
                                'change': stock_data.change_percent
                            })
                
                if valid_stocks > 0:
                    avg_performance = total_change / valid_stocks
                    
                    # Sort top performers
                    top_performers.sort(key=lambda x: x['change'], reverse=True)
                    top_performer_symbols = [tp['symbol'] for tp in top_performers[:3]]
                    
                    sector_data.append(SectorData(
                        sector=sector,
                        performance=round(avg_performance, 2),
                        top_performers=top_performer_symbols,
                        market_cap=0,  # Would be calculated from actual data
                        volume=total_volume
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error processing sector {sector}: {str(e)}")
                continue
        
        return sector_data

    async def get_market_movers(self, limit: int = 10) -> Dict[str, List[StockData]]:
        """Get top gainers and losers"""
        all_data = []
        
        # Get data for top stocks
        for symbol in list(self.nse_stock_tokens.keys())[:20]:  # Limit to avoid too many calls
            stock_data = await self.get_live_stock_data(symbol)
            if stock_data:
                all_data.append(stock_data)
        
        # Sort by performance
        gainers = sorted(all_data, key=lambda x: x.change_percent, reverse=True)[:limit]
        losers = sorted(all_data, key=lambda x: x.change_percent)[:limit]
        
        # Most active by volume
        most_active = sorted(all_data, key=lambda x: x.volume, reverse=True)[:limit]
        
        return {
            'gainers': gainers,
            'losers': losers,
            'most_active': most_active
        }

    async def get_nifty_data(self) -> Optional[StockData]:
        """Get Nifty 50 index data"""
        # Mock Nifty data
        import random
        base_price = 22500
        price_variation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + price_variation)
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        return StockData(
            symbol="NIFTY",
            price=round(current_price, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=0,
            high=round(current_price * 1.01, 2),
            low=round(current_price * 0.99, 2),
            open=round(base_price, 2),
            exchange="NSE",
            last_updated=datetime.now()
        )

    async def get_bank_nifty_data(self) -> Optional[StockData]:
        """Get Bank Nifty index data"""
        # Mock Bank Nifty data
        import random
        base_price = 48500
        price_variation = random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + price_variation)
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        return StockData(
            symbol="BANKNIFTY",
            price=round(current_price, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=0,
            high=round(current_price * 1.01, 2),
            low=round(current_price * 0.99, 2),
            open=round(base_price, 2),
            exchange="NSE",
            last_updated=datetime.now()
        )

    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for stocks by name or symbol"""
        try:
            results = []
            query_lower = query.lower()
            
            # Search in our known symbols
            for symbol in self.nse_stock_tokens.keys():
                if query_lower in symbol.lower():
                    stock_data = await self.get_live_stock_data(symbol)
                    if stock_data:
                        results.append({
                            'symbol': stock_data.symbol,
                            'name': stock_data.symbol,  # In production, fetch company name
                            'price': stock_data.price,
                            'change_percent': stock_data.change_percent,
                            'sector': stock_data.sector
                        })
                        
                        if len(results) >= limit:
                            break
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching stocks: {str(e)}")
            return []

    def get_trading_style_stocks(self, trading_style: str, limit: int = 5) -> List[str]:
        """Get recommended stocks based on trading style"""
        style_recommendations = {
            'scalping': ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'BHARTIARTL'],
            'intraday': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFOSYS', 'ITC'],
            'swing': ['MARUTI', 'SUNPHARMA', 'ASIANPAINT', 'TITAN', 'ULTRACEMCO'],
            'positional': ['TCS', 'INFOSYS', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR'],
            'delivery': ['RELIANCE', 'TCS', 'HDFCBANK', 'HINDUNILVR', 'ASIANPAINT'],
            'technical': ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'BHARTIARTL'],
            'fundamental': ['TCS', 'INFOSYS', 'HDFCBANK', 'HINDUNILVR', 'ASIANPAINT'],
            'momentum': ['ADANIENT', 'JSWSTEEL', 'TATAMOTORS', 'BHARTIARTL', 'ONGC']
        }
        
        return style_recommendations.get(trading_style, list(self.nse_stock_tokens.keys())[:limit])

# Global instance
angel_one_engine = AngelOneEngine()