import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [currentView, setCurrentView] = useState('welcome');
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState([]);
  const [userId] = useState(() => `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/questionnaire`);
      const data = await response.json();
      setQuestions(data.questions);
    } catch (error) {
      console.error('Error fetching questions:', error);
    }
  };

  const handleAnswerSelect = (answer, score) => {
    const newResponses = [...responses];
    const questionId = questions[currentQuestionIndex].id;
    
    // Update or add response
    const existingIndex = newResponses.findIndex(r => r.question_id === questionId);
    if (existingIndex >= 0) {
      newResponses[existingIndex] = { question_id: questionId, answer, score };
    } else {
      newResponses.push({ question_id: questionId, answer, score });
    }
    
    setResponses(newResponses);

    // Auto-advance to next question
    setTimeout(() => {
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        submitAssessment(newResponses);
      }
    }, 500);
  };

  const submitAssessment = async (finalResponses) => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/assess-trading-style`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          responses: finalResponses
        })
      });

      if (response.ok) {
        const result = await response.json();
        setAnalysisResult(result);
        setCurrentView('results');
      } else {
        console.error('Error submitting assessment');
      }
    } catch (error) {
      console.error('Error submitting assessment:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/dashboard/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
        setCurrentView('dashboard');
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const restartAssessment = () => {
    setCurrentView('welcome');
    setCurrentQuestionIndex(0);
    setResponses([]);
    setAnalysisResult(null);
    setDashboardData(null);
  };

  const WelcomeScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="max-w-4xl mx-auto text-center">
        <div className="mb-8">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Trade Smarter,<br />
            <span className="bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              Not Harder
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Discover your unique trading psychology and get AI-powered insights tailored to your style. 
            Join the 10% who consistently profit in the markets.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
            <div className="text-4xl mb-4">🧠</div>
            <h3 className="text-xl font-semibold text-white mb-2">AI Psychology Analysis</h3>
            <p className="text-gray-300">Understand your trading personality and behavioral patterns</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-white mb-2">Personalized Dashboard</h3>
            <p className="text-gray-300">Get insights tailored to your specific trading style</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-white mb-2">Smart Recommendations</h3>
            <p className="text-gray-300">AI-powered suggestions based on market conditions</p>
          </div>
        </div>

        <button
          onClick={() => setCurrentView('questionnaire')}
          className="bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white text-xl font-bold py-4 px-12 rounded-full transform hover:scale-105 transition-all duration-300 shadow-2xl"
        >
          Start Trading Style Assessment
        </button>

        <div className="mt-8 text-gray-400">
          <p>✨ Takes 2-3 minutes • 100% Free • Instant Results</p>
        </div>
      </div>
    </div>
  );

  const QuestionnaireScreen = () => {
    const currentQuestion = questions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

    if (!currentQuestion) return null;

    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-4">
        <div className="max-w-4xl mx-auto pt-8">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-white font-medium">Question {currentQuestionIndex + 1} of {questions.length}</span>
              <span className="text-white font-medium">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-white/20 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-green-400 to-blue-500 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Question */}
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 shadow-2xl">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-8 leading-relaxed">
              {currentQuestion.question}
            </h2>

            <div className="space-y-4">
              {currentQuestion.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswerSelect(option.text, option.score)}
                  className="w-full text-left p-4 bg-white/5 hover:bg-white/15 border border-white/10 hover:border-white/30 rounded-xl transition-all duration-300 text-white hover:scale-[1.02] transform"
                >
                  <div className="flex items-center">
                    <div className="w-6 h-6 rounded-full border-2 border-white/40 mr-4 flex-shrink-0 hover:border-white/80 transition-colors">
                      <div className="w-full h-full rounded-full bg-gradient-to-r from-blue-400 to-purple-500 opacity-0 hover:opacity-100 transition-opacity"></div>
                    </div>
                    <span className="text-lg">{option.text}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Navigation */}
          {currentQuestionIndex > 0 && (
            <div className="mt-8 text-center">
              <button
                onClick={() => setCurrentQuestionIndex(currentQuestionIndex - 1)}
                className="text-white/70 hover:text-white underline"
              >
                ← Previous Question
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  const ResultsScreen = () => {
    if (!analysisResult) return null;

    const styleEmojis = {
      scalping: "⚡",
      intraday: "📈",
      swing: "🎯",
      positional: "📊",
      delivery: "🏦",
      technical: "🔍",
      fundamental: "📋",
      momentum: "🚀"
    };

    const styleDescriptions = {
      scalping: "You thrive on quick, high-frequency trades with small profits",
      intraday: "You prefer single-day trades with moderate risk",
      swing: "You capture medium-term price movements over days/weeks",
      positional: "You hold positions for weeks to months",
      delivery: "You're a long-term investor focused on wealth building",
      technical: "You rely heavily on chart patterns and indicators",
      fundamental: "You analyze company financials and business value",
      momentum: "You follow market trends and price momentum"
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 via-teal-900 to-blue-900 p-4">
        <div className="max-w-4xl mx-auto pt-8">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="text-6xl mb-4">{styleEmojis[analysisResult.trading_style] || "📊"}</div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Your Trading Style: <span className="text-yellow-400">{analysisResult.trading_style.toUpperCase()}</span>
            </h1>
            <p className="text-xl text-gray-300 mb-4">
              {styleDescriptions[analysisResult.trading_style]}
            </p>
            <div className="bg-white/10 backdrop-blur-sm rounded-full px-6 py-2 inline-block">
              <span className="text-white font-semibold">
                Confidence: {analysisResult.style_confidence.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 mb-8 border border-white/20">
            <h3 className="text-2xl font-bold text-white mb-6 flex items-center">
              🤖 AI Personality Analysis
            </h3>
            <div className="prose prose-invert max-w-none">
              <p className="text-gray-200 text-lg leading-relaxed whitespace-pre-line">
                {analysisResult.ai_analysis}
              </p>
            </div>
          </div>

          {/* Style Scores */}
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 mb-8 border border-white/20">
            <h3 className="text-2xl font-bold text-white mb-6">📊 Your Trading Style Breakdown</h3>
            <div className="space-y-4">
              {Object.entries(analysisResult.style_scores)
                .sort(([,a], [,b]) => b - a)
                .map(([style, score]) => {
                  const percentage = (score / Math.max(...Object.values(analysisResult.style_scores))) * 100;
                  return (
                    <div key={style} className="flex items-center">
                      <div className="w-24 text-white font-medium capitalize">{style}</div>
                      <div className="flex-1 mx-4 bg-white/20 rounded-full h-3">
                        <div 
                          className="bg-gradient-to-r from-yellow-400 to-orange-500 h-3 rounded-full transition-all duration-1000"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <div className="w-16 text-white text-right">{score}</div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="text-center space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
            <button
              onClick={loadDashboard}
              disabled={loading}
              className="w-full sm:w-auto bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white font-bold py-4 px-8 rounded-full transform hover:scale-105 transition-all duration-300 shadow-xl disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'View My Dashboard 🚀'}
            </button>
            <button
              onClick={restartAssessment}
              className="w-full sm:w-auto bg-white/10 hover:bg-white/20 text-white font-bold py-4 px-8 rounded-full border border-white/30 hover:border-white/50 transition-all duration-300"
            >
              Retake Assessment
            </button>
          </div>
        </div>
      </div>
    );
  };

  const DashboardScreen = () => {
    if (!dashboardData) return null;

    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-8">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div>
                <h1 className="text-3xl font-bold mb-2">Your Trading Dashboard</h1>
                <p className="text-blue-200">
                  Style: <span className="font-semibold text-yellow-300">{dashboardData.user_profile.trading_style.toUpperCase()}</span> • 
                  Confidence: <span className="font-semibold text-yellow-300">{dashboardData.user_profile.confidence.toFixed(1)}%</span>
                </p>
                {dashboardData.last_updated && (
                  <p className="text-blue-200 text-sm mt-1">
                    🔄 Last updated: {new Date(dashboardData.last_updated).toLocaleTimeString()}
                  </p>
                )}
              </div>
              <div className="mt-4 md:mt-0 space-x-2">
                <button
                  onClick={loadDashboard}
                  className="bg-green-500 hover:bg-green-600 px-4 py-2 rounded-full font-medium transition-colors text-sm"
                >
                  🔄 Refresh Data
                </button>
                <button
                  onClick={restartAssessment}
                  className="bg-white/20 hover:bg-white/30 px-6 py-2 rounded-full font-medium transition-colors"
                >
                  New Assessment
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Market Insights */}
            <div className="lg:col-span-2">
              {/* Live Market Status */}
              <div className="bg-gradient-to-r from-green-500 to-blue-500 rounded-xl p-6 mb-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold">📊 Live Market Data</h2>
                    <p className="text-green-100">Real-time NSE/BSE feeds active</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-300 rounded-full animate-pulse"></div>
                    <span className="text-sm">LIVE</span>
                  </div>
                </div>
              </div>

              <h2 className="text-2xl font-bold text-gray-800 mb-6">🎯 AI-Powered Insights for {dashboardData.user_profile.trading_style.toUpperCase()} Style</h2>
              <div className="space-y-4">
                {dashboardData.market_insights.map((insight, index) => (
                  <div key={index} className="bg-white rounded-xl p-6 shadow-md border-l-4 border-blue-500 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-gray-700 font-medium">{insight}</p>
                        <div className="mt-2 text-sm text-gray-500">
                          📈 Optimal timeframes: {dashboardData.recommended_timeframes.join(" • ")}
                        </div>
                      </div>
                      <span className="ml-4 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                        AI Insight
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Top Stocks */}
              <h3 className="text-xl font-bold text-gray-800 mt-8 mb-4">📈 Real-Time Stock Recommendations</h3>
              <div className="bg-white rounded-xl shadow-md overflow-hidden">
                <div className="px-6 py-4 bg-gray-50 border-b">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-800">Live Prices • NSE</h4>
                    <span className="text-sm text-gray-500">Updated every 30s</span>
                  </div>
                </div>
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-500 uppercase">Symbol</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-500 uppercase">Price</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-500 uppercase">Change</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-500 uppercase">Volume</th>
                      <th className="px-6 py-3 text-left text-sm font-medium text-gray-500 uppercase">Signal</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {dashboardData.top_stocks.map((stock, index) => (
                      <tr key={index} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 font-medium text-gray-900">{stock.symbol}</td>
                        <td className="px-6 py-4 text-gray-700 font-mono">₹{stock.price}</td>
                        <td className={`px-6 py-4 font-medium font-mono ${
                          stock.change.startsWith('+') ? 'text-green-600' : 
                          stock.change.startsWith('-') ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {stock.change}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {stock.volume ? (stock.volume / 1000000).toFixed(1) + 'M' : 'N/A'}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            stock.signal === 'BUY' ? 'bg-green-100 text-green-800' :
                            stock.signal === 'SELL' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {stock.signal}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-8">
              {/* Recommendations */}
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-xl font-bold text-gray-800 mb-4">💡 Personalized Tips</h3>
                <ul className="space-y-3">
                  {dashboardData.user_profile.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-green-500 font-bold mr-2">•</span>
                      <span className="text-gray-700 text-sm">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Sector Performance */}
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                  📊 Live Sector Performance
                  <span className="ml-2 w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                </h3>
                <div className="space-y-3">
                  {dashboardData.sector_performance.map((sector, index) => (
                    <div key={index} className="flex justify-between items-center p-2 rounded hover:bg-gray-50 transition-colors">
                      <span className="text-gray-700 font-medium">{sector.sector}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`font-bold font-mono ${
                          sector.performance.startsWith('+') ? 'text-green-600' : 
                          sector.performance.startsWith('-') ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {sector.performance}
                        </span>
                        {sector.performance.startsWith('+') ? (
                          <span className="text-green-500">📈</span>
                        ) : sector.performance.startsWith('-') ? (
                          <span className="text-red-500">📉</span>
                        ) : (
                          <span className="text-gray-500">➡️</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Market Status */}
              <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl p-6 text-white">
                <h3 className="text-xl font-bold mb-4">🏛️ Market Status</h3>
                <div className="space-y-2 text-indigo-100 text-sm">
                  <div className="flex justify-between">
                    <span>NSE Status:</span>
                    <span className="text-green-300 font-semibold">OPEN</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Data Source:</span>
                    <span className="text-yellow-300">yfinance + Twelvedata</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Update Freq:</span>
                    <span className="text-blue-300">Real-time</span>
                  </div>
                </div>
              </div>

              {/* Trading Tips */}
              <div className="bg-gradient-to-br from-orange-500 to-red-600 rounded-xl p-6 text-white">
                <h3 className="text-xl font-bold mb-4">🎯 Style-Specific Tip</h3>
                <p className="text-orange-100 text-sm">
                  As a <strong>{dashboardData.user_profile.trading_style}</strong> trader, focus on your recommended timeframes: <strong>{dashboardData.recommended_timeframes[0]}</strong> to <strong>{dashboardData.recommended_timeframes[2]}</strong>. 
                  Stick to your discipline over chasing quick profits.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white text-xl">Analyzing your trading style...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {currentView === 'welcome' && <WelcomeScreen />}
      {currentView === 'questionnaire' && <QuestionnaireScreen />}
      {currentView === 'results' && <ResultsScreen />}
      {currentView === 'dashboard' && <DashboardScreen />}
    </div>
  );
}

export default App;
