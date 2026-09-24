from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    source_name = Column(String(100), nullable=True)
    url = Column(String(1000), nullable=False, unique=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sentiment_records = relationship(
        "SentimentAnalysis", back_populates="article", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<NewsArticle id={self.id} title={self.title[:40]!r}>"


class SentimentAnalysis(Base):
    """
    Phase 1 (link, at ingestion time): a row is created as soon as an
    article is associated with an asset. sentiment_score, confidence_score,
    impact_rating, model_version, and scored_at are all NULL at this point —
    the row's existence records "this article is about this asset."

    Phase 2 (score, by the sentiment agent): FinBERT scores the pair and
    fills in the sentiment fields + scored_at, completing the row in place.

    This keeps "which articles map to which assets" decoupled from "has
    this pair been scored yet," so ingestion never blocks on the model.
    """

    __tablename__ = "sentiment_analysis"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False, index=True)

    sentiment_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    impact_rating = Column(String(20), nullable=True)
    model_version = Column(String(50), nullable=True)
    scored_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("article_id", "asset_id", name="uq_sentiment_article_asset"),
    )

    article = relationship("NewsArticle", back_populates="sentiment_records")
    asset = relationship("Asset", back_populates="sentiment_records")

    def __repr__(self) -> str:
        return f"<SentimentAnalysis article_id={self.article_id} asset_id={self.asset_id} scored={self.scored_at is not None}>"
