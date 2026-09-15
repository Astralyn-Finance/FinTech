from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Asset(Base):
    __tablename__ = "assets"

    # Surrogate key by design: asset_id, not ticker, is the PK/FK target
    # everywhere. Tickers get reused and change on corporate actions
    # (renames, mergers, delistings); asset_id never does.
    asset_id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True)
    asset_class = Column(String(50), nullable=False)  # e.g. equity, index, etf

    prices = relationship(
        "AssetDailyPrice", back_populates="asset", cascade="all, delete-orphan"
    )
    positions = relationship("PortfolioPosition", back_populates="asset")
    sentiment_records = relationship("SentimentAnalysis", back_populates="asset")
    backtests_as_benchmark = relationship("BacktestResult", back_populates="benchmark_asset")

    def __repr__(self) -> str:
        return f"<Asset asset_id={self.asset_id} ticker={self.ticker!r}>"
