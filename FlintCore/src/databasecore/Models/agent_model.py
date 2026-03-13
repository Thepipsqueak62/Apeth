from sqlalchemy import engine, Column, Integer, String

from FlintCore.src.databasecore.base import Base
class AgentModel(Base):
    __tablename__ = "agents"
    agent_id = Column(String, primary_key=True)
    ip = Column(String)
    hostname = Column(String)
    os = Column(String)
    last_seen = Column(String)

    def __repr__(self):
        return f"Agent(agent_id={self.agent_id}, ip={self.ip}, hostname={self.hostname}, os={self.os}, last_seen={self.last_seen})"