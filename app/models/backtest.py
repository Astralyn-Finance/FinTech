from sqlalchemy import CheckConstraint, Column, Date, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    # Nullable: a backtest can run without a benchmark comparison.
    benchmark_asset_id = Column(Integer, ForeignKey("assets.asset_id", ondelete="RESTRICT"), nullable=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    cumulative_return = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_backtest_date_range"),
    )

    portfolio = relationship("Portfolio", back_populates="backtests")
    benchmark_asset = relationship("Asset", back_populates="backtests_as_benchmark")

    def __repr__(self) -> str:
        return f"<BacktestResult portfolio_id={self.portfolio_id} {self.start_date}->{self.end_date}>"
