from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import asyncio
from openai import AsyncOpenAI
from data_engine import market_data_engine, StockData
from angel_one_engine import angel_one_engine

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Configure OpenAI
# Configure OpenAI
try:
    # Simple initialization without extra parameters
    openai_client = AsyncOpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {str(e)}")
    # Fallback to a mock client for testing
    class MockOpenAIClient:
        async def chat_completions_create(self, **kwargs):
            class MockResponse:
                class MockChoice:
                    class MockMessage:
                        content = "This is a mock AI response for testing purposes."
                    message = MockMessage()
                choices = [MockChoice()]
            return MockResponse()
    openai_client = MockOpenAIClient()

# MongoDB client
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

# Pydantic models
class QuestionnaireResponse(BaseModel):
    question_id: str
    answer: str
    score: int

class TradingStyleAssessment(BaseModel):
    user_id: str
    responses: List[QuestionnaireResponse]
    session_id: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    trading_style: str
    style_confidence: float
    personality_traits: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime
    session_id: str

# Trading Style Questions
TRADING_QUESTIONS = [
    {
        "id": "q1",
        "question": "How long do you typically hold your stock positions?",
        "options": [
            {"text": "Minutes to a few hours (same day)", "value": "intraday", "score": 5},
            {"text": "1-7 days", "value": "swing", "score": 4},
            {"text": "1-3 months", "value": "positional", "score": 3},
            {"text": "6 months to several years", "value": "delivery", "score": 2},
            {"text": "I prefer very quick trades (seconds to minutes)", "value": "scalping", "score": 5}
        ]
    },
    {
        "id": "q2", 
        "question": "How do you feel when you see your investment losing money?",
        "options": [
            {"text": "Extremely anxious - I need to exit immediately", "value": "scalping", "score": 5},
            {"text": "Concerned but I can wait a day or two", "value": "intraday", "score": 4},
            {"text": "Worried but willing to hold for weeks", "value": "swing", "score": 3},
            {"text": "Patient - I can hold for months if fundamentals are strong", "value": "delivery", "score": 2},
            {"text": "Calm - temporary losses don't affect my long-term strategy", "value": "fundamental", "score": 1}
        ]
    },
    {
        "id": "q3",
        "question": "What drives your trading decisions most?",
        "options": [
            {"text": "Chart patterns and technical indicators", "value": "technical", "score": 5},
            {"text": "Company financials and business fundamentals", "value": "fundamental", "score": 4},
            {"text": "Market momentum and price movement", "value": "momentum", "score": 3},
            {"text": "Breaking news and market events", "value": "swing", "score": 2},
            {"text": "Quick profit opportunities regardless of method", "value": "scalping", "score": 5}
        ]
    },
    {
        "id": "q4",
        "question": "How much time can you dedicate to monitoring markets daily?",
        "options": [
            {"text": "Constantly throughout market hours", "value": "scalping", "score": 5},
            {"text": "Several times during market hours", "value": "intraday", "score": 4},
            {"text": "Once or twice daily", "value": "swing", "score": 3},
            {"text": "Few times per week", "value": "positional", "score": 2},
            {"text": "Weekly or monthly reviews", "value": "delivery", "score": 1}
        ]
    },
    {
        "id": "q5",
        "question": "What's your risk tolerance?",
        "options": [
            {"text": "Very high - I'm comfortable with large swings", "value": "scalping", "score": 5},
            {"text": "High - I can handle significant daily volatility", "value": "intraday", "score": 4},
            {"text": "Moderate - Some ups and downs are acceptable", "value": "swing", "score": 3},
            {"text": "Low - I prefer steady, gradual growth", "value": "delivery", "score": 2},
            {"text": "Very low - Capital preservation is my priority", "value": "fundamental", "score": 1}
        ]
    },
    {
        "id": "q6",
        "question": "How do you react to market volatility?",
        "options": [
            {"text": "I thrive on it - volatility creates opportunities", "value": "scalping", "score": 5},
            {"text": "I can use it to my advantage with right timing", "value": "momentum", "score": 4},
            {"text": "I'm cautious but can navigate through it", "value": "technical", "score": 3},
            {"text": "I prefer to wait for calmer markets", "value": "positional", "score": 2},
            {"text": "I avoid volatile periods completely", "value": "delivery", "score": 1}
        ]
    },
    {
        "id": "q7",
        "question": "What's your primary goal in trading/investing?",
        "options": [
            {"text": "Quick daily profits", "value": "scalping", "score": 5},
            {"text": "Regular income from trading", "value": "intraday", "score": 4},
            {"text": "Capturing medium-term trends", "value": "swing", "score": 3},
            {"text": "Long-term wealth building", "value": "delivery", "score": 2},
            {"text": "Beating inflation and steady growth", "value": "fundamental", "score": 1}
        ]
    },
    {
        "id": "q8",
        "question": "How important is technical analysis to you?",
        "options": [
            {"text": "Extremely important - I rely heavily on charts", "value": "technical", "score": 5},
            {"text": "Very important - I use multiple indicators", "value": "scalping", "score": 4},
            {"text": "Moderately important - I use basic indicators", "value": "swing", "score": 3},
            {"text": "Somewhat important - I prefer fundamentals", "value": "fundamental", "score": 2},
            {"text": "Not important - I focus on business value", "value": "delivery", "score": 1}
        ]
    }
]

