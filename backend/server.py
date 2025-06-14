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
from emergentintegrations.llm.chat import LlmChat, UserMessage

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
DB_NAME = os.environ.get('DB_NAME')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

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

        # Initialize AI chat
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=session_id,
            system_message="""You are an expert trading psychology analyst. Analyze the user's questionnaire responses to provide:
1. A detailed personality profile for trading
2. Specific trading recommendations based on their style
3. Risk management suggestions
4. Key strengths and potential weaknesses

Be specific and actionable in your recommendations."""
        ).with_model("openai", "gpt-4o")

        user_message = UserMessage(
            text=f"""Analyze these trading questionnaire responses:

{responses_text}

Detected Primary Style: {primary_style.title()}
Confidence: {confidence:.1f}%

Provide a comprehensive analysis including:
1. Personality traits for trading
2. 5 specific actionable recommendations
3. Risk management advice
4. Potential challenges to watch for"""
        )

        ai_response = await chat.send_message(user_message)

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
    """Get personalized dashboard for user"""
    try:
        # Get user profile
        profile = await db.user_profiles.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        # Mock market data based on trading style
        trading_style = profile["trading_style"]
        
        # Generate style-specific mock data
        if trading_style == "scalping":
            mock_insights = [
                "High volatility detected in RELIANCE - potential scalping opportunity",
                "BANKNIFTY showing strong momentum in 5-min timeframe",
                "TCS breaking resistance at ₹3,450 - quick profit target ₹3,465"
            ]
            timeframes = ["1min", "5min", "15min"]
        elif trading_style == "intraday":
            mock_insights = [
                "HDFC Bank showing bullish divergence on RSI",
                "IT sector momentum building for intraday moves",
                "INFY approaching key support at ₹1,580 - watch for bounce"
            ]
            timeframes = ["5min", "15min", "1hour"]
        elif trading_style == "swing":
            mock_insights = [
                "ONGC forming bullish flag pattern - 3-5 day breakout expected", 
                "Pharma sector showing accumulation signs",
                "MARUTI testing 200-DMA support - potential swing entry"
            ]
            timeframes = ["1hour", "4hour", "1day"]
        else:
            mock_insights = [
                "Strong fundamentals detected in ICICI Bank",
                "Tech sector showing long-term growth potential",
                "Defensive stocks gaining institutional interest"
            ]
            timeframes = ["1day", "1week", "1month"]

        dashboard_data = {
            "user_profile": {
                "trading_style": profile["trading_style"],
                "confidence": profile["style_confidence"],
                "recommendations": profile["recommendations"]
            },
            "market_insights": mock_insights,
            "recommended_timeframes": timeframes,
            "top_stocks": [
                {"symbol": "RELIANCE", "price": 2456.75, "change": "+1.2%", "signal": "BUY"},
                {"symbol": "TCS", "price": 3442.30, "change": "+0.8%", "signal": "HOLD"},
                {"symbol": "HDFC", "price": 1678.90, "change": "-0.3%", "signal": "WATCH"},
                {"symbol": "INFY", "price": 1587.45, "change": "+2.1%", "signal": "BUY"}
            ],
            "sector_performance": [
                {"sector": "IT", "performance": "+1.5%"},
                {"sector": "Banking", "performance": "+0.8%"},
                {"sector": "Pharma", "performance": "-0.2%"},
                {"sector": "Auto", "performance": "+1.1%"}
            ]
        }

        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard: {str(e)}")

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
