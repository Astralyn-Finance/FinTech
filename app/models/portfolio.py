from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    strategy_type = Column(String(100), nullable=True)
    risk_tolerance = Column(String(50), nullable=True)
    horizon_years = Column(Integer, nullable=True)
    status = Column(String(30), nullable=False, default="active", server_default="active")

    __table_args__ = (
        CheckConstraint("horizon_years IS NULL OR horizon_years > 0", name="ck_portfolios_horizon_positive"),
    )

    user = relationship("User", back_populates="portfolios")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")
    backtests = relationship("BacktestResult", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Portfolio id={self.id} name={self.name!r}>"


class PortfolioSnapshot(Base):
    """
    Append-only time series of portfolio-level performance metrics.
    One row per (portfolio, as_of_date) — never mutated, matching the same
    point-in-time philosophy as asset_daily_prices.
    """

    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    expected_return = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    total_value = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("portfolio_id", "as_of_date", name="uq_portfolio_snapshot_date"),
    )

    portfolio = relationship("Portfolio", back_populates="snapshots")

    def __repr__(self) -> str:
        return f"<PortfolioSnapshot portfolio_id={self.portfolio_id} as_of_date={self.as_of_date}>"


class PortfolioPosition(Base):
    """
    Target/actual weight of a single asset within a portfolio as of a date.
    sentiment_view_delta captures how much the sentiment agent's view nudged
    the weight away from the pure optimizer output (populated in a later phase).
    """

    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id", ondelete="RESTRICT"), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False)
    weight = Column(Float, nullable=False)
    sentiment_view_delta = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", "as_of_date", name="uq_portfolio_position_date"),
        CheckConstraint("weight >= 0 AND weight <= 1", name="ck_position_weight_range"),
    )

    portfolio = relationship("Portfolio", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")

    def __repr__(self) -> str:
        return f"<PortfolioPosition portfolio_id={self.portfolio_id} asset_id={self.asset_id} weight={self.weight}>"