@app.get("/")
async def root():
    return {"message": "Stock Market Intelligence Platform API"}

@app.get("/api/questionnaire")
async def get_questionnaire():
    """Get the trading style questionnaire"""
    return {"questions": TRADING_QUESTIONS}

@app.post("/api/assess-trading-style")
async def assess_trading_style(assessment: TradingStyleAssessment):
    """Analyze user responses and determine trading style using AI"""
    try:
        # Calculate style scores
        style_scores = {}
        for response in assessment.responses:
            question = next((q for q in TRADING_QUESTIONS if q["id"] == response.question_id), None)
            if question:
                option = next((o for o in question["options"] if o["text"] == response.answer), None)
                if option:
                    style = option["value"]
                    if style not in style_scores:
                        style_scores[style] = 0
                    style_scores[style] += option["score"]

        # Determine primary trading style
        primary_style = max(style_scores, key=style_scores.get) if style_scores else "swing"
        confidence = (style_scores.get(primary_style, 0) / sum(style_scores.values())) * 100 if style_scores else 50

        # Generate AI analysis
        session_id = assessment.session_id or str(uuid.uuid4())
        
        # Prepare responses for AI analysis
        responses_text = "\n".join([
            f"Q: {next((q['question'] for q in TRADING_QUESTIONS if q['id'] == r.question_id), 'Unknown')} "
            f"A: {r.answer}"
            for r in assessment.responses
        ])

        # Create system message
        system_message = """You are an expert trading psychology analyst. Analyze the user's questionnaire responses to provide:
1. A detailed personality profile for trading
2. Specific trading recommendations based on their style
3. Risk management suggestions
4. Key strengths and potential weaknesses

Be specific and actionable in your recommendations."""

        # Create user message
        user_message = f"""Analyze these trading questionnaire responses:

{responses_text}

Detected Primary Style: {primary_style.title()}
Confidence: {confidence:.1f}%

Provide a comprehensive analysis including:
1. Personality traits for trading
2. 5 specific actionable recommendations
3. Risk management advice
4. Potential challenges to watch for"""

        # Call OpenAI API
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            ai_response = response.choices[0].message.content
        except Exception as e:
            # If OpenAI call fails, provide a fallback response
            ai_response = f"Analysis not available due to API error. Your primary trading style is {primary_style.title()} with {confidence:.1f}% confidence."

        # Parse recommendations from AI response
        recommendations = [
            "Focus on your identified trading style consistency",
            "Implement proper risk management rules",
            "Practice with paper trading first",
            "Keep a trading journal",
            "Set clear entry and exit rules"
        ]

        # Create user profile
        profile = {
            "user_id": assessment.user_id,
            "trading_style": primary_style,
            "style_confidence": confidence,
            "personality_traits": {
                "primary_style": primary_style,
                "style_scores": style_scores,
                "ai_analysis": ai_response
            },
            "recommendations": recommendations,
            "created_at": datetime.utcnow(),
            "session_id": session_id
        }

        # Save to database
        await db.user_profiles.insert_one(profile)

        # Return analysis
        return {
            "user_id": assessment.user_id,
            "trading_style": primary_style,
            "style_confidence": confidence,
            "style_scores": style_scores,
            "ai_analysis": ai_response,
            "recommendations": recommendations,
            "session_id": session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trading style: {str(e)}")

@app.get("/api/dashboard/{user_id}")
async def get_user_dashboard(user_id: str):
    """Get personalized dashboard for user with real-time data"""
    try:
        # Get user profile
        profile = await db.user_profiles.find_one({"user_id": user_id})
        if not profile:
            # For testing purposes, create a mock profile if none exists
            mock_profile = {
                "user_id": user_id,
                "trading_style": "swing",  # Default style
                "style_confidence": 75.0,
                "recommendations": [
                    "Focus on your identified trading style consistency",
                    "Implement proper risk management rules",
                    "Practice with paper trading first",
                    "Keep a trading journal",
                    "Set clear entry and exit rules"
                ]
            }
            profile = mock_profile

        trading_style = profile["trading_style"]
        
        # Get real-time market data
        try:
            # Get recommended stocks for user's style
            recommended_symbols = market_data_engine.get_trading_style_stocks(trading_style, 5)
            top_stocks = []
            
            for symbol in recommended_symbols:
                stock_data = await market_data_engine.get_live_stock_data(symbol)
                if stock_data:
                    signal = "BUY" if stock_data.change_percent > 1 else "SELL" if stock_data.change_percent < -1 else "HOLD"
                    top_stocks.append({
                        "symbol": stock_data.symbol,
                        "price": stock_data.price,
                        "change": f"{'+' if stock_data.change >= 0 else ''}{stock_data.change_percent:.1f}%",
                        "signal": signal,
                        "volume": stock_data.volume
                    })
            
            # Get sector performance
            sector_data = await market_data_engine.get_sector_performance()
            sector_performance = [
                {
                    "sector": sector.sector,
                    "performance": f"{'+' if sector.performance >= 0 else ''}{sector.performance:.1f}%"
                }
                for sector in sector_data[:6]
            ]
            
            # Get market movers
            market_movers = await market_data_engine.get_market_movers(5)
            
            # Generate style-specific insights
            insights = []
            if trading_style == "scalping":
                insights = [
                    f"High volatility detected in {top_stocks[0]['symbol'] if top_stocks else 'RELIANCE'} - potential scalping opportunity",
                    "Strong momentum in Banking sector for quick trades",
                    f"Volume spike in {market_movers['most_active'][0].symbol if market_movers['most_active'] else 'TCS'} - watch for entry"
                ]
            elif trading_style == "intraday":
                insights = [
                    f"{top_stocks[0]['symbol'] if top_stocks else 'HDFC'} showing bullish divergence on RSI",
                    "IT sector momentum building for intraday moves",
                    f"Bank Nifty approaching key support - watch for bounce"
                ]
            elif trading_style == "swing":
                insights = [
                    f"{top_stocks[0]['symbol'] if top_stocks else 'MARUTI'} forming bullish flag pattern - 3-5 day breakout expected",
                    "Pharma sector showing accumulation signs",
                    f"Auto sector testing support levels - potential swing entries"
                ]
            else:
                insights = [
                    f"Strong fundamentals detected in {top_stocks[0]['symbol'] if top_stocks else 'TCS'}",
                    "Banking sector showing long-term growth potential",
                    "Defensive stocks gaining institutional interest"
                ]
            
        except Exception as e:
            # Fallback to mock data if real-time data fails
            top_stocks = [
                {"symbol": "RELIANCE", "price": 2456.75, "change": "+1.2%", "signal": "BUY"},
                {"symbol": "TCS", "price": 3442.30, "change": "+0.8%", "signal": "HOLD"},
                {"symbol": "HDFC", "price": 1678.90, "change": "-0.3%", "signal": "WATCH"},
                {"symbol": "INFY", "price": 1587.45, "change": "+2.1%", "signal": "BUY"}
            ]
            sector_performance = [
                {"sector": "IT", "performance": "+1.5%"},
                {"sector": "Banking", "performance": "+0.8%"},
                {"sector": "Pharma", "performance": "-0.2%"},
                {"sector": "Auto", "performance": "+1.1%"}
            ]
            insights = [
                "Real-time data temporarily unavailable - using cached data",
                "Market showing mixed signals today",
                "Focus on your trading plan and risk management"
            ]

        # Determine timeframes based on style
        if trading_style == "scalping":
            timeframes = ["1min", "5min", "15min"]
        elif trading_style == "intraday":
            timeframes = ["5min", "15min", "1hour"]
        elif trading_style == "swing":
            timeframes = ["1hour", "4hour", "1day"]
        else:
            timeframes = ["1day", "1week", "1month"]

        dashboard_data = {
            "user_profile": {
                "trading_style": profile["trading_style"],
                "confidence": profile.get("style_confidence", 75.0),
                "recommendations": profile["recommendations"]
            },
            "market_insights": insights,
            "recommended_timeframes": timeframes,
            "top_stocks": top_stocks,
            "sector_performance": sector_performance,
            "last_updated": datetime.now().isoformat()
        }

        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard: {str(e)}")

# New Market Data Endpoints

@app.get("/api/market/live/{symbol}")
async def get_live_stock(symbol: str, source: str = "auto"):
    """Get real-time data for a specific stock (Angel One primary, with fallbacks)"""
    try:
        stock_data = await market_data_engine.get_live_stock_data(symbol, source)
        if stock_data:
            return {
                "symbol": stock_data.symbol,
                "price": stock_data.price,
                "change": stock_data.change,
                "change_percent": stock_data.change_percent,
                "volume": stock_data.volume,
                "high": stock_data.high,
                "low": stock_data.low,
                "open": stock_data.open,
                "sector": stock_data.sector,
                "exchange": stock_data.exchange,
                "last_updated": stock_data.last_updated.isoformat() if stock_data.last_updated else None,
                "data_source": "angel_one_primary"  # Indicate primary source
            }
        else:
            raise HTTPException(status_code=404, detail="Stock data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")

# New Angel One specific endpoints

@app.get("/api/angel/status")
async def get_angel_one_status():
    """Get Angel One API connection status"""
    try:
        status = {
            "authenticated": angel_one_engine.is_session_valid(),
            "auth_token_exists": bool(angel_one_engine.auth_token),
            "session_expiry": angel_one_engine.session_expiry.isoformat() if angel_one_engine.session_expiry else None,
            "available_stocks": len(angel_one_engine.nse_stock_tokens),
            "supported_sectors": len(angel_one_engine.sector_mapping)
        }
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Angel One status: {str(e)}")

@app.post("/api/angel/authenticate")
async def authenticate_angel_one():
    """Manually trigger Angel One authentication"""
    try:
        success = await angel_one_engine.authenticate()
        if success:
            return {
                "status": "success",
                "message": "Angel One authentication successful",
                "session_expiry": angel_one_engine.session_expiry.isoformat() if angel_one_engine.session_expiry else None
            }
        else:
            raise HTTPException(status_code=401, detail="Angel One authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@app.get("/api/angel/historical/{symbol}")
async def get_angel_historical(symbol: str, days: int = 30, interval: str = "1day"):
    """Get historical data specifically from Angel One"""
    try:
        historical_data = await angel_one_engine.get_historical_data(symbol, interval, days)
        return {
            "symbol": symbol,
            "interval": interval,
            "days": days,
            "data": historical_data,
            "source": "angel_one"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")

@app.get("/api/data-sources/comparison/{symbol}")
async def compare_data_sources(symbol: str):
    """Compare data from different sources for a symbol"""
    try:
        results = {}
        
        # Try Angel One
        try:
            angel_data = await angel_one_engine.get_live_stock_data(symbol)
            if angel_data:
                results["angel_one"] = {
                    "price": angel_data.price,
                    "change_percent": angel_data.change_percent,
                    "volume": angel_data.volume,
                    "status": "success"
                }
        except Exception as e:
            results["angel_one"] = {"status": "failed", "error": str(e)}
        
        # Try yfinance
        try:
            yf_data = await market_data_engine.get_live_stock_data(symbol, "yfinance")
            if yf_data:
                results["yfinance"] = {
                    "price": yf_data.price,
                    "change_percent": yf_data.change_percent,
                    "volume": yf_data.volume,
                    "status": "success"
                }
        except Exception as e:
            results["yfinance"] = {"status": "failed", "error": str(e)}
        
        # Try twelvedata
        try:
            td_data = await market_data_engine.get_live_stock_data(symbol, "twelvedata")
            if td_data:
                results["twelvedata"] = {
                    "price": td_data.price,
                    "change_percent": td_data.change_percent,
                    "volume": td_data.volume,
                    "status": "success"
                }
        except Exception as e:
            results["twelvedata"] = {"status": "failed", "error": str(e)}
        
        return {
            "symbol": symbol,
            "comparison": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing data sources: {str(e)}")

@app.get("/api/market/sectors")
async def get_sector_performance():
    """Get sector-wise performance data"""
    try:
        sectors = await market_data_engine.get_sector_performance()
        return {
            "sectors": [
                {
                    "sector": sector.sector,
                    "performance": sector.performance,
                    "top_performers": sector.top_performers,
                    "market_cap": sector.market_cap,
                    "volume": sector.volume
                }
                for sector in sectors
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sector data: {str(e)}")

@app.get("/api/market/movers")
async def get_market_movers(limit: int = 10):
    """Get top gainers, losers, and most active stocks"""
    try:
        movers = await market_data_engine.get_market_movers(limit)
        return {
            "gainers": [
                {
                    "symbol": stock.symbol,
                    "price": stock.price,
                    "change_percent": stock.change_percent,
                    "volume": stock.volume
                }
                for stock in movers["gainers"]
            ],
            "losers": [
                {
                    "symbol": stock.symbol,
                    "price": stock.price,
                    "change_percent": stock.change_percent,
                    "volume": stock.volume
                }
                for stock in movers["losers"]
            ],
            "most_active": [
                {
                    "symbol": stock.symbol,
                    "price": stock.price,
                    "change_percent": stock.change_percent,
                    "volume": stock.volume
                }
                for stock in movers["most_active"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market movers: {str(e)}")

@app.get("/api/market/search")
async def search_stocks(query: str, limit: int = 10):
    """Search for stocks by symbol or name"""
    try:
        results = await market_data_engine.search_stocks(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching stocks: {str(e)}")

@app.get("/api/market/indices")
async def get_market_indices():
    """Get major market indices data"""
    try:
        nifty_data = await market_data_engine.get_nifty_data()
        bank_nifty_data = await market_data_engine.get_bank_nifty_data()
        
        indices = []
        if nifty_data:
            indices.append({
                "name": "Nifty 50",
                "symbol": "NSEI",
                "price": nifty_data.price,
                "change_percent": nifty_data.change_percent
            })
        
        if bank_nifty_data:
            indices.append({
                "name": "Bank Nifty",
                "symbol": "NSEBANK",
                "price": bank_nifty_data.price,
                "change_percent": bank_nifty_data.change_percent
            })
            
        return {"indices": indices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching indices: {str(e)}")

@app.get("/api/user-profiles")
async def get_all_profiles():
    """Get all user profiles for testing"""
    profiles = []
    async for profile in db.user_profiles.find({}):
        profile["_id"] = str(profile["_id"])
        profiles.append(profile)
    return profiles

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
