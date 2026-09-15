from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship  # noqa: F401  (kept for consistency; no relationships yet)

from app.database.base import Base


class AgentExecutionLog(Base):
    """
    Generalized audit trail for every agent run (not just ingestion).
    No FK to a specific agent table by design — agents are code, not rows —
    session_id is the correlation key across a single orchestrated run.
    """

    __tablename__ = "agent_execution_logs"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # e.g. running, success, failed
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    execution_ms = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentExecutionLog session={self.session_id} agent={self.agent_name} status={self.status}>"
