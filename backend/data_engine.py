"""
Enhanced Market Data Engine for Stock Market Intelligence Platform
Supports multiple data sources: Angel One Smart API (primary), yfinance, Twelvedata (fallback)
"""

import yfinance as yf
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import aiohttp
from dataclasses import dataclass
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Import Angel One after environment is loaded
import sys
sys.path.append('/app/backend')

try:
    from angel_one_engine import angel_one_engine, StockData, SectorData
    ANGEL_ONE_AVAILABLE = True
except ImportError as e:
    print(f"Angel One engine not available: {e}")
    ANGEL_ONE_AVAILABLE = False
    
    # Define local classes if Angel One is not available
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

class MarketDataEngine:
    """Enhanced market data engine supporting Angel One Smart API and fallback sources"""
    
    def __init__(self):
        self.twelvedata_api_key = os.getenv('TWELVEDATA_API_KEY')
        self.logger = logging.getLogger(__name__)
        
        # Primary data source: Angel One (if available)
        self.angel_engine = angel_one_engine if ANGEL_ONE_AVAILABLE else None
        
        # NSE Top 50 stocks for quick access (fallback)
        self.nse_top_stocks = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS', 'ICICIBANK.NS',
            'INFOSYS.NS', 'SBIN.NS', 'LICI.NS', 'ITC.NS', 'HINDUNILVR.NS',
            'LT.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS',
            'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ONGC.NS',
            'NTPC.NS', 'JSWSTEEL.NS', 'POWERGRID.NS', 'M&M.NS', 'TECHM.NS',
            'TATAMOTORS.NS', 'HCLTECH.NS', 'INDUSINDBK.NS', 'ADANIENT.NS', 'COALINDIA.NS'
        ]
        
        # Sector mapping
        self.sector_mapping = {
            'Banking': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'INDUSINDBK.NS'],
            'IT': ['TCS.NS', 'INFOSYS.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS'],
            'Oil & Gas': ['RELIANCE.NS', 'ONGC.NS'],
            'Telecom': ['BHARTIARTL.NS'],
            'FMCG': ['HINDUNILVR.NS', 'ITC.NS'],
            'Pharma': ['SUNPHARMA.NS'],
            'Auto': ['MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS'],
            'Metals': ['JSWSTEEL.NS'],
            'Cement': ['ULTRACEMCO.NS'],
            'Paints': ['ASIANPAINT.NS'],
            'Jewelry': ['TITAN.NS'],
            'Infrastructure': ['LT.NS', 'POWERGRID.NS', 'NTPC.NS', 'COALINDIA.NS']
        }

    async def get_live_stock_data(self, symbol: str, source: str = "auto") -> Optional[StockData]:
        """Get real-time stock data with Angel One primary and fallback sources"""
        try:
            # Try Angel One first (primary source) if available
            if (source == "auto" or source == "angel_one") and ANGEL_ONE_AVAILABLE and self.angel_engine:
                try:
                    # Clean symbol for Angel One
                    clean_symbol = symbol.replace('.NS', '').upper()
                    angel_data = await self.angel_engine.get_live_stock_data(clean_symbol)
                    if angel_data:
                        self.logger.info(f"Successfully fetched data from Angel One for {symbol}")
                        return angel_data
                except Exception as e:
                    self.logger.warning(f"Angel One failed for {symbol}: {str(e)}")
            
            # Fallback to yfinance
            if source == "auto" or source == "yfinance":
                try:
                    yf_data = await self._get_yfinance_data(symbol)
                    if yf_data:
                        self.logger.info(f"Fallback to yfinance successful for {symbol}")
                        return yf_data
                except Exception as e:
                    self.logger.warning(f"yfinance failed for {symbol}: {str(e)}")
            
            # Fallback to twelvedata
            if source == "auto" or source == "twelvedata":
                try:
                    td_data = await self._get_twelvedata_data(symbol)
                    if td_data:
                        self.logger.info(f"Fallback to twelvedata successful for {symbol}")
                        return td_data
                except Exception as e:
                    self.logger.warning(f"Twelvedata failed for {symbol}: {str(e)}")
            
            self.logger.error(f"All data sources failed for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    async def _get_yfinance_data(self, symbol: str) -> Optional[StockData]:
        """Fetch data using yfinance"""
        try:
            # Ensure NSE format
            if not symbol.endswith('.NS'):
                symbol = f"{symbol}.NS"
            
            stock = yf.Ticker(symbol)
            
            # Get current data
            hist = stock.history(period="2d")
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            
            # Get additional info
            info = stock.info
            
            return StockData(
                symbol=symbol.replace('.NS', ''),
                price=round(current_price, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=int(hist['Volume'].iloc[-1]),
                high=round(hist['High'].iloc[-1], 2),
                low=round(hist['Low'].iloc[-1], 2),
                open=round(hist['Open'].iloc[-1], 2),
                market_cap=info.get('marketCap'),
                sector=info.get('sector'),
                exchange="NSE",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"yfinance error for {symbol}: {str(e)}")
            return None

    async def _get_twelvedata_data(self, symbol: str) -> Optional[StockData]:
        """Fetch data using Twelvedata API"""
        try:
            if not self.twelvedata_api_key:
                self.logger.warning("Twelvedata API key not found")
                return None
            
            # Format symbol for NSE
            formatted_symbol = f"{symbol}:NSE"
            
            url = "https://api.twelvedata.com/price"
            params = {
                'symbol': formatted_symbol,
                'apikey': self.twelvedata_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        price_data = await response.json()
                        
                        if 'price' in price_data:
                            current_price = float(price_data['price'])
                            
                            # Get additional data (quote)
                            quote_url = "https://api.twelvedata.com/quote"
                            quote_params = {
                                'symbol': formatted_symbol,
                                'apikey': self.twelvedata_api_key
                            }
                            
                            async with session.get(quote_url, params=quote_params) as quote_response:
                                if quote_response.status == 200:
                                    quote_data = await quote_response.json()
                                    
                                    return StockData(
                                        symbol=symbol,
                                        price=current_price,
                                        change=float(quote_data.get('change', 0)),
                                        change_percent=float(quote_data.get('percent_change', 0)),
                                        volume=int(quote_data.get('volume', 0)),
                                        high=float(quote_data.get('high', current_price)),
                                        low=float(quote_data.get('low', current_price)),
                                        open=float(quote_data.get('open', current_price)),
                                        exchange="NSE",
                                        last_updated=datetime.now()
                                    )
                        
        except Exception as e:
            self.logger.error(f"Twelvedata error for {symbol}: {str(e)}")
            return None

    async def get_sector_performance(self) -> List[SectorData]:
        """Get sector-wise performance data with Angel One primary source"""
        try:
            # Try Angel One first
            angel_sectors = await self.angel_engine.get_sector_performance()
            if angel_sectors:
                self.logger.info("Successfully fetched sector data from Angel One")
                return angel_sectors
        except Exception as e:
            self.logger.warning(f"Angel One sector data failed: {str(e)}")
        
        # Fallback to original implementation
        sector_data = []
        
        for sector, symbols in self.sector_mapping.items():
            try:
                total_change = 0
                valid_stocks = 0
                top_performers = []
                total_market_cap = 0
                total_volume = 0
                
                # Get data for all stocks in sector
                for symbol in symbols:
                    stock_data = await self.get_live_stock_data(symbol.replace('.NS', ''))
                    if stock_data:
                        total_change += stock_data.change_percent
                        valid_stocks += 1
                        total_volume += stock_data.volume
                        
                        if stock_data.market_cap:
                            total_market_cap += stock_data.market_cap
                        
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
                        market_cap=total_market_cap,
                        volume=total_volume
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error processing sector {sector}: {str(e)}")
                continue
        
        return sector_data

    async def get_market_movers(self, limit: int = 10) -> Dict[str, List[StockData]]:
        """Get top gainers and losers with Angel One primary source"""
        try:
            # Try Angel One first
            angel_movers = await self.angel_engine.get_market_movers(limit)
            if angel_movers:
                self.logger.info("Successfully fetched market movers from Angel One")
                return angel_movers
        except Exception as e:
            self.logger.warning(f"Angel One market movers failed: {str(e)}")
        
        # Fallback to original implementation
        all_data = []
        
        # Get data for top stocks
        for symbol in self.nse_top_stocks[:30]:  # Limit to avoid API rate limits
            stock_data = await self.get_live_stock_data(symbol.replace('.NS', ''))
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
        """Get Nifty 50 index data with Angel One primary source"""
        try:
            # Try Angel One first
            angel_nifty = await self.angel_engine.get_nifty_data()
            if angel_nifty:
                return angel_nifty
        except Exception as e:
            self.logger.warning(f"Angel One Nifty data failed: {str(e)}")
        
        # Fallback to yfinance
        return await self.get_live_stock_data('^NSEI')

    async def get_bank_nifty_data(self) -> Optional[StockData]:
        """Get Bank Nifty index data with Angel One primary source"""
        try:
            # Try Angel One first
            angel_bank_nifty = await self.angel_engine.get_bank_nifty_data()
            if angel_bank_nifty:
                return angel_bank_nifty
        except Exception as e:
            self.logger.warning(f"Angel One Bank Nifty data failed: {str(e)}")
        
        # Fallback to yfinance
        return await self.get_live_stock_data('^NSEBANK')

    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for stocks by name or symbol with Angel One primary source"""
        try:
            # Try Angel One first
            angel_results = await self.angel_engine.search_stocks(query, limit)
            if angel_results:
                return angel_results
        except Exception as e:
            self.logger.warning(f"Angel One search failed: {str(e)}")
        
        # Fallback to original implementation
        try:
            results = []
            query_lower = query.lower()
            
            # Search in our known symbols
            for symbol in self.nse_top_stocks:
                symbol_clean = symbol.replace('.NS', '')
                if query_lower in symbol_clean.lower():
                    stock_data = await self.get_live_stock_data(symbol_clean)
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
        """Get recommended stocks based on trading style with Angel One integration"""
        try:
            # Use Angel One recommendations
            return self.angel_engine.get_trading_style_stocks(trading_style, limit)
        except Exception as e:
            self.logger.warning(f"Angel One trading style stocks failed: {str(e)}")
            
            # Fallback to original recommendations
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
            
            return style_recommendations.get(trading_style, self.nse_top_stocks[:limit])

# Global instance
market_data_engine = MarketDataEngine()
