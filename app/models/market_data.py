from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class AssetDailyPrice(Base):
    """
    Deliberately append-only. Price revisions (e.g. a provider correcting an
    OHLCV bar after the fact) are inserted as NEW rows with a later
    ingested_at, never as UPDATEs to an existing row. This is what makes
    point-in-time reconstruction possible: "what did we believe the price
    was, as of ingestion time X" is answerable by filtering on ingested_at,
    not by trusting the latest state.

    No unique constraint on (asset_id, ts) — that's intentional, multiple
    rows per (asset_id, ts) are expected over time as revisions arrive.
    """

    __tablename__ = "asset_daily_prices"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id", ondelete="RESTRICT"), nullable=False, index=True)
    ts = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    adj_close = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    source = Column(String(50), nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_asset_prices_asset_ts", "asset_id", "ts"),
        CheckConstraint("high >= low", name="ck_price_high_ge_low"),
        CheckConstraint("open >= 0 AND high >= 0 AND low >= 0 AND close >= 0", name="ck_price_nonnegative"),
    )

    asset = relationship("Asset", back_populates="prices")

    def __repr__(self) -> str:
        return f"<AssetDailyPrice asset_id={self.asset_id} ts={self.ts} close={self.close}>"
