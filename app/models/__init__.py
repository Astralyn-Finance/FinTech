"""
Importing every model module here ensures Base.metadata is fully populated
before Alembic (or anything else) inspects it for autogenerate/create_all.
Forgetting to import a model here is the #1 cause of "migration didn't
pick up my new table" — so this file is the single source of truth for
"which models exist."
"""

from app.database import Base
from app.models.agent_log import AgentExecutionLog
from app.models.asset import Asset
from app.models.backtest import BacktestResult
from app.models.market_data import AssetDailyPrice
from app.models.news_sentiment import NewsArticle, SentimentAnalysis
from app.models.portfolio import Portfolio, PortfolioPosition, PortfolioSnapshot
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Asset",
    "Portfolio",
    "PortfolioSnapshot",
    "PortfolioPosition",
    "AssetDailyPrice",
    "NewsArticle",
    "SentimentAnalysis",
    "BacktestResult",
    "AgentExecutionLog",
]
